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

const isCritique = desc => {
  if (!desc) return false;
  const d = desc.toLowerCase();
  return d.includes('pneu') || d.includes('fuite') || d.includes('frein') || d.includes('huile') || d.includes('moteur') || d.includes('urgence');
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
      {sorted.map((item, idx) => (
        <div
          className="timeline-item"
          key={idx}
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 18,
            background: idx % 2 === 0 ? '#f8f9fa' : '#fff',
            borderRadius: 14,
            marginBottom: 18,
            padding: '18px 22px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.06)',
            minHeight: 70,
            flexWrap: 'wrap',
          }}
        >
          <div style={{ fontSize: 28, marginRight: 8, minWidth: 38, textAlign: 'center' }}>
            {typeToIcon[item.type] || '🕒'}
          </div>
          <div style={{ flex: 1, minWidth: 180 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 2 }}>
              <span style={{ fontWeight: 700, color: '#007bff', fontSize: 17, minWidth: 60 }}>{item.timestamp ? new Date(item.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : ''}</span>
              <span style={{ fontWeight: 600, fontSize: 16 }}>{item.nom || item.operateur_id}</span>
              {item.type === 'anomalie' ? (
                <>
                  <span style={{
                    background: '#ffc10722', color: '#ffc107', borderRadius: 8, padding: '2px 12px', fontWeight: 600, fontSize: 14, marginLeft: 4, minWidth: 80, textAlign: 'center',
                  }}>Anomalie</span>
                  {item.description && (
                    <>
                      <span style={{
                        background: isCritique(item.description) ? '#fd7e14' : '#eee',
                        color: isCritique(item.description) ? '#fff' : '#888',
                        borderRadius: 8,
                        padding: '2px 12px',
                        fontWeight: 700,
                        fontSize: 14,
                        marginLeft: 8,
                        textAlign: 'center',
                        boxShadow: isCritique(item.description) ? '0 0 6px #fd7e14' : 'none',
                      }}>{item.description}</span>
                      {(!item.statut || !['traitée', 'traité', 'résolue', 'résolu'].includes(item.statut.toLowerCase())) && (
                        <span style={{
                          background: '#e74c3c',
                          color: '#fff',
                          borderRadius: 8,
                          padding: '2px 10px',
                          fontWeight: 700,
                          fontSize: 13,
                          marginLeft: 8,
                          textAlign: 'center',
                          display: 'inline-flex',
                          alignItems: 'center',
                          boxShadow: '0 0 6px #e74c3c55',
                        }}>
                          ⚠️ À traiter
                        </span>
                      )}
                    </>
                  )}
                </>
              ) : (
                <span style={{
                  background: item.type === 'prise_de_poste' ? '#28a74522' : item.type === 'fin' ? '#dc354522' : item.type === 'urgence' ? '#e74c3c22' : item.type === 'checklist' ? '#20c99722' : '#eee',
                  color: item.type === 'prise_de_poste' ? '#28a745' : item.type === 'fin' ? '#dc3545' : item.type === 'urgence' ? '#e74c3c' : item.type === 'checklist' ? '#20c997' : '#888',
                  borderRadius: 8,
                  padding: '2px 12px',
                  fontWeight: 600,
                  fontSize: 14,
                  marginLeft: 4,
                  minWidth: 80,
                  textAlign: 'center',
                }}>{typeToLabel[item.type] || item.type}</span>
              )}
            </div>
            {item.type !== 'anomalie' && item.description && <div style={{ fontSize: 14, color: '#333', marginTop: 2 }}>{item.description}</div>}
            {item.statut && <div style={{ fontSize: 13, color: '#888', marginTop: 2 }}>Statut : {item.statut}</div>}
          </div>
        </div>
      ))}
    </div>
  );
};

export default TimelineActions; 