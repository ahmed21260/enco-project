import { realtimeDb } from '../firebaseRealtime';
import { ref, onValue } from 'firebase/database';
import { useState, useEffect } from 'react';

const [positionsLive, setPositionsLive] = useState([]);

useEffect(() => {
  // Écoute live Realtime Database
  const positionsRef = ref(realtimeDb, 'positions');
  const unsubscribe = onValue(positionsRef, (snapshot) => {
    const data = snapshot.val();
    const arr = data ? Object.entries(data).map(([id, value]) => ({ id, ...value })) : [];
    setPositionsLive(arr);
  });
  return () => unsubscribe();
}, []);

// Remplace positions par positionsLive si dispo
const positionsToShow = positionsLive.length > 0 ? positionsLive : positions;

// Dans le rendu, remplace positions par positionsToShow 