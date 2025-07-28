import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './Dashboard.css';
import CardsSummary from './CardsSummary';
import StatsCharts from './StatsCharts';
import TimelineActions from './TimelineActions';
import Operateurs from './Operateurs';
import BonsAttachement from './BonsAttachement';
import OutilsFerroviaires from './OutilsFerroviaires';
import PlanningPro from './PlanningPro';
import PlanningDiagnostic from './PlanningDiagnostic';
import PlanningTest from './PlanningTest';
import PlanningDebug from './PlanningDebug';
import ScoringDashboard from './ScoringDashboard';
import PhotoTest from './PhotoTest';
import { realtimeDb } from '../firebaseRealtime';
import { ref, onValue } from 'firebase/database';
import { collection, onSnapshot } from 'firebase/firestore';
import { db } from '../../firebaseConfig';
import { useOperateursLive } from '../hooks/useOperateursLive';
import { toast } from 'react-toastify';

// Fix pour les icônes Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const getColorForStatus = (status) => {
  switch (status) {
    case 'prise_de_poste': return '#28a745'; // Vert
    case 'fin_de_poste': return '#dc3545';   // Rouge
    case 'anomalie': return '#ffc107';       // Orange
    case 'urgence': return '#e74c3c';        // Rouge vif
    default: return '#6c757d';               // Gris
  }
};

const createOperatorIcon = (status) => {
  const color = getColorForStatus(status);
  return L.divIcon({
    className: 'custom-operator-marker',
    html: `<div style="
      background-color: ${color};
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 2px solid white;
      box-shadow: 0 1px 3px rgba(0,0,0,0.3);
      "></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
};

// Icône pour les alertes
const createAlertIcon = (type) => {
  const color = type === 'urgence' ? '#dc3545' : '#ffc107';
  const symbol = type === 'urgence' ? '🚨' : '⚠️';
  return L.divIcon({
    className: 'alert-marker',
    html: `<div style="
      background-color: ${color};
      width: 24px;
      height: 24px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      animation: pulse 1s infinite;
    ">${symbol}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

const Dashboard = ({ onLogout, user }) => {
  const { operateursLive, stats, positions, anomalies, urgences, checklists } = useOperateursLive();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('carte');
  const [selectedAction, setSelectedAction] = useState(null);
  const [alertesUrgence, setAlertesUrgence] = useState([]);
  const [alertes, setAlertes] = useState([]);
  const [historiqueFiltre, setHistoriqueFiltre] = useState({ operateur: 'all', type: 'all', date: '' });
  const actions = [
    ...positions.map(a => ({ ...a, type: a.type || 'prise_de_poste' })),
    ...anomalies.map(a => ({ ...a, type: 'anomalie' })),
    ...urgences.map(a => ({ ...a, type: 'urgence' })),
    ...checklists.map(a => ({ ...a, type: 'checklist' })),
  ];
  const filteredActions = actions.filter(a => {
    if (historiqueFiltre.operateur !== 'all' && a.operateur_id !== historiqueFiltre.operateur) return false;
    if (historiqueFiltre.type !== 'all' && a.type !== historiqueFiltre.type) return false;
    if (historiqueFiltre.date && (!a.timestamp || !a.timestamp.startsWith(historiqueFiltre.date))) return false;
    return true;
  }).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  // Centre de la carte (France)
  const defaultCenter = [46.603354, 1.888334];

  // Références pour détecter les nouvelles urgences/anomalies/checklists
  const prevUrgences = useRef([]);
  const prevAnomalies = useRef([]);
  const prevChecklists = useRef([]);
  const notifiedChecklistsRef = useRef({});

  // Toast pour nouvelle urgence
  useEffect(() => {
    if (prevUrgences.current.length && urgences.length > prevUrgences.current.length) {
      const newUrgence = urgences.find(u => !prevUrgences.current.some(pu => pu.id === u.id));
      if (newUrgence) {
        toast.error(`🚨 URGENCE signalée par ${newUrgence.operateur_nom || newUrgence.operateur_id || 'un opérateur'} !`, { autoClose: 6000 });
      }
    }
    prevUrgences.current = urgences;
  }, [urgences]);

  // Toast pour nouvelle anomalie
  useEffect(() => {
    if (prevAnomalies.current.length && anomalies.length > prevAnomalies.current.length) {
      const newAnomalie = anomalies.find(a => !prevAnomalies.current.some(pa => pa.id === a.id));
      if (newAnomalie) {
        toast.warn(`❗ Nouvelle anomalie détectée par ${newAnomalie.operateur_nom || newAnomalie.operateur_id || 'un opérateur'} !`, { autoClose: 6000 });
      }
    }
    prevAnomalies.current = anomalies;
  }, [anomalies]);

  // Toast checklist manquante (une seule fois par opérateur et par jour)
  useEffect(() => {
    if (operateursLive.length && checklists.length) {
      const now = new Date();
      const today = now.toISOString().slice(0, 10);
      operateursLive.forEach(op => {
        const hasChecklist = checklists.some(cl => cl.operateur_id === op.operateur_id && cl.timestamp && cl.timestamp.startsWith(today));
        const key = `${op.operateur_id}_${today}`;
        if (!hasChecklist && !notifiedChecklistsRef.current[key]) {
          toast.info(`⚠️ Checklist manquante pour ${op.nom || op.operateur_id} !`, { autoClose: 8000 });
          notifiedChecklistsRef.current[key] = true;
        }
        // Si la checklist est complétée, on peut réinitialiser la notification pour ce jour
        if (hasChecklist && notifiedChecklistsRef.current[key]) {
          delete notifiedChecklistsRef.current[key];
        }
      });
    }
    prevChecklists.current = checklists;
  }, [checklists, operateursLive]);

  useEffect(() => {
    setLoading(true);
    const unsub = onSnapshot(collection(db, 'positions_log'), (snap) => {
      // setPositions(snap.docs.map(doc => ({ id: doc.id, ...doc.data() }))); // Supprimer l'appel à setPositions
      setLoading(false);
    }, (err) => {
      setLoading(false);
      // setPositions([]); // Supprimer l'appel à setPositions
    });
    return () => unsub();
  }, []);

  // Écouter les alertes et urgences
  useEffect(() => {
    const unsubAlertes = onSnapshot(collection(db, 'alertes'), (snap) => {
      setAlertes(snap.docs.map(doc => ({ id: doc.id, ...doc.data() })));
    });
    
    const unsubUrgences = onSnapshot(collection(db, 'urgences'), (snap) => {
      setAlertesUrgence(snap.docs.map(doc => ({ id: doc.id, ...doc.data() })));
    });
    
    return () => {
      unsubAlertes();
      unsubUrgences();
    };
  }, []);

  const renderCarte = () => (
    <div className="carte-section" style={{ position: 'relative' }}>
      <div className="carte-header">
        <h2>🗺️ Carte des Opérateurs ENCO</h2>
        <div className="carte-controls">
          <span className="operateurs-count">👥 {operateursLive.length} opérateur(s) en poste</span>
          <span className="total-count">📊 {positions.length} total</span>
        </div>
      </div>
      
      <MapContainer 
        center={positions.length > 0 && typeof positions[0].latitude === 'number' && typeof positions[0].longitude === 'number' ? [positions[0].latitude, positions[0].longitude] : defaultCenter}
        zoom={positions.length > 0 && typeof positions[0].latitude === 'number' && typeof positions[0].longitude === 'number' ? 10 : 6}
        className="map-container"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
        
        {positions.filter(pos => typeof pos.latitude === 'number' && typeof pos.longitude === 'number').map((pos, index) => (
          <Marker
            key={`${pos.operateur_id}-${index}`}
            position={[pos.latitude, pos.longitude]}
            icon={createOperatorIcon(pos.type)}
          >
            <Popup>
              <div className="popup-content">
                <h3>👤 {pos.nom || pos.operateur_id}</h3>
                <p><strong>ID:</strong> {pos.operateur_id}</p>
                <p><strong>Statut:</strong> {pos.type === 'prise_de_poste' ? '🟢 En poste' : '🔴 Fin de poste'}</p>
                <p><strong>Heure:</strong> {new Date(pos.timestamp).toLocaleString('fr-FR')}</p>
                <p><strong>Position:</strong> {typeof pos.latitude === 'number' && typeof pos.longitude === 'number' ? `${pos.latitude.toFixed(4)}, ${pos.longitude.toFixed(4)}` : 'N/A'}</p>
                {pos.description && (
                  <p><strong>Action:</strong> {pos.description}</p>
                )}
                {pos.photoUrl && (
                  <div style={{marginTop: 10}}>
                    <img src={pos.photoUrl} alt="Photo opérateur" style={{maxWidth: 200, borderRadius: 8}} />
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
        
        {/* Marqueurs pour les alertes */}
        {alertes.filter(alerte => typeof alerte.latitude === 'number' && typeof alerte.longitude === 'number').map((alerte, index) => (
          <Marker
            key={`alerte-${alerte.id}-${index}`}
            position={[alerte.latitude, alerte.longitude]}
            icon={createAlertIcon('alerte')}
          >
            <Popup>
              <div className="popup-content">
                <h3>⚠️ Alerte</h3>
                <p><strong>Opérateur:</strong> {alerte.operateur_nom || alerte.operateur_id}</p>
                <p><strong>Type:</strong> {alerte.type || 'Anomalie'}</p>
                <p><strong>Description:</strong> {alerte.description}</p>
                <p><strong>Heure:</strong> {new Date(alerte.timestamp).toLocaleString('fr-FR')}</p>
                {alerte.photoUrl && (
                  <div style={{marginTop: 10}}>
                    <img src={alerte.photoUrl} alt="Photo alerte" style={{maxWidth: 200, borderRadius: 8}} />
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
        
        {/* Marqueurs pour les urgences */}
        {urgences.filter(urgence => typeof urgence.latitude === 'number' && typeof urgence.longitude === 'number').map((urgence, index) => (
          <Marker
            key={`urgence-${urgence.id}-${index}`}
            position={[urgence.latitude, urgence.longitude]}
            icon={createAlertIcon('urgence')}
          >
            <Popup>
              <div className="popup-content">
                <h3>🚨 Urgence</h3>
                <p><strong>Opérateur:</strong> {urgence.operateur_nom || urgence.operateur_id}</p>
                <p><strong>Type:</strong> {urgence.type || 'Urgence'}</p>
                <p><strong>Description:</strong> {urgence.description}</p>
                <p><strong>Heure:</strong> {new Date(urgence.timestamp).toLocaleString('fr-FR')}</p>
                {urgence.photoUrl && (
                  <div style={{marginTop: 10}}>
                    <img src={urgence.photoUrl} alt="Photo urgence" style={{maxWidth: 200, borderRadius: 8}} />
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      {/* Légende overlay dans la carte */}
      <div className="map-legend-overlay">
        <b>Légende</b>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '8px 0 4px 0' }}><span style={{ width: 14, height: 14, borderRadius: '50%', background: '#28a745', display: 'inline-block', border: '2px solid #fff' }}></span> <span>En poste</span></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}><span style={{ width: 14, height: 14, borderRadius: '50%', background: '#dc3545', display: 'inline-block', border: '2px solid #fff' }}></span> <span>Fin de poste</span></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}><span style={{ width: 14, height: 14, borderRadius: '50%', background: '#ffc107', display: 'inline-block', border: '2px solid #fff' }}></span> <span>Alerte</span></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}><span style={{ width: 14, height: 14, borderRadius: '50%', background: '#e74c3c', display: 'inline-block', border: '2px solid #fff' }}></span> <span>Urgence</span></div>
      </div>
    </div>
  );

  const renderHistorique = () => {
    // Regroupement par date pour affichage métier
    const actionsByDate = {};
    filteredActions.forEach(action => {
      const date = action.timestamp ? new Date(action.timestamp).toLocaleDateString('fr-FR') : 'Date inconnue';
      if (!actionsByDate[date]) actionsByDate[date] = [];
      actionsByDate[date].push(action);
    });
    return (
      <div className="historique-section">
        <h2>📊 Historique des Actions</h2>
        {/* Un seul bloc de filtres, en haut */}
        <div className="historique-content">
          <div className="filters" style={{ marginBottom: 24, display: 'flex', gap: 12, alignItems: 'center' }}>
            <select value={historiqueFiltre.operateur} onChange={e => setHistoriqueFiltre(f => ({ ...f, operateur: e.target.value }))}>
              <option value="all">Tous les opérateurs</option>
              {positions.map(pos => (
                <option key={pos.operateur_id} value={pos.operateur_id}>{pos.nom}</option>
              ))}
            </select>
            <select value={historiqueFiltre.type} onChange={e => setHistoriqueFiltre(f => ({ ...f, type: e.target.value }))}>
              <option value="all">Tous types</option>
              <option value="prise_de_poste">Prise de poste</option>
              <option value="fin">Fin de poste</option>
              <option value="anomalie">Anomalie</option>
              <option value="urgence">Urgence</option>
              <option value="checklist">Checklist</option>
            </select>
            <input type="date" value={historiqueFiltre.date} onChange={e => setHistoriqueFiltre(f => ({ ...f, date: e.target.value }))} />
            <button onClick={() => setHistoriqueFiltre({ operateur: 'all', type: 'all', date: '' })}>Réinitialiser</button>
          </div>
          <div className="historique-list" style={{ marginTop: 16 }}>
            {loading ? (
              <div>Chargement…</div>
            ) : filteredActions.length === 0 ? (
              <div>Aucune action enregistrée</div>
            ) : (
              Object.entries(actionsByDate).map(([date, actions], idx) => (
                <div key={date} style={{marginBottom:32}}>
                  <div style={{fontWeight:700, color:'#007bff', marginBottom:8, fontSize:17}}>{date}</div>
                  {actions.map((action, index) => (
                    <div key={index} className="historique-item" style={{ display: 'flex', alignItems: 'center', gap: 16, background: index%2===0 ? '#f8f9fa' : '#fff', borderRadius: 8, marginBottom: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
                      <div style={{ fontSize: 22 }}>
                        {action.type === 'prise_de_poste' ? '🟢' : action.type === 'fin' ? '🔴' : action.type === 'anomalie' ? '🚨' : action.type === 'urgence' ? '🚨' : action.type === 'checklist' ? '✅' : '🕒'}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600 }}>{action.nom || action.operateur_id}</div>
                        <div style={{ color: '#888', fontSize: 14 }}>{action.type === 'prise_de_poste' ? 'Prise de poste' : action.type === 'fin' ? 'Fin de poste' : action.type.charAt(0).toUpperCase() + action.type.slice(1)}</div>
                        <div style={{ fontSize: 13 }}>{action.timestamp && new Date(action.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</div>
                        {action.description && <div style={{ fontSize: 13, color: '#333', marginTop: 4 }}>{action.description}</div>}
                      </div>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button onClick={() => setSelectedAction(action)} style={{ background: '#f5f5f5', border: '1px solid #eee', borderRadius: 6, padding: '4px 12px', cursor: 'pointer' }}>📋 Détails</button>
                        <button style={{ background: '#f5f5f5', border: '1px solid #eee', borderRadius: 6, padding: '4px 12px', cursor: 'pointer' }}>🗺️ Voir sur carte</button>
                      </div>
                    </div>
                  ))}
                </div>
              ))
            )}
          </div>
          {/* Modale de détail d'action (inchangée) */}
          {selectedAction && (
            <div className="modal-overlay" style={{ position: 'fixed', top:0, left:0, width:'100vw', height:'100vh', background:'rgba(0,0,0,0.3)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000 }} onClick={() => setSelectedAction(null)}>
              <div className="modal-content" style={{ background:'#fff', borderRadius:12, padding:32, minWidth:340, minHeight:180, boxShadow:'0 2px 16px rgba(0,0,0,0.15)', position:'relative' }} onClick={e => e.stopPropagation()}>
                <button style={{ position:'absolute', top:8, right:12, background:'none', border:'none', fontSize:22, cursor:'pointer' }} onClick={() => setSelectedAction(null)}>×</button>
                <h2 style={{marginBottom:8}}>{selectedAction.nom || selectedAction.operateur_id}</h2>
                <div style={{marginBottom:8}}><b>Type d'action :</b> {selectedAction.type === 'prise_de_poste' ? 'Prise de poste' : selectedAction.type === 'fin' ? 'Fin de poste' : selectedAction.type.charAt(0).toUpperCase() + selectedAction.type.slice(1)}</div>
                <div style={{marginBottom:8}}><b>Date/heure :</b> {selectedAction.timestamp && new Date(selectedAction.timestamp).toLocaleString('fr-FR')}</div>
                {selectedAction.description && <div style={{marginBottom:8}}><b>Message :</b> {selectedAction.description}</div>}
                {selectedAction.photoUrl && <div style={{marginBottom:8}}><img src={selectedAction.photoUrl} alt="photo action" style={{maxWidth:180, borderRadius:8, border:'1px solid #eee'}} /></div>}
                {selectedAction.latitude && selectedAction.longitude && (
                  <div style={{ width: 220, height: 140, margin: '12px 0', borderRadius: 8, overflow: 'hidden', border: '1px solid #eee' }}>
                    <iframe
                      title="Mini-carte"
                      width="100%"
                      height="100%"
                      frameBorder="0"
                      style={{ border:0 }}
                      src={`https://www.openstreetmap.org/export/embed.html?bbox=${selectedAction.longitude-0.001}%2C${selectedAction.latitude-0.001}%2C${selectedAction.longitude+0.001}%2C${selectedAction.latitude+0.001}&layer=mapnik&marker=${selectedAction.latitude}%2C${selectedAction.longitude}`}
                      allowFullScreen
                    ></iframe>
                  </div>
                )}
                <div style={{marginTop:12, color:'#888', fontSize:13}}>
                  ID: {selectedAction.operateur_id || selectedAction.id}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderDocuments = () => (
    <div className="documents-section">
      <h2>📄 Documents et Guides</h2>
      <div className="documents-grid">
        <div className="document-card">
          <h3>🚜 CAT 323 M</h3>
          <p>VGP, carte grise, manuel d'utilisation</p>
          <button>📋 Voir documents</button>
        </div>
        <div className="document-card">
          <h3>🚛 D2R</h3>
          <p>VGP, carte grise, manuel d'utilisation</p>
          <button>📋 Voir documents</button>
        </div>
        <div className="document-card">
          <h3>🏗️ ATLAS 1404</h3>
          <p>VGP, carte grise, manuel d'utilisation</p>
          <button>📋 Voir documents</button>
        </div>
        <div className="document-card">
          <h3>🔧 MECALAC</h3>
          <p>VGP, carte grise, manuel d'utilisation</p>
          <button>📋 Voir documents</button>
        </div>
      </div>
    </div>
  );

  const renderStats = () => (
    <div className="stats-section">
      <CardsSummary stats={stats} operateursActifs={operateursLive} alertesUrgenceList={urgences} />
      <StatsCharts />
      <h3 style={{marginTop:'2rem'}}>Dernières actions</h3>
      <TimelineActions />
      <div style={{marginTop:'3rem'}}>
        <ScoringDashboard />
      </div>
    </div>
  );

  return (
    <div className="dashboard" style={{ display: 'flex', minHeight: '100vh', width: '100vw', background: '#f5f6fa' }}>
      <div className="sidebar">
        <div className="logo-section">
          <img src="/photos/logo-enco.png" alt="ENCO Logo" className="logo" />
          <h1>ENCO</h1>
        </div>
        
        <nav className="sidebar-nav">
          <button 
            className={`nav-btn ${activeTab === 'carte' ? 'active' : ''}`}
            onClick={() => setActiveTab('carte')}
          >
            🗺️ Carte
          </button>
          <button 
            className={`nav-btn ${activeTab === 'historique' ? 'active' : ''}`}
            onClick={() => setActiveTab('historique')}
          >
            📊 Historique
          </button>
          <button 
            className={`nav-btn ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            📄 Documents
          </button>
          <button 
            className={`nav-btn ${activeTab === 'stats' ? 'active' : ''}`}
            onClick={() => setActiveTab('stats')}
          >
            📈 Statistiques
          </button>
          <button 
            className={`nav-btn ${activeTab === 'operateurs' ? 'active' : ''}`}
            onClick={() => setActiveTab('operateurs')}
          >
            👷 Opérateurs
          </button>
          <button 
            className={`nav-btn ${activeTab === 'bons' ? 'active' : ''}`}
            onClick={() => setActiveTab('bons')}
          >
            📄 Bons d'attachement
          </button>
          <button 
            className={`nav-btn urgences ${activeTab === 'outils' ? 'active' : ''}`}
            onClick={() => setActiveTab('outils')}
            style={{ position: 'relative' }}
          >
            🗺️ Outils ferroviaires
            {/* Badge rouge dynamique sur Urgences */}
            {urgences.length > 0 && <span className="badge">{urgences.length}</span>}
          </button>
          <button 
            className={`nav-btn ${activeTab === 'planning' ? 'active' : ''}`}
            onClick={() => setActiveTab('planning')}
          >
            🗓️ Planning
          </button>
          <button 
            className={`nav-btn ${activeTab === 'planning-diagnostic' ? 'active' : ''}`}
            onClick={() => setActiveTab('planning-diagnostic')}
          >
            🔧 Diagnostic Planning
          </button>
          <button 
            className={`nav-btn ${activeTab === 'planning-test' ? 'active' : ''}`}
            onClick={() => setActiveTab('planning-test')}
          >
            🧪 Test Nouvelles Fonctionnalités
          </button>
          <button 
            className={`nav-btn ${activeTab === 'planning-debug' ? 'active' : ''}`}
            onClick={() => setActiveTab('planning-debug')}
          >
            🐛 Debug Planning
          </button>
          <button 
            className={`nav-btn ${activeTab === 'phototest' ? 'active' : ''}`}
            onClick={() => setActiveTab('phototest')}
          >
            🧪 Test Photos
          </button>

        </nav>
      </div>

      <div className="main-content" style={{ flex: 1, width: '100%', maxWidth: '100vw', padding: 0 }}>
        <header className="dashboard-header">
          <h2>{activeTab === 'carte' ? 'Carte des Opérateurs' : 
               activeTab === 'historique' ? 'Historique' :
               activeTab === 'documents' ? 'Documents' :
               activeTab === 'operateurs' ? 'Opérateurs' : 
               activeTab === 'bons' ? 'Bons d\'attachement' :
               activeTab === 'outils' ? 'Outils ferroviaires' :
               activeTab === 'planning' ? 'Planning' :
               activeTab === 'planning-diagnostic' ? 'Diagnostic Planning' :
               activeTab === 'planning-test' ? 'Test Nouvelles Fonctionnalités' :
               activeTab === 'planning-debug' ? 'Debug Planning' :
               activeTab === 'phototest' ? 'Test Photos' : 'Dashboard'}</h2>
          <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span className="status">🟢 Système opérationnel</span>
            {/* Bouton utilisateur connecté */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button style={{
              display: 'flex', alignItems: 'center', gap: 8,
              background: '#fff', border: '1px solid #eee', borderRadius: 20, padding: '6px 16px',
              fontWeight: 'bold', fontSize: 15, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', cursor: 'pointer',
              transition: 'box-shadow 0.2s',
            }}>
              <span style={{
                display: 'inline-block', width: 32, height: 32, borderRadius: '50%',
                background: 'linear-gradient(135deg,#007bff 60%,#28a745 100%)', color: '#fff',
                fontWeight: 'bold', fontSize: 18, textAlign: 'center', lineHeight: '32px',
                }}>
                  {user?.email?.charAt(0).toUpperCase() || 'U'}
                </span>
                {user?.email || 'Utilisateur'}
              </button>
              
              {/* Bouton de déconnexion */}
              <button 
                onClick={onLogout}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  background: '#dc3545', color: 'white', border: 'none', borderRadius: 20, 
                  padding: '6px 12px', fontWeight: 'bold', fontSize: 14, 
                  boxShadow: '0 1px 4px rgba(220, 53, 69, 0.3)', cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = '#c82333';
                  e.target.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = '#dc3545';
                  e.target.style.transform = 'translateY(0)';
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <polyline points="16,17 21,12 16,7"/>
                  <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
                Déconnexion
            </button>
            </div>
          </div>
        </header>

        <main className="content-area" style={{ width: '100%', maxWidth: '100vw', margin: 0, padding: 0 }}>
          {loading && <div className="loading">🔄 Chargement...</div>}
          {error && <div className="error">❌ {error}</div>}
          
          {!loading && !error && (
            <>
              {activeTab === 'carte' && renderCarte()}
              {activeTab === 'historique' && renderHistorique()}
              {activeTab === 'documents' && renderDocuments()}
              {activeTab === 'stats' && renderStats()}
              {activeTab === 'operateurs' && <Operateurs />}
              {activeTab === 'bons' && <BonsAttachement />}
              {activeTab === 'outils' && <OutilsFerroviaires />}
              {activeTab === 'planning' && <PlanningPro />}
              {activeTab === 'planning-diagnostic' && <PlanningDiagnostic />}
              {activeTab === 'planning-test' && <PlanningTest />}
              {activeTab === 'planning-debug' && <PlanningDebug />}
              {activeTab === 'phototest' && <PhotoTest />}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default Dashboard; 