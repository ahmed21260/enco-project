# 📅 Guide d'Utilisation - Système de Planning ENCO

## 🎯 Vue d'ensemble

Le système de planning ENCO permet de gérer les affectations des opérateurs avec envoi automatique de PDF et notifications Telegram.

## 🆕 Nouvelles Fonctionnalités

### 📅 Dates de début et fin
- **Remplacement** de la date unique par une **période** (début → fin)
- **Validation automatique** : la date de début doit être antérieure à la date de fin
- **Calcul de durée** : affichage du nombre de jours de la période

### 📱 Envoi direct Telegram
- **Bouton "📱 Envoyer Telegram"** pour chaque planning
- **Message formaté** avec toutes les informations
- **Indicateur visuel** : opérateurs avec ID Telegram affichent 📱
- **Suivi des envois** : badge "✅ Telegram" après envoi

### 🏗️ Champs complets
- **Nom du chantier** : EIFFAGE-PROLIX, SPIE-THERON, COLAS-SOULAH
- **Adresse du chantier** : VILLENEUVE ST GEORGES, ARLES, TALENCE
- **Contact** : Chef de chantier avec numéro de téléphone
- **Numéro de machine** : CATM323F, CAT 323M, CAT 320

## 🚀 Comment utiliser le système

### 1. Accéder au planning
- Cliquez sur le bouton "🗓️ Planning" dans le dashboard
- Vous arrivez sur l'interface de gestion des plannings

### 2. Ajouter une affectation

#### Remplir le formulaire :
- **👤 Opérateur** : Sélectionnez l'opérateur (📱 = a un ID Telegram)
- **📅 Date de début** : Date de début de l'affectation
- **📅 Date de fin** : Date de fin de l'affectation
- **⏰ Équipe** : Équipe 1 (Matin), Équipe 2 (Après-midi), Équipe 3 (Nuit)
- **🏗️ Nom du chantier** : Ex: EIFFAGE-PROLIX A900-135406
- **📍 Adresse du chantier** : Ex: VILLENEUVE ST GEORGES
- **📞 Contact** : Ex: Chef de chantier - 01 23 45 67 89
- **🚜 Numéro de machine** : Ex: CATM323F

#### Validation :
- Tous les champs sont **obligatoires**
- La **date de début** doit être **antérieure** à la **date de fin**
- Le système affiche des **exemples** pour vous aider

### 3. Actions disponibles

#### Pour chaque planning créé :
- **📄 Générer PDF** : Crée un PDF professionnel avec toutes les informations
- **📱 Envoyer Telegram** : Envoie directement le planning à l'opérateur (si ID Telegram disponible)
- **📧 Envoyer rappel** : Envoie un rappel par email
- **✅ Badges de confirmation** : Indiquent les envois effectués

### 4. Affichage des plannings

#### Informations affichées :
- **Opérateur** et **statut** (planifié, confirmé, en cours, terminé)
- **Période** : Date début - Date fin (X jours)
- **Équipe** et **horaires**
- **Chantier**, **adresse**, **contact**, **machine**
- **Actions** disponibles selon l'état

## 🔧 Outils de diagnostic

### 🔧 Diagnostic Planning
- **Bouton "🔧 Diagnostic Planning"** dans le dashboard
- **Tests automatiques** de toutes les fonctionnalités
- **Rapport détaillé** des erreurs et succès
- **Vérification** : Firestore, PDF, Email, Telegram

### 🧪 Test Nouvelles Fonctionnalités
- **Bouton "🧪 Test Nouvelles Fonctionnalités"** dans le dashboard
- **Tests spécifiques** des nouvelles features
- **Validation** des dates début/fin
- **Test** de l'envoi Telegram

## 📊 Exemples d'utilisation

### Exemple 1 : Planning standard
```
Opérateur : Jean Dupont (📱)
Période : 15/01/2024 - 20/01/2024 (6 jours)
Équipe : Équipe 1 - Matin (06:00-14:00)
Chantier : EIFFAGE-PROLIX A900-135406
Adresse : VILLENEUVE ST GEORGES
Contact : Chef de chantier - 01 23 45 67 89
Machine : CATM323F
```

### Exemple 2 : Planning avec envoi Telegram
1. Créer le planning avec les informations complètes
2. Cliquer sur "📱 Envoyer Telegram"
3. Le message est envoyé directement à l'opérateur
4. Badge "✅ Telegram" apparaît

## ⚠️ Résolution des problèmes

### Erreur "process is not defined"
- ✅ **Corrigé** : Utilisation de `import.meta.env` au lieu de `process.env`
- Le système fonctionne maintenant sans erreur

### Opérateur sans ID Telegram
- L'opérateur n'affiche pas 📱 dans la liste
- Le bouton "📱 Envoyer Telegram" n'apparaît pas
- Utilisez uniquement "📄 Générer PDF"

### Validation des dates
- **Erreur** : "La date de début doit être antérieure à la date de fin"
- **Solution** : Vérifiez l'ordre des dates dans le formulaire

### PDF non généré
- Vérifiez que tous les champs sont remplis
- Utilisez le "🔧 Diagnostic Planning" pour identifier le problème

## 🎨 Interface utilisateur

### Couleurs et indicateurs :
- **🟢 Vert** : Succès, confirmé
- **🔵 Bleu** : Planifié, en cours
- **🟡 Jaune** : Avertissement
- **🔴 Rouge** : Erreur, terminé
- **📱** : Opérateur avec ID Telegram

### Boutons d'action :
- **📄 Générer PDF** : Bleu
- **📱 Envoyer Telegram** : Bleu Telegram
- **📧 Envoyer rappel** : Gris
- **✅ Badges** : Vert pour confirmé

## 🔮 Fonctionnalités futures

### Intégrations prévues :
- **API Telegram réelle** (remplacer la simulation)
- **Notifications push** sur mobile
- **Calendrier interactif** pour visualiser les plannings
- **Synchronisation** avec d'autres systèmes

### Améliorations possibles :
- **Templates personnalisables** pour les PDF
- **Historique des modifications** des plannings
- **Statistiques** d'utilisation et de performance
- **Export Excel** des plannings

---

## 📞 Support

Pour toute question ou problème :
1. Utilisez le "🔧 Diagnostic Planning"
2. Vérifiez la console du navigateur
3. Contactez l'équipe technique

**Système ENCO - Version 2.0** 🚀 