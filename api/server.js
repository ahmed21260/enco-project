const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const admin = require('firebase-admin');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');
// 🔮 OpenAI SDK (v4)
const { OpenAI } = require('openai');

// Instance configurée une seule fois
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

/**
 * Appelle l'API OpenAI avec un prompt texte et renvoie la réponse brute.
 * Le modèle et la température peuvent être surchargés via variables d'environnement.
 */
async function callOpenAIAPI(prompt) {
  const completion = await openai.chat.completions.create({
    model: process.env.OPENAI_MODEL || 'gpt-3.5-turbo-0125',
    temperature: 0.3,
    messages: [
      { role: 'system', content: 'Tu es un assistant expert ferroviaire pour le projet ENCO.' },
      { role: 'user', content: prompt }
    ]
  });
  return completion.choices?.[0]?.message?.content?.trim() || '';
}

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: "https://enco-prestarail.web.app"
}));
app.use(express.json());

const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT
  ? JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT)
  : require('./serviceAccountKey.json'); // fallback local

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: process.env.FIREBASE_STORAGE_BUCKET || 'enco-prestarail.appspot.com'
});

const upload = multer({ storage: multer.memoryStorage() });

// Route pour récupérer les positions des opérateurs
app.get('/api/positions', (req, res) => {
    try {
        const logPath = path.join(__dirname, '../bot/positions_log.jsonl');
        
        if (!fs.existsSync(logPath)) {
            return res.json([]);
        }
        
        const data = fs.readFileSync(logPath, 'utf8');
        const positions = data.trim().split('\n')
            .filter(line => line.trim())
            .map(line => JSON.parse(line))
            .filter(pos => pos.latitude && pos.longitude);
        
        res.json(positions);
    } catch (error) {
        console.error('Erreur lecture positions:', error);
        res.status(500).json({ error: 'Erreur lecture positions' });
    }
});

// Route pour récupérer les dernières positions (pour les pings en temps réel)
app.get('/api/positions/latest', (req, res) => {
    try {
        const logPath = path.join(__dirname, '../bot/positions_log.jsonl');
        
        if (!fs.existsSync(logPath)) {
            return res.json([]);
        }
        
        const data = fs.readFileSync(logPath, 'utf8');
        const positions = data.trim().split('\n')
            .filter(line => line.trim())
            .map(line => JSON.parse(line))
            .filter(pos => pos.latitude && pos.longitude);
        
        // Grouper par opérateur et prendre la dernière position
        const latestPositions = {};
        positions.forEach(pos => {
            if (!latestPositions[pos.operateur_id] || 
                new Date(pos.timestamp) > new Date(latestPositions[pos.operateur_id].timestamp)) {
                latestPositions[pos.operateur_id] = pos;
            }
        });
        
        res.json(Object.values(latestPositions));
    } catch (error) {
        console.error('Erreur lecture dernières positions:', error);
        res.status(500).json({ error: 'Erreur lecture dernières positions' });
    }
});

// Route pour récupérer la liste des photos Telegram uploadées
app.get('/api/photos', (req, res) => {
    const logPath = path.join(__dirname, '../bot/photos_log.jsonl');
    if (!fs.existsSync(logPath)) return res.json([]);
    const data = fs.readFileSync(logPath, 'utf8');
    const photos = data.trim().split('\n')
        .filter(line => line.trim())
        .map(line => JSON.parse(line));
    res.json(photos);
});

// Route pour récupérer la liste des anomalies
app.get('/api/anomalies', (req, res) => {
    const logPath = path.join(__dirname, '../bot/photos_log.jsonl');
    if (!fs.existsSync(logPath)) return res.json([]);
    const data = fs.readFileSync(logPath, 'utf8');
    const anomalies = data.trim().split('\n')
        .filter(line => line.includes('anomalie') || line.includes('anomalies'))
        .map(line => JSON.parse(line))
        .filter(item => item.firebase_url && (item.photo_path.includes('anomalie') || item.photo_path.includes('anomalies')));
    res.json(anomalies);
});

// Route pour récupérer la liste des urgences
app.get('/api/urgences', (req, res) => {
    const logPath = path.join(__dirname, '../bot/photos_log.jsonl');
    if (!fs.existsSync(logPath)) return res.json([]);
    const data = fs.readFileSync(logPath, 'utf8');
    const urgences = data.trim().split('\n')
        .filter(line => line.includes('urgence'))
        .map(line => JSON.parse(line))
        .filter(item => item.firebase_url && (item.photo_path.includes('urgence')));
    res.json(urgences);
});

// Route pour récupérer la liste des opérateurs (depuis positions_log.jsonl)
app.get('/api/operateurs', (req, res) => {
    const logPath = path.join(__dirname, '../bot/positions_log.jsonl');
    if (!fs.existsSync(logPath)) return res.json([]);
    const data = fs.readFileSync(logPath, 'utf8');
    const operateurs = {};
    data.trim().split('\n')
        .filter(line => line.trim())
        .map(line => JSON.parse(line))
        .forEach(pos => {
            if (pos.operateur_id && pos.nom) {
                operateurs[pos.operateur_id] = { operateur_id: pos.operateur_id, nom: pos.nom };
            }
        });
    res.json(Object.values(operateurs));
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

// --------------
// 🔗 Webhook IA : analyse et priorisation des anomalies pour Firebuzz
// --------------

app.post('/webhook', async (req, res) => {
  const startTs = Date.now();
  try {
    // Sécurité : header Source obligatoire
    const sourceHeader = req.get('source') || req.get('Source') || '';
    if (sourceHeader !== 'backend-agent') {
      console.warn('🚫 Requête refusée – header Source manquant ou incorrect');
      return res.status(400).json({ error: 'Source non autorisée' });
    }

    const { input = {}, metadata = {} } = req.body || {};

    // Construction du prompt dynamique pour l'IA
    const prompt = `Tu es un assistant expert ferroviaire pour le projet ENCO.\nVoici les données reçues :\n- Messages Telegram : ${JSON.stringify(metadata.telegramMessages || [])}\n- Anomalies détectées : ${JSON.stringify(metadata.anomalies || [])}\n- Pings géolocalisés : ${JSON.stringify(metadata.pings || [])}\n- Données Firestore : ${JSON.stringify(metadata.firestoreData || {})}\n- Logique métier Highway : ${metadata.highwayLogic || ''}\n\nAnalyse ces données, puis :\n1) Classe et priorise les anomalies.\n2) Propose un résumé clair et structuré.\n3) Donne une recommandation/action rapide.\n4) Effectue une mini recherche (synthèse) sur l'anomalie la plus urgente pour aider le technicien qui la reçoit.\n\nRéponds en JSON avec ces champs :\n{\n  \"priorite\": \"Critique|Moyenne|Basse\",\n  \"resume\": \"...\",\n  \"action\": \"...\",\n  \"miniRecherche\": \"Texte explicatif pour aider le technicien\"\n}`;

    // Appel OpenAI
    const openaiResponse = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      store: true,
      temperature: 0.3,
      messages: [
        { role: 'user', content: prompt }
      ]
    });

    const content = openaiResponse.choices?.[0]?.message?.content || '';

    // Tentative de parse JSON, sinon fallback
    let parsed;
    try {
      parsed = JSON.parse(content);
      // Contrôle minimal des champs
      if (!parsed.priorite || !parsed.resume) {
        throw new Error('Champs essentiels manquants');
      }
    } catch (err) {
      console.warn('⚠️  Réponse IA non JSON ou incomplète, fallback activé');
      parsed = {
        raw: content,
        priorite: 'Indéterminée',
        action: 'Revue humaine nécessaire',
        miniRecherche: 'Veuillez consulter un expert.'
      };
    }

    console.log('✅ Analyse IA complétée en', Date.now() - startTs, 'ms');
    return res.json({ response: parsed });
  } catch (err) {
    console.error('❌ Erreur /webhook :', err);
    return res.status(500).json({ error: 'Erreur interne serveur', details: err.message });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).send('OK');
  console.log('✅ Route /health prête');
});

app.listen(PORT, () => {
    const publicUrl = process.env.PUBLIC_URL || `http://localhost:${PORT}`;
    console.log(`\n🚀 API serveur démarré sur ${publicUrl}`);
    console.log(`📡 Endpoints disponibles :
   - GET /api/positions
   - GET /api/positions/latest
   - GET /api/photos
   - GET /api/anomalies
   - GET /api/urgences
   - GET /api/operateurs
   - POST /prise-poste
   - POST /upload-photo
   - POST /upload-bon-signe
   - POST /webhook (IA)
   - GET  /health`);
});