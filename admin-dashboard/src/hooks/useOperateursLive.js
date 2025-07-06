import { useEffect, useState } from 'react';
import { collection, onSnapshot, collectionGroup } from 'firebase/firestore';
import { db } from '../firebaseConfig';

export function useOperateursLive() {
  const [positions, setPositions] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [urgences, setUrgences] = useState([]);
  const [checklists, setChecklists] = useState([]);
  const [prisesPoste, setPrisesPoste] = useState([]);
  const [positionsLog, setPositionsLog] = useState([]);
  const [messagesIA, setMessagesIA] = useState([]);
  const [operateurs, setOperateurs] = useState([]);

  useEffect(() => {
    // Écoute des positions actuelles des opérateurs
    const unsubPos = onSnapshot(collection(db, 'positions_operateurs'), snap => {
      setPositions(snap.docs.map(doc => doc.data()));
    });
    
    // Écoute des anomalies
    const unsubAno = onSnapshot(collection(db, 'anomalies'), snap => {
      setAnomalies(snap.docs.map(doc => doc.data()));
    });
    
    // Écoute des urgences
    const unsubUrg = onSnapshot(collection(db, 'urgences'), snap => {
      setUrgences(snap.docs.map(doc => doc.data()));
    });
    
    // Écoute des checklists
    const unsubChk = onSnapshot(collection(db, 'checklists'), snap => {
      setChecklists(snap.docs.map(doc => doc.data()));
    });
    
    // Écoute des prises de poste (historique détaillé)
    const unsubPrises = onSnapshot(collection(db, 'prises_poste'), snap => {
      setPrisesPoste(snap.docs.map(doc => doc.data()));
    });
    
    // Écoute du log des positions (historique complet)
    const unsubPosLog = onSnapshot(collection(db, 'positions_log'), snap => {
      setPositionsLog(snap.docs.map(doc => doc.data()));
    });
    
    // Écoute de tous les messages IA (collection group)
    const unsubMessages = onSnapshot(collectionGroup(db, 'messages'), snap => {
      setMessagesIA(snap.docs.map(doc => ({ id: doc.id, ...doc.data() })));
    });
    
    // Écoute des fiches opérateurs
    const unsubOperateurs = onSnapshot(collection(db, 'operateurs'), snap => {
      setOperateurs(snap.docs.map(doc => ({ id: doc.id, ...doc.data() })));
    });
    
    return () => { 
      unsubPos(); 
      unsubAno(); 
      unsubUrg(); 
      unsubChk(); 
      unsubPrises();
      unsubPosLog();
      unsubMessages();
      unsubOperateurs();
    };
  }, []);

  // Logique métier centralisée : dernière action/statut par opérateur (tous types)
  const latestByOperator = {};
  [...positions, ...anomalies, ...urgences, ...checklists, ...prisesPoste].forEach(item => {
    const id = item.operatorId || item.operateur_id;
    if (!id) return;
    if (!latestByOperator[id] || new Date(item.timestamp) > new Date(latestByOperator[id].timestamp)) {
      latestByOperator[id] = item;
    }
  });

  // Logique métier : dernière prise_de_poste par opérateur
  const prisePosteByOperator = {};
  prisesPoste.forEach(item => {
    const id = item.operatorId || item.operateur_id;
    if (!id) return;
    if (!prisePosteByOperator[id] || new Date(item.timestamp) > new Date(prisePosteByOperator[id].timestamp)) {
      prisePosteByOperator[id] = item;
    }
  });
  
  // Liste des opérateurs actuellement en poste (dernière action = prise_de_poste, pas de fin de poste après)
  const operateursEnPoste = Object.values(prisePosteByOperator).filter(prise => {
    const id = prise.operatorId || prise.operateur_id;
    // Chercher une fin de poste plus récente
    const fin = positionsLog.find(p => (p.operatorId || p.operateur_id) === id && (p.type === 'fin_de_poste' || p.type === 'fin') && new Date(p.timestamp) > new Date(prise.timestamp));
    return !fin;
  });

  // Stats globales enrichies
  const stats = {
    enPoste: operateursEnPoste.length,
    finPoste: Object.values(latestByOperator).filter(o => o.type === 'fin_de_poste' || o.type === 'fin').length,
    anomalies: anomalies.length,
    urgences: urgences.length,
    checklists: checklists.length,
    messagesIA: messagesIA.length,
    total: Object.keys(latestByOperator).length,
    operateurs: operateurs.length
  };

  return {
    operateursLive: Object.values(latestByOperator),
    operateursEnPoste, // <-- la vraie liste métier avec timestamp prise de poste
    stats,
    positions,
    anomalies,
    urgences,
    checklists,
    prisesPoste,
    positionsLog,
    messagesIA,
    operateurs
  };
} 