import React, { useState, useEffect } from 'react';
import { collection, getDocs } from 'firebase/firestore';
import { db } from '../firebaseConfig';

const PhotoTest = () => {
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPhotos();
  }, []);

  const loadPhotos = async () => {
    try {
      setLoading(true);
      const photosSnapshot = await getDocs(collection(db, 'photos'));
      const photosData = photosSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setPhotos(photosData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const testImageUrl = (url) => {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve({ url, status: 'success', width: img.width, height: img.height });
      img.onerror = () => resolve({ url, status: 'error' });
      img.src = url;
    });
  };

  const [testResults, setTestResults] = useState({});

  const runImageTests = async () => {
    const results = {};
    
    for (const photo of photos) {
      const url = photo.url || photo.urlPhoto || photo.photoURL || photo.photoUrl;
      if (url) {
        results[photo.id] = await testImageUrl(url);
      }
    }
    
    setTestResults(results);
  };

  if (loading) return <div>Chargement des photos...</div>;
  if (error) return <div>Erreur: {error}</div>;

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>🧪 Test d'affichage des photos</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={runImageTests}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          🔍 Tester toutes les images
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>📊 Statistiques</h3>
        <p>Total photos: {photos.length}</p>
        <p>Photos avec URL: {photos.filter(p => p.url || p.urlPhoto || p.photoURL || p.photoUrl).length}</p>
        <p>Tests réussis: {Object.values(testResults).filter(r => r.status === 'success').length}</p>
        <p>Tests échoués: {Object.values(testResults).filter(r => r.status === 'error').length}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
        {photos.map((photo) => {
          const url = photo.url || photo.urlPhoto || photo.photoURL || photo.photoUrl;
          const testResult = testResults[photo.id];
          
          return (
            <div 
              key={photo.id} 
              style={{
                border: '1px solid #ddd',
                borderRadius: '8px',
                padding: '15px',
                backgroundColor: testResult?.status === 'error' ? '#ffe6e6' : '#f8f9fa'
              }}
            >
              <h4>Photo {photo.id}</h4>
              <p><strong>URL:</strong> {url || 'Aucune URL'}</p>
              <p><strong>Opérateur:</strong> {photo.operateur_id || photo.operatorId || 'Inconnu'}</p>
              <p><strong>Timestamp:</strong> {photo.timestamp || 'Inconnu'}</p>
              
              {testResult && (
                <div style={{ marginTop: '10px' }}>
                  <p><strong>Test:</strong> 
                    <span style={{ 
                      color: testResult.status === 'success' ? 'green' : 'red',
                      fontWeight: 'bold'
                    }}>
                      {testResult.status === 'success' ? '✅ Succès' : '❌ Échec'}
                    </span>
                  </p>
                  {testResult.status === 'success' && (
                    <p><strong>Dimensions:</strong> {testResult.width} x {testResult.height}</p>
                  )}
                </div>
              )}
              
              {url && (
                <div style={{ marginTop: '10px' }}>
                  <img 
                    src={url} 
                    alt="Test" 
                    style={{
                      maxWidth: '100%',
                      maxHeight: '200px',
                      border: testResult?.status === 'error' ? '2px solid red' : '1px solid #ddd',
                      borderRadius: '4px'
                    }}
                    onError={(e) => {
                      e.target.style.border = '2px solid red';
                      e.target.style.opacity = '0.5';
                    }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {photos.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          <h3>📭 Aucune photo trouvée</h3>
          <p>Il n'y a pas de photos dans la collection Firestore.</p>
        </div>
      )}
    </div>
  );
};

export default PhotoTest; 