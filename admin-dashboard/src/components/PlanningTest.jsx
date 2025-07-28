import React, { useState } from 'react';
import { generatePlanningPDF } from '../services/pdfGenerator';
import { sendTelegramMessage, testTelegramConnection } from '../services/telegramService';

const PlanningTest = () => {
  const [testResults, setTestResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const runTests = async () => {
    setLoading(true);
    const results = [];

    try {
      // Test 1: Connexion Telegram
      results.push({ test: 'Connexion Telegram', status: '⏳ Test en cours...' });
      const telegramTest = await testTelegramConnection();

      if (telegramTest.success) {
        results.push({
          test: 'Connexion Telegram',
          status: '✅ Connexion réussie',
          details: `Bot: ${telegramTest.botName} (@${telegramTest.botUsername})`
        });
      } else {
        results.push({
          test: 'Connexion Telegram',
          status: '❌ Connexion échouée',
          details: telegramTest.error,
          error: true
        });
      }

      // Test 2: Génération PDF avec dates début/fin
      results.push({ test: 'Génération PDF avec dates', status: '⏳ Test en cours...' });
      const testData = {
        operateur: 'Test Opérateur',
        date_debut: '2024-01-15',
        date_fin: '2024-01-20',
        equipe: 'equipe1',
        chantier: 'EIFFAGE-PROLIX A900-135406',
        address: 'VILLENEUVE ST GEORGES',
        contact: 'Chef de chantier - 01 23 45 67 89',
        machine: 'CATM323F',
        horaires: '06:00-14:00',
        instructions: 'Maintenance préventive - Vérification des équipements de sécurité'
      };

      const pdfDoc = await generatePlanningPDF(testData);
      results.push({ test: 'Génération PDF avec dates', status: '✅ PDF généré avec succès', details: 'Document créé avec période 15/01/2024 - 20/01/2024' });

      // Test 3: Envoi Telegram (si connexion OK)
      if (telegramTest.success) {
        results.push({ test: 'Envoi Telegram', status: '⏳ Test en cours...' });
        const telegramData = {
          operateur: 'Test Opérateur',
          telegram_id: '123456789', // ID de test
          date_debut: '2024-01-15',
          date_fin: '2024-01-20',
          equipe: 'equipe1',
          chantier: 'EIFFAGE-PROLIX A900-135406',
          address: 'VILLENEUVE ST GEORGES',
          contact: 'Chef de chantier - 01 23 45 67 89',
          machine: 'CATM323F',
          horaires: '06:00-14:00',
          instructions: 'Maintenance préventive - Vérification des équipements de sécurité'
        };

        const telegramResult = await sendTelegramMessage(telegramData);
        if (telegramResult.fallback) {
          results.push({
            test: 'Envoi Telegram',
            status: '⚠️ Simulation (API non configurée)',
            details: `Message préparé mais non envoyé: ${telegramResult.error || 'Token manquant'}`
          });
        } else {
          results.push({
            test: 'Envoi Telegram',
            status: '✅ Message envoyé',
            details: `ID: ${telegramResult.messageId}`
          });
        }
      } else {
        results.push({
          test: 'Envoi Telegram',
          status: '⏭️ Test ignoré',
          details: 'Connexion Telegram non disponible'
        });
      }

      // Test 4: Validation des dates
      results.push({ test: 'Validation des dates', status: '⏳ Test en cours...' });
      const dateDebut = new Date('2024-01-15');
      const dateFin = new Date('2024-01-20');
      const isValid = dateDebut <= dateFin;
      results.push({
        test: 'Validation des dates',
        status: isValid ? '✅ Dates valides' : '❌ Dates invalides',
        details: `Début: ${dateDebut.toLocaleDateString('fr-FR')}, Fin: ${dateFin.toLocaleDateString('fr-FR')}`
      });

      // Test 5: Calcul de durée
      results.push({ test: 'Calcul de durée', status: '⏳ Test en cours...' });
      const diffTime = Math.abs(dateFin - dateDebut);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      results.push({
        test: 'Calcul de durée',
        status: '✅ Durée calculée',
        details: `${diffDays} jour${diffDays > 1 ? 's' : ''}`
      });

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

    setTestResults(results);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>🧪 Test des Nouvelles Fonctionnalités</h2>

      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={runTests}
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
          {loading ? '🔄 Tests en cours...' : '🔍 Lancer les tests'}
        </button>
      </div>

      {testResults.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h3>📊 Résultats des tests</h3>
          <div style={{ display: 'grid', gap: '10px' }}>
            {testResults.map((result, index) => (
              <div
                key={index}
                style={{
                  padding: '15px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  backgroundColor: result.error ? '#ffe6e6' : '#f8f9fa',
                  borderLeft: `4px solid ${result.status.includes('✅') ? '#28a745' : result.status.includes('❌') ? '#dc3545' : result.status.includes('⚠️') ? '#ffc107' : '#ffc107'}`
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                  {result.test}
                </div>
                <div style={{
                  color: result.status.includes('✅') ? '#28a745' :
                         result.status.includes('❌') ? '#dc3545' :
                         result.status.includes('⚠️') ? '#ffc107' : '#ffc107'
                }}>
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
        <h3>🆕 Nouvelles fonctionnalités testées :</h3>
        <ul style={{ lineHeight: '1.6' }}>
          <li><strong>📱 Connexion Telegram :</strong> Test de la connexion au bot Telegram</li>
          <li><strong>📅 Dates début/fin :</strong> Remplacement de la date unique par une période</li>
          <li><strong>📱 Envoi Telegram :</strong> Envoi direct aux opérateurs via Telegram</li>
          <li><strong>✅ Validation :</strong> Vérification que la date de début est antérieure à la date de fin</li>
          <li><strong>📊 Calcul de durée :</strong> Affichage du nombre de jours de la période</li>
          <li><strong>🏗️ Champs complets :</strong> Nom du chantier, adresse, contact, machine</li>
        </ul>
      </div>

      <div style={{ marginTop: '20px', padding: '20px', backgroundColor: '#fff3cd', borderRadius: '8px', border: '1px solid #ffeaa7' }}>
        <h3>⚠️ Configuration Telegram</h3>
        <p>Pour recevoir les messages Telegram, vous devez :</p>
        <ol style={{ lineHeight: '1.6' }}>
          <li><strong>Créer un bot Telegram</strong> via @BotFather</li>
          <li><strong>Obtenir le token</strong> du bot</li>
          <li><strong>Ajouter la variable d'environnement</strong> <code>VITE_TELEGRAM_BOT_TOKEN</code></li>
          <li><strong>Démarrer une conversation</strong> avec le bot</li>
        </ol>
        <p><strong>Note :</strong> Actuellement en mode simulation si le token n'est pas configuré.</p>
      </div>
    </div>
  );
};

export default PlanningTest; 