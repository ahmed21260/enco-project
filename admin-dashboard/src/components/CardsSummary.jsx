import React, { useState } from 'react';
import './CardsSummary.css';
import { useOperateursLive } from '../hooks/useOperateursLive';

const Card = ({ title, value, icon, color, onClick }) => (
  <div className="card-summary" style={{ borderLeft: `5px solid ${color}`, cursor: 'pointer' }} onClick={onClick}>
    <div className="card-icon">{icon}</div>
    <div className="card-content">
      <div className="card-title">{title}</div>
      <div className="card-value">{value}</div>
    </div>
  </div>
);

const CardsSummary = () => {
  const { stats, operateursLive, urgences } = useOperateursLive();
  const [modal, setModal] = useState(null);
  const cards = [
    { key: 'operateurs', title: "Opérateurs actifs / total", value: `${stats.enPoste} / ${stats.total}`, icon: "👷", color: "#28a745" },
    { key: 'anomalies', title: "Anomalies", value: stats.anomalies, icon: "🚨", color: "#ffc107" },
    { key: 'urgences', title: "Urgences", value: stats.urgences, icon: "🚨", color: "#e74c3c" },
    { key: 'checklists', title: "Checklists", value: stats.checklists, icon: "✅", color: "#20c997" },
    { key: 'finPoste', title: "Fins de poste", value: stats.finPoste, icon: "🔴", color: "#dc3545" },
  ];
  return (
    <>
      <div className="cards-summary-container">
        {cards.map((card, idx) => (
          <Card key={card.title} {...card} onClick={() => setModal(card)} />
        ))}
      </div>
      {/* Modal et détails peuvent être adaptés ici */}
    </>
  );
};

export default CardsSummary; 