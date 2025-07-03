import React, { useState } from 'react';
import './CardsSummary.css';

const Card = ({ title, value, icon, color, onClick }) => (
  <div className="card-summary" style={{ borderLeft: `5px solid ${color}`, cursor: 'pointer' }} onClick={onClick}>
    <div className="card-icon">{icon}</div>
    <div className="card-content">
      <div className="card-title">{title}</div>
      <div className="card-value">{value}</div>
    </div>
  </div>
);

const CardsSummary = ({ stats, operateursActifs = [], alertesUrgenceList = [] }) => {
  const [modal, setModal] = useState(null);
  const cards = [
    { key: 'operateurs', title: "Opérateurs actifs / total", value: `${stats.enLigne} / ${stats.totalOperateurs}`, icon: "👷", color: "#28a745" },
    { key: 'bonsJour', title: "Bons d'attachement (jour)", value: stats.bonsJour, icon: "📄", color: "#007bff" },
    { key: 'bonsSemaine', title: "Bons d'attachement (semaine)", value: stats.bonsSemaine, icon: "📅", color: "#6f42c1" },
    { key: 'pannesEnCours', title: "Pannes en cours", value: stats.pannesEnCours, icon: "🛠️", color: "#dc3545" },
    { key: 'pannesResolues', title: "Pannes résolues", value: stats.pannesResolues, icon: "✅", color: "#20c997" },
    { key: 'alertesUrgence', title: "Alertes urgences SNCF", value: stats.alertesUrgence, icon: "🚨", color: "#fd7e14" },
  ];
  return (
    <>
      <div className="cards-summary-container">
        {cards.map((card, idx) => (
          <Card key={card.title} {...card} onClick={() => setModal(card)} />
        ))}
      </div>
      {modal && (
        <div className="modal-overlay" style={{ position: 'fixed', top:0, left:0, width:'100vw', height:'100vh', background:'rgba(0,0,0,0.3)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000 }} onClick={() => setModal(null)}>
          <div className="modal-content" style={{ background:'#fff', borderRadius:12, padding:32, minWidth:340, minHeight:120, boxShadow:'0 2px 16px rgba(0,0,0,0.15)', position:'relative' }} onClick={e => e.stopPropagation()}>
            <button style={{ position:'absolute', top:8, right:12, background:'none', border:'none', fontSize:22, cursor:'pointer' }} onClick={() => setModal(null)}>×</button>
            <h2 style={{marginBottom:16}}>{modal.icon} {modal.title}</h2>
            <div style={{fontSize:32, fontWeight:'bold', marginBottom:16}}>{modal.value}</div>
            {/* Affichage dynamique selon la carte */}
            {modal.key === 'operateurs' && (
              <div>
                <h4 style={{margin:'12px 0 8px'}}>Opérateurs actifs :</h4>
                {operateursActifs.length === 0 && <div style={{color:'#888'}}>Aucun opérateur actif.</div>}
                <ul style={{maxHeight:220, overflowY:'auto', paddingLeft:18}}>
                  {operateursActifs.map(op => (
                    <li key={op.operateur_id || op.id} style={{marginBottom:8, display:'flex', alignItems:'center', gap:8}}>
                      <span style={{fontWeight:'bold'}}>{op.nom}</span>
                      <span style={{color:'#666'}}>{op.poste}</span>
                      <span style={{color:'#007bff'}}>{op.timestamp && new Date(op.timestamp).toLocaleTimeString('fr-FR')}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {modal.key === 'alertesUrgence' && (
              <div>
                <h4 style={{margin:'12px 0 8px'}}>Alertes urgences SNCF :</h4>
                {alertesUrgenceList.length === 0 && <div style={{color:'#888'}}>Aucune alerte d'urgence.</div>}
                <ul style={{maxHeight:220, overflowY:'auto', paddingLeft:18}}>
                  {alertesUrgenceList.map(a => (
                    <li key={a.id} style={{marginBottom:12, borderBottom:'1px solid #eee', paddingBottom:8}}>
                      <div style={{fontWeight:'bold'}}>{a.message || a.type}</div>
                      <div style={{color:'#666', fontSize:13}}>{a.timestamp && new Date(a.timestamp).toLocaleString('fr-FR')}</div>
                      {a.photoUrl && <img src={a.photoUrl} alt="photo alerte" style={{width:48, height:48, objectFit:'cover', borderRadius:6, border:'1px solid #eee', margin:'6px 0'}} />}
                      {a.gps && a.gps.latitude && a.gps.longitude && (
                        <div style={{ width: 120, height: 80, margin: '6px 0', borderRadius: 6, overflow: 'hidden', border: '1px solid #eee' }}>
                          <iframe
                            title="Mini-carte"
                            width="100%"
                            height="100%"
                            frameBorder="0"
                            style={{ border:0 }}
                            src={`https://www.openstreetmap.org/export/embed.html?bbox=${a.gps.longitude-0.001}%2C${a.gps.latitude-0.001}%2C${a.gps.longitude+0.001}%2C${a.gps.latitude+0.001}&layer=mapnik&marker=${a.gps.latitude}%2C${a.gps.longitude}`}
                            allowFullScreen
                          ></iframe>
                        </div>
                      )}
                      <div style={{color:'#888', fontSize:12}}>{a.chantier && `Chantier: ${a.chantier}`}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {/* Pour les autres cartes, détail à venir */}
            {modal.key !== 'operateurs' && modal.key !== 'alertesUrgence' && (
              <div style={{color:'#888'}}>Détail à venir...</div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default CardsSummary; 