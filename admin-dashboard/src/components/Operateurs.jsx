import React, { useEffect, useState, useRef } from 'react';
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
const FichePhotos = ({ photosPrises, photosAnomalies, photosFinPoste }) => (
  <div style={{display:'flex', flexDirection:'column', gap:16}}>
    <div>
      <b>📌 Prises de poste</b>
      <div style={{display:'flex', gap:8, flexWrap:'wrap', marginTop:4}}>
        {photosPrises.length === 0 && <span style={{color:'#888'}}>Aucune photo de prise de poste</span>}
        {photosPrises.map((p, idx) => (
          <img key={p.url+idx} src={p.url} alt="" style={{width:64, height:64, objectFit:'cover', borderRadius:6, cursor:'pointer'}} onClick={() => window.open(p.url, '_blank')} />
        ))}
      </div>
    </div>
    <div>
      <b>🚨 Anomalies</b>
      <div style={{display:'flex', gap:8, flexWrap:'wrap', marginTop:4}}>
        {photosAnomalies.length === 0 && <span style={{color:'#888'}}>Aucune photo d'anomalie</span>}
        {photosAnomalies.map((a, idx) => (
          <img key={a.url+idx} src={a.url} alt="" style={{width:64, height:64, objectFit:'cover', borderRadius:6, cursor:'pointer'}} onClick={() => window.open(a.url, '_blank')} />
        ))}
      </div>
    </div>
    <div>
      <b>🔴 Fin de poste</b>
      <div style={{display:'flex', gap:8, flexWrap:'wrap', marginTop:4}}>
        {photosFinPoste.length === 0 && <span style={{color:'#888'}}>Aucune photo de fin de poste</span>}
        {photosFinPoste.map((f, idx) => (
          <img key={f.url+idx} src={f.url} alt="" style={{width:64, height:64, objectFit:'cover', borderRadius:6, cursor:'pointer'}} onClick={() => window.open(f.url, '_blank')} />
        ))}
      </div>
    </div>
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
      <li key={idx}>
        {a.timestamp} {a.description || ''}
        {Array.isArray(a.photos) && a.photos.map((url, i) => (
          <a key={i} href={url} target="_blank" rel="noopener noreferrer">📸</a>
        ))}
      </li>
    ))}
  </ul>
);
const FicheUrgences = ({ urgences }) => (
  <ul style={{maxHeight:120, overflowY:'auto', paddingLeft:18}}>
    {urgences.length === 0 && <li style={{color:'#888'}}>Aucune urgence</li>}
    {urgences.map((u, idx) => (
      <li key={idx}>
        {u.timestamp} {u.type}
        {Array.isArray(u.photos) && u.photos.map((url, i) => (
          <a key={i} href={url} target="_blank" rel="noopener noreferrer">📸</a>
        ))}
      </li>
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

const groupPhotosByDayAndType = (allPhotos) => {
  // Regroupe les photos par jour (YYYY-MM-DD) puis par type
  const grouped = {};
  allPhotos.forEach(photo => {
    if (!photo.timestamp) return;
    const day = new Date(photo.timestamp).toISOString().slice(0, 10); // YYYY-MM-DD
    if (!grouped[day]) grouped[day] = { 'prise_de_poste': [], 'fin_de_poste': [], 'anomalie': [], 'urgence': [] };
    if (photo.type && grouped[day][photo.type]) {
      grouped[day][photo.type].push(photo);
    }
  });
  return grouped;
};

const sectionOrder = ['prise_de_poste', 'fin_de_poste', 'anomalie', 'urgence'];
const sectionLabels = {
  'prise_de_poste': '📌 Prises de poste',
  'fin_de_poste': '🔴 Fin de poste',
  'anomalie': '🚨 Anomalies',
  'urgence': '⚡ Urgences',
};

const FichePhotosArchive = ({ groupedPhotos }) => {
  const typeLabels = {
    'prise_de_poste': '📌 Prises de poste',
    'fin_de_poste': '🔴 Fin de poste',
    'anomalie': '🚨 Anomalies',
    'urgence': '⚡ Urgences',
  };
  const typeOrder = ['prise_de_poste', 'fin_de_poste', 'anomalie', 'urgence'];
  const days = Object.keys(groupedPhotos).sort((a, b) => new Date(b) - new Date(a));
  const [openDays, setOpenDays] = useState(() => Object.fromEntries(days.map(day => [day, true])));
  const toggleDay = (day) => setOpenDays(prev => ({ ...prev, [day]: !prev[day] }));
  return (
    <div style={{display:'flex', flexDirection:'column', gap:32}}>
      {days.length === 0 && <div style={{color:'#888'}}>Aucune photo</div>}
      {days.map(day => (
        <div key={day} style={{background:'#fafbfc', borderRadius:12, boxShadow:'0 2px 8px #0001', padding:'18px 22px', marginBottom:0}}>
          <div style={{display:'flex', alignItems:'center', cursor:'pointer', marginBottom:10}} onClick={()=>toggleDay(day)}>
            <span style={{fontWeight:700, fontSize:18, color:'#222', flex:1}}>
              🗓️ {new Date(day).toLocaleDateString('fr-FR', {weekday:'long', year:'numeric', month:'long', day:'numeric'})}
            </span>
            <span style={{fontSize:18, color:'#1976d2', marginLeft:8}}>{openDays[day] ? '▼' : '▶'}</span>
          </div>
          {openDays[day] && (
            <div style={{display:'flex', flexDirection:'column', gap:18}}>
              {typeOrder.map(type => (
                <div key={type} style={{marginBottom:0}}>
                  <div style={{display:'flex', alignItems:'center', marginBottom:6}}>
                    <span style={{fontSize:20, marginRight:8}}>{typeLabels[type].split(' ')[0]}</span>
                    <span style={{fontWeight:600, fontSize:16, color:'#222'}}>{typeLabels[type].split(' ').slice(1).join(' ')}</span>
                    <span style={{marginLeft:10, background:'#1976d2', color:'#fff', borderRadius:12, fontSize:12, fontWeight:600, padding:'1px 8px'}}>{groupedPhotos[day][type].length}</span>
                  </div>
                  {groupedPhotos[day][type].length === 0 ? (
                    <div style={{color:'#bbb', fontSize:15, margin:'10px 0 8px 0'}}>Aucune</div>
                  ) : (
                    <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(110px, 1fr))', gap:14}}>
                      {groupedPhotos[day][type].map((p, idx) => (
                        <div key={p.url+idx} style={{display:'flex', flexDirection:'column', alignItems:'center', background:'#fff', borderRadius:8, boxShadow:'0 1px 4px #0001', padding:7}}>
                          <img src={p.url} alt="" style={{width:88, height:88, objectFit:'cover', borderRadius:6, marginBottom:5, cursor:'pointer'}} onClick={() => window.open(p.url, '_blank')} />
                          <span style={{fontSize:12, color:'#888', marginTop:2}}>{p.timestamp ? new Date(p.timestamp).toLocaleString('fr-FR') : ''}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const Operateurs = () => {
  const { operateursLive, stats, positions, anomalies, urgences, checklists, prisesPoste, positionsLog } = useOperateursLive();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [activeTab, setActiveTab] = useState('Infos');
  const [loadingFiche, setLoadingFiche] = useState(false);
  const [loading, setLoading] = useState(true);
  const [focusedSection, setFocusedSection] = useState(null); // null ou type section

  // Sécurité : reset focusedSection quand on ferme la modal opérateur
  const handleCloseModal = () => {
    setSelected(null);
    setFocusedSection(null);
  };

  const getLastPrise = (operatorId) => {
    return positions
      .filter(p => p.operatorId === operatorId && (p.type === 'prise_de_poste' || p.type === 'prise'))
      .sort((a, b) => new Date(b.timestamp || b.heure) - new Date(a.timestamp || a.heure))[0];
  };
  const getLastFin = (operatorId) => {
    return positionsLog
      .filter(p => (p.operatorId === operatorId) && (p.type === 'fin_de_poste' || p.type === 'fin'))
      .sort((a, b) => new Date(b.timestamp || b.heure) - new Date(a.timestamp || a.heure))[0];
  };

  // Filtrer les opérateurs selon la recherche
  const filtered = operateursLive.map(op => {
    const lastPrise = getLastPrise(op.operatorId);
    const lastFin = getLastFin(op.operatorId);
    let type = op.type;
    if (lastPrise && (!lastFin || new Date(lastPrise.timestamp || lastPrise.heure) > new Date(lastFin.timestamp || lastFin.heure))) {
      type = 'prise_de_poste';
    } else if (lastFin) {
      type = 'fin_de_poste';
    }
    return { ...op, type };
  }).filter(op => (op.nom || '').toLowerCase().includes(search.toLowerCase()));

  // Fusionne toutes les photos avec enrichissement type
  const photosPrises = prisesPoste
    .filter(p => (p.operatorId === selected?.operatorId || p.operateur_id === selected?.operatorId))
    .flatMap(p => Array.isArray(p.photos) ? p.photos.map(url => ({ url, timestamp: p.timestamp, type: 'prise_de_poste' })) : []);
  const photosAnomalies = anomalies
    .filter(a => (a.operatorId === selected?.operatorId || a.operateur_id === selected?.operatorId))
    .flatMap(a => Array.isArray(a.photos) ? a.photos.map(url => ({ url, timestamp: a.timestamp, type: 'anomalie' })) : []);
  const photosUrgences = urgences
    .filter(u => (u.operatorId === selected?.operatorId || u.operateur_id === selected?.operatorId))
    .flatMap(u => Array.isArray(u.photos) ? u.photos.map(url => ({ url, timestamp: u.timestamp, type: 'urgence' })) : []);
  const photosFinPoste = positionsLog
    .filter(p => (p.operatorId === selected?.operatorId || p.operateur_id === selected?.operatorId) && (p.type === 'fin_de_poste' || p.type === 'fin'))
    .flatMap(p => {
      if (Array.isArray(p.photos)) {
        return p.photos.map(url => ({ url, timestamp: p.timestamp, type: 'fin_de_poste' }));
      } else if (p.photoURL) {
        return [{ url: p.photoURL, timestamp: p.timestamp, type: 'fin_de_poste' }];
      } else if (p.photo_file_id) {
        return [{ url: `https://api.telegram.org/file/bot<YOUR_BOT_TOKEN>/${p.photo_file_id}`, timestamp: p.timestamp, type: 'fin_de_poste' }];
      }
      return [];
    });
  // Fusionne tout
  const allPhotos = [...photosPrises, ...photosFinPoste, ...photosAnomalies, ...photosUrgences];
  // Grouper par jour et type
  const groupedPhotos = groupPhotosByDayAndType(allPhotos);

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
        <div className="modal-overlay" style={{ position: 'fixed', top:0, left:0, width:'100vw', height:'100vh', background:'rgba(0,0,0,0.3)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000 }} onClick={handleCloseModal}>
          <div className="modal-content" style={{ background:'#fff', borderRadius:12, padding:32, minWidth:320, maxWidth:900, width:'95vw', maxHeight:'90vh', overflowY:'auto', boxShadow:'0 2px 16px rgba(0,0,0,0.15)', position:'relative' }} onClick={e => e.stopPropagation()}>
            <button style={{ position:'absolute', top:8, right:12, background:'none', border:'none', fontSize:22, cursor:'pointer' }} onClick={handleCloseModal}>×</button>
            <h2 style={{margin:0}}>{selected.nom}</h2>
            <Tabs tabs={['Infos', 'Photos', 'Bons', 'Anomalies', 'Urgences', 'Maintenance', 'Historique', 'Statistiques']} active={activeTab} onChange={setActiveTab} />
            {loadingFiche ? <div>Chargement fiche...</div> : (
              <div>
                {activeTab === 'Infos' && <FicheInfos operateur={selected} prises={getLastPrise(selected.operatorId) ? [getLastPrise(selected.operatorId)] : []} />}
                {activeTab === 'Photos' && (
                  <div>
                    <FichePhotosArchive groupedPhotos={groupedPhotos} />
                  </div>
                )}
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