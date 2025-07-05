import React, { useState, useEffect } from 'react';
import { collection, onSnapshot, query, orderBy } from 'firebase/firestore';
import { db } from '../../firebaseConfig';
import './OutilsFerroviaires.css';

const OutilsFerroviaires = () => {
  const [rapports, setRapports] = useState([]);
  const [actionsGeoportail, setActionsGeoportail] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('outils');

  useEffect(() => {
    setLoading(true);
    
    // Rapports techniques
    const qRapports = query(collection(db, 'rapports_techniques'), orderBy('timestamp', 'desc'));
    const unsubscribeRapports = onSnapshot(qRapports, (snapshot) => {
      const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setRapports(data);
      setLoading(false);
      setError(null);
    }, (err) => {
      setError('Erreur lors du chargement des rapports techniques');
      setLoading(false);
    });

    // Actions géoportail
    const qGeoportail = query(collection(db, 'actions_geoportail'), orderBy('timestamp', 'desc'));
    const unsubscribeGeoportail = onSnapshot(qGeoportail, (snapshot) => {
      const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setActionsGeoportail(data);
    });

    return () => {
      unsubscribeRapports();
      unsubscribeGeoportail();
    };
  }, []);

  const formatDate = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString('fr-FR');
    } catch (e) {
      return 'Date invalide';
    }
  };

  const Tabs = ({ tabs, active, onChange }) => (
    <div style={{display:'flex', gap:8, margin:'8px 0'}}>
      {tabs.map(tab => (
        <button key={tab} onClick={() => onChange(tab)} style={{
          background: active === tab ? '#1976d2' : '#eee',
          color: active === tab ? '#fff' : '#333',
          border: 'none', borderRadius: 6, padding: '4px 14px', cursor: 'pointer', fontWeight: 600
        }}>{tab}</button>
      ))}
    </div>
  );

  if (loading) {
    return (
      <div className="outils-container">
        <div className="loading">🔄 Chargement des outils ferroviaires...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="outils-container">
        <div className="error">❌ {error}</div>
      </div>
    );
  }

  return (
    <div className="outils-container">
      <div className="outils-header">
        <h2>🗺️ Outils Ferroviaires ENCO</h2>
        <div className="stats">
          <span>📋 {rapports.length} rapport(s) technique(s)</span>
          <span style={{marginLeft: '20px'}}>📍 {actionsGeoportail.length} action(s) géoportail</span>
        </div>
      </div>

      <Tabs tabs={['Outils', 'Rapports techniques', 'Actions géoportail']} active={activeTab} onChange={setActiveTab} />

      {activeTab === 'Outils' && (
        <div className="outils-grid">
          <div className="outil-card">
            <h3>📍 Géoportail SNCF</h3>
            <p>Accès aux portails SNCF les plus proches selon votre position GPS</p>
            <div className="outil-links">
              <a href="https://www.sncf.com/geoportail" target="_blank" rel="noopener noreferrer">
                🌐 Géoportail SNCF
              </a>
            </div>
          </div>

          <div className="outil-card">
            <h3>📘 Règlement Sécurité</h3>
            <p>Règlement sécurité ENCO/SNCF et procédures obligatoires</p>
            <div className="outil-links">
              <a href="https://enco-docs.com/reglement-securite" target="_blank" rel="noopener noreferrer">
                📘 Règlement ENCO
              </a>
              <a href="https://sncf.com/procedures-securite" target="_blank" rel="noopener noreferrer">
                🚨 Procédures SNCF
              </a>
            </div>
          </div>

          <div className="outil-card">
            <h3>📄 Procédures d'urgence</h3>
            <p>Procédures d'évacuation, choc électrique, incendie</p>
            <div className="outil-links">
              <a href="https://enco-docs.com/evacuation" target="_blank" rel="noopener noreferrer">
                📄 Évacuation
              </a>
              <a href="https://enco-docs.com/choc-electrique" target="_blank" rel="noopener noreferrer">
                ⚡ Choc électrique
              </a>
              <a href="https://enco-docs.com/incendie" target="_blank" rel="noopener noreferrer">
                🔥 Incendie
              </a>
            </div>
          </div>

          <div className="outil-card">
            <h3>📦 Fiche Chantier</h3>
            <p>Dernière version de la fiche chantier ENCO v3.2</p>
            <div className="outil-links">
              <a href="https://enco-docs.com/fiche-chantier-v3.2" target="_blank" rel="noopener noreferrer">
                📦 Fiche chantier v3.2
              </a>
              <a href="https://enco-docs.com/plan-intervention" target="_blank" rel="noopener noreferrer">
                📊 Plan d'intervention
              </a>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'Rapports techniques' && (
        <div className="rapports-list">
          {rapports.length === 0 ? (
            <div className="no-data">
              📋 Aucun rapport technique disponible
              <br />
              <small>Les rapports apparaîtront ici quand les opérateurs les enregistreront</small>
            </div>
          ) : (
            rapports.map((rapport) => (
              <div key={rapport.id} className="rapport-card">
                <div className="rapport-header">
                  <div className="rapport-info">
                    <h3>📋 {rapport.type_rapport}</h3>
                    <p className="rapport-operator">👤 {rapport.operatorName}</p>
                    <p className="rapport-date">📅 {formatDate(rapport.timestamp)}</p>
                  </div>
                  <div className="rapport-status">
                    <span className={`status-badge ${rapport.handled ? 'resolu' : 'en-cours'}`}>
                      {rapport.handled ? '✅ Résolu' : '🔄 En cours'}
                    </span>
                  </div>
                </div>
                
                {rapport.description && (
                  <div className="rapport-description">
                    <p><strong>Description :</strong> {rapport.description}</p>
                  </div>
                )}
                
                {rapport.photo_file_id && (
                  <div className="rapport-photo">
                    <p><strong>Photo :</strong> 📸 Photo jointe</p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'Actions géoportail' && (
        <div className="geoportail-list">
          {actionsGeoportail.length === 0 ? (
            <div className="no-data">
              📍 Aucune action géoportail disponible
              <br />
              <small>Les actions apparaîtront ici quand les opérateurs utiliseront le géoportail</small>
            </div>
          ) : (
            actionsGeoportail.map((action) => (
              <div key={action.id} className="geoportail-card">
                <div className="geoportail-header">
                  <h3>📍 {action.portail_suggere}</h3>
                  <p className="geoportail-operator">👤 {action.operatorName}</p>
                  <p className="geoportail-date">📅 {formatDate(action.timestamp)}</p>
                </div>
                
                <div className="geoportail-details">
                  <p><strong>Distance :</strong> {action.distance_km} km</p>
                  <p><strong>Position :</strong> {typeof action.latitude === 'number' && typeof action.longitude === 'number' ? `${action.latitude.toFixed(4)}, ${action.longitude.toFixed(4)}` : 'N/A'}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default OutilsFerroviaires; 