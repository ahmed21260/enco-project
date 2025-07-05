import React, { useState, useEffect, useRef } from 'react';
import './CardsSummary.css';
import { useOperateursLive } from '../hooks/useOperateursLive';

const Card = ({ title, value, icon, color, onClick, active, disabled }) => (
  <div
    className="card-summary"
    style={{
      borderLeft: `5px solid ${color}`,
      cursor: disabled ? 'not-allowed' : 'pointer',
      background: active ? '#f8f9fa' : '#fff',
      boxShadow: active ? '0 2px 8px rgba(0,0,0,0.08)' : 'none',
      flex: 1,
      minWidth: 180,
      margin: '0 8px',
      opacity: disabled ? 0.6 : 1,
      transition: 'background 0.2s, opacity 0.2s',
    }}
    onClick={disabled ? undefined : onClick}
  >
    <div className="card-icon">{icon}</div>
    <div className="card-content">
      <div className="card-title">{title}</div>
      <div className="card-value">{value}</div>
    </div>
  </div>
);

const CardsSummary = () => {
  const { stats, operateursLive, operateursEnPoste, urgences, anomalies, checklists } = useOperateursLive();
  const [active, setActive] = useState(null);
  // États "non traitées" pour chaque type (id)
  const unread = {
    anomalies: anomalies.map(a => a.id),
    urgences: urgences.map(u => u.id),
    checklists: checklists.map(c => c.id),
    finPoste: operateursEnPoste.map(o => o.id || o.operateur_id),
  };
  // Mémoriser la liste précédente pour ajouter les nouvelles
  const prevIds = useRef({
    anomalies: anomalies.map(a => a.id),
    urgences: urgences.map(u => u.id),
    checklists: checklists.map(c => c.id),
    finPoste: operateursLive.filter(o => o.type === 'fin_de_poste').map(o => o.id || o.operateur_id),
  });
  useEffect(() => {
    // setUnread({
    //   anomalies: anomalies.map(a => a.id),
    //   urgences: urgences.map(u => u.id),
    //   checklists: checklists.map(c => c.id),
    //   finPoste: operateursEnPoste.map(o => o.id || o.operateur_id),
    // });
  }, [anomalies, urgences, checklists, operateursEnPoste]);

  const nbActifs = operateursEnPoste.length;
  const cards = [
    { key: 'operateurs', title: "Opérateurs actifs / total", value: `${stats.enPoste} / ${stats.total}`, icon: "👷", color: "#28a745", enabled: nbActifs > 0 },
    { key: 'anomalies', title: "Anomalies", value: unread.anomalies.length, icon: "🚨", color: "#ffc107", enabled: unread.anomalies.length > 0 },
    { key: 'urgences', title: "Urgences", value: unread.urgences.length, icon: "🚨", color: "#e74c3c", enabled: unread.urgences.length > 0 },
    { key: 'checklists', title: "Checklists", value: unread.checklists.length, icon: "✅", color: "#20c997", enabled: unread.checklists.length > 0 },
    { key: 'finPoste', title: "Fins de poste", value: unread.finPoste.length, icon: "🔴", color: "#dc3545", enabled: unread.finPoste.length > 0 },
  ];
  // Détail métier pour chaque type (uniquement non traitées)
  const details = {
    anomalies: anomalies && unread.anomalies.length > 0 ? (
      <ul style={{margin:0, paddingLeft:18}}>{anomalies.filter(a => unread.anomalies.includes(a.id)).slice(0,5).map((a,i) => <li key={a.id} style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>{a.nom || a.operateur_id} : {a.description || 'Non renseignée'} <button style={{marginLeft:8, background:'#007bff', color:'#fff', border:'none', borderRadius:6, padding:'2px 10px', cursor:'pointer', fontSize:13}} onClick={() => setUnread(u => ({...u, anomalies: u.anomalies.filter(id => id !== a.id)}))}>Traiter</button></li>)}</ul>
    ) : <div style={{color:'#888'}}>Aucune anomalie non traitée</div>,
    urgences: urgences && unread.urgences.length > 0 ? (
      <ul style={{margin:0, paddingLeft:18}}>{urgences.filter(u2 => unread.urgences.includes(u2.id)).slice(0,5).map((u,i) => <li key={u.id} style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>{u.nom || u.operateur_id} : {u.description || 'Non renseignée'} <button style={{marginLeft:8, background:'#007bff', color:'#fff', border:'none', borderRadius:6, padding:'2px 10px', cursor:'pointer', fontSize:13}} onClick={() => setUnread(u2s => ({...u2s, urgences: u2s.urgences.filter(id => id !== u.id)}))}>Traiter</button></li>)}</ul>
    ) : <div style={{color:'#888'}}>Aucune urgence non traitée</div>,
    checklists: checklists && unread.checklists.length > 0 ? (
      <ul style={{margin:0, paddingLeft:18}}>{checklists.filter(c => unread.checklists.includes(c.id)).slice(0,5).map((c,i) => <li key={c.id} style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>{c.nom || c.operateur_id} : {c.statut || 'Checklist complétée'} <button style={{marginLeft:8, background:'#007bff', color:'#fff', border:'none', borderRadius:6, padding:'2px 10px', cursor:'pointer', fontSize:13}} onClick={() => setUnread(u => ({...u, checklists: u.checklists.filter(id => id !== c.id)}))}>Traiter</button></li>)}</ul>
    ) : <div style={{color:'#888'}}>Aucune checklist non traitée</div>,
    finPoste: operateursLive && unread.finPoste.length > 0 ? (
      <ul style={{margin:0, paddingLeft:18}}>{operateursLive.filter(o => o.type === 'fin_de_poste' && unread.finPoste.includes(o.id || o.operateur_id)).slice(0,5).map((o,i) => <li key={o.id || o.operateur_id} style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>{o.nom || o.operateur_id} : Fin de poste <button style={{marginLeft:8, background:'#007bff', color:'#fff', border:'none', borderRadius:6, padding:'2px 10px', cursor:'pointer', fontSize:13}} onClick={() => setUnread(u => ({...u, finPoste: u.finPoste.filter(id => id !== (o.id || o.operateur_id))}))}>Traiter</button></li>)}</ul>
    ) : <div style={{color:'#888'}}>Aucune fin de poste non traitée</div>,
    operateurs: operateursEnPoste && operateursEnPoste.length > 0 ? (
      <ul style={{margin:0, paddingLeft:18}}>{operateursEnPoste.map((o,i) => {
        // Calcul du temps depuis la prise de poste (gestion multi-format)
        let duree = '';
        let start = null;
        if (o.timestamp) {
          if (typeof o.timestamp === 'string' || o.timestamp instanceof String) {
            start = new Date(o.timestamp);
          } else if (o.timestamp && typeof o.timestamp.seconds === 'number') {
            start = new Date(o.timestamp.seconds * 1000);
          } else if (o.timestamp instanceof Date) {
            start = o.timestamp;
          }
          if (start && !isNaN(start.getTime())) {
            const now = new Date();
            const diffMs = now - start;
            const diffH = Math.floor(diffMs / (1000*60*60));
            const diffM = Math.floor((diffMs / (1000*60)) % 60);
            duree = diffH > 0 ? `${diffH}h${diffM.toString().padStart(2,'0')}` : `${diffM} min`;
          } else {
            duree = '-';
          }
        }
        return <li key={o.id || o.operateur_id} style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>{o.nom || o.operateur_id} <span style={{marginLeft:8, color:'#888', fontSize:13}}>{duree}</span></li>;
      })}</ul>
    ) : <div style={{color:'#888'}}>Aucun opérateur en poste</div>,
  };
  // Fermer le détail (ne remet plus tout à zéro)
  const handleClose = () => {
    setActive(null);
  };
  return (
    <div className="cards-summary-horizontal-container" style={{ display: 'flex', flexDirection: 'row', gap: 0, marginBottom: 24, width: '100%' }}>
      {cards.map((card, idx) => (
        <div key={card.title} style={{ flex: 1, position: 'relative' }}>
          <Card {...card} onClick={() => {
            if (card.enabled) setActive(active === card.key ? null : card.key);
          }} active={active === card.key} disabled={!card.enabled} />
          {active === card.key && card.enabled && (
            <div className="card-summary-details" style={{ position: 'absolute', left: 0, right: 0, top: '100%', background: '#f8f9fa', borderRadius: 8, padding: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', zIndex: 10, marginTop: 4 }}>
              <b>Détail {card.title} :</b>
              <div style={{marginTop:6}}>{details[card.key]}</div>
              <button style={{marginTop:10, float:'right', background:'#888', color:'#fff', border:'none', borderRadius:6, padding:'4px 16px', cursor:'pointer'}} onClick={handleClose}>Fermer</button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default CardsSummary; 