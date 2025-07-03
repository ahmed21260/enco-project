const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const http = require('http');
const { Server } = require('socket.io');
const admin = require('firebase-admin');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');

const app = express();
const httpServer = http.createServer(app);
const io = new Server(httpServer, { cors: { origin: '*' } });

const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT
  ? JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT)
  : require('./serviceAccountKey.json'); // fallback local

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: process.env.FIREBASE_STORAGE_BUCKET || 'enco-prestarail.firebasestorage.app'
});

const db = admin.firestore();

// Socket.IO listeners: propager changements Firestore en temps réel
const watchCollection = (colName, eventName) => {
  db.collection(colName).onSnapshot((snap) => {
    snap.docChanges().forEach((change) => {
      io.emit(eventName, {
        type: change.type,
        id: change.doc.id,
        data: change.doc.data(),
      });
    });
  }, (err) => console.error(`❌ Firestore watch error on ${colName}:`, err));
};

watchCollection('positions_current', 'positions');
watchCollection('photos', 'photos');
watchCollection('anomalies', 'anomalies');

const upload = multer({ storage: multer.memoryStorage() });

// Route pour récupérer toutes les positions (historique)
app.get('/api/positions', async (req, res) => {
  try {
    const snap = await db.collection('positions_log').orderBy('timestamp', 'desc').limit(1000).get();
    const positions = snap.docs.map((d) => d.data()).filter((p) => p.latitude && p.longitude);
    res.json(positions);
  } catch (error) {
    console.error('Erreur lecture positions:', error);
    res.status(500).json({ error: 'Erreur lecture positions' });
  }
});

// Route pour récupérer les dernières positions (pour les pings en temps réel)
app.get('/api/positions/latest', async (req, res) => {
  try {
    const snap = await db.collection('positions_current').get();
    res.json(snap.docs.map((d) => d.data()));
  } catch (error) {
    console.error('Erreur lecture dernières positions:', error);
    res.status(500).json({ error: 'Erreur lecture dernières positions' });
  }
});

