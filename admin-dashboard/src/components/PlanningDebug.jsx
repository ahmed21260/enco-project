import React, { useState, useEffect } from 'react';
import { collection, getDocs, updateDoc, doc } from 'firebase/firestore';
import { db } from '../firebaseConfig';

const PlanningDebug = () => {
  const [operateurs, setOperateurs] = useState([]);
  const [planning, setPlanning] = useState([]);
  const [loading, setLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Charger les opérateurs
      const operateursSnapshot = await getDocs(collection(db, 'operateurs'));
      const operateursData = operateursSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setOperateurs(operateursData);

      // Charger le planning
      const planningSnapshot = await getDocs(collection(db, 'planning'));
      const planningData = planningSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setPlanning(planningData);

      // Analyser les données
      analyzeData(operateursData, planningData);
    } catch (error) {
      console.error('Erreur chargement données:', error);
      setDebugInfo('❌ Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const analyzeData = (operateursData, planningData) => {
    let info = '🔍 ANALYSE DES DONNÉES\n\n';
    
    // Analyser les opérateurs
    info += '📊 OPÉRATEURS:\n';
    operateursData.forEach(op => {
      const telegramId = op.telegram_id || op.telegramUserId || (op.id === op.telegram_id ? op.id : null);
      info += `- ${op.nom} (ID: ${op.id})\n`;
      info += `  telegram_id: ${op.telegram_id || 'N/A'}\n`;
      info += `  telegramUserId: ${op.telegramUserId || 'N/A'}\n`;
      info += `  ID = telegram_id: ${op.id === op.telegram_id ? 'OUI' : 'NON'}\n`;
      info += `  → Telegram ID final: ${telegramId || '❌ MANQUANT'}\n\n`;
    });

    // Analyser le planning
    info += '📅 PLANNING:\n';
    planningData.forEach(plan => {
      const operateur = operateursData.find(op => op.id === plan.operateur_id);
      const telegramId = operateur?.telegram_id || operateur?.telegramUserId || (operateur?.id === operateur?.telegram_id ? operateur?.id : null);
      
      info += `- ${plan.operateur_nom} (ID: ${plan.operateur_id})\n`;
      info += `  Opérateur trouvé: ${operateur ? 'OUI' : 'NON'}\n`;
      info += `  Telegram ID: ${telegramId || '❌ MANQUANT'}\n`;
      info += `  Envoyé Telegram: ${plan.envoyé_telegram ? 'OUI' : 'NON'}\n\n`;
    });

    setDebugInfo(info);
  };

  const fixOperateurTelegramId = async (operateurId) => {
    try {
      const operateur = operateurs.find(op => op.id === operateurId);
      if (!operateur) {
        setDebugInfo('❌ Opérateur non trouvé');
        return;
      }

      // Essayer de récupérer telegram_id
      const telegramId = operateur.telegram_id || operateur.telegramUserId || operateur.id;
      
      if (telegramId && telegramId !== operateur.telegram_id) {
        await updateDoc(doc(db, 'operateurs', operateurId), {
          telegram_id: telegramId
        });
        setDebugInfo(`✅ Telegram ID corrigé pour ${operateur.nom}: ${telegramId}`);
        loadData(); // Recharger les données
      } else {
        setDebugInfo(`ℹ️ Aucune correction nécessaire pour ${operateur.nom}`);
      }
    } catch (error) {
      console.error('Erreur correction:', error);
      setDebugInfo('❌ Erreur lors de la correction');
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>🔧 Debug Planning - Analyse des Données</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={loadData}
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
          {loading ? '🔄 Chargement...' : '🔄 Recharger les données'}
        </button>
      </div>

      {debugInfo && (
        <div style={{ 
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #dee2e6',
          borderRadius: '8px',
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace',
          fontSize: '12px'
        }}>
          {debugInfo}
        </div>
      )}

      {operateurs.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h3>🔧 Actions de correction</h3>
          <div style={{ display: 'grid', gap: '10px' }}>
            {operateurs.map(op => {
              const telegramId = op.telegram_id || op.telegramUserId || (op.id === op.telegram_id ? op.id : null);
              const needsFix = !op.telegram_id && (op.telegramUserId || op.id === op.telegram_id);
              
              return (
                <div key={op.id} style={{
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '5px',
                  backgroundColor: needsFix ? '#fff3cd' : '#f8f9fa'
                }}>
                  <strong>{op.nom}</strong> (ID: {op.id})
                  <br />
                  <small>
                    telegram_id: {op.telegram_id || 'N/A'} | 
                    telegramUserId: {op.telegramUserId || 'N/A'} | 
                    Final: {telegramId || '❌ MANQUANT'}
                  </small>
                  {needsFix && (
                    <button 
                      onClick={() => fixOperateurTelegramId(op.id)}
                      style={{
                        marginLeft: '10px',
                        padding: '5px 10px',
                        backgroundColor: '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      🔧 Corriger
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlanningDebug;