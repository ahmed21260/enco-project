import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './Dashboard.css';
import CardsSummary from './CardsSummary';
import StatsCharts from './StatsCharts';
import TimelineActions from './TimelineActions';
import Operateurs from './Operateurs';
import BonsAttachement from './BonsAttachement';
import { realtimeDb } from '../firebaseRealtime';
import { ref, onValue } from 'firebase/database';

// Fix pour les icônes Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Icône personnalisée pour les opérateurs
const createOperatorIcon = (type) => {
  const color = type === 'prise_de_poste' ? '#28a745' : '#dc3545';
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${color};
      width: 20px;
      height: 20px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      animation: pulse 2s infinite;
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

const Dashboard = () => {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('carte');
  const [stats, setStats] = useState({
    totalOperateurs: 12,
    enLigne: 5,
    bonsJour: 7,
    bonsSemaine: 32,
    pannesEnCours: 2,
    pannesResolues: 6,
    alertesUrgence: 1
  });
  const [selectedAction, setSelectedAction] = useState(null);
  const [alertesUrgence, setAlertesUrgence] = useState([]);

  // Centre de la carte (France)
  const defaultCenter = [46.603354, 1.888334];

  const fetchPositions = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/positions/latest');
      if (!response.ok) throw new Error('Erreur API');
      const data = await response.json();
      setPositions(data);
      
      // Calculer les stats
      const enLigne = data.filter(pos => pos.type === 'prise_de_poste').length;
      setStats({
        totalOperateurs: data.length,
        enLigne,
        prisesPoste: data.filter(pos => pos.type === 'prise_de_poste').length,
        anomalies: 0 // À connecter avec les anomalies
      });
      
      setError(null);
    } catch (err) {
      setError('Erreur de connexion à l\'API');
      console.error('Erreur fetch positions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPositions();
    
    // Rafraîchir toutes les 30 secondes
    const interval = setInterval(fetchPositions, 30000);
    // Récupérer les alertes urgences SNCF depuis Firebase (comme dans AlertesLive)
    const alertesRef = ref(realtimeDb, 'alertes');
    const unsubscribe = onValue(alertesRef, (snapshot) => {
      const data = snapshot.val();
      const arr = data ? Object.entries(data).map(([id, value]) => ({ id, ...value })) : [];
      setAlertesUrgence(arr.filter(a => a.type === 'urgence'));
    });
    return () => { clearInterval(interval); unsubscribe(); };
  }, []);

  const renderCarte = () => (
    <div className="carte-section">
      <div className="carte-header">
        <h2>🗺️ Carte des Opérateurs ENCO</h2>
        <div className="carte-controls">
          <span className="operateurs-count">👥 {positions.length} opérateur(s)</span>
          <button onClick={fetchPositions} className="refresh-btn">🔄 Actualiser</button>
        </div>
      </div>
      
      <MapContainer 
        center={positions.length > 0 ? [positions[0].latitude, positions[0].longitude] : defaultCenter}
        zoom={positions.length > 0 ? 10 : 6}
        className="map-container"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
        
        {positions.map((pos, index) => (
          <Marker
            key={`${pos.operateur_id}-${index}`}
            position={[pos.latitude, pos.longitude]}
            icon={createOperatorIcon(pos.type)}
          >
            <Popup>
              <div className="popup-content">
                <h3>👤 {pos.nom}</h3>
                <p><strong>ID:</strong> {pos.operateur_id}</p>
                <p><strong>Statut:</strong> {pos.type === 'prise_de_poste' ? '🟢 En poste' : '🔴 Fin de poste'}</p>
                <p><strong>Heure:</strong> {new Date(pos.timestamp).toLocaleString('fr-FR')}</p>
                <p><strong>Position:</strong> {pos.latitude.toFixed(4)}, {pos.longitude.toFixed(4)}</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );

  const renderHistorique = () => (
    <div className="historique-section">
      <h2>📊 Historique des Actions</h2>
      <TimelineActions />
      <div className="historique-content">
        <div className="filters">
          <select defaultValue="all">
            <option value="all">Tous les opérateurs</option>
            {positions.map(pos => (
              <option key={pos.operateur_id} value={pos.operateur_id}>{pos.nom}</option>
            ))}
          </select>
          <input type="date" />
          <button>🔍 Filtrer</button>
        </div>
        <div className="historique-list">
          {positions.map((pos, index) => (
            <div key={index} className="historique-item">
              <div className="item-icon">
                {pos.type === 'prise_de_poste' ? '🟢' : '🔴'}
              </div>
              <div className="item-content">
                <h4>{pos.nom}</h4>
                <p>{pos.type === 'prise_de_poste' ? 'Prise de poste' : 'Fin de poste'}</p>
                <small>{new Date(pos.timestamp).toLocaleString('fr-FR')}</small>
              </div>
              <div className="item-actions">
                <button onClick={() => setSelectedAction(pos)}>📋 Détails</button>
                <button>🗺️ Voir sur carte</button>
              </div>
            </div>
          ))}
        </div>
        {/* Modale de détail d'action */}
        {selectedAction && (
          <div className="modal-overlay" style={{ position: 'fixed', top:0, left:0, width:'100vw', height:'100vh', background:'rgba(0,0,0,0.3)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000 }} onClick={() => setSelectedAction(null)}>
            <div className="modal-content" style={{ background:'#fff', borderRadius:12, padding:32, minWidth:340, minHeight:180, boxShadow:'0 2px 16px rgba(0,0,0,0.15)', position:'relative' }} onClick={e => e.stopPropagation()}>
              <button style={{ position:'absolute', top:8, right:12, background:'none', border:'none', fontSize:22, cursor:'pointer' }} onClick={() => setSelectedAction(null)}>×</button>
              <h2 style={{marginBottom:8}}>{selectedAction.nom || selectedAction.operateur_id}</h2>
              <div style={{marginBottom:8}}><b>Type d'action :</b> {selectedAction.type === 'prise_de_poste' ? 'Prise de poste' : selectedAction.type === 'fin' ? 'Fin de poste' : selectedAction.type || 'Action'}</div>
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
                {/* Affiche tout autre détail utile ici */}
                ID: {selectedAction.operateur_id || selectedAction.id}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

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

  const operateursActifs = positions.filter(pos => pos.type === 'prise_de_poste');

  const renderStats = () => (
    <div className="stats-section">
      <CardsSummary stats={stats} operateursActifs={operateursActifs} alertesUrgenceList={alertesUrgence} />
      <StatsCharts />
      <h3 style={{marginTop:'2rem'}}>Dernières actions</h3>
      <TimelineActions />
    </div>
  );

  return (
    <div className="dashboard">
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
        </nav>
      </div>

      <div className="main-content">
        <header className="dashboard-header">
          <h2>{activeTab === 'carte' ? 'Carte des Opérateurs' : 
               activeTab === 'historique' ? 'Historique' :
               activeTab === 'documents' ? 'Documents' :
               activeTab === 'operateurs' ? 'Opérateurs' : 'Bons d\'attachement'}</h2>
          <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span className="status">🟢 Système opérationnel</span>
            <button onClick={fetchPositions}>🔄 Actualiser</button>
            {/* Bouton utilisateur admin */}
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
              }}>F</span>
              Admin Freddy DEBOVES
            </button>
          </div>
        </header>

        <main className="content-area">
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
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default Dashboard; 