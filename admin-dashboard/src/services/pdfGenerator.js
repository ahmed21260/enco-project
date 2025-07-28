/**
 * Service de génération de PDF professionnel pour les plannings ENCO
 * Génère des PDF avec mise en page professionnelle et envoi automatique
 */

import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Configuration du PDF
const PDF_CONFIG = {
  pageSize: 'A4',
  orientation: 'portrait',
  unit: 'mm',
  format: 'a4'
};

// Couleurs de l'entreprise
const BRAND_COLORS = {
  primary: '#3498db',
  secondary: '#2c3e50',
  success: '#27ae60',
  warning: '#f39c12',
  danger: '#e74c3c',
  light: '#ecf0f1'
};

/**
 * Génère un PDF de planning professionnel
 */
export const generatePlanningPDF = async (planningData) => {
  try {
    console.log('📄 Génération PDF planning:', planningData);
    
    const doc = new jsPDF(PDF_CONFIG);
    
    // En-tête professionnel
    addHeader(doc);
    
    // Informations de l'opérateur
    addOperatorInfo(doc, planningData);
    
    // Détails du planning
    addPlanningDetails(doc, planningData);
    
    // Informations du chantier
    addChantierInfo(doc, planningData);
    
    // Instructions de sécurité
    addSafetyInstructions(doc, planningData);
    
    // Signature et validation
    addSignatureSection(doc);
    
    // Pied de page
    addFooter(doc);
    
    return doc;
  } catch (error) {
    console.error('❌ Erreur génération PDF:', error);
    throw error;
  }
};

const addHeader = (doc) => {
  // Logo ENCO (simulé)
  doc.setFillColor(52, 152, 219);
  doc.rect(20, 20, 170, 15, 'F');
  
  // Titre
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.text('ENCO - Planning Opérateur', 105, 30, { align: 'center' });
  
  // Sous-titre
  doc.setFontSize(10);
  doc.text('Système de Gestion Ferroviaire', 105, 40, { align: 'center' });
  
  // Reset colors
  doc.setTextColor(0, 0, 0);
};

const addOperatorInfo = (doc, data) => {
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('INFORMATIONS OPÉRATEUR', 20, 60);
  
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  
  const operatorInfo = [
    ['Nom de l\'opérateur:', data.operateur],
    ['Période d\'affectation:', `${formatDate(data.date_debut)} - ${formatDate(data.date_fin)}`],
    ['Équipe:', getEquipeName(data.equipe)],
    ['Horaires:', data.horaires]
  ];
  
  autoTable(doc, {
    startY: 65,
    head: [],
    body: operatorInfo,
    theme: 'plain',
    styles: {
      fontSize: 10,
      cellPadding: 3
    },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 50 },
      1: { cellWidth: 50 }
    }
  });
};

const addPlanningDetails = (doc, data) => {
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('DÉTAILS DE L\'AFFECTATION', 20, 120);
  
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  
  const planningInfo = [
    ['Type d\'intervention:', getInterventionType(data.chantier)],
    ['Priorité:', getPriority(data.chantier)],
    ['Équipements requis:', getRequiredEquipment(data.machine)],
    ['Durée estimée:', getEstimatedDuration(data.chantier)]
  ];
  
  autoTable(doc, {
    startY: 125,
    head: [],
    body: planningInfo,
    theme: 'plain',
    styles: {
      fontSize: 10,
      cellPadding: 3
    },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 50 },
      1: { cellWidth: 50 }
    }
  });
};

const addChantierInfo = (doc, data) => {
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('INFORMATIONS CHANTIER', 20, 180);
  
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  
  const chantierInfo = [
    ['Nom du chantier:', data.chantier],
    ['Adresse:', data.address || 'Non spécifiée'],
    ['Contact:', data.contact || 'Non spécifié'],
    ['Machine assignée:', data.machine || 'Non spécifiée']
  ];
  
  autoTable(doc, {
    startY: 185,
    head: [],
    body: chantierInfo,
    theme: 'plain',
    styles: {
      fontSize: 10,
      cellPadding: 3
    },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 50 },
      1: { cellWidth: 50 }
    }
  });
};

const addSafetyInstructions = (doc, data) => {
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('CONSIGNES DE SÉCURITÉ', 20, 240);
  
  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  
  const instructions = [
    '• Port obligatoire des EPI (casque, gilet, chaussures de sécurité)',
    '• Respect strict des procédures de sécurité ENCO',
    '• Vérification des équipements avant utilisation',
    '• Signalement immédiat de toute anomalie',
    '• Coordination avec l\'encadrement en cas de problème',
    `• ${data.instructions}`
  ];
  
  let yPos = 245;
  instructions.forEach(instruction => {
    doc.text(instruction, 20, yPos);
    yPos += 5;
  });
};

const addSignatureSection = (doc) => {
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text('VALIDATION', 20, 280);
  
  // Ligne de signature
  doc.line(20, 290, 80, 290);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.text('Signature opérateur', 50, 295, { align: 'center' });
  
  doc.line(110, 290, 170, 290);
  doc.text('Signature encadrement', 140, 295, { align: 'center' });
  
  // Date
  doc.setFontSize(10);
  doc.text(`Date: ${formatDate(new Date().toISOString())}`, 20, 310);
};

const addFooter = (doc) => {
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(128, 128, 128);
  doc.text('Document généré automatiquement par le système ENCO', 105, 290, { align: 'center' });
  doc.text('Pour toute question, contactez l\'encadrement', 105, 295, { align: 'center' });
};

/**
 * Envoie le PDF par email (simulation)
 */
export const sendPlanningPDF = async (pdfDoc, planningData) => {
  try {
    console.log('📧 Envoi du PDF par email...');
    
    // Convertir le PDF en base64
    const pdfBase64 = pdfDoc.output('datauristring');
    
    // Simulation d'envoi email
    const emailData = {
      to: `${planningData.operateur}@enco.fr`,
      subject: `Planning ENCO - ${formatDate(planningData.date_debut)} à ${formatDate(planningData.date_fin)}`,
      body: generateEmailBody(planningData),
      attachment: pdfBase64
    };
    
    console.log('📧 Email préparé:', emailData);
    
    // Ici on appellerait l'API d'envoi d'email
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    return {
      success: true,
      message: 'PDF envoyé avec succès',
      emailData
    };
  } catch (error) {
    console.error('❌ Erreur envoi PDF:', error);
    throw error;
  }
};

const generateEmailBody = (data) => {
  return `
Bonjour ${data.operateur},

Veuillez trouver ci-joint votre planning pour la période du ${formatDate(data.date_debut)} au ${formatDate(data.date_fin)}.

Détails de l'affectation :
- Chantier : ${data.chantier}
- Adresse : ${data.address || 'Non spécifiée'}
- Contact : ${data.contact || 'Non spécifié'}
- Machine : ${data.machine || 'Non spécifiée'}
- Horaires : ${data.horaires}

Consignes de sécurité : ${data.instructions}

Merci de confirmer la réception de ce planning.

Cordialement,
L'équipe ENCO
  `;
};

// Utility functions
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

const getEquipeName = (equipeId) => {
  const equipes = {
    'equipe1': 'Équipe 1 - Matin (06:00-14:00)',
    'equipe2': 'Équipe 2 - Après-midi (14:00-22:00)',
    'equipe3': 'Équipe 3 - Nuit (22:00-06:00)'
  };
  return equipes[equipeId] || equipeId;
};

const getInterventionType = (chantier) => {
  if (chantier.includes('EIFFAGE')) return 'Maintenance préventive';
  if (chantier.includes('SPIE')) return 'Inspection technique';
  if (chantier.includes('COLAS')) return 'Travaux de terrassement';
  if (chantier.includes('CDG')) return 'Travaux aéroportuaires';
  return 'Intervention standard';
};

const getPriority = (chantier) => {
  if (chantier.includes('URGENT') || chantier.includes('CDG')) return 'Haute';
  if (chantier.includes('MAINTENANCE')) return 'Moyenne';
  return 'Normale';
};

const getRequiredEquipment = (machine) => {
  if (machine.includes('CAT')) return 'Pelle mécanique, EPI complets';
  if (machine.includes('Chargeur')) return 'Chargeur, gants de protection';
  return 'Équipements standard ENCO';
};

const getEstimatedDuration = (chantier) => {
  if (chantier.includes('CDG')) return '8-10 heures';
  if (chantier.includes('MAINTENANCE')) return '6-8 heures';
  return '8 heures standard';
};

export default {
  generatePlanningPDF,
  sendPlanningPDF
}; 