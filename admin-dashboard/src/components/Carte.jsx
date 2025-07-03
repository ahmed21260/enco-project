import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { collection, onSnapshot } from 'firebase/firestore';
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

  // Centre de la carte (France)
  const defaultCenter = [46.603354, 1.888334];

  useEffect(() => {
    setLoading(true);
    const unsubscribe = onSnapshot(
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
    return () => unsubscribe();
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

  return (
    <div className="carte-container">
      <div className="carte-header">
        <h2>🗺️ Carte des Opérateurs ENCO</h2>
        <div className="stats">
          <span>👥 {positions.length} opérateur(s) en ligne</span>
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
                <p><strong>Position:</strong> {pos.latitude.toFixed(4)}, {pos.longitude.toFixed(4)}</p>
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