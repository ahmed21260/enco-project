import { collection, query, where, getDocs, orderBy, limit, doc, updateDoc } from 'firebase/firestore';
import { db } from '../firebaseConfig';

// Configuration des badges
export const BADGES = {
  REGULARITE: {
    BRONZE: { name: '🥉 Régularité Bronze', minScore: 50, color: '#cd7f32' },
    ARGENT: { name: '🥈 Régularité Argent', minScore: 75, color: '#c0c0c0' },
    OR: { name: '🥇 Régularité Or', minScore: 90, color: '#ffd700' },
    PLATINE: { name: '💎 Régularité Platine', minScore: 95, color: '#e5e4e2' }
  },
  PHOTOS: {
    PHOTOGRAPHE: { name: '📷 Photographe', minPhotos: 50, color: '#3498db' },
    EXPERT: { name: '📸 Expert Photo', minPhotos: 100, color: '#9b59b6' },
    MAITRE: { name: '🎞️ Maître Photographe', minPhotos: 200, color: '#e74c3c' }
  },
  ANOMALIES: {
    VIGILANT: { name: '👁️ Vigilant', minAnomalies: 10, color: '#f39c12' },
    DETECTEUR: { name: '🔍 Détecteur', minAnomalies: 25, color: '#e67e22' },
    EXPERT: { name: '🔧 Expert Détection', minAnomalies: 50, color: '#d35400' }
  },
  URGENCES: {
    RAPIDE: { name: '⚡ Réactif', minUrgences: 5, color: '#e74c3c' },
    HERO: { name: '🦸 Héro', minUrgences: 15, color: '#c0392b' },
    LEGENDE: { name: '🏆 Légende', minUrgences: 30, color: '#8e44ad' }
  }
};

// Points par action
export const POINTS = {
  PRISE_POSTE: 10,
  FIN_POSTE: 5,
  PHOTO: 2,
  BON_ATTACHEMENT: 15,
  ANOMALIE: 8,
  URGENCE: 12,
  RAPPORT_TECHNIQUE: 10,
  CHECKLIST: 5,
  PLANNING_CONSULTATION: 3
};

/**
 * Calcule le score d'un opérateur
 */
