/**
 * Script de diagnostic et correction des problèmes de photos ENCO
 * Résout les problèmes d'affichage des images dans le dashboard
 */

import { db, storage } from './admin-dashboard/src/firebaseConfig.js';
import { collection, getDocs, updateDoc, doc } from 'firebase/firestore';
import { ref, getDownloadURL } from 'firebase/storage';

// Configuration Cloudinary
const CLOUDINARY_CLOUD_NAME = 'enco-prestarail';
const CLOUDINARY_UPLOAD_PRESET = 'enco_photos';

console.log('🔧 Démarrage du diagnostic des photos...');

/**
 * Teste l'accès aux images Cloudinary
 */
async function testCloudinaryAccess() {
  console.log('\n📸 Test d\'accès Cloudinary...');
  
  try {
    // Test d'une URL Cloudinary basique
    const testUrl = `https://res.cloudinary.com/${CLOUDINARY_CLOUD_NAME}/image/upload/v1/enco_photos/test.jpg`;
    const response = await fetch(testUrl, { method: 'HEAD' });
    
    if (response.ok) {
      console.log('✅ Accès Cloudinary OK');
      return true;
    } else {
      console.log('❌ Accès Cloudinary échoué:', response.status);
      return false;
    }
  } catch (error) {
    console.log('❌ Erreur accès Cloudinary:', error.message);
    return false;
  }
}

/**
 * Vérifie et corrige les URLs des photos dans Firestore
 */
async function checkAndFixPhotoUrls() {
  console.log('\n🔍 Vérification des URLs de photos...');
  
  try {
    const photosSnapshot = await getDocs(collection(db, 'photos'));
    let corrections = 0;
    
    for (const docSnapshot of photosSnapshot.docs) {
      const data = docSnapshot.data();
      let updateNeeded = false;
      const updates = {};
      
      // Vérifier les différents champs d'URL possibles
      const urlFields = ['url', 'urlPhoto', 'photoURL', 'photoUrl'];
      
      for (const field of urlFields) {
        if (data[field]) {
          const url = data[field];
          
          // Corriger les URLs Firebase Storage
          if (url.includes('firebasestorage.googleapis.com') && !url.includes('token=')) {
            updates[field] = url + '?alt=media';
            updateNeeded = true;
            console.log(`  🔄 Photo ${docSnapshot.id}: ${field} corrigé`);
          }
          
          // Corriger les URLs Cloudinary
          if (url.includes('cloudinary.com') && !url.includes('upload/')) {
            const publicId = url.split('/').pop();
            updates[field] = `https://res.cloudinary.com/${CLOUDINARY_CLOUD_NAME}/image/upload/v1/enco_photos/${publicId}`;
            updateNeeded = true;
            console.log(`  🔄 Photo ${docSnapshot.id}: ${field} corrigé vers Cloudinary`);
          }
        }
      }
      
      if (updateNeeded) {
        await updateDoc(docSnapshot.ref, updates);
        corrections++;
      }
    }
    
    console.log(`✅ ${corrections} URLs de photos corrigées`);
    return corrections;
  } catch (error) {
    console.error('❌ Erreur vérification URLs:', error);
    return 0;
  }
}

/**
 * Génère des URLs de test pour Cloudinary
 */
function generateTestUrls() {
  console.log('\n🧪 Génération d\'URLs de test...');
  
  const testUrls = [
    `https://res.cloudinary.com/${CLOUDINARY_CLOUD_NAME}/image/upload/v1/enco_photos/test1.jpg`,
    `https://res.cloudinary.com/${CLOUDINARY_CLOUD_NAME}/image/upload/v1/enco_photos/test2.jpg`,
    `https://res.cloudinary.com/${CLOUDINARY_CLOUD_NAME}/image/upload/v1/enco_photos/test3.jpg`
  ];
  
  console.log('URLs de test générées:');
  testUrls.forEach((url, index) => {
    console.log(`  ${index + 1}. ${url}`);
  });
  
  return testUrls;
}

/**
 * Vérifie la configuration Firebase Storage
 */
async function checkFirebaseStorage() {
  console.log('\n🔥 Vérification Firebase Storage...');
  
  try {
    // Test d'accès au bucket
    const bucketRef = ref(storage, 'test-image.jpg');
    const url = await getDownloadURL(bucketRef);
    console.log('✅ Firebase Storage accessible');
    return true;
  } catch (error) {
    console.log('❌ Firebase Storage inaccessible:', error.message);
    return false;
  }
}

/**
 * Fonction principale de diagnostic
 */
async function runDiagnostic() {
  console.log('🚀 Démarrage du diagnostic complet des photos...\n');
  
  // Tests d'accès
  const cloudinaryOk = await testCloudinaryAccess();
  const firebaseOk = await checkFirebaseStorage();
  
  // Correction des URLs
  const corrections = await checkAndFixPhotoUrls();
  
  // Génération d'URLs de test
  const testUrls = generateTestUrls();
  
  // Résumé
  console.log('\n📊 Résumé du diagnostic:');
  console.log(`  • Cloudinary: ${cloudinaryOk ? '✅ OK' : '❌ Problème'}`);
  console.log(`  • Firebase Storage: ${firebaseOk ? '✅ OK' : '❌ Problème'}`);
  console.log(`  • URLs corrigées: ${corrections}`);
  console.log(`  • URLs de test générées: ${testUrls.length}`);
  
  if (!cloudinaryOk && !firebaseOk) {
    console.log('\n⚠️  Problème critique: Aucun service de stockage accessible');
    console.log('💡 Solutions possibles:');
    console.log('  1. Vérifier la configuration Cloudinary');
    console.log('  2. Vérifier les permissions Firebase');
    console.log('  3. Utiliser un service de stockage local temporaire');
  }
  
  return {
    cloudinaryOk,
    firebaseOk,
    corrections,
    testUrls
  };
}

// Exécution du diagnostic
runDiagnostic().catch(console.error); 