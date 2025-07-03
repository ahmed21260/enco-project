import React, { useEffect, useState } from 'react';
import { db } from '../../firebaseConfig';
import { collection, getDocs, onSnapshot } from 'firebase/firestore';
import './BonsAttachement.css';

// MOCK DATA (remplace par Firestore si dispo)
const mockBons = [
  { id: 'b1', chantier: 'Chantier A', date: '2024-07-01', operateur: 'Dupont', statut: 'Validé', details: 'Bon n°123', photo: '/photos/bon1.jpg' },
  { id: 'b2', chantier: 'Chantier B', date: '2024-07-01', operateur: 'Martin', statut: 'En attente', details: 'Bon n°124', photo: '/photos/bon2.jpg' },
  { id: 'b3', chantier: 'Chantier A', date: '2024-06-30', operateur: 'Durand', statut: 'Validé', details: 'Bon n°125', photo: '/photos/bon3.jpg' },
];

// Si tu utilises une API pour les bons, mets ici l'URL prod :
const API_BONS_URL = 'https://believable-motivation-production.up.railway.app/api/bons_attachement';

function exportCSV(data) {
  const csv = [
    ['ID', 'Chantier', 'Date', 'Opérateur', 'Statut', 'Détails'],
    ...data.map(b => [b.id, b.chantier, b.date, b.operateur, b.statut, b.details])
  ].map(e => e.join(';')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'bons_attachement.csv';
  a.click();
  URL.revokeObjectURL(url);
}

const BonsAttachement = () => {
  const [bons, setBons] = useState([]);
  const [chantier, setChantier] = useState('');
  const [date, setDate] = useState('');
  const [lightbox, setLightbox] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const unsub = onSnapshot(collection(db, 'bons_attachement'), snap => {
      setBons(snap.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      setLoading(false);
    }, (err) => {
      setLoading(false);
      setBons([]);
    });
    return () => unsub();
  }, []);

  const filtered = bons.filter(b =>
    (!chantier || b.chantier === chantier) &&
    (!date || b.date === date)
  );

  const chantiers = Array.from(new Set(bons.map(b => b.chantier)));

  return (
    <div className="bons-section">
      <h2>📄 Bons d'attachement</h2>
      <div className="bons-filtres">
        <select value={chantier} onChange={e => setChantier(e.target.value)}>
          <option value="">Tous les chantiers</option>
          {chantiers.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <input type="date" value={date} onChange={e => setDate(e.target.value)} />
        <button onClick={() => exportCSV(filtered)}>Exporter CSV</button>
      </div>
      <div className="bons-list">
        {loading ? (
          <div>Chargement…</div>
        ) : filtered.length === 0 ? (
          <div>Aucun bon d'attachement disponible</div>
        ) : filtered.map(bon => (
          <div className="bon-card" key={bon.id}>
            {(bon.url || bon.photo || bon.urlDocument) ? (
              <img
                src={bon.url || bon.photo || bon.urlDocument}
                alt={bon.details || bon.type || 'Bon'}
                className="bon-photo"
                style={{ cursor: 'pointer' }}
                onClick={() => setLightbox(bon.url || bon.photo || bon.urlDocument)}
                onError={e => e.target.style.display='none'}
              />
            ) : null}
            <div className="bon-info">
              <h4>{bon.chantier} - {bon.date}</h4>
              <p><b>Opérateur :</b> {bon.operateur || bon.operatorId}</p>
              <p><b>Statut :</b> {bon.statut || bon.status}</p>
              <p><b>Détails :</b> {bon.details || bon.type}</p>
            </div>
          </div>
        ))}
      </div>
      {lightbox && (
        <div className="lightbox-overlay" onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="agrandi" className="lightbox-img" />
        </div>
      )}
    </div>
  );
};

export default BonsAttachement; 