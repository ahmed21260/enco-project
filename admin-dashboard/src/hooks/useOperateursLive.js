import { useEffect, useState } from 'react';
import { collection, onSnapshot } from 'firebase/firestore';
import { db } from '../firebaseConfig';

export function useOperateursLive() {
  const [positions, setPositions] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [urgences, setUrgences] = useState([]);
  const [checklists, setChecklists] = useState([]);

  useEffect(() => {
    const unsubPos = onSnapshot(collection(db, 'positions_operateurs'), snap => {
      setPositions(snap.docs.map(doc => doc.data()));
    });
    const unsubAno = onSnapshot(collection(db, 'anomalies'), snap => {
      setAnomalies(snap.docs.map(doc => doc.data()));
    });
    const unsubUrg = onSnapshot(collection(db, 'urgences'), snap => {
      setUrgences(snap.docs.map(doc => doc.data()));
    });
    const unsubChk = onSnapshot(collection(db, 'checklists'), snap => {
      setChecklists(snap.docs.map(doc => doc.data()));
    });
    return () => { unsubPos(); unsubAno(); unsubUrg(); unsubChk(); };
  }, []);

  // Logique métier centralisée : dernière action/statut par opérateur
  const latestByOperator = {};
  [...positions, ...anomalies, ...urgences, ...checklists].forEach(item => {
    const id = item.operatorId || item.operateur_id;
    if (!id) return;
    if (!latestByOperator[id] || new Date(item.timestamp) > new Date(latestByOperator[id].timestamp)) {
      latestByOperator[id] = item;
    }
  });

  // Stats globales
  const stats = {
    enPoste: Object.values(latestByOperator).filter(o => o.type === 'prise_de_poste').length,
    finPoste: Object.values(latestByOperator).filter(o => o.type === 'fin_de_poste' || o.type === 'fin').length,
    anomalies: Object.values(latestByOperator).filter(o => o.type === 'anomalie').length,
    urgences: Object.values(latestByOperator).filter(o => o.type === 'urgence').length,
    checklists: Object.values(latestByOperator).filter(o => o.type === 'checklist').length,
    total: Object.keys(latestByOperator).length
  };

  return {
    operateursLive: Object.values(latestByOperator),
    stats,
    positions,
    anomalies,
    urgences,
    checklists
  };
} 