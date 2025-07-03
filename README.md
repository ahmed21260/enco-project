# 🚀 ENCO - Système de Gestion Opérateurs

## 📋 Description
Système complet de gestion de prise de poste, suivi machine et traçabilité opérateur via Telegram, QR codes, et dashboard admin en temps réel.

## 🏗️ Architecture

### 📱 Bot Telegram
- **Prise/Fin de poste** avec géolocalisation
- **Checklist sécurité** automatisée
- **Signalement d'anomalies** avec photos
- **Consultation documents** machine
- **Urgences** et mise hors voie
- **Portails SNCF** et contacts

### 🖥️ Dashboard Admin
- **Carte interactive** avec pings opérateurs en temps réel
- **Historique** des actions et positions
- **Documents** et guides machines
- **Statistiques** et métriques

### 🔧 API Backend
- **Serveur Node.js** pour exposer les données
- **Logs positions** en JSONL pour exploitation
- **Endpoints REST** pour le dashboard

## 🚀 Installation et Démarrage

### 1. **Prérequis**
```bash
# Node.js 18+ et Python 3.8+
npm install -g nodemon
pip install python-telegram-bot python-dotenv
```

### 2. **Configuration**
```bash
# Copier le logo ENCO
cp votre-logo.png admin-dashboard/public/photos/logo-enco.png

# Configurer le token Telegram
echo "TELEGRAM_TOKEN=votre_token_ici" > bot/.env
```

### 3. **Installation des dépendances**
```bash
# API Backend
cd api
npm install

# Dashboard React
cd ../admin-dashboard
npm install --legacy-peer-deps
```

### 4. **Démarrage du système**

#### Terminal 1 - API Backend
```bash
cd api
npm start
# Serveur accessible sur http://localhost:3001
```

#### Terminal 2 - Dashboard Admin
```bash
cd admin-dashboard
npm run dev
# Dashboard accessible sur http://localhost:5173
```

#### Terminal 3 - Bot Telegram
```bash
cd bot
python main.py
# Bot actif sur Telegram
```

## 📱 Utilisation du Bot Telegram

### Commandes principales
- `/start` - Menu principal et guide
- `/prise` - Prise de poste (géolocalisation)
- `/fin` - Fin de poste (géolocalisation)
- `/checklist` - Checklist sécurité
- `/anomalie` - Signaler une anomalie
- `/docs` - Consulter documents
- `/historique` - Voir l'historique
- `/aide` - Aide complète

### Boutons du menu
- **Envoyer une photo** - Signalement avec photo
- **Partager ma position** - Géolocalisation
- **Checklist sécurité** - Vérification pré-démarrage
- **Déclencher une urgence** - Alerte immédiate
- **Mise hors voie urgente** - Évacuation
- **Portail d'accès SNCF** - Contacts et portails
- **Fiches techniques** - Documents machines
- **Historique** - Actions passées
- **Paramètres** - Configuration

## 🗺️ Dashboard Admin

### Fonctionnalités
- **Carte interactive** avec pings opérateurs en temps réel
- **Historique** avec filtres par opérateur/date
- **Documents** par machine (CAT 323 M, D2R, ATLAS 1404, MECALAC)
- **Statistiques** en temps réel (opérateurs en ligne, prises de poste, anomalies)

### Navigation
- **Sidebar** avec logo ENCO et navigation
- **Header** avec statut système et actualisation
- **Contenu** adaptatif selon la section

## 📊 Données et Logs

### Fichiers de données
- `bot/positions_log.jsonl` - Positions des opérateurs
- `bot/checklists_temp.json` - Checklists sécurité
- `bot/positions_temp.json` - Positions temporaires

### API Endpoints
- `GET /api/positions` - Toutes les positions
- `GET /api/positions/latest` - Dernières positions par opérateur

## 🔧 Configuration Avancée

### Variables d'environnement
```bash
# bot/.env
TELEGRAM_TOKEN=votre_token_telegram
FIREBASE_CREDENTIALS=../firebase/serviceAccountKey.json

# api/.env (optionnel)
PORT=3001
```

### Personnalisation
- **Logo** : Remplacer `admin-dashboard/public/photos/logo-enco.png`
- **Couleurs** : Modifier `admin-dashboard/src/components/Dashboard.css`
- **Machines** : Ajouter dans `bot/handlers/consult_docs.py`

## 🚨 Urgences et Sécurité

### Procédures d'urgence
1. **Déclencher une urgence** - Alerte immédiate encadrement
2. **Mise hors voie urgente** - Évacuation immédiate
3. **Contacts SNCF** - 3635 pour assistance

### Logs de sécurité
- Toutes les positions d'urgence sont loggées
- Historique complet des actions
- Traçabilité opérateur/machine/temps

## 📈 Évolutions Futures

### Phase 2 - IA et Automatisation
- Détection automatique photos manquantes/floues
- Suggestions maintenance préventive
- Résumé automatique anomalies
- Génération rapports PDF/Excel

### Phase 3 - Intégrations
- Firebase/Google Drive pour stockage cloud
- QR codes par machine
- Notifications push
- Export données avancé

## 🆘 Support

### Problèmes courants
- **Bot ne répond pas** : Vérifier le token dans `bot/.env`
- **Carte ne se charge pas** : Démarrer l'API backend
- **Erreurs npm** : Utiliser `--legacy-peer-deps`

### Logs et Debug
- Console du bot : `python main.py`
- Console API : `npm start`
- Console Dashboard : `npm run dev`

---

**ENCO - Système de Gestion Opérateurs**  
*Version 1.0 - Prêt pour démo*