export const calculateOperatorScore = async (operatorId, days = 30) => {
  try {
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    let totalScore = 0;
    let actions = {
      prises_poste: 0,
      fins_poste: 0,
      photos: 0,
      bons_attachement: 0,
      anomalies: 0,
      urgences: 0,
      rapports_techniques: 0,
      checklists: 0,
      consultations_planning: 0
    };
    
    // Prise de poste
    const prisesQuery = query(
      collection(db, 'positions_operateurs'),
      where('operatorId', '==', operatorId),
      where('type', '==', 'prise_de_poste'),
      where('timestamp', '>=', startDate.toISOString())
    );
    const prisesSnapshot = await getDocs(prisesQuery);
    actions.prises_poste = prisesSnapshot.size;
    totalScore += prisesSnapshot.size * POINTS.PRISE_POSTE;
    
    // Fin de poste
    const finsQuery = query(
      collection(db, 'positions_operateurs'),
      where('operatorId', '==', operatorId),
      where('type', '==', 'fin_de_poste'),
      where('timestamp', '>=', startDate.toISOString())
    );
    const finsSnapshot = await getDocs(finsQuery);
    actions.fins_poste = finsSnapshot.size;
    totalScore += finsSnapshot.size * POINTS.FIN_POSTE;
    
    // Photos
    const photosQuery = query(
      collection(db, 'photos'),
      where('operatorId', '==', operatorId),
      where('timestamp', '>=', startDate.toISOString())
    );
    const photosSnapshot = await getDocs(photosQuery);
    actions.photos = photosSnapshot.size;
    totalScore += photosSnapshot.size * POINTS.PHOTO;
    
    // Bons d'attachement
    const bonsQuery = query(
      collection(db, 'bons_attachement'),
      where('operatorId', '==', operatorId),
      where('timestamp', '>=', startDate.toISOString())
    );
    const bonsSnapshot = await getDocs(bonsQuery);
    actions.bons_attachement = bonsSnapshot.size;
    totalScore += bonsSnapshot.size * POINTS.BON_ATTACHEMENT;
    
    // Anomalies
    const anomaliesQuery = query(
      collection(db, 'anomalies'),
      where('operatorId', '==', operatorId),
      where('timestamp', '>=', startDate.toISOString())
    );
    const anomaliesSnapshot = await getDocs(anomaliesQuery);
    actions.anomalies = anomaliesSnapshot.size;
    totalScore += anomaliesSnapshot.size * POINTS.ANOMALIE;
    
    // Urgences
    const urgencesQuery = query(
      collection(db, 'urgences'),
      where('operatorId', '==', operatorId),
      where('timestamp', '>=', startDate.toISOString())
    );
    const urgencesSnapshot = await getDocs(urgencesQuery);
    actions.urgences = urgencesSnapshot.size;
    totalScore += urgencesSnapshot.size * POINTS.URGENCE;
    
    // Rapports techniques
    const rapportsQuery = query(
      collection(db, 'rapports_techniques'),
      where('operatorId', '==', operatorId),
      where('timestamp', '>=', startDate.toISOString())
    );
    const rapportsSnapshot = await getDocs(rapportsQuery);
    actions.rapports_techniques = rapportsSnapshot.size;
    totalScore += rapportsSnapshot.size * POINTS.RAPPORT_TECHNIQUE;
    
    // Consultations planning
    const planningQuery = query(
      collection(db, 'consultations_planning'),
      where('operatorId', '==', operatorId),
      where('timestamp', '>=', startDate.toISOString())
    );
    const planningSnapshot = await getDocs(planningQuery);
    actions.consultations_planning = planningSnapshot.size;
    totalScore += planningSnapshot.size * POINTS.PLANNING_CONSULTATION;
    
    // Calcul du score de régularité (basé sur les prises de poste)
    const joursOuvres = Math.min(days, 22); // 22 jours ouvrables par mois
    const regulariteScore = Math.min(100, (actions.prises_poste / joursOuvres) * 100);
    
    return {
      totalScore,
      regulariteScore: Math.round(regulariteScore),
      actions,
      period: `${days} jours`,
      lastCalculated: new Date().toISOString()
    };
  } catch (error) {
    console.error('Erreur calcul score:', error);
    return {
      totalScore: 0,
      regulariteScore: 0,
      actions: {},
      period: `${days} jours`,
      lastCalculated: new Date().toISOString()
    };
  }
};

/**
 * Détermine les badges d'un opérateur
 */
export const getOperatorBadges = (score, actions) => {
  const badges = [];
  
  // Badges de régularité
  if (score.regulariteScore >= BADGES.REGULARITE.PLATINE.minScore) {
    badges.push(BADGES.REGULARITE.PLATINE);
  } else if (score.regulariteScore >= BADGES.REGULARITE.OR.minScore) {
    badges.push(BADGES.REGULARITE.OR);
  } else if (score.regulariteScore >= BADGES.REGULARITE.ARGENT.minScore) {
    badges.push(BADGES.REGULARITE.ARGENT);
  } else if (score.regulariteScore >= BADGES.REGULARITE.BRONZE.minScore) {
    badges.push(BADGES.REGULARITE.BRONZE);
  }
  
  // Badges photos
  if (actions.photos >= BADGES.PHOTOS.MAITRE.minPhotos) {
    badges.push(BADGES.PHOTOS.MAITRE);
  } else if (actions.photos >= BADGES.PHOTOS.EXPERT.minPhotos) {
    badges.push(BADGES.PHOTOS.EXPERT);
  } else if (actions.photos >= BADGES.PHOTOS.PHOTOGRAPHE.minPhotos) {
    badges.push(BADGES.PHOTOS.PHOTOGRAPHE);
  }
  
  // Badges anomalies
  if (actions.anomalies >= BADGES.ANOMALIES.EXPERT.minAnomalies) {
    badges.push(BADGES.ANOMALIES.EXPERT);
  } else if (actions.anomalies >= BADGES.ANOMALIES.DETECTEUR.minAnomalies) {
    badges.push(BADGES.ANOMALIES.DETECTEUR);
  } else if (actions.anomalies >= BADGES.ANOMALIES.VIGILANT.minAnomalies) {
    badges.push(BADGES.ANOMALIES.VIGILANT);
  }
  
  // Badges urgences
  if (actions.urgences >= BADGES.URGENCES.LEGENDE.minUrgences) {
    badges.push(BADGES.URGENCES.LEGENDE);
  } else if (actions.urgences >= BADGES.URGENCES.HERO.minUrgences) {
    badges.push(BADGES.URGENCES.HERO);
  } else if (actions.urgences >= BADGES.URGENCES.RAPIDE.minUrgences) {
    badges.push(BADGES.URGENCES.RAPIDE);
  }
  
  return badges;
};

