import React, { useState, useEffect } from 'react';
import { collection, onSnapshot, query, orderBy, limit } from 'firebase/firestore';
import { db } from '../firebaseConfig';
import { getOperatorRanking, calculateOperatorScore, getOperatorBadges, generateMotivationReport } from '../services/scoringSystem';
import './ScoringDashboard.css';

const ScoringDashboard = () => {
  const [ranking, setRanking] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(30);
  const [selectedOperator, setSelectedOperator] = useState(null);
  const [operatorScore, setOperatorScore] = useState(null);
  const [motivationReport, setMotivationReport] = useState(null);

  useEffect(() => {
    loadRanking();
  }, []);

  const loadRanking = async () => {
    try {
      setLoading(true);
      const rankingData = await getOperatorRanking(20);
      setRanking(rankingData);
      setLoading(false);
    } catch (error) {
      console.error('Erreur chargement classement:', error);
      setLoading(false);
    }
  };

  const loadOperatorDetails = async (operatorId) => {
    try {
      const score = await calculateOperatorScore(operatorId, selectedPeriod);
      const badges = getOperatorBadges(score, score.actions);
      const report = generateMotivationReport(score, badges);
      
      setOperatorScore(score);
      setMotivationReport(report);
      setSelectedOperator(operatorId);
    } catch (error) {
      console.error('Erreur chargement détails opérateur:', error);
    }
  };

  const getBadgeIcon = (badgeName) => {
    if (badgeName.includes('Or')) return '🥇';
    if (badgeName.includes('Argent')) return '🥈';
    if (badgeName.includes('Bronze')) return '🥉';
    if (badgeName.includes('Platine')) return '💎';
    if (badgeName.includes('Photo')) return '📷';
    if (badgeName.includes('Vigilant')) return '👁️';
    if (badgeName.includes('Héro')) return '🦸';
    if (badgeName.includes('Légende')) return '🏆';
    return '🏅';
  };

  const getScoreColor = (score) => {
    if (score >= 90) return '#28a745';
    if (score >= 75) return '#ffc107';
    if (score >= 50) return '#fd7e14';
    return '#dc3545';
  };

  const renderRankingTable = () => (
    <div className="ranking-section">
      <div className="section-header">
        <h3>🏆 Classement des Opérateurs</h3>
        <button onClick={loadRanking} className="btn-refresh">
          🔄 Actualiser
        </button>
      </div>
      
      <div className="ranking-table">
        <div className="table-header">
          <div className="header-cell">Rang</div>
          <div className="header-cell">Opérateur</div>
          <div className="header-cell">Score</div>
          <div className="header-cell">Régularité</div>
          <div className="header-cell">Badges</div>
          <div className="header-cell">Actions</div>
        </div>
        
        {ranking.map((operator, index) => (
          <div 
            key={operator.operatorId} 
            className={`table-row ${selectedOperator === operator.operatorId ? 'selected' : ''}`}
            onClick={() => loadOperatorDetails(operator.operatorId)}
          >
            <div className="table-cell rank">
              {index < 3 ? (
                <span className="medal">
                  {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                </span>
              ) : (
                <span className="rank-number">{index + 1}</span>
              )}
            </div>
            <div className="table-cell operator">
              <strong>{operator.operatorName}</strong>
            </div>
            <div className="table-cell score">
              <span 
                className="score-value"
                style={{ color: getScoreColor(operator.score) }}
              >
                {operator.score}
              </span>
            </div>
            <div className="table-cell regularite">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ 
                    width: `${operator.regulariteScore || 0}%`,
                    backgroundColor: getScoreColor(operator.regulariteScore || 0)
                  }}
                ></div>
                <span className="progress-text">{operator.regulariteScore || 0}%</span>
              </div>
            </div>
            <div className="table-cell badges">
              <div className="badges-container">
                {operator.badges?.slice(0, 3).map((badge, badgeIndex) => (
                  <span key={badgeIndex} className="badge" title={badge}>
                    {getBadgeIcon(badge)}
                  </span>
                ))}
                {operator.badges?.length > 3 && (
                  <span className="badge-more">+{operator.badges.length - 3}</span>
                )}
              </div>
            </div>
            <div className="table-cell actions">
              <button 
                className="btn-details"
                onClick={(e) => {
                  e.stopPropagation();
                  loadOperatorDetails(operator.operatorId);
                }}
              >
                📊 Détails
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderOperatorDetails = () => {
    if (!operatorScore || !motivationReport) return null;

    return (
      <div className="operator-details-section">
        <div className="section-header">
          <h3>📊 Détails Opérateur</h3>
          <button onClick={() => setSelectedOperator(null)} className="btn-close">
            ✕
          </button>
        </div>
        
        <div className="details-grid">
          <div className="score-card">
            <h4>Score Global</h4>
            <div className="score-display">
              <span 
                className="main-score"
                style={{ color: getScoreColor(operatorScore.totalScore) }}
              >
                {operatorScore.totalScore}
              </span>
              <span className="score-label">points</span>
            </div>
            <div className="score-breakdown">
              <div className="breakdown-item">
                <span>Régularité:</span>
                <span>{operatorScore.regulariteScore}%</span>
              </div>
              <div className="breakdown-item">
                <span>Période:</span>
                <span>{operatorScore.period}</span>
              </div>
            </div>
          </div>

          <div className="actions-card">
            <h4>Actions Réalisées</h4>
            <div className="actions-grid">
              <div className="action-item">
                <span className="action-icon">📌</span>
                <span className="action-label">Prises de poste</span>
                <span className="action-count">{operatorScore.actions.prises_poste}</span>
              </div>
              <div className="action-item">
                <span className="action-icon">📷</span>
                <span className="action-label">Photos</span>
                <span className="action-count">{operatorScore.actions.photos}</span>
              </div>
              <div className="action-item">
                <span className="action-icon">📄</span>
                <span className="action-label">Bons d'attachement</span>
                <span className="action-count">{operatorScore.actions.bons_attachement}</span>
              </div>
              <div className="action-item">
                <span className="action-icon">🔧</span>
                <span className="action-label">Anomalies</span>
                <span className="action-count">{operatorScore.actions.anomalies}</span>
              </div>
              <div className="action-item">
                <span className="action-icon">🚨</span>
                <span className="action-label">Urgences</span>
                <span className="action-count">{operatorScore.actions.urgences}</span>
              </div>
              <div className="action-item">
                <span className="action-icon">📋</span>
                <span className="action-label">Rapports</span>
                <span className="action-count">{operatorScore.actions.rapports_techniques}</span>
              </div>
            </div>
          </div>

          <div className="motivation-card">
            <h4>💪 Rapport de Motivation</h4>
            <div className="motivation-content">
              <p className="motivation-message">{motivationReport.message}</p>
              
              {motivationReport.suggestions.length > 0 && (
                <div className="suggestions">
                  <h5>Suggestions d'amélioration:</h5>
                  <ul>
                    {motivationReport.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {motivationReport.achievements.length > 0 && (
                <div className="achievements">
                  <h5>Réalisations:</h5>
                  <div className="achievements-list">
                    {motivationReport.achievements.map((achievement, index) => (
                      <span key={index} className="achievement-badge">
                        {achievement}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="scoring-dashboard">
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Chargement du classement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="scoring-dashboard">
      <div className="dashboard-header">
        <h2>🏆 Système de Scoring & Motivation</h2>
        <div className="header-controls">
          <select 
            value={selectedPeriod} 
            onChange={(e) => setSelectedPeriod(parseInt(e.target.value))}
            className="period-selector"
          >
            <option value={7}>7 jours</option>
            <option value={30}>30 jours</option>
            <option value={90}>90 jours</option>
          </select>
        </div>
      </div>

      <div className="dashboard-content">
        {renderRankingTable()}
        {renderOperatorDetails()}
      </div>
    </div>
  );
};

export default ScoringDashboard; 