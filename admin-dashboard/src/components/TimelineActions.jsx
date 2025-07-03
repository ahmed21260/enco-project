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

const TimelineActions = () => {
  const [actions, setActions] = useState([]);

  useEffect(() => {
    const unsubPos = onSnapshot(collection(db, 'positions_operateurs'), (snap) => {
      const pos = snap.docs.map(doc => ({ ...doc.data(), type: doc.data().type || 'prise_de_poste' }));
      setActions(prev => {
        const others = prev.filter(a => a._src !== 'pos');
        return [...others, ...pos.map(p => ({ ...p, _src: 'pos' }))];
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
    return () => { unsubPos(); unsubAno(); unsubChk(); };
  }, []);

  const sorted = actions
    .filter(a => a.timestamp)
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 20);

  return (
    <div className="timeline-actions">
      {sorted.map((item, idx) => (
        <div className="timeline-item" key={idx}>
          <div className="timeline-icon">{typeToIcon[item.type] || '🕒'}</div>
          <div className="timeline-content">
            <div className="timeline-time">{new Date(item.timestamp).toLocaleTimeString('fr-FR')}</div>
            <div className="timeline-user">{item.nom || item.operateur_id}</div>
            <div className="timeline-action">
              {item.type === 'anomalie' && `Anomalie : ${item.description}`}
              {item.type === 'checklist' && 'Checklist sécurité'}
              {item.type === 'prise_de_poste' && 'Prise de poste'}
              {item.type === 'fin' && 'Fin de poste'}
              {item.type === 'urgence' && 'Urgence'}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TimelineActions; 