/**
 * Récupère le classement des opérateurs
 */
export const getOperatorRanking = async (limitCount = 10) => {
  try {
    const operateursQuery = query(
      collection(db, 'operateurs'),
      orderBy('score', 'desc'),
      limit(limitCount)
    );
    
    const snapshot = await getDocs(operateursQuery);
    const ranking = [];
    
    snapshot.forEach((doc, index) => {
      const data = doc.data();
      ranking.push({
        rank: index + 1,
        operatorId: doc.id,
        operatorName: data.nom || 'Opérateur',
        score: data.score || 0,
        badges: data.badges || []
      });
    });
    
    return ranking;
  } catch (error) {
    console.error('Erreur récupération classement:', error);
    return [];
  }
};

/**
 * Met à jour le score d'un opérateur
 */
export const updateOperatorScore = async (operatorId) => {
  try {
    const score = await calculateOperatorScore(operatorId);
    const badges = getOperatorBadges(score, score.actions);
    
    // Mise à jour dans Firestore
    const operatorRef = doc(db, 'operateurs', operatorId);
    await updateDoc(operatorRef, {
      score: score.totalScore,
      regulariteScore: score.regulariteScore,
      badges: badges.map(badge => badge.name),
      lastScoreUpdate: new Date().toISOString()
    });
    
    return { score, badges };
  } catch (error) {
    console.error('Erreur mise à jour score:', error);
    throw error;
  }
};

/**
 * Génère un rapport de motivation
 */
export const generateMotivationReport = (score, badges, previousScore = null) => {
  const report = {
    message: '',
    suggestions: [],
    achievements: []
  };
  
  // Message principal
  if (score.regulariteScore >= 90) {
    report.message = "🌟 Excellent travail ! Votre régularité est exemplaire.";
  } else if (score.regulariteScore >= 75) {
    report.message = "👍 Bon travail ! Continuez sur cette lancée.";
  } else if (score.regulariteScore >= 50) {
    report.message = "📈 Vous progressez bien ! Quelques efforts supplémentaires.";
  } else {
    report.message = "💪 Gardez la motivation ! Chaque action compte.";
  }
  
  // Suggestions d'amélioration
  if (score.regulariteScore < 90) {
    report.suggestions.push("📌 Effectuez votre prise de poste quotidiennement");
  }
  if (score.actions.photos < 20) {
    report.suggestions.push("📷 Envoyez plus de photos pour documenter votre travail");
  }
  if (score.actions.bons_attachement < 5) {
    report.suggestions.push("📄 N'oubliez pas les bons d'attachement");
  }
  
  // Réalisations
  if (badges.length > 0) {
    report.achievements = badges.map(badge => `🏆 ${badge.name}`);
  }
  
  // Progression
  if (previousScore && score.totalScore > previousScore.totalScore) {
    const progression = score.totalScore - previousScore.totalScore;
    report.message += ` 📈 +${progression} points depuis la dernière évaluation !`;
  }
  
  return report;
}; 