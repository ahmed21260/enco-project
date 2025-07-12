# 🌐 Alternative ngrok (pour tests rapides)

## **Installation ngrok :**
```bash
# Windows (avec chocolatey)
choco install ngrok

# Ou télécharger depuis https://ngrok.com/
```

## **Utilisation :**

### 1. **Démarrer l'API locale**
```bash
cd api/
npm start
# API tourne sur http://localhost:3001
```

### 2. **Créer un tunnel ngrok**
```bash
ngrok http 3001
```

### 3. **Résultat :**
ngrok va te donner une URL publique comme :
```
https://abc123.ngrok.io -> http://localhost:3001
```

### 4. **Mettre à jour le bot temporairement**
Dans `bot/main.py`, change :
```python
API_URL = "https://abc123.ngrok.io"  # URL ngrok
```

## **Avantages ngrok :**
✅ Rapide à mettre en place  
✅ Pas besoin de déployer  
✅ URL publique temporaire  
✅ Parfait pour les tests  

## **Inconvénients :**
❌ URL change à chaque redémarrage  
❌ Limité en bande passante  
❌ Pas pour la production  

## **Recommandation :**
Utilise ngrok pour tester, puis déploie sur Railway pour la production ! 