import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import { collection, onSnapshot, query, where, orderBy } from 'firebase/firestore';
import { db } from '../firebaseConfig';
import L from 'leaflet';
import './LiveMap.css';

// Fix pour les icônes Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Icônes personnalisées pour les opérateurs
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

// Composant pour mettre à jour la vue de la carte
const MapUpdater = ({ center, zoom }) => {
  const map = useMap();
  
  useEffect(() => {
    if (center && center.length === 2) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);
  
  return null;
};

const LiveMap = () => {
  const [operateurs, setOperateurs] = useState([]);
  const [alertes, setAlertes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOperator, setSelectedOperator] = useState(null);
  const [mapCenter, setMapCenter] = useState([46.603354, 1.888334]); // Centre France
  const [mapZoom, setMapZoom] = useState(6);
  const [filters, setFilters] = useState({
    showActive: true,
    showInactive: false,
    showUrgences: true,
    showAnomalies: true
  });
  
  const mapRef = useRef();

  useEffect(() => {
    // Écouter les positions des opérateurs en temps réel
    const positionsQuery = query(
      collection(db, 'positions_operateurs'),
      orderBy('timestamp', 'desc')
    );

    const unsubscribePositions = onSnapshot(positionsQuery, (snapshot) => {
      const positionsData = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      
      // Grouper par opérateur et prendre la position la plus récente
      const latestPositions = positionsData.reduce((acc, pos) => {
        if (!acc[pos.operatorId] || new Date(pos.timestamp) > new Date(acc[pos.operatorId].timestamp)) {
          acc[pos.operatorId] = pos;
        }
        return acc;
      }, {});
      
      setOperateurs(Object.values(latestPositions));
      setLoading(false);
    });

    // Écouter les alertes en temps réel
    const alertesQuery = query(
      collection(db, 'urgences'),
      where('resolved', '==', false)
    );

    const unsubscribeAlertes = onSnapshot(alertesQuery, (snapshot) => {
      const alertesData = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setAlertes(alertesData);
    });

    // Écouter les anomalies en temps réel
    const anomaliesQuery = query(
      collection(db, 'anomalies'),
      where('resolved', '==', false)
    );

    const unsubscribeAnomalies = onSnapshot(anomaliesQuery, (snapshot) => {
      const anomaliesData = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data(),
        type: 'anomalie'
      }));
      setAlertes(prev => [...prev.filter(a => a.type !== 'anomalie'), ...anomaliesData]);
    });

    return () => {
      unsubscribePositions();
      unsubscribeAlertes();
      unsubscribeAnomalies();
    };
  }, []);

  // Centrer la carte sur un opérateur
  const centerOnOperator = (operator) => {
    if (operator.latitude && operator.longitude) {
      setMapCenter([operator.latitude, operator.longitude]);
      setMapZoom(12);
    }
  };

  // Filtrer les opérateurs selon les critères
  const filteredOperateurs = operateurs.filter(op => {
    if (op.type === 'prise_de_poste' && !filters.showActive) return false;
    if (op.type === 'fin_de_poste' && !filters.showInactive) return false;
    return true;
  });

  // Filtrer uniquement ceux qui ont une position pour la carte
  const operateursAvecPosition = filteredOperateurs.filter(op => typeof op.latitude === 'number' && typeof op.longitude === 'number');

  // Filtrer les alertes
  const filteredAlertes = alertes.filter(alerte => {
    if (alerte.type === 'urgence' && !filters.showUrgences) return false;
    if (alerte.type === 'anomalie' && !filters.showAnomalies) return false;
    return true;
  });

  const getOperatorStatus = (operator) => {
    const hasUrgence = alertes.some(a => a.operatorId === operator.operatorId && a.type === 'urgence');
    const hasAnomalie = alertes.some(a => a.operatorId === operator.operatorId && a.type === 'anomalie');
    
    if (hasUrgence) return 'urgence';
    if (hasAnomalie) return 'anomalie';
    return operator.type;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'urgence': return '#e74c3c';
      case 'anomalie': return '#f39c12';
      case 'prise_de_poste': return '#28a745';
      case 'fin_de_poste': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'urgence': return '🚨 URGENCE';
      case 'anomalie': return '🔧 ANOMALIE';
      case 'prise_de_poste': return '🟢 En poste';
      case 'fin_de_poste': return '🔴 Fin de poste';
      default: return '⚪ Inconnu';
    }
  };

  if (loading) {
    return (
      <div className="live-map-container">
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Chargement de la carte en temps réel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="live-map-container">
      <div className="map-header">
        <h2>🗺️ Carte Live des Opérateurs</h2>
        <div className="map-stats">
          <span className="stat-item">
            <span className="stat-dot active"></span>
            {filteredOperateurs.filter(op => op.type === 'prise_de_poste').length} actifs
          </span>
          <span className="stat-item">
            <span className="stat-dot urgence"></span>
            {filteredAlertes.filter(a => a.type === 'urgence').length} urgences
          </span>
          <span className="stat-item">
            <span className="stat-dot anomalie"></span>
            {filteredAlertes.filter(a => a.type === 'anomalie').length} anomalies
          </span>
        </div>
      </div>

      <div className="map-controls">
        <div className="filters">
          <label>
            <input
              type="checkbox"
              checked={filters.showActive}
              onChange={(e) => setFilters(prev => ({ ...prev, showActive: e.target.checked }))}
            />
            🟢 Actifs
          </label>
          <label>
            <input
              type="checkbox"
              checked={filters.showInactive}
              onChange={(e) => setFilters(prev => ({ ...prev, showInactive: e.target.checked }))}
            />
            🔴 Inactifs
          </label>
          <label>
            <input
              type="checkbox"
              checked={filters.showUrgences}
              onChange={(e) => setFilters(prev => ({ ...prev, showUrgences: e.target.checked }))}
            />
            🚨 Urgences
          </label>
          <label>
            <input
              type="checkbox"
              checked={filters.showAnomalies}
              onChange={(e) => setFilters(prev => ({ ...prev, showAnomalies: e.target.checked }))}
            />
            🔧 Anomalies
          </label>
        </div>
        
        <button 
          className="btn-center"
          onClick={() => {
            setMapCenter([46.603354, 1.888334]);
            setMapZoom(6);
          }}
        >
          🏠 Vue France
        </button>
      </div>

      <div className="map-wrapper">
        <MapContainer
          ref={mapRef}
          center={mapCenter}
          zoom={mapZoom}
          className="live-map"
          zoomControl={true}
        >
          <MapUpdater center={mapCenter} zoom={mapZoom} />
          
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />

          {/* Marqueurs des opérateurs */}
          {operateursAvecPosition.map((operator) => {
            const status = getOperatorStatus(operator);
            const hasAlert = alertes.some(a => a.operatorId === operator.operatorId);
            
            return (
              <Marker
                key={operator.id}
                position={[operator.latitude, operator.longitude]}
                icon={createOperatorIcon(status)}
                eventHandlers={{
                  click: () => setSelectedOperator(operator)
                }}
              >
                <Popup>
                  <div className="operator-popup">
                    <h3>👤 {operator.operatorName || operator.nom}</h3>
                    <p><strong>Statut:</strong> {getStatusText(status)}</p>
                    <p><strong>Heure:</strong> {new Date(operator.timestamp).toLocaleString('fr-FR')}</p>
                    <p><strong>Position:</strong> {typeof operator.latitude === 'number' && typeof operator.longitude === 'number' ? `${operator.latitude.toFixed(4)}, ${operator.longitude.toFixed(4)}` : 'N/A'}</p>
                    {operator.chantier && <p><strong>Chantier:</strong> {operator.chantier}</p>}
                    {operator.machine && <p><strong>Machine:</strong> {operator.machine}</p>}
                    {hasAlert && (
                      <div className="alert-info">
                        <p>🚨 <strong>ALERTE ACTIVE</strong></p>
                        <button 
                          className="btn-resolve"
                          onClick={() => {/* Logique de résolution */}}
                        >
                          Résoudre
                        </button>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {/* Cercles pour les alertes */}
          {filteredAlertes.map((alerte) => {
            const operator = operateurs.find(op => op.operatorId === alerte.operatorId);
            if (!operator) return null;
            
            return (
              <Circle
                key={alerte.id}
                center={[operator.latitude, operator.longitude]}
                radius={500}
                pathOptions={{
                  color: alerte.type === 'urgence' ? '#e74c3c' : '#f39c12',
                  fillColor: alerte.type === 'urgence' ? '#e74c3c' : '#f39c12',
                  fillOpacity: 0.2,
                  weight: 2
                }}
              />
            );
          })}
        </MapContainer>
      </div>

      {/* Liste des opérateurs */}
      <div className="operators-list">
        <h3>👥 Opérateurs ({filteredOperateurs.length})</h3>
        <div className="operators-grid">
          {filteredOperateurs.map((operator) => {
            const status = getOperatorStatus(operator);
            const hasAlert = alertes.some(a => a.operatorId === operator.operatorId);
            
            return (
              <div 
                key={operator.id} 
                className={`operator-card ${hasAlert ? 'has-alert' : ''}`}
                onClick={() => centerOnOperator(operator)}
              >
                <div className="operator-header">
                  <h4>{operator.operatorName || operator.nom}</h4>
                  <span 
                    className="status-badge"
                    style={{ backgroundColor: getStatusColor(status) }}
                  >
                    {getStatusText(status)}
                  </span>
                </div>
                <div className="operator-details">
                  <p><strong>Heure:</strong> {new Date(operator.timestamp).toLocaleTimeString('fr-FR')}</p>
                  {operator.chantier && <p><strong>Chantier:</strong> {operator.chantier}</p>}
                  {operator.machine && <p><strong>Machine:</strong> {operator.machine}</p>}
                </div>
                {hasAlert && (
                  <div className="alert-indicator">
                    🚨 Alerte active
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default LiveMap; 