// Route pour récupérer la liste des photos Telegram uploadées
app.get('/api/photos', async (req, res) => {
  try {
    const snap = await db.collection('photos').orderBy('createdAt', 'desc').limit(200).get();
    res.json(snap.docs.map((d) => d.data()));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Route pour récupérer la liste des anomalies
app.get('/api/anomalies', async (req, res) => {
  try {
    const snap = await db.collection('anomalies').orderBy('timestamp', 'desc').limit(200).get();
    res.json(snap.docs.map((d) => d.data()));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Route pour récupérer la liste des urgences
app.get('/api/urgences', async (req, res) => {
  try {
    const snap = await db.collection('urgences').orderBy('timestamp', 'desc').limit(200).get();
    res.json(snap.docs.map((d) => d.data()));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Route pour récupérer la liste des opérateurs (depuis positions_log.jsonl)
app.get('/api/operateurs', async (req, res) => {
  try {
    const snap = await db.collection('operateurs').get();
    res.json(snap.docs.map((d) => ({ operateur_id: d.id, ...d.data() })));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/prise-poste', async (req, res) => {
  try {
    const {
      telegram_id, nom, pelle, parc, client, chantier, geoloc, heure
    } = req.body;
    const db = admin.firestore();
    // 1. Vérifier si l'opérateur existe
    let opSnap = await db.collection('operateurs').where('telegram_id', '==', telegram_id).limit(1).get();
    let operateurId;
    if (opSnap.empty) {
      // Créer l'opérateur
      const opRef = await db.collection('operateurs').add({
        telegram_id,
        nom: nom || '',
        actif: true,
        createdAt: new Date().toISOString()
      });
      operateurId = opRef.id;
    } else {
      operateurId = opSnap.docs[0].id;
      // Mettre à jour actif=true
      await db.collection('operateurs').doc(operateurId).update({ actif: true });
    }
    // 2. Créer la prise de poste
    const priseData = {
      operateur_id: operateurId,
      telegram_id,
      nom: nom || '',
      pelle, parc, client, chantier,
      geoloc,
      heure: heure || new Date().toISOString(),
      createdAt: new Date().toISOString()
    };
    const priseRef = await db.collection('prises_poste').add(priseData);
    res.json({ success: true, prise_poste_id: priseRef.id, operateur_id: operateurId });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/upload-photo', upload.single('photo'), async (req, res) => {
  try {
    const { telegram_id, prise_poste_id, type } = req.body;
    const file = req.file;
    if (!file) return res.status(400).json({ error: 'Aucune photo reçue' });
    const ext = file.mimetype === 'image/webp' ? 'webp' : 'jpg';
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    // Récupérer nom opérateur
    const db = admin.firestore();
    let opSnap = await db.collection('operateurs').where('telegram_id', '==', telegram_id).limit(1).get();
    let nom = 'Operateur';
    if (!opSnap.empty) nom = opSnap.docs[0].data().nom || 'Operateur';
    // Nom du fichier : Nom_YYYY-MM-DD_PriseID_Type_UUID.jpg
    const fileName = `${nom}_${dateStr}_${prise_poste_id}_${type || 'photo'}_${uuidv4()}.${ext}`.replace(/\s+/g, '_');
    const bucket = admin.storage().bucket();
    const fileRef = bucket.file(`photos/${fileName}`);
    await fileRef.save(file.buffer, { contentType: file.mimetype });
    await fileRef.makePublic();
    const url = fileRef.publicUrl();
    // Enregistrer dans Firestore
    const photoDoc = {
      url,
      operateur_id: opSnap.empty ? null : opSnap.docs[0].id,
      telegram_id,
      prise_poste_id,
      type: type || 'photo',
      createdAt: now.toISOString(),
      fileName
    };
    const docRef = await db.collection('photos').add(photoDoc);
    res.json({ success: true, url, photo_id: docRef.id });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/upload-bon-signe', upload.single('photo'), async (req, res) => {
  try {
    const { telegram_id, prise_poste_id, client, chantier } = req.body;
    const file = req.file;
    if (!file) return res.status(400).json({ error: 'Aucune photo reçue' });
    const ext = file.mimetype === 'image/webp' ? 'webp' : 'jpg';
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    // Récupérer nom opérateur
    const db = admin.firestore();
    let opSnap = await db.collection('operateurs').where('telegram_id', '==', telegram_id).limit(1).get();
    let nom = 'Operateur';
    if (!opSnap.empty) nom = opSnap.docs[0].data().nom || 'Operateur';
    // Nom du fichier : Ahmed_2025-07-03_LGV_ColasRail.jpg
    const chantierStr = chantier ? chantier.replace(/\s+/g, '') : 'Chantier';
    const clientStr = client ? client.replace(/\s+/g, '') : 'Client';
    const fileName = `${nom}_${dateStr}_${chantierStr}_${clientStr}.${ext}`.replace(/\s+/g, '_');
    const bucket = admin.storage().bucket();
    const fileRef = bucket.file(`bons_attachement/${fileName}`);
    await fileRef.save(file.buffer, { contentType: file.mimetype });
    await fileRef.makePublic();
    const url = fileRef.publicUrl();
    // Enregistrer dans Firestore
    const bonDoc = {
      url,
      operateur_id: opSnap.empty ? null : opSnap.docs[0].id,
      telegram_id,
      prise_poste_id,
      client: client || '',
      chantier: chantier || '',
      createdAt: now.toISOString(),
      fileName
    };
    const docRef = await db.collection('bons_attachement').add(bonDoc);
    res.json({ success: true, url, bon_id: docRef.id });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const payload = {
      status: 'ok',
      uptime: process.uptime(),
      timestamp: Date.now()
    };
    res.status(200).json(payload);
    console.log('✅ Health check OK', payload);
  } catch (err) {
    console.error('❌ Health check error:', err);
    res.status(500).json({ status: 'error', message: err?.message || 'unknown' });
  }
});

httpServer.listen(PORT, () => {
    console.log(`\n🚀 API + Socket.IO démarrés sur http://localhost:${PORT}`);
    console.log(`📡 Endpoints disponibles:`);
    console.log(`   - GET /api/positions (toutes les positions)`);
    console.log(`   - GET /api/positions/latest (dernières positions par opérateur)`);
    console.log(`   - GET /api/photos (liste des photos Telegram uploadées)`);
    console.log(`   - GET /api/anomalies (liste des anomalies)`);
    console.log(`   - GET /api/urgences (liste des urgences)`);
    console.log(`   - GET /api/operateurs (liste des opérateurs)`);
    console.log(`   - POST /prise-poste`);
    console.log(`   - POST /upload-photo`);
    console.log(`   - POST /upload-bon-signe`);
}); 