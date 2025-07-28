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

  // Harmonisation des champs photo pour toutes les entités
  function getPhotosFromPrise(prise) {
    // Prise de poste : photos_urls (array d'URL)
    if (Array.isArray(prise.photos_urls) && prise.photos_urls.length > 0) return prise.photos_urls;
    // Compatibilité anciens champs
    if (Array.isArray(prise.photos_url) && prise.photos_url.length > 0) return prise.photos_url;
    if (prise.photoURL) return [prise.photoURL];
    if (prise.urlPhoto) return [prise.urlPhoto];
    if (prise.photoUrl) return [prise.photoUrl];
    return [];
  }
  function getPhotoFromAnomalie(anomalie) {
    // Anomalie : photoURL, photoUrl, urlPhoto
    return [anomalie.photoURL || anomalie.photoUrl || anomalie.urlPhoto].filter(Boolean);
  }
  function getPhotoFromUrgence(urgence) {
    return [urgence.photoURL || urgence.photoUrl || urgence.urlPhoto].filter(Boolean);
  }

  // Enrichir chaque entité avec un champ universel 'photos' (toujours un array)
  const positionsEnriched = positions.map(p => ({ ...p, photos: getPhotosFromPrise(p) }));
  const prisesPosteEnriched = prisesPoste.map(p => ({ ...p, photos: getPhotosFromPrise(p) }));
  const anomaliesEnriched = anomalies.map(a => ({ ...a, photos: getPhotoFromAnomalie(a) }));
  const urgencesEnriched = urgences.map(u => ({ ...u, photos: getPhotoFromUrgence(u) }));

  return {
    operateursLive: Object.values(latestByOperator),
    operateursEnPoste, // <-- la vraie liste métier avec timestamp prise de poste
    stats,
    positions: positionsEnriched,
    anomalies: anomaliesEnriched,
    urgences: urgencesEnriched,
    checklists,
    prisesPoste: prisesPosteEnriched,
    positionsLog,
    messagesIA,
    operateurs
  };
} 