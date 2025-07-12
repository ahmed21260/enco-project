import React, { useEffect, useState } from 'react';
import './Operateurs.css';
import { collection, query, where, onSnapshot } from 'firebase/firestore';
import { db } from '../../firebaseConfig';
import { useOperateursLive } from '../hooks/useOperateursLive';

const API_OPERATEURS = 'https://believable-motivation-production.up.railway.app/api/operateurs';
const API_POSITIONS = 'https://believable-motivation-production.up.railway.app/api/positions';
const API_ANOMALIES = 'https://believable-motivation-production.up.railway.app/api/anomalies';
const API_URGENCES = 'https://believable-motivation-production.up.railway.app/api/urgences';
const API_MAINTENANCE = 'https://believable-motivation-production.up.railway.app/api/maintenance_issues';

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

const FicheInfos = ({ operateur, prises }) => (
  <div>
    <b>👤 {operateur.nom}</b><br/>
    <b>Statut :</b> {operateur.status || '—'}<br/>
    <b>Poste :</b> {operateur.poste || '—'}<br/>
    <b>Chantier :</b> {operateur.chantier || '—'}<br/>
    <b>Dernière prise :</b> {prises[0] ? new Date(prises[0].heure).toLocaleString('fr-FR') : '—'}<br/>
    {/* Affichage checklist */}
    {prises[0] && prises[0].checklistEffectuee && (
      <div style={{marginTop:8, background:'#e8f5e9', padding:8, borderRadius:6}}>
        <b>✅ Checklist effectuée</b>
        <ul style={{margin:'6px 0 0 0', paddingLeft:18}}>
          {prises[0].checklist && Object.entries(prises[0].checklist).map(([q, a], idx) => (
            <li key={idx}><b>{q}</b> : {a}</li>
          ))}
        </ul>
      </div>
    )}
  </div>
);
const FichePhotos = ({ photos }) => (
  <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
    {photos.length === 0 && <span style={{color:'#888'}}>Aucune photo</span>}
    {photos.map((photo, idx) => (
      <img key={idx} src={photo.urlPhoto} alt="" style={{width:64, height:64, objectFit:'cover', borderRadius:6, cursor:'pointer'}} onClick={() => window.open(photo.urlPhoto, '_blank')} />
    ))}
  </div>
);
const FicheBons = ({ bons }) => (
  <div>
    {bons.length === 0 && <span style={{color:'#888'}}>Aucun bon</span>}
    {bons.map((bon, idx) => (
      <button key={idx} onClick={() => window.open(bon.urlDocument, '_blank')}>Consulter</button>
    ))}
  </div>
);
const FicheAnomalies = ({ anomalies }) => (
  <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
    {anomalies.length === 0 && <li style={{color:'#888'}}>Aucune anomalie</li>}
    {anomalies.map((a, idx) => (
      <li key={idx}>{a.timestamp} {a.description || ''} {a.firebase_url && <a href={a.firebase_url} target="_blank" rel="noopener noreferrer">📸</a>}</li>
    ))}
  </ul>
);
const FicheUrgences = ({ urgences }) => (
  <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
    {urgences.length === 0 && <li style={{color:'#888'}}>Aucune urgence</li>}
    {urgences.map((u, idx) => (
      <li key={idx}>{u.timestamp} {u.type} {u.firebase_url && <a href={u.firebase_url} target="_blank" rel="noopener noreferrer">📸</a>}</li>
    ))}
  </ul>
);
const FicheMaintenance = ({ maintenance }) => (
  <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
    {maintenance.length === 0 && <li style={{color:'#888'}}>Aucun incident déclaré.</li>}
    {maintenance.map((m, idx) => (
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
  </ul>
);
const FicheHistorique = ({ historique }) => (
  <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
    {historique.length === 0 && <li style={{color:'#888'}}>Aucun historique</li>}
    {historique.map((h, idx) => (
      <li key={idx}>{h.timestamp} {h.type} {h.description || ''}</li>
    ))}
  </ul>
);
const FicheStats = ({ stats }) => (
  <div>
    <b>Prises de poste :</b> {stats.prises}<br/>
    <b>Photos :</b> {stats.photos}<br/>
    <b>Bons :</b> {stats.bons}<br/>
    <b>Anomalies :</b> {stats.anomalies}<br/>
    <b>Urgences :</b> {stats.urgences}<br/>
    <b>Maintenance :</b> {stats.maintenance}<br/>
  </div>
);

const Operateurs = () => {
  const { operateursLive, stats, positions, anomalies, urgences, checklists } = useOperateursLive();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [activeTab, setActiveTab] = useState('Infos');
  const [loadingFiche, setLoadingFiche] = useState(false);
  const [loading, setLoading] = useState(true);

  // Filtrer les opérateurs selon la recherche
  const filtered = operateursLive.filter(op => (op.nom || '').toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="operateurs-section">
      <h2>👷‍♂️ Liste des Opérateurs</h2>
      <input type="text" placeholder="Rechercher un opérateur..." value={search} onChange={e => setSearch(e.target.value)} />
      <div className="operateurs-list-table">
        <div className="operateurs-table-header">
          <span style={{width:48}}></span>
          <span style={{flex:2, fontWeight:700, color:'#333'}}>Nom</span>
          <span style={{flex:1, fontWeight:700, color:'#333'}}>Statut</span>
          <span style={{width:80}}></span>
        </div>
        {filtered.map((op, idx) => {
          const initial = (op.nom || '?').charAt(0).toUpperCase();
          const isPrise = op.type === 'prise_de_poste';
          const isFin = op.type === 'fin_de_poste' || op.type === 'fin';
          return (
            <div key={op.operatorId || op.operateur_id} className={`operateur-row${idx%2===0?' operateur-row-alt':''}`} onClick={() => setSelected(op)}>
              <div className="operateur-avatar" style={{
                width: 36, height: 36, fontSize: 18, marginRight: 0, border: `2px solid ${isPrise ? '#28a745' : isFin ? '#dc3545' : '#ccc'}`
              }}>{initial}</div>
              <span style={{ flex:2, fontWeight: 600, fontSize: 15, color: '#222' }}>{op.nom}</span>
              <span className="operateur-badge" style={{
                background: isPrise ? '#28a74522' : isFin ? '#dc354522' : '#eee',
                color: isPrise ? '#28a745' : isFin ? '#dc3545' : '#888',
                borderRadius: 16,
                padding: '3px 12px',
                fontWeight: 600,
                fontSize: 14,
                minWidth: 80,
                textAlign: 'center',
                display: 'inline-block',
              }}>{op.type === 'prise_de_poste' ? 'Prise de poste' : op.type === 'fin_de_poste' || op.type === 'fin' ? 'Fin de poste' : op.type}</span>
              <button className="operateur-detail-btn" style={{marginLeft:12, background:'#f5f5f5', border:'none', borderRadius:8, padding:'4px 12px', cursor:'pointer', fontWeight:600, color:'#1976d2'}} onClick={e => {e.stopPropagation();setSelected(op);}}>Détail</button>
            </div>
          );
        })}
      </div>
      {selected && (
        <div className="modal-overlay" style={{ position: 'fixed', top:0, left:0, width:'100vw', height:'100vh', background:'rgba(0,0,0,0.3)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000 }} onClick={() => setSelected(null)}>
          <div className="modal-content" style={{ background:'#fff', borderRadius:12, padding:32, minWidth:340, minHeight:180, boxShadow:'0 2px 16px rgba(0,0,0,0.15)', position:'relative' }} onClick={e => e.stopPropagation()}>
            <button style={{ position:'absolute', top:8, right:12, background:'none', border:'none', fontSize:22, cursor:'pointer' }} onClick={() => setSelected(null)}>×</button>
            <h2 style={{margin:0}}>{selected.nom}</h2>
            <Tabs tabs={['Infos', 'Photos', 'Bons', 'Anomalies', 'Urgences', 'Maintenance', 'Historique', 'Statistiques']} active={activeTab} onChange={setActiveTab} />
            {loadingFiche ? <div>Chargement fiche...</div> : (
              <div>
                {activeTab === 'Infos' && <FicheInfos operateur={selected} prises={positions.filter(p => p.operatorId === selected.operatorId)} />}
                {activeTab === 'Photos' && <FichePhotos photos={positions.filter(p => p.operatorId === selected.operatorId).map(p => ({ ...p, operatorId: selected.operatorId }))} />}
                {activeTab === 'Bons' && <FicheBons bons={positions.filter(p => p.operatorId === selected.operatorId).map(p => ({ ...p, operatorId: selected.operatorId }))} />}
                {activeTab === 'Anomalies' && <FicheAnomalies anomalies={anomalies.filter(a => a.operatorId === selected.operatorId)} />}
                {activeTab === 'Urgences' && <FicheUrgences urgences={urgences.filter(u => u.operatorId === selected.operatorId)} />}
                {activeTab === 'Maintenance' && <FicheMaintenance maintenance={positions.filter(p => p.operatorId === selected.operatorId).map(p => ({ ...p, operatorId: selected.operatorId }))} />}
                {activeTab === 'Historique' && <FicheHistorique historique={positions.filter(p => p.operatorId === selected.operatorId).map(p => ({ ...p, operatorId: selected.operatorId }))} />}
                {activeTab === 'Statistiques' && <FicheStats stats={stats} />}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Operateurs; 