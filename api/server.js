const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const admin = require('firebase-admin');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: ["https://enco-prestarail.web.app", "http://localhost:3000", "http://localhost:5173"]
}));
app.use(express.json());

const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT
  ? JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT)
  : require('./serviceAccountKey.json'); // fallback local

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: process.env.FIREBASE_STORAGE_BUCKET || 'enco-prestarail.firebasestorage.app'
});

const db = admin.firestore();
const upload = multer({ storage: multer.memoryStorage() });

// Healthcheck pour Railway
app.get('/', (req, res) => {
  res.json({ 
    status: 'OK', 
    message: 'ENCO API Server', 
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Route pour récupérer les positions des opérateurs (depuis Firestore)
app.get('/api/positions', async (req, res) => {
    try {
        const positionsSnapshot = await db.collection('positions_operateurs').get();
        const positions = [];
        
        positionsSnapshot.forEach(doc => {
            const data = doc.data();
            if (data.latitude && data.longitude) {
                positions.push({
                    id: doc.id,
                    ...data
                });
            }
        });
        
        res.json(positions);
    } catch (error) {
        console.error('Erreur lecture positions:', error);
        res.status(500).json({ error: 'Erreur lecture positions' });
    }
});

// Route pour récupérer les dernières positions (pour les pings en temps réel)
app.get('/api/positions/latest', async (req, res) => {
    try {
        const positionsSnapshot = await db.collection('positions_operateurs').get();
        const positions = [];
        
        positionsSnapshot.forEach(doc => {
            const data = doc.data();
            if (data.latitude && data.longitude) {
                positions.push({
                    id: doc.id,
                    ...data
                });
            }
        });
        
        res.json(positions);
    } catch (error) {
        console.error('Erreur lecture dernières positions:', error);
        res.status(500).json({ error: 'Erreur lecture dernières positions' });
    }
});

// Route pour récupérer la liste des anomalies (depuis Firestore)
app.get('/api/anomalies', async (req, res) => {
    try {
        const anomaliesSnapshot = await db.collection('anomalies').get();
        const anomalies = [];
        
        anomaliesSnapshot.forEach(doc => {
            anomalies.push({
                id: doc.id,
                ...doc.data()
            });
        });
        
        res.json(anomalies);
    } catch (error) {
        console.error('Erreur lecture anomalies:', error);
        res.status(500).json({ error: 'Erreur lecture anomalies' });
    }
});

// Route pour récupérer la liste des urgences (depuis Firestore)
app.get('/api/urgences', async (req, res) => {
    try {
        const urgencesSnapshot = await db.collection('urgences').get();
        const urgences = [];
        
        urgencesSnapshot.forEach(doc => {
            urgences.push({
                id: doc.id,
                ...doc.data()
            });
        });
        
        res.json(urgences);
    } catch (error) {
        console.error('Erreur lecture urgences:', error);
        res.status(500).json({ error: 'Erreur lecture urgences' });
    }
});

// Route pour récupérer la liste des opérateurs (depuis Firestore)
app.get('/api/operateurs', async (req, res) => {
    try {
        const operateursSnapshot = await db.collection('operateurs').get();
        const operateurs = [];
        
        operateursSnapshot.forEach(doc => {
            operateurs.push({
                id: doc.id,
                ...doc.data()
            });
        });
        
        res.json(operateurs);
    } catch (error) {
        console.error('Erreur lecture operateurs:', error);
        res.status(500).json({ error: 'Erreur lecture operateurs' });
    }
});

// Route pour récupérer les prises de poste (depuis Firestore)
app.get('/api/prises-poste', async (req, res) => {
    try {
        const prisesSnapshot = await db.collection('prises_poste').get();
        const prises = [];
        
        prisesSnapshot.forEach(doc => {
            prises.push({
                id: doc.id,
                ...doc.data()
            });
        });
        
        res.json(prises);
    } catch (error) {
        console.error('Erreur lecture prises de poste:', error);
        res.status(500).json({ error: 'Erreur lecture prises de poste' });
    }
});

// Route pour récupérer les messages IA (depuis Firestore)
app.get('/api/messages-ia', async (req, res) => {
    try {
        const messagesSnapshot = await db.collectionGroup('messages').get();
        const messages = [];
        
        messagesSnapshot.forEach(doc => {
            messages.push({
                id: doc.id,
                ...doc.data()
            });
        });
        
        res.json(messages);
    } catch (error) {
        console.error('Erreur lecture messages IA:', error);
        res.status(500).json({ error: 'Erreur lecture messages IA' });
    }
});

app.post('/prise-poste', async (req, res) => {
  try {
    const {
      telegram_id, nom, pelle, parc, client, chantier, geoloc, heure
    } = req.body;
    
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
      fileName,
      createdAt: new Date().toISOString()
    };
    
    await db.collection('photos').add(photoDoc);
    res.json({ success: true, url, fileName });
  } catch (e) {
    console.error('Erreur upload photo:', e);
    res.status(500).json({ error: e.message });
  }
});

// Route pour récupérer la liste des bons d'attachement
app.get('/api/bons-attachement', async (req, res) => {
    try {
        const bonsSnapshot = await db.collection('bons_attachement').get();
        const bons = [];
        bonsSnapshot.forEach(doc => {
            bons.push({ id: doc.id, ...doc.data() });
        });
        res.json(bons);
    } catch (error) {
        console.error('Erreur lecture bons d\'attachement:', error);
        res.status(500).json({ error: 'Erreur lecture bons d\'attachement' });
    }
});

// Route pour récupérer la liste des alertes
app.get('/api/alertes', async (req, res) => {
    try {
        const alertesSnapshot = await db.collection('alertes').get();
        const alertes = [];
        alertesSnapshot.forEach(doc => {
            alertes.push({ id: doc.id, ...doc.data() });
        });
        res.json(alertes);
    } catch (error) {
        console.error('Erreur lecture alertes:', error);
        res.status(500).json({ error: 'Erreur lecture alertes' });
    }
});

// Route pour récupérer la liste des scans QR
app.get('/api/scans-qr', async (req, res) => {
    try {
        const scansSnapshot = await db.collection('scans_qr').get();
        const scans = [];
        scansSnapshot.forEach(doc => {
            scans.push({ id: doc.id, ...doc.data() });
        });
        res.json(scans);
    } catch (error) {
        console.error('Erreur lecture scans QR:', error);
        res.status(500).json({ error: 'Erreur lecture scans QR' });
    }
});

// Route pour récupérer la liste des tickets de maintenance
app.get('/api/maintenance-issues', async (req, res) => {
    try {
        const issuesSnapshot = await db.collection('maintenance_issues').get();
        const issues = [];
        issuesSnapshot.forEach(doc => {
            issues.push({ id: doc.id, ...doc.data() });
        });
        res.json(issues);
    } catch (error) {
        console.error('Erreur lecture maintenance issues:', error);
        res.status(500).json({ error: 'Erreur lecture maintenance issues' });
    }
});

// Route pour récupérer la liste des actions géoportail
app.get('/api/actions-geoportail', async (req, res) => {
    try {
        const actionsSnapshot = await db.collection('actions_geoportail').get();
        const actions = [];
        actionsSnapshot.forEach(doc => {
            actions.push({ id: doc.id, ...doc.data() });
        });
        res.json(actions);
    } catch (error) {
        console.error('Erreur lecture actions geoportail:', error);
        res.status(500).json({ error: 'Erreur lecture actions geoportail' });
    }
});

// Route pour récupérer la liste des rapports techniques
app.get('/api/rapports-techniques', async (req, res) => {
    try {
        const rapportsSnapshot = await db.collection('rapports_techniques').get();
        const rapports = [];
        rapportsSnapshot.forEach(doc => {
            rapports.push({ id: doc.id, ...doc.data() });
        });
        res.json(rapports);
    } catch (error) {
        console.error('Erreur lecture rapports techniques:', error);
        res.status(500).json({ error: 'Erreur lecture rapports techniques' });
    }
});

// Route pour récupérer la liste des consultations de planning
app.get('/api/consultations-planning', async (req, res) => {
    try {
        const consultationsSnapshot = await db.collection('consultations_planning').get();
        const consultations = [];
        consultationsSnapshot.forEach(doc => {
            consultations.push({ id: doc.id, ...doc.data() });
        });
        res.json(consultations);
    } catch (error) {
        console.error('Erreur lecture consultations planning:', error);
        res.status(500).json({ error: 'Erreur lecture consultations planning' });
    }
});

// Route pour récupérer la liste des plannings opérateurs
app.get('/api/plannings-operateurs', async (req, res) => {
    try {
        const planningsSnapshot = await db.collection('plannings_operateurs').get();
        const plannings = [];
        planningsSnapshot.forEach(doc => {
            plannings.push({ id: doc.id, ...doc.data() });
        });
        res.json(plannings);
    } catch (error) {
        console.error('Erreur lecture plannings opérateurs:', error);
        res.status(500).json({ error: 'Erreur lecture plannings opérateurs' });
    }
});

// Route pour récupérer la liste des envois de planning
app.get('/api/envois-planning', async (req, res) => {
    try {
        const envoisSnapshot = await db.collection('envois_planning').get();
        const envois = [];
        envoisSnapshot.forEach(doc => {
            envois.push({ id: doc.id, ...doc.data() });
        });
        res.json(envois);
    } catch (error) {
        console.error('Erreur lecture envois planning:', error);
        res.status(500).json({ error: 'Erreur lecture envois planning' });
    }
});

// Affichage dynamique de toutes les routes disponibles (compatibilité Railway)
try {
    const listEndpoints = require('express-list-endpoints');
    const endpoints = listEndpoints(app);
    console.log('📚 Toutes les routes disponibles :');
    endpoints.forEach(route => {
        console.log(`${route.methods.join(', ')} ${route.path}`);
    });
} catch (e) {
    console.warn('express-list-endpoints non installé, routes non listées dynamiquement.');
}

app.listen(PORT, () => {
  console.log(`🚀 ENCO API Server démarré sur le port ${PORT}`);
  console.log(`📊 Healthcheck: http://localhost:${PORT}/`);
  console.log(`🗺️ Positions: http://localhost:${PORT}/api/positions`);
  console.log(`🚨 Anomalies: http://localhost:${PORT}/api/anomalies`);
  console.log(`🚨 Urgences: http://localhost:${PORT}/api/urgences`);
  console.log(`👥 Opérateurs: http://localhost:${PORT}/api/operateurs`);
}); 