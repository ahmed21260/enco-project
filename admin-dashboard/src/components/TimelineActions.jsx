import React, { useEffect, useState } from 'react';
import './TimelineActions.css';
import { collection, onSnapshot } from 'firebase/firestore';
import { db } from '../../firebaseConfig';

const typeToIcon = {
  'prise_de_poste': '🟢',
  'fin': '🔴',
  'anomalie': '🚨',
  'checklist': '✅',
  'urgence': '🚨',
};

const typeToLabel = {
  'prise_de_poste': 'Prise de poste',
  'fin': 'Fin de poste',
  'anomalie': 'Anomalie',
  'checklist': 'Checklist sécurité',
  'urgence': 'Urgence',
};

const TimelineActions = () => {
  const [actions, setActions] = useState([]);

  useEffect(() => {
    const unsubPos = onSnapshot(collection(db, 'positions_operateurs'), (snap) => {
      const pos = snap.docs.map(doc => ({ ...doc.data(), type: doc.data().type || 'prise_de_poste', _src: 'pos_operateurs' }));
      setActions(prev => {
        const others = prev.filter(a => a._src !== 'pos_operateurs');
        return [...others, ...pos];
      });
    });
    const unsubPosLog = onSnapshot(collection(db, 'positions_log'), (snap) => {
      const poslog = snap.docs.map(doc => ({ ...doc.data(), type: doc.data().type || 'prise_de_poste', _src: 'pos_log' }));
      setActions(prev => {
        const others = prev.filter(a => a._src !== 'pos_log');
        return [...others, ...poslog];
      });
    });
    const unsubAno = onSnapshot(collection(db, 'anomalies'), (snap) => {
      const ano = snap.docs.map(doc => ({ ...doc.data(), type: 'anomalie', _src: 'ano' }));
      setActions(prev => {
        const others = prev.filter(a => a._src !== 'ano');
        return [...others, ...ano];
      });
    });
    const unsubChk = onSnapshot(collection(db, 'checklists'), (snap) => {
      const chk = snap.docs.map(doc => ({ ...doc.data(), type: 'checklist', _src: 'chk' }));
      setActions(prev => {
        const others = prev.filter(a => a._src !== 'chk');
        return [...others, ...chk];
      });
    });
    const unsubUrg = onSnapshot(collection(db, 'urgences'), (snap) => {
      const urg = snap.docs.map(doc => ({ ...doc.data(), type: 'urgence', _src: 'urg' }));
      setActions(prev => {
        const others = prev.filter(a => a._src !== 'urg');
        return [...others, ...urg];
      });
    });
    return () => { unsubPos(); unsubPosLog(); unsubAno(); unsubChk(); unsubUrg(); };
  }, []);

  const sorted = actions
    .filter(a => a.timestamp)
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 20);

  // Résumé rapide par type
  const resume = sorted.reduce((acc, a) => {
    acc[a.type] = (acc[a.type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="timeline-actions">
      <div className="timeline-resume" style={{display:'flex', gap:16, marginBottom:16, flexWrap:'wrap'}}>
        <span>🟢 Prises de poste : <b>{resume['prise_de_poste'] || 0}</b></span>
        <span>🔴 Fins de poste : <b>{resume['fin'] || 0}</b></span>
        <span>🚨 Urgences : <b>{resume['urgence'] || 0}</b></span>
        <span>🚨 Anomalies : <b>{resume['anomalie'] || 0}</b></span>
        <span>✅ Checklists : <b>{resume['checklist'] || 0}</b></span>
      </div>
      {sorted.map((item, idx) => (
        <div className="timeline-item" key={idx}>
          <div className="timeline-icon">{typeToIcon[item.type] || '🕒'}</div>
          <div className="timeline-content">
            <div className="timeline-time">{new Date(item.timestamp).toLocaleTimeString('fr-FR')}</div>
            <div className="timeline-user">{item.nom || item.operateur_id}</div>
            <div className="timeline-action">
              <b>{typeToLabel[item.type] || item.type}</b>
              {item.type === 'anomalie' && <> : {item.description || <span style={{color:'#888'}}>Non renseignée</span>}</>}
              {item.type === 'urgence' && <> : {item.description || <span style={{color:'#888'}}>Non renseignée</span>}</>}
              {item.type === 'checklist' && <> : {item.statut || 'Checklist complétée'}</>}
              {item.type === 'prise_de_poste' && item.description && <> : {item.description}</>}
              {item.type === 'fin' && item.description && <> : {item.description}</>}
            </div>
            {item.statut && <div className="timeline-status">Statut : {item.statut}</div>}
          </div>
        </div>
      ))}
    </div>
  );
};

export default TimelineActions; 