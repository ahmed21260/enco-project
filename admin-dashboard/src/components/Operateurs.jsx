import React, { useEffect, useState } from 'react';
import './Operateurs.css';

const API_OPERATEURS = 'http://localhost:3001/api/operateurs';
const API_POSITIONS = 'http://localhost:3001/api/positions';
const API_ANOMALIES = 'http://localhost:3001/api/anomalies';
const API_URGENCES = 'http://localhost:3001/api/urgences';
const API_MAINTENANCE = 'https://believable-motivation-production.up.railway.app/api/maintenance_issues';

const Operateurs = () => {
  const [operateurs, setOperateurs] = useState([]);
  const [positions, setPositions] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [urgences, setUrgences] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetch(API_OPERATEURS).then(r => r.json()).then(setOperateurs);
    fetch(API_POSITIONS).then(r => r.json()).then(setPositions);
    fetch(API_ANOMALIES).then(r => r.json()).then(setAnomalies);
    fetch(API_URGENCES).then(r => r.json()).then(setUrgences);
    fetch(API_MAINTENANCE).then(r => r.json()).then(setMaintenance);
  }, []);

  // Correction du bug : robustesse sur le filtre
  const filtered = operateurs.filter(op => (op.nom || '').toLowerCase().includes(search.toLowerCase()));

  // Regroupe les infos par opérateur
  const getDetails = (op) => {
    const prises = positions.filter(p => p.operateur_id === op.operateur_id && p.type === 'prise_de_poste');
    const fins = positions.filter(p => p.operateur_id === op.operateur_id && p.type === 'fin_de_poste');
    const opAnomalies = anomalies.filter(a => a.operateur_id === op.operateur_id);
    const opUrgences = urgences.filter(u => u.operateur_id === op.operateur_id);
    const opMaintenance = maintenance.filter(m => m.operatorId === op.operateur_id);
    return { prises, fins, anomalies: opAnomalies, urgences: opUrgences, maintenance: opMaintenance };
  };

  return (
    <div className="operateurs-section">
      <h2>👷 Liste des Opérateurs</h2>
      <input
        type="text"
        placeholder="Rechercher un opérateur..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="search-input"
      />
      <div className="operateurs-list">
        {filtered.map(op => (
          <div className="operateur-card" key={op.operateur_id} style={{ cursor: 'pointer', position: 'relative' }} onClick={() => setSelected(op)}>
            <div className="operateur-info">
              <h4>{op.nom}</h4>
              {/* Badge rouge si incident non résolu */}
              {maintenance.some(m => m.operatorId === op.operateur_id && m.statut !== 'resolu') && (
                <span title="Incident non résolu" style={{position:'absolute',top:8,right:36,fontSize:22,color:'#e00'}}>🛠️</span>
              )}
              {/* Alerte visuelle si urgence */}
              {urgences.some(u => u.operateur_id === op.operateur_id) && (
                <span title="Alerte urgence" style={{position:'absolute',top:8,right:8,fontSize:22,color:'#e00'}}>🚨</span>
              )}
            </div>
          </div>
        ))}
      </div>
      {selected && (
        <div className="modal-overlay" style={{ position: 'fixed', top:0, left:0, width:'100vw', height:'100vh', background:'rgba(0,0,0,0.3)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000 }} onClick={() => setSelected(null)}>
          <div className="modal-content" style={{ background:'#fff', borderRadius:12, padding:32, minWidth:340, minHeight:180, boxShadow:'0 2px 16px rgba(0,0,0,0.15)', position:'relative' }} onClick={e => e.stopPropagation()}>
            <button style={{ position:'absolute', top:8, right:12, background:'none', border:'none', fontSize:22, cursor:'pointer' }} onClick={() => setSelected(null)}>×</button>
            <h2 style={{margin:0}}>{selected.nom}</h2>
            <div style={{marginBottom:8, fontWeight:'bold'}}>Prises de poste :</div>
            <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
              {getDetails(selected).prises.map((p, idx) => (
                <li key={idx}>{p.timestamp} {p.type}</li>
              ))}
            </ul>
            <div style={{marginBottom:8, fontWeight:'bold'}}>Fins de poste :</div>
            <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
              {getDetails(selected).fins.map((f, idx) => (
                <li key={idx}>{f.timestamp} {f.type}</li>
              ))}
            </ul>
            <div style={{marginBottom:8, fontWeight:'bold'}}>Anomalies :</div>
            <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
              {getDetails(selected).anomalies.map((a, idx) => (
                <li key={idx}>{a.timestamp} {a.description || ''} {a.firebase_url && <a href={a.firebase_url} target="_blank" rel="noopener noreferrer">📸</a>}</li>
              ))}
            </ul>
            <div style={{marginBottom:8, fontWeight:'bold'}}>Urgences :</div>
            <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
              {getDetails(selected).urgences.map((u, idx) => (
                <li key={idx}>{u.timestamp} {u.type} {u.firebase_url && <a href={u.firebase_url} target="_blank" rel="noopener noreferrer">📸</a>}</li>
              ))}
            </ul>
            <div style={{marginBottom:8, fontWeight:'bold'}}>Incidents / Maintenance :</div>
            <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
              {getDetails(selected).maintenance.map((m, idx) => (
                <li key={idx} style={{marginBottom:8}}>
                  <b>{m.typeIncident}</b> ({m.date && m.date.slice(0,16).replace('T',' ')})<br/>
                  Machine : {m.machineId || '—'}<br/>
                  {m.photoURL && <a href={m.photoURL} target="_blank" rel="noopener noreferrer"><img src={m.photoURL} alt="photo panne" style={{width:48, height:48, objectFit:'cover', borderRadius:6, border:'1px solid #eee', margin:'6px 0'}} /></a>}
                  <span style={{color:'#888', fontSize:13}}>{m.commentaire}</span>
                  {m.statut !== 'resolu' && (
                    <button style={{marginLeft:12, background:'#e00', color:'#fff', border:'none', borderRadius:6, padding:'2px 10px', cursor:'pointer'}} onClick={() => {/* TODO: action admin pour traiter */}}>Traité</button>
                  )}
                </li>
              ))}
              {getDetails(selected).maintenance.length === 0 && <li style={{color:'#888'}}>Aucun incident déclaré.</li>}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default Operateurs; 