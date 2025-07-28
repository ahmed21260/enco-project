/**
 * Patch Dashboard ENCO - Vérification et correction
 * Vérifie la configuration Firebase, les routes et les composants
 */

import { db } from './firebaseConfig';
import { collection, getDocs, query, where, orderBy, limit } from 'firebase/firestore';

const BUCKET_CORRECT = "enco-prestarail.firebasestorage.app";
const COLLECTIONS_ATTENDUES = [
    'positions_operateurs',
    'positions_log', 
    'anomalies',
    'urgences',
    'checklists',
    'prises_poste',
    'photos',
    'operateurs',
    'bons_attachement'
];

export async function verifierConfigurationDashboard() {
    console.log("🔧 Vérification configuration dashboard...");
    
    // Vérifier la config Firebase
    const config = db.app.options;
    console.log("📦 Config Firebase:", {
        projectId: config.projectId,
        storageBucket: config.storageBucket
    });
    
    if (config.storageBucket !== BUCKET_CORRECT) {
        console.warn(`⚠️  Bucket incorrect! Attendu: ${BUCKET_CORRECT}, Actuel: ${config.storageBucket}`);
        return false;
    }
    
    console.log("✅ Configuration Firebase correcte");
    return true;
}

export async function verifierCollectionsDashboard() {
    console.log("\n📋 Vérification collections dashboard...");
    
    const stats = {};
    
    for (const collectionName of COLLECTIONS_ATTENDUES) {
        try {
            const querySnapshot = await getDocs(collection(db, collectionName));
            const count = querySnapshot.size;
            stats[collectionName] = count;
            
            console.log(`  ${count > 0 ? '✅' : '⚠️'} ${collectionName}: ${count} documents`);
            
            if (count > 0) {
                // Afficher un exemple
                const firstDoc = querySnapshot.docs[0];
                const data = firstDoc.data();
                console.log(`    Exemple: ${firstDoc.id} - ${data.timestamp || 'N/A'}`);
            }
        } catch (error) {
            console.error(`  ❌ Erreur collection ${collectionName}:`, error);
            stats[collectionName] = 0;
        }
    }
    
    return stats;
}

export async function verifierDonneesTempsReel() {
    console.log("\n🔄 Vérification données temps réel...");
    
    try {
        // Vérifier les positions actuelles
        const positionsQuery = query(
            collection(db, 'positions_operateurs'),
            orderBy('timestamp', 'desc'),
            limit(5)
        );
        const positionsSnapshot = await getDocs(positionsQuery);
        console.log(`  📍 Positions actuelles: ${positionsSnapshot.size} opérateurs`);
        
        // Vérifier les anomalies non résolues
        const anomaliesQuery = query(
            collection(db, 'anomalies'),
            where('handled', '==', false)
        );
        const anomaliesSnapshot = await getDocs(anomaliesQuery);
        console.log(`  🚨 Anomalies non résolues: ${anomaliesSnapshot.size}`);
        
        // Vérifier les urgences non résolues
        const urgencesQuery = query(
            collection(db, 'urgences'),
            where('handled', '==', false)
        );
        const urgencesSnapshot = await getDocs(urgencesQuery);
        console.log(`  🛑 Urgences non résolues: ${urgencesSnapshot.size}`);
        
        return {
            positions: positionsSnapshot.size,
            anomalies: anomaliesSnapshot.size,
            urgences: urgencesSnapshot.size
        };
    } catch (error) {
        console.error("❌ Erreur vérification temps réel:", error);
        return { positions: 0, anomalies: 0, urgences: 0 };
    }
}

export async function corrigerReferencesBucket() {
    console.log("\n🔧 Correction références bucket...");
    
    let corrections = 0;
    
    try {
        // Corriger les photos avec mauvaises URLs
        const photosSnapshot = await getDocs(collection(db, 'photos'));
        
        for (const doc of photosSnapshot.docs) {
            const data = doc.data();
            let updateNeeded = false;
            const updates = {};
            
            // Corriger les URLs de bucket
            if (data.url && !data.url.includes(BUCKET_CORRECT)) {
                updates.url = data.url.replace('default', BUCKET_CORRECT);
                updateNeeded = true;
                console.log(`  🔄 Photo ${doc.id}: ${data.url} → ${updates.url}`);
            }
            
            if (updateNeeded) {
                await doc.ref.update(updates);
                corrections++;
            }
        }
        
        console.log(`✅ ${corrections} références de bucket corrigées`);
    } catch (error) {
        console.error("❌ Erreur correction bucket:", error);
    }
    
    return corrections;
}

export async function genererRapportDashboard() {
    console.log("\n" + "="*60);
    console.log("📊 RAPPORT DASHBOARD - PATCH COMPLET");
    console.log("="*60);
    
    // 1. Vérifier la configuration
    const configOk = await verifierConfigurationDashboard();
    
    // 2. Vérifier les collections
    const statsCollections = await verifierCollectionsDashboard();
    
    // 3. Vérifier les données temps réel
    const statsTempsReel = await verifierDonneesTempsReel();
    
    // 4. Corriger les références si nécessaire
    if (configOk) {
        await corrigerReferencesBucket();
    }
    
    // 5. Générer le rapport
    console.log("\n📊 Résumé:");
    console.log(`  - Configuration: ${configOk ? '✅' : '❌'}`);
    console.log(`  - Collections avec données: ${Object.values(statsCollections).filter(c => c > 0).length}/${COLLECTIONS_ATTENDUES.length}`);
    console.log(`  - Opérateurs actifs: ${statsTempsReel.positions}`);
    console.log(`  - Anomalies en cours: ${statsTempsReel.anomalies}`);
    console.log(`  - Urgences en cours: ${statsTempsReel.urgences}`);
    
    // Actions recommandées
    console.log("\n🎯 Actions recommandées:");
    if (!configOk) {
        console.log("  - Vérifier la configuration Firebase");
    }
    
    const collectionsVides = COLLECTIONS_ATTENDUES.filter(coll => statsCollections[coll] === 0);
    if (collectionsVides.length > 0) {
        console.log(`  - Collections vides: ${collectionsVides.join(', ')}`);
    }
    
    if (statsTempsReel.positions === 0) {
        console.log("  - Aucun opérateur actif détecté");
    }
    
    console.log("\n✅ Rapport dashboard terminé!");
    
    return {
        configOk,
        statsCollections,
        statsTempsReel,
        collectionsVides
    };
}

// Fonction pour exécuter le patch complet
export async function executerPatchDashboard() {
    console.log("🚀 Démarrage du patch dashboard ENCO");
    console.log("="*50);
    
    try {
        const rapport = await genererRapportDashboard();
        return rapport;
    } catch (error) {
        console.error("❌ Erreur patch dashboard:", error);
        return null;
    }
}

// Export pour utilisation dans la console
if (typeof window !== 'undefined') {
    window.patchDashboard = executerPatchDashboard;
} 