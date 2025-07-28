/**
 * Service d'envoi d'email pour les plannings ENCO
 * Gère l'envoi automatique des PDF aux opérateurs
 */

// Configuration email (à adapter selon votre service d'email)
const EMAIL_CONFIG = {
  apiUrl: 'https://api.emailjs.com/api/v1.0/email/send',
  serviceId: 'enco_email_service',
  templateId: 'planning_template',
  userId: 'your_user_id' // À remplacer par votre clé API
};

/**
 * Envoie un email avec pièce jointe PDF
 */
export const sendEmailWithPDF = async (emailData) => {
  try {
    console.log('📧 Envoi email avec PDF:', emailData);
    
    // Simulation d'envoi email (remplacer par votre service)
    const emailPayload = {
      to: emailData.to,
      subject: emailData.subject,
      body: emailData.body,
      attachment: emailData.attachment,
      attachmentName: `planning_${new Date().toISOString().split('T')[0]}.pdf`
    };
    
    // Ici on appellerait votre service d'email (SendGrid, Mailgun, etc.)
    console.log('📧 Email préparé:', emailPayload);
    
    // Simulation de délai d'envoi
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    return {
      success: true,
      messageId: `email_${Date.now()}`,
      sentAt: new Date().toISOString()
    };
  } catch (error) {
    console.error('❌ Erreur envoi email:', error);
    throw error;
  }
};

/**
 * Envoie un email de confirmation de planning
 */
export const sendPlanningConfirmation = async (planningData) => {
  try {
    const emailBody = generateConfirmationEmail(planningData);
    
    const emailData = {
      to: `${planningData.operateur}@enco.fr`,
      subject: `Planning confirmé - ${formatDate(planningData.date_debut)} à ${formatDate(planningData.date_fin)}`,
      body: emailBody
    };
    
    return await sendEmailWithPDF(emailData);
  } catch (error) {
    console.error('❌ Erreur envoi confirmation:', error);
    throw error;
  }
};

/**
 * Envoie un email de rappel
 */
export const sendPlanningReminder = async (planningData) => {
  try {
    const emailBody = generateReminderEmail(planningData);
    
    const emailData = {
      to: `${planningData.operateur}@enco.fr`,
      subject: `Rappel - Planning ENCO du ${formatDate(planningData.date_debut)} au ${formatDate(planningData.date_fin)}`,
      body: emailBody
    };
    
    return await sendEmailWithPDF(emailData);
  } catch (error) {
    console.error('❌ Erreur envoi rappel:', error);
    throw error;
  }
};

const generateConfirmationEmail = (data) => {
  return `
Bonjour ${data.operateur},

Votre planning pour la période du ${formatDate(data.date_debut)} au ${formatDate(data.date_fin)} a été confirmé.

Détails de l'affectation :
- Chantier : ${data.chantier}
- Adresse : ${data.address || 'Non spécifiée'}
- Contact : ${data.contact || 'Non spécifié'}
- Machine : ${data.machine || 'Non spécifiée'}
- Équipe : ${getEquipeName(data.equipe)}
- Horaires : ${data.horaires}

Consignes de sécurité : ${data.instructions}

Merci de confirmer votre disponibilité.

Cordialement,
L'équipe ENCO
  `;
};

const generateReminderEmail = (data) => {
  return `
Bonjour ${data.operateur},

Rappel : Votre planning pour la période du ${formatDate(data.date_debut)} au ${formatDate(data.date_fin)} approche.

Détails de l'affectation :
- Chantier : ${data.chantier}
- Adresse : ${data.address || 'Non spécifiée'}
- Contact : ${data.contact || 'Non spécifié'}
- Machine : ${data.machine || 'Non spécifiée'}
- Équipe : ${getEquipeName(data.equipe)}
- Horaires : ${data.horaires}

N'oubliez pas de :
• Confirmer votre présence
• Vérifier les consignes de sécurité
• Contacter l'encadrement si nécessaire

Cordialement,
L'équipe ENCO
  `;
};

export const notifySupervisor = async (planningData) => {
  try {
    const supervisorEmail = generateSupervisorNotification(planningData);
    
    const emailData = {
      to: 'superviseur@enco.fr',
      subject: `Nouveau planning - ${planningData.operateur} - ${formatDate(planningData.date_debut)} à ${formatDate(planningData.date_fin)}`,
      body: supervisorEmail
    };
    
    return await sendEmailWithPDF(emailData);
  } catch (error) {
    console.error('❌ Erreur notification superviseur:', error);
    throw error;
  }
};

const generateSupervisorNotification = (data) => {
  return `
Nouveau planning créé :

Opérateur : ${data.operateur}
Période : ${formatDate(data.date_debut)} - ${formatDate(data.date_fin)}
Chantier : ${data.chantier}
Adresse : ${data.address || 'Non spécifiée'}
Contact : ${data.contact || 'Non spécifié'}
Machine : ${data.machine || 'Non spécifiée'}
Équipe : ${getEquipeName(data.equipe)}
Horaires : ${data.horaires}

Consignes : ${data.instructions}

Planning envoyé automatiquement à l'opérateur.

---
Système ENCO - Notification automatique
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

export default {
  sendEmailWithPDF,
  sendPlanningConfirmation,
  sendPlanningReminder,
  notifySupervisor
}; 