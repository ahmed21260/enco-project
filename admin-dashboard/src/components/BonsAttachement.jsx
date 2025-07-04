import React, { useState, useEffect } from 'react';
import { collection, onSnapshot, query, orderBy } from 'firebase/firestore';
import { db } from '../../firebaseConfig';
import './BonsAttachement.css';

const BonsAttachement = () => {
  const [bons, setBons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    const q = query(collection(db, 'bons_attachement'), orderBy('timestamp', 'desc'));
    
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setBons(data);
      setLoading(false);
      setError(null);
    }, (err) => {
      setError('Erreur lors du chargement des bons d\'attachement');
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const formatDate = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString('fr-FR');
    } catch (e) {
      return 'Date invalide';
    }
  };

  const getFileIcon = (fileType) => {
    return fileType === 'photo' ? '📷' : '📄';
  };

  if (loading) {
    return (
      <div className="bons-container">
        <div className="loading">🔄 Chargement des bons d'attachement...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bons-container">
        <div className="error">❌ {error}</div>
      </div>
    );
  }

  return (
    <div className="bons-container">
      <div className="bons-header">
        <h2>📄 Bons d'attachement</h2>
        <div className="stats">
          <span>📋 {bons.length} bon(s) enregistré(s)</span>
        </div>
      </div>
      
      <div className="bons-list">
        {bons.length === 0 ? (
          <div className="no-data">
            📄 Aucun bon d'attachement disponible
            <br />
            <small>Les bons apparaîtront ici quand les opérateurs les enregistreront</small>
          </div>
        ) : (
          bons.map((bon) => (
            <div key={bon.id} className="bon-card">
              <div className="bon-header">
                <div className="bon-info">
                  <h3>{getFileIcon(bon.file_type)} {bon.numero}</h3>
                  <p className="bon-operator">👤 {bon.operatorName}</p>
                  <p className="bon-date">📅 {formatDate(bon.timestamp)}</p>
                </div>
                <div className="bon-type">
                  <span className="type-badge">{bon.type_travail}</span>
                </div>
              </div>
              
              {bon.description && (
                <div className="bon-description">
                  <p><strong>Description :</strong> {bon.description}</p>
                </div>
              )}
              
              <div className="bon-details">
                <p><strong>Type de fichier :</strong> {bon.file_type === 'photo' ? 'Photo' : 'Document PDF'}</p>
                <p><strong>ID fichier :</strong> {bon.file_id}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default BonsAttachement; 