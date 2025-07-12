# ENCO Admin Dashboard

Dashboard web pour l'administration et la supervision en temps réel des prises de poste, anomalies, positions, etc.

## Installation

1. Placez le fichier `.env` (fourni) dans `admin-dashboard/`.
2. Installez les dépendances :
   ```bash
   npm install
   ```
3. Lancez le dashboard en local :
   ```bash
   npm run dev
   ```

## Fonctionnalités prévues
- Authentification Google (admin)
- Visualisation en temps réel des prises de poste
- Visualisation des anomalies/alertes (avec carte)
- Filtres par opérateur/machine/date
- Export CSV/PDF (à venir)
- Notifications (à venir)

## Configuration Firebase
Les variables d'environnement sont dans `.env` et utilisées dans `firebaseConfig.js`.

## Sécurité
- Seuls les comptes Google autorisés peuvent accéder au dashboard (à configurer dans Firebase Auth).
 