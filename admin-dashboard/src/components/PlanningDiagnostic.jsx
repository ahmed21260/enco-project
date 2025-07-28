import React, { useState, useEffect } from 'react';
import { collection, getDocs, addDoc } from 'firebase/firestore';
import { db } from '../firebaseConfig';
import { generatePlanningPDF, sendPlanningPDF } from '../services/pdfGenerator';
import { sendPlanningReminder } from '../services/emailService';

const PlanningDiagnostic = () => {
  const [diagnosticResults, setDiagnosticResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const runDiagnostic = async () => {
    setLoading(true);
    const results = [];

    try {
      // Test 1: Connexion Firestore
      results.push({ test: 'Connexion Firestore', status: '⏳ Test en cours...' });
      const testCollection = await getDocs(collection(db, 'operateurs'));
      results.push({ test: 'Connexion Firestore', status: '✅ Connexion réussie', details: `${testCollection.size} opérateurs trouvés` });

      // Test 2: Collection planning
      results.push({ test: 'Collection planning', status: '⏳ Test en cours...' });
      const planningCollection = await getDocs(collection(db, 'planning'));
      results.push({ test: 'Collection planning', status: '✅ Collection accessible', details: `${planningCollection.size} entrées trouvées` });

      // Test 3: Génération PDF
      results.push({ test: 'Génération PDF', status: '⏳ Test en cours...' });
      const testData = {
        operateur: 'Test Opérateur',
        date: '2024-01-15',
        equipe: 'equipe1',
        chantier: 'Test Chantier',
        horaires: '06:00-14:00',
        instructions: 'Instructions de test'
      };
      
      const pdfDoc = await generatePlanningPDF(testData);
      results.push({ test: 'Génération PDF', status: '✅ PDF généré avec succès', details: 'Document créé' });

      // Test 4: Envoi email (simulation)
      results.push({ test: 'Envoi email', status: '⏳ Test en cours...' });
      const emailResult = await sendPlanningPDF(pdfDoc, testData);
      results.push({ test: 'Envoi email', status: '✅ Email simulé avec succès', details: emailResult.message });

      // Test 5: Ajout entrée planning
      results.push({ test: 'Ajout planning', status: '⏳ Test en cours...' });
      const newEntry = {
        operateur_id: 'test_operator',
        operateur_nom: 'Test Opérateur',
        date: new Date().toISOString().split('T')[0],
        equipe: 'equipe1',
        chantier: 'Test Chantier',
        statut: 'planifié',
        created_at: new Date().toISOString(),
        envoyé: false,
        confirmé: false
      };
      
      const docRef = await addDoc(collection(db, 'planning'), newEntry);
      results.push({ test: 'Ajout planning', status: '✅ Entrée ajoutée', details: `ID: ${docRef.id}` });

      // Test 6: Rappel email
      results.push({ test: 'Rappel email', status: '⏳ Test en cours...' });
      const reminderData = {
        operateur: 'Test Opérateur',
        date: '2024-01-15',
        equipe: 'equipe1',
        chantier: 'Test Chantier',
        horaires: '06:00-14:00'
      };
      
      await sendPlanningReminder(reminderData);
      results.push({ test: 'Rappel email', status: '✅ Rappel simulé avec succès', details: 'Email de rappel envoyé' });

    } catch (error) {
      results.push({ 
        test: 'Erreur générale', 
        status: '❌ Erreur détectée', 
        details: error.message,
        error: true 
      });
    } finally {
      setLoading(false);
    }

    setDiagnosticResults(results);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>🔧 Diagnostic du Système de Planning</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={runDiagnostic}
          disabled={loading}
          style={{
            padding: '12px 24px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '16px',
            fontWeight: 'bold'
          }}
        >
          {loading ? '🔄 Diagnostic en cours...' : '🔍 Lancer le diagnostic'}
        </button>
      </div>

      {diagnosticResults.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h3>📊 Résultats du diagnostic</h3>
          <div style={{ display: 'grid', gap: '10px' }}>
            {diagnosticResults.map((result, index) => (
              <div 
                key={index}
                style={{
                  padding: '15px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  backgroundColor: result.error ? '#ffe6e6' : '#f8f9fa',
                  borderLeft: `4px solid ${result.status.includes('✅') ? '#28a745' : result.status.includes('❌') ? '#dc3545' : '#ffc107'}`
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                  {result.test}
                </div>
                <div style={{ color: result.status.includes('✅') ? '#28a745' : result.status.includes('❌') ? '#dc3545' : '#ffc107' }}>
                  {result.status}
                </div>
                {result.details && (
                  <div style={{ marginTop: '5px', fontSize: '14px', color: '#666' }}>
                    {result.details}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: '30px', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h3>💡 Informations de débogage</h3>
        <ul style={{ lineHeight: '1.6' }}>
          <li><strong>Firebase Config:</strong> Vérifiez que firebaseConfig.js est correctement configuré</li>
          <li><strong>Dépendances:</strong> jspdf et jspdf-autotable doivent être installés</li>
          <li><strong>Collections Firestore:</strong> 'operateurs' et 'planning' doivent exister</li>
          <li><strong>Permissions:</strong> Vérifiez les règles de sécurité Firestore</li>
          <li><strong>Console:</strong> Ouvrez la console du navigateur pour voir les erreurs détaillées</li>
        </ul>
      </div>
    </div>
  );
};

export default PlanningDiagnostic; 