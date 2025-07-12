import React, { useEffect, useState } from 'react';
import './GaleriePhotos.css';
import { collection, onSnapshot } from 'firebase/firestore';
import { db } from '../../firebaseConfig';

// URL de l'API à adapter selon ton backend
const API_URL = 'https://believable-motivation-production.up.railway.app/api/photos';
const API_QR_URL = 'https://believable-motivation-production.up.railway.app/api/scans_qr';
const API_PRISES_URL = 'https://believable-motivation-production.up.railway.app/api/prises_poste';

const formatDate = (iso) => {
  const d = new Date(iso);
  return d.toLocaleDateString('fr-FR');
};

const formatTime = (iso) => {
  const d = new Date(iso);
  return d.toLocaleTimeString('fr-FR');
};

// Ajout d'une fonction utilitaire pour récupérer l'ID opérateur universel
const getOperateurId = (photo) => photo.operateur_id || photo.operatorId || photo.telegram_id;
const getPhotoUrl = (photo) => photo.url || photo.urlPhoto;

// Ajout d'un composant pour la galerie d'un opérateur donné
export const GaleriePhotosOperateur = ({ operateurId, nom }) => {
  const [data, setData] = useState([]);
  useEffect(() => {
    const unsubPhotos = onSnapshot(collection(db, 'photos'), snap => setData(snap.docs.map(doc => ({ id: doc.id, ...doc.data() }))));
    return () => unsubPhotos();
  }, []);
  const photos = data.filter(photo => String(getOperateurId(photo)) === String(operateurId));
  return (
    <div>
      <h3>Photos de {nom}</h3>
      <div style={{ display: 'flex', gap: 8 }}>
        {photos.length === 0 && <div>Aucune photo trouvée pour cet opérateur.</div>}
        {photos.map((photo, idx) => (
          <img key={idx} src={getPhotoUrl(photo) || 'https://via.placeholder.com/80x80?text=Photo'} alt="photo" style={{ maxWidth: 80, maxHeight: 80, borderRadius: 6, marginRight: 6, cursor: 'pointer' }} />
        ))}
      </div>
    </div>
  );
};

const GaleriePhotos = () => {
  const [data, setData] = useState([]);
  const [qrData, setQrData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lightbox, setLightbox] = useState(null);
  const [prises, setPrises] = useState([]);

  useEffect(() => {
    const unsubPhotos = onSnapshot(collection(db, 'photos'), snap => setData(snap.docs.map(doc => ({ id: doc.id, ...doc.data() }))));
    // const unsubQr = onSnapshot(collection(db, 'scans_qr'), snap => setQrData(snap.docs.map(doc => ({ id: doc.id, ...doc.data() })))); // Pas encore implémenté dans le bot
    // const unsubPrises = onSnapshot(collection(db, 'prises_poste'), snap => setPrises(snap.docs.map(doc => ({ id: doc.id, ...doc.data() })))); // Prises dans positions_operateurs
    return () => {
      unsubPhotos();
      // unsubQr();
      // unsubPrises();
    };
  }, []);

  // Regrouper par opérateur puis par jour
  const photosParOperateur = {};
  data.forEach(photo => {
    // Accepte operateur_id ou operatorId
    const opId = getOperateurId(photo);
    if (!opId) return;
    if (!photosParOperateur[opId]) {
      photosParOperateur[opId] = { nom: photo.nom, jours: {} };
    }
    const jour = formatDate(photo.timestamp);
    if (!photosParOperateur[opId].jours[jour]) {
      photosParOperateur[opId].jours[jour] = [];
    }
    photosParOperateur[opId].jours[jour].push(photo);
  });

  // Regrouper les scans QR par opérateur puis par jour
  const qrParOperateur = {};
  qrData.forEach(scan => {
    if (!scan.operateur_id) return;
    if (!qrParOperateur[scan.operateur_id]) {
      qrParOperateur[scan.operateur_id] = { nom: scan.nom, jours: {} };
    }
    const jour = formatDate(scan.timestamp);
    if (!qrParOperateur[scan.operateur_id].jours[jour]) {
      qrParOperateur[scan.operateur_id].jours[jour] = [];
    }
    qrParOperateur[scan.operateur_id].jours[jour].push(scan);
  });

  // Indexer les scans QR par prise_poste_id
  const qrByPrise = {};
  qrData.forEach(scan => {
    if (scan.prise_poste_id) {
      qrByPrise[scan.prise_poste_id] = scan;
    }
  });

  // Indexer les photos par prise_poste_id
  const photosByPrise = {};
  data.forEach(photo => {
    if (photo.prise_poste_id) {
      if (!photosByPrise[photo.prise_poste_id]) photosByPrise[photo.prise_poste_id] = [];
      photosByPrise[photo.prise_poste_id].push(photo);
    }
  });

  // Regrouper les prises par opérateur et jour
  const prisesParOperateur = {};
  prises.forEach(prise => {
    if (!prise.operateur_id) return;
    if (!prisesParOperateur[prise.operateur_id]) prisesParOperateur[prise.operateur_id] = { nom: prise.nom, jours: {} };
    const jour = formatDate(prise.heure || prise.createdAt);
    if (!prisesParOperateur[prise.operateur_id].jours[jour]) prisesParOperateur[prise.operateur_id].jours[jour] = [];
    prisesParOperateur[prise.operateur_id].jours[jour].push(prise);
  });

  if (loading) return <div>Chargement...</div>;
  if (error) return <div>Erreur : {error}</div>;

  return (
    <div>
      <h2>🗓️ Prises de poste, machines et photos</h2>
      {Object.entries(prisesParOperateur).map(([operateurId, { nom, jours }]) => (
        <div key={operateurId} className="operateur-section">
          <h3>👤 {nom} (ID: {operateurId})</h3>
          {Object.entries(jours).map(([jour, prises]) => (
            <div key={jour} className="jour-section">
              <h4>📅 {jour}</h4>
              {prises.map((prise, idx) => (
                <div key={prise.id || idx} className="prise-block">
                  <div><b>Heure :</b> {formatTime(prise.heure || prise.createdAt)} | <b>Chantier :</b> {prise.chantier}</div>
                  <div><b>Machine utilisée :</b> {qrByPrise[prise.id]?.qr_content || '—'}</div>
                  <div><b>Photos :</b>
                    {(photosByPrise[prise.id] || []).map((photo, pidx) => (
                      <img key={pidx} src={getPhotoUrl(photo)} alt="photo" style={{ maxWidth: 80, maxHeight: 80, borderRadius: 6, marginRight: 6, cursor: 'pointer' }} onClick={() => setLightbox(getPhotoUrl(photo))} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      ))}
      <h2>📦 Historique des scans QR</h2>
      {Object.entries(qrParOperateur).map(([operateurId, { nom, jours }]) => (
        <div key={operateurId} className="operateur-section">
          <h3>👤 {nom} (ID: {operateurId})</h3>
          {Object.entries(jours).map(([jour, scans]) => (
            <div key={jour} className="jour-section">
              <h4>📅 {jour}</h4>
              <ul>
                {scans.map((scan, idx) => (
                  <li key={idx}>
                    <b>Heure :</b> {formatTime(scan.timestamp)} | <b>QR :</b> {scan.qr_content}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ))}
      {lightbox && (
        <div className="lightbox-overlay" onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="agrandi" className="lightbox-img" />
        </div>
      )}
    </div>
  );
};

export default GaleriePhotos; 