import React, { useEffect, useState } from 'react';
import './Operateurs.css';
import { collection, query, where, onSnapshot } from 'firebase/firestore';
import { db } from '../../firebaseConfig';

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
  const [operateurs, setOperateurs] = useState([]);
  const [positions, setPositions] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [urgences, setUrgences] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [historique, setHistorique] = useState([]);
  const [stats, setStats] = useState({});
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [prises, setPrises] = useState([]);
  const [photos, setPhotos] = useState([]);
  const [bons, setBons] = useState([]);
  const [loadingFiche, setLoadingFiche] = useState(false);
  const [activeTab, setActiveTab] = useState('Infos');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const unsub = onSnapshot(collection(db, 'operateurs'), snap => {
      setOperateurs(snap.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      setLoading(false);
    }, (err) => {
      setLoading(false);
      setOperateurs([]);
    });
    return () => unsub();
  }, []);

  // Fonction pour mettre à jour les stats basées sur les données actuelles
  const updateStats = (prisesData, photosData, bonsData, anomaliesData, urgencesData, maintenanceData) => {
    setStats({
      prises: prisesData.length,
      photos: photosData.length,
      bons: bonsData.length,
      anomalies: anomaliesData.length,
      urgences: urgencesData.length,
      maintenance: maintenanceData.length
    });
  };

  // Fonction pour mettre à jour l'historique basé sur toutes les données
  const updateHistorique = (prisesData, photosData, bonsData, anomaliesData, urgencesData, maintenanceData) => {
    const allHistorique = [
      ...prisesData.map(prise => ({ type: 'prise', ...prise })),
      ...photosData.map(photo => ({ type: 'photo', ...photo })),
      ...bonsData.map(bon => ({ type: 'bon', ...bon })),
      ...anomaliesData.map(anomalie => ({ type: 'anomalie', ...anomalie })),
      ...urgencesData.map(urgence => ({ type: 'urgence', ...urgence })),
      ...maintenanceData.map(maintenance => ({ type: 'maintenance', ...maintenance }))
    ];
    allHistorique.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
    setHistorique(allHistorique);
  };

  useEffect(() => {
    if (!selected || !selected.operatorId) {
      // Nettoyer les données si aucun opérateur sélectionné
      setPrises([]);
      setPhotos([]);
      setBons([]);
      setAnomalies([]);
      setUrgences([]);
      setMaintenance([]);
      setHistorique([]);
      setStats({});
      setLoadingFiche(false);
      return;
    }

    setLoadingFiche(true);
    
    // Abonnement aux prises de poste de l'opérateur (dans positions_operateurs avec type="prise_de_poste")
    const qPrises = query(collection(db, 'positions_operateurs'), where('operatorId', '==', selected.operatorId), where('type', '==', 'prise_de_poste'));
    const unsubPrises = onSnapshot(qPrises, (prisesSnap) => {
      const prisesData = prisesSnap.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setPrises(prisesData);
      
      // Mettre à jour les stats et l'historique avec les nouvelles données
      updateStats(prisesData, photos, bons, anomalies, urgences, maintenance);
      updateHistorique(prisesData, photos, bons, anomalies, urgences, maintenance);
      setLoadingFiche(false);
      setActiveTab('Infos');
    });

    // Abonnement aux photos de l'opérateur
    const qPhotos = query(collection(db, 'photos'), where('operatorId', '==', selected.operatorId));
    const unsubPhotos = onSnapshot(qPhotos, (photosSnap) => {
      const photosData = photosSnap.docs.map(doc => ({ ...doc.data(), id: doc.id }));
      setPhotos(photosData);
      
      // Mettre à jour les stats et l'historique
      updateStats(prises, photosData, bons, anomalies, urgences, maintenance);
      updateHistorique(prises, photosData, bons, anomalies, urgences, maintenance);
    });

    // Abonnement aux bons d'attachement de l'opérateur (pas encore implémenté dans le bot)
    // const qBons = query(collection(db, 'bons_attachement'), where('operatorId', '==', selected.operatorId));
    // const unsubBons = onSnapshot(qBons, (bonsSnap) => {
    //   const bonsData = bonsSnap.docs.map(doc => ({ ...doc.data(), id: doc.id }));
    //   setBons(bonsData);
    //   
    //   // Mettre à jour les stats et l'historique
    //   updateStats(prises, photos, bonsData, anomalies, urgences, maintenance);
    //   updateHistorique(prises, photos, bonsData, anomalies, urgences, maintenance);
    // });
    const unsubBons = () => {}; // Placeholder pour les bons (pas encore implémenté)

    // Abonnement aux anomalies de l'opérateur
    const qAnomalies = query(collection(db, 'anomalies'), where('operatorId', '==', selected.operatorId));
    const unsubAnomalies = onSnapshot(qAnomalies, (anomaliesSnap) => {
      const anomaliesData = anomaliesSnap.docs.map(doc => ({ ...doc.data(), id: doc.id }));
      setAnomalies(anomaliesData);
      
      // Mettre à jour les stats et l'historique
      updateStats(prises, photos, bons, anomaliesData, urgences, maintenance);
      updateHistorique(prises, photos, bons, anomaliesData, urgences, maintenance);
    });

    // Abonnement aux urgences de l'opérateur
    const qUrgences = query(collection(db, 'incidents'), where('operatorId', '==', selected.operatorId));
    const unsubUrgences = onSnapshot(qUrgences, (urgencesSnap) => {
      const urgencesData = urgencesSnap.docs.map(doc => ({ ...doc.data(), id: doc.id }));
      setUrgences(urgencesData);
      
      // Mettre à jour les stats et l'historique
      updateStats(prises, photos, bons, anomalies, urgencesData, maintenance);
      updateHistorique(prises, photos, bons, anomalies, urgencesData, maintenance);
    });

    // Abonnement aux incidents de maintenance de l'opérateur (pas encore implémenté dans le bot)
    // const qMaintenance = query(collection(db, 'maintenance_issues'), where('operatorId', '==', selected.operatorId));
    // const unsubMaintenance = onSnapshot(qMaintenance, (maintenanceSnap) => {
    //   const maintenanceData = maintenanceSnap.docs.map(doc => ({ ...doc.data(), id: doc.id }));
    //   setMaintenance(maintenanceData);
    //   
    //   // Mettre à jour les stats et l'historique
    //   updateStats(prises, photos, bons, anomalies, urgences, maintenanceData);
    //   updateHistorique(prises, photos, bons, anomalies, urgences, maintenanceData);
    // });
    const unsubMaintenance = () => {}; // Placeholder pour la maintenance (pas encore implémenté)

    // Nettoyer tous les abonnements quand l'opérateur change ou le composant se démonte
    return () => {
      unsubPrises();
      unsubPhotos();
      unsubBons();
      unsubAnomalies();
      unsubUrgences();
      unsubMaintenance();
    };
  }, [selected]);

  const filtered = operateurs.filter(op => (op.nom || '').toLowerCase().includes(search.toLowerCase()));

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
        {loading ? (
          <div>Chargement…</div>
        ) : operateurs.length === 0 ? (
          <div>Aucun opérateur disponible</div>
        ) : operateurs.map(op => (
          <div className="operateur-card" key={op.id} style={{ cursor: 'pointer', position: 'relative' }} onClick={() => setSelected(op)}>
            <div className="operateur-info">
              <h4>{op.nom}</h4>
            </div>
          </div>
        ))}
      </div>
      {selected && (
        <div className="modal-overlay" style={{ position: 'fixed', top:0, left:0, width:'100vw', height:'100vh', background:'rgba(0,0,0,0.3)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000 }} onClick={() => setSelected(null)}>
          <div className="modal-content" style={{ background:'#fff', borderRadius:12, padding:32, minWidth:340, minHeight:180, boxShadow:'0 2px 16px rgba(0,0,0,0.15)', position:'relative' }} onClick={e => e.stopPropagation()}>
            <button style={{ position:'absolute', top:8, right:12, background:'none', border:'none', fontSize:22, cursor:'pointer' }} onClick={() => setSelected(null)}>×</button>
            <h2 style={{margin:0}}>{selected.nom}</h2>
            <Tabs tabs={['Infos', 'Photos', 'Bons', 'Anomalies', 'Urgences', 'Maintenance', 'Historique', 'Statistiques']} active={activeTab} onChange={setActiveTab} />
            {loadingFiche ? <div>Chargement fiche...</div> : (
              <div>
                {activeTab === 'Infos' && <FicheInfos operateur={selected} prises={prises} />}
                {activeTab === 'Photos' && <FichePhotos photos={photos.filter(p => p.operatorId === selected.operatorId)} />}
                {activeTab === 'Bons' && <FicheBons bons={bons.filter(b => b.operatorId === selected.operatorId)} />}
                {activeTab === 'Anomalies' && <FicheAnomalies anomalies={anomalies.filter(a => a.operatorId === selected.operatorId)} />}
                {activeTab === 'Urgences' && <FicheUrgences urgences={urgences.filter(u => u.operatorId === selected.operatorId)} />}
                {activeTab === 'Maintenance' && <FicheMaintenance maintenance={maintenance.filter(m => m.operatorId === selected.operatorId)} />}
                {activeTab === 'Historique' && <FicheHistorique historique={historique.filter(h => h.operatorId === selected.operatorId)} />}
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