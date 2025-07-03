import React, { useEffect, useState } from 'react';
import { realtimeDb } from '../firebaseRealtime';
import { ref, onValue, update } from 'firebase/database';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const PRIORITY_COLORS = {
  'haute': '#dc3545', // rouge
  'moyenne': '#fd7e14', // orange
  'basse': '#20c997', // vert
};
const STATUS_COLORS = {
  'en cours': '#ffc107', // jaune
  'résolu': '#28a745', // vert
};

const AlertesLive = () => {
  const [alertes, setAlertes] = useState([]);
  const [chantier, setChantier] = useState('');
  const [machine, setMachine] = useState('');
  const [operateur, setOperateur] = useState('');

  useEffect(() => {
    const alertesRef = ref(realtimeDb, 'alertes');
    const unsubscribe = onValue(alertesRef, (snapshot) => {
      const data = snapshot.val();
      const arr = data ? Object.entries(data).map(([id, value]) => ({ id, ...value })) : [];
      setAlertes(arr.sort((a, b) => b.timestamp - a.timestamp));
    });
    return () => unsubscribe();
  }, []);

  // Récupération des valeurs uniques pour les filtres
  const chantiers = Array.from(new Set(alertes.map(a => a.chantier).filter(Boolean)));
  const machines = Array.from(new Set(alertes.map(a => a.machine).filter(Boolean)));
  const operateurs = Array.from(new Set(alertes.map(a => a.operateur).filter(Boolean)));

  // Filtrage
  const filtered = alertes.filter(a =>
    (!chantier || a.chantier === chantier) &&
    (!machine || a.machine === machine) &&
    (!operateur || a.operateur === operateur)
  );

  // Action : marquer comme résolu
  const markAsResolved = (id) => {
    update(ref(realtimeDb, `alertes/${id}`), { statut: 'résolu' });
  };
  // Action : alerte envoyée (exemple, ici on change juste un champ)
  const markAlertSent = (id) => {
    update(ref(realtimeDb, `alertes/${id}`), { alerteEnvoyee: true });
  };

  return (
    <div className="alertes-live">
      <h3>🚨 Pannes & Alertes</h3>
      <div className="alertes-filtres" style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <select value={chantier} onChange={e => setChantier(e.target.value)}>
          <option value="">Tous les chantiers</option>
          {chantiers.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={machine} onChange={e => setMachine(e.target.value)}>
          <option value="">Toutes les machines</option>
          {machines.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <select value={operateur} onChange={e => setOperateur(e.target.value)}>
          <option value="">Tous les opérateurs</option>
          {operateurs.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      </div>
      <div className="alertes-list" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {filtered.length === 0 && <div>Aucune alerte pour ces filtres.</div>}
        {filtered.map(a => (
          <div key={a.id} className="alerte-card" style={{
            border: `2px solid ${PRIORITY_COLORS[a.priorite] || '#ccc'}`,
            borderRadius: 12,
            padding: 16,
            background: '#fff',
            boxShadow: '0 2px 8px rgba(0,0,0,0.07)',
            display: 'flex',
            gap: 16,
            alignItems: 'flex-start',
          }}>
            {/* Photo */}
            {a.photoUrl && (
              <img src={a.photoUrl} alt="photo alerte" style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 8, border: '1px solid #eee' }} />
            )}
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                {/* Priorité */}
                <span style={{
                  background: PRIORITY_COLORS[a.priorite] || '#eee',
                  color: '#fff',
                  borderRadius: 6,
                  padding: '2px 8px',
                  fontWeight: 'bold',
                  fontSize: 13,
                }}>
                  {a.priorite ? `🔴 ${a.priorite}` : 'Priorité N/A'}
                </span>
                {/* Statut */}
                <span style={{
                  background: STATUS_COLORS[a.statut] || '#eee',
                  color: '#222',
                  borderRadius: 6,
                  padding: '2px 8px',
                  fontWeight: 'bold',
                  fontSize: 13,
                }}>
                  {a.statut ? (a.statut === 'résolu' ? '🟢 Résolu' : '🟡 En cours') : 'Statut N/A'}
                </span>
                <span style={{ marginLeft: 8, color: '#888', fontSize: 13 }}>
                  {a.chantier && `🏗️ ${a.chantier}`} {a.machine && `| 🏭 ${a.machine}`} {a.operateur && `| 👷 ${a.operateur}`}
                </span>
              </div>
              <div style={{ fontWeight: 'bold', fontSize: 16, marginBottom: 4 }}>{a.type} : {a.message}</div>
              <div style={{ color: '#666', fontSize: 13, marginBottom: 4 }}>
                {a.timestamp && `[${new Date(a.timestamp).toLocaleString('fr-FR')}]`}
              </div>
              {/* Mini-carte si GPS */}
              {a.gps && a.gps.latitude && a.gps.longitude && (
                <div style={{ width: 180, height: 120, margin: '8px 0', borderRadius: 8, overflow: 'hidden', border: '1px solid #eee' }}>
                  <MapContainer center={[a.gps.latitude, a.gps.longitude]} zoom={15} style={{ width: '100%', height: '100%' }} scrollWheelZoom={false} dragging={false} doubleClickZoom={false} zoomControl={false} attributionControl={false}>
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    <Marker position={[a.gps.latitude, a.gps.longitude]} />
                  </MapContainer>
                </div>
              )}
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                {a.statut !== 'résolu' && (
                  <button onClick={() => markAsResolved(a.id)} style={{ background: '#28a745', color: '#fff', border: 'none', borderRadius: 6, padding: '6px 12px', cursor: 'pointer' }}>Marquer comme résolu</button>
                )}
                <button onClick={() => markAlertSent(a.id)} style={{ background: '#007bff', color: '#fff', border: 'none', borderRadius: 6, padding: '6px 12px', cursor: 'pointer' }}>Alerte envoyée</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
export default AlertesLive; 