const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const admin = require('firebase-admin');

const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(express.json());

const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT
  ? JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT)
  : require('./serviceAccountKey.json'); // fallback local

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: process.env.FIREBASE_STORAGE_BUCKET || 'enco-prestarail.appspot.com'
});

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

app.listen(PORT, () => {
    console.log(`🚀 API serveur démarré sur http://localhost:${PORT}`);
    console.log(`📡 Endpoints disponibles:`);
    console.log(`   - GET /api/positions (toutes les positions)`);
    console.log(`   - GET /api/positions/latest (dernières positions par opérateur)`);
    console.log(`   - GET /api/photos (liste des photos Telegram uploadées)`);
    console.log(`   - GET /api/anomalies (liste des anomalies)`);
    console.log(`   - GET /api/urgences (liste des urgences)`);
    console.log(`   - GET /api/operateurs (liste des opérateurs)`);
}); 