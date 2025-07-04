import React, { useEffect, useState } from 'react';
import './TimelineActions.css';
import { collection, onSnapshot } from 'firebase/firestore';
import { db } from '../../firebaseConfig';
import { useOperateursLive } from '../hooks/useOperateursLive';

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
  const { positions, anomalies, urgences, checklists } = useOperateursLive();
  const actions = [
    ...positions.map(a => ({ ...a, type: a.type || 'prise_de_poste' })),
    ...anomalies.map(a => ({ ...a, type: 'anomalie' })),
    ...urgences.map(a => ({ ...a, type: 'urgence' })),
    ...checklists.map(a => ({ ...a, type: 'checklist' })),
  ];
  const sorted = actions.filter(a => a.timestamp).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 20);

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