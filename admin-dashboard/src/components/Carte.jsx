import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { collection, onSnapshot, query, where } from 'firebase/firestore';
import { db } from '../../firebaseConfig';

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
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

const Carte = () => {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [urgences, setUrgences] = useState([]);
  const [anomalies, setAnomalies] = useState([]);

  // Centre de la carte (France)
  const defaultCenter = [46.603354, 1.888334];

  useEffect(() => {
    setLoading(true);
    const unsubscribePositions = onSnapshot(
      collection(db, 'positions_operateurs'),
      (snapshot) => {
        const data = snapshot.docs.map(doc => doc.data());
        setPositions(data);
        setLoading(false);
        setError(null);
      },
      (err) => {
        setError('Erreur Firestore');
        setLoading(false);
      }
    );
    const unsubscribePositionsLog = onSnapshot(
      collection(db, 'positions_log'),
      (snapshot) => {
        const data = snapshot.docs.map(doc => doc.data());
        setPositions(prev => [...prev, ...data]);
      }
    );
    
    // Urgences non résolues
    const qUrgences = query(collection(db, 'urgences'), where('handled', '==', false));
    const unsubscribeUrgences = onSnapshot(qUrgences, (snapshot) => {
      setUrgences(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
    });
    
    // Anomalies non résolues
    const qAnomalies = query(collection(db, 'anomalies'), where('handled', '==', false));
    const unsubscribeAnomalies = onSnapshot(qAnomalies, (snapshot) => {
      setAnomalies(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
    });
    
    return () => {
      unsubscribePositions();
      unsubscribePositionsLog();
      unsubscribeUrgences();
      unsubscribeAnomalies();
    };
  }, []);

  if (loading) {
    return (
      <div className="carte-container">
        <div className="loading">🔄 Chargement de la carte...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="carte-container">
        <div className="error">❌ {error}</div>
      </div>
    );
  }

  const handleResolveUrgence = async (urgenceId) => {
    await db.collection('urgences').doc(urgenceId).update({ handled: true });
  };

  const handleResolveAnomalie = async (anomalieId) => {
    await db.collection('anomalies').doc(anomalieId).update({ handled: true });
  };

  return (
    <div className="carte-container">
      <div className="carte-header">
        <h2>🗺️ Carte des Opérateurs ENCO</h2>
        <div className="stats">
          <span>👥 {positions.length} opérateur(s) en ligne</span>
          <span style={{marginLeft: '20px', color: '#e00'}}>🚨 {urgences.length} urgence(s)</span>
          <span style={{marginLeft: '20px', color: '#f90'}}>🔧 {anomalies.length} anomalie(s)</span>
        </div>
      </div>
      
      <MapContainer 
        center={positions.length > 0 ? [positions[0].latitude, positions[0].longitude] : defaultCenter}
        zoom={positions.length > 0 ? 10 : 6}
        style={{ height: '600px', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
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
                <p><strong>Type:</strong> {pos.type === 'prise_de_poste' ? '🟢 Prise de poste' : '🔴 Fin de poste'}</p>
                <p><strong>Heure:</strong> {new Date(pos.timestamp).toLocaleString('fr-FR')}</p>
                <p><strong>Position:</strong> {typeof pos.latitude === 'number' && typeof pos.longitude === 'number' ? `${pos.latitude.toFixed(4)}, ${pos.longitude.toFixed(4)}` : 'N/A'}</p>
                {pos.checklistEffectuee && (
                  <p style={{color: '#28a745', fontWeight: 'bold'}}>✅ Checklist effectuée</p>
                )}
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Urgences - Ping rouge */}
        {urgences.map((urgence) => (
          <Marker
            key={`urgence-${urgence.id}`}
            position={[urgence.latitude, urgence.longitude]}
            icon={L.divIcon({
              className: 'urgence-marker',
              html: `<div style="
                background:#e00;
                width:32px;
                height:32px;
                border-radius:50%;
                border:4px solid #fff;
                box-shadow:0 4px 12px #e005;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:20px;
                animation: pulse 2s infinite;
              ">🚨</div>`
            })}
          >
            <Popup>
              <div style={{color:'#e00',fontWeight:'bold',fontSize:'16px'}}>🚨 URGENCE CRITIQUE</div>
              <div><b>Opérateur :</b> {urgence.nom}</div>
              <div><b>Type :</b> {urgence.type}</div>
              <div><b>Description :</b> {urgence.description || 'Aucune'}</div>
              <div><b>Heure :</b> {new Date(urgence.timestamp).toLocaleString('fr-FR')}</div>
              <div><b>Position :</b> {typeof urgence.latitude === 'number' && typeof urgence.longitude === 'number' ? `${urgence.latitude.toFixed(4)}, ${urgence.longitude.toFixed(4)}` : 'N/A'}</div>
              <div style={{marginTop:'8px'}}>
                <button 
                  onClick={() => handleResolveUrgence(urgence.id)}
                  style={{
                    background:'#e00',
                    color:'#fff',
                    border:'none',
                    padding:'4px 8px',
                    borderRadius:'4px',
                    cursor:'pointer'
                  }}
                >
                  Marquer comme résolu
                </button>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Anomalies - Ping orange */}
        {anomalies.map((anomalie) => (
          <Marker
            key={`anomalie-${anomalie.id}`}
            position={[anomalie.latitude, anomalie.longitude]}
            icon={L.divIcon({
              className: 'anomalie-marker',
              html: `<div style="
                background:#f90;
                width:28px;
                height:28px;
                border-radius:50%;
                border:3px solid #fff;
                box-shadow:0 3px 10px #f905;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:16px;
              ">🔧</div>`
            })}
          >
            <Popup>
              <div style={{color:'#f90',fontWeight:'bold',fontSize:'14px'}}>🔧 ANOMALIE</div>
              <div><b>Opérateur :</b> {anomalie.nom}</div>
              <div><b>Machine :</b> {anomalie.machine || 'Non spécifiée'}</div>
              <div><b>Type :</b> {anomalie.type_anomalie || 'Non spécifié'}</div>
              <div><b>Anomalie :</b> {anomalie.anomalie_specifique || 'Non spécifiée'}</div>
              <div><b>Description :</b> {anomalie.description || 'Aucune'}</div>
              <div><b>Heure :</b> {new Date(anomalie.timestamp).toLocaleString('fr-FR')}</div>
              <div style={{marginTop:'8px'}}>
                <button 
                  onClick={() => handleResolveAnomalie(anomalie.id)}
                  style={{
                    background:'#f90',
                    color:'#fff',
                    border:'none',
                    padding:'4px 8px',
                    borderRadius:'4px',
                    cursor:'pointer'
                  }}
                >
                  Marquer comme résolu
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      
      {positions.length === 0 && (
        <div className="no-data">
          📍 Aucune position d'opérateur disponible
          <br />
          <small>Les positions apparaîtront ici quand les opérateurs feront leur prise/fin de poste</small>
        </div>
      )}
    </div>
  );
};

export default Carte; 