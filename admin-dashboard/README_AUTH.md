# Configuration de l'Authentification Firebase - ENCO Dashboard

## 🚀 Nouvelle Page de Connexion

Le dashboard ENCO dispose maintenant d'une page de connexion sécurisée avec Firebase Auth.

## 📋 Configuration Requise

### 1. Variables d'Environnement

Créez un fichier `.env` dans le dossier `admin-dashboard/` avec les variables suivantes :

```env
VITE_FIREBASE_API_KEY=your_firebase_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_FIREBASE_MEASUREMENT_ID=your_measurement_id
```

### 2. Configuration Firebase

1. Allez sur [Firebase Console](https://console.firebase.google.com/)
2. Sélectionnez votre projet ENCO
3. Dans "Authentication" > "Sign-in method"
4. Activez "Email/Password"
5. Créez un utilisateur admin :
   - Email : `admin@enco.fr`
   - Mot de passe : `Enco2024!`

## 🎨 Fonctionnalités

### Page de Connexion
- ✅ Design moderne avec animations
- ✅ Validation des champs en temps réel
- ✅ Gestion des erreurs Firebase
- ✅ Affichage/masquage du mot de passe
- ✅ Animations de particules en arrière-plan
- ✅ Responsive design

### Sécurité
- ✅ Authentification Firebase Auth
- ✅ Protection des routes
- ✅ Gestion des sessions
- ✅ Déconnexion sécurisée

### Interface Utilisateur
- ✅ Écran de chargement professionnel
- ✅ Notifications toast pour les actions
- ✅ Affichage de l'utilisateur connecté
- ✅ Bouton de déconnexion dans le header

## 🔧 Utilisation

### Démarrage
```bash
cd admin-dashboard
npm install
npm run dev
```

### Connexion
1. Ouvrez l'application dans votre navigateur
2. Entrez vos identifiants Firebase
3. Cliquez sur "Se connecter"
4. Vous serez redirigé vers le dashboard

### Déconnexion
- Cliquez sur le bouton "Déconnexion" dans le header
- Vous serez redirigé vers la page de connexion

## 🎯 Logique Métier

### Flux d'Authentification
1. **Page de Connexion** → Vérification des identifiants
2. **Écran de Chargement** → Initialisation du dashboard
3. **Dashboard** → Accès complet aux fonctionnalités
4. **Déconnexion** → Retour à la page de connexion

### Gestion d'État
- `AuthProvider` : Gère l'état global d'authentification
- `Login` : Composant de connexion
- `Dashboard` : Interface principale (inchangée)

## 🛡️ Sécurité

- Toutes les routes sont protégées
- Session persistante avec Firebase
- Validation côté client et serveur
- Gestion des erreurs d'authentification

## 📱 Responsive

- Design adaptatif pour mobile/tablette/desktop
- Animations optimisées pour les performances
- Support du mode sombre

## 🔄 Mise à Jour

Le dashboard existant n'a pas été modifié, seule la couche d'authentification a été ajoutée.

---

**Développé avec ❤️ pour ENCO par Freddy Deboves** 