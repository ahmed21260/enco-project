import React, { useState, useEffect } from 'react';
import { collection, getDocs, addDoc, updateDoc, doc } from 'firebase/firestore';
import { db } from '../firebaseConfig';
import { generatePlanningPDF, sendPlanningPDF } from '../services/pdfGenerator';
import { sendPlanningReminder, notifySupervisor } from '../services/emailService';
import { sendTelegramMessage, sendTelegramFile } from '../services/telegramService';
import './PlanningPro.css';

const PlanningPro = () => {
  const [operateurs, setOperateurs] = useState([]);
  const [planning, setPlanning] = useState([]);
  const [selectedOperateur, setSelectedOperateur] = useState('');
  const [dateDebut, setDateDebut] = useState('');
  const [dateFin, setDateFin] = useState('');
  const [selectedShift, setSelectedShift] = useState('');
  const [chantierName, setChantierName] = useState('');
  const [chantierAddress, setChantierAddress] = useState('');
  const [contactInfo, setContactInfo] = useState('');
  const [machineNumber, setMachineNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Configuration des équipes
  const equipes = [
    { id: 'equipe1', nom: 'Équipe 1 - Matin', horaires: '06:00-14:00', couleur: '#28a745' },
    { id: 'equipe2', nom: 'Équipe 2 - Après-midi', horaires: '14:00-22:00', couleur: '#007bff' },
    { id: 'equipe3', nom: 'Équipe 3 - Nuit', horaires: '22:00-06:00', couleur: '#6f42c1' }
  ];

  // Exemples de chantiers basés sur votre document
  const chantiersExamples = [
    'EIFFAGE-PROLIX A900-135406 VILLENEUVE ST GEORGES',
    'WILBUILD-ANDERS POF 12483 SEVRAN LIVRY',
    'SPIE-THERON ATLAS 1404-301275+ROM ARLES',
    'SFERIS-COCCO 136 MIRAIL-174019 VARENNES SUR FOUZON',
    'COLAS-SOULAH CATM323F-300107 TALENCE',
    'COLAS-KOLAGINSKO A914-93355 SOSPEL',
    'CDG 2X175-7 MAUREGARD (77)',
    'EIFFAGE-PROLIX PC138 VILLENEUVE ST GEORGES',
    'SPIE-ANDRIEU CATM323F-200050+RM127 CDG'
  ];

  // Exemples de machines
  const machinesExamples = [
    'CATM323F',
    'CAT 323M',
    'CAT 320',
    'CAT 330',
    'CAT 336',
    'Pelle mécanique',
    'Chargeur',
    'Bulldozer'
  ];

  useEffect(() => {
    loadOperateurs();
    loadPlanning();
  }, []);

  const loadOperateurs = async () => {
    try {
      const snapshot = await getDocs(collection(db, 'operateurs'));
      const operateursData = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      
      // Debug: afficher la structure des données
      console.log('🔍 Structure des opérateurs:', operateursData);
      
      setOperateurs(operateursData);
    } catch (error) {
      console.error('Erreur chargement opérateurs:', error);
      setMessage('❌ Erreur lors du chargement des opérateurs');
    }
  };

  const loadPlanning = async () => {
    try {
      const snapshot = await getDocs(collection(db, 'planning'));
      const planningData = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setPlanning(planningData);
    } catch (error) {
      console.error('Erreur chargement planning:', error);
      setMessage('❌ Erreur lors du chargement du planning');
    }
  };

  const addPlanningEntry = async () => {
    if (!selectedOperateur || !dateDebut || !dateFin || !selectedShift || !chantierName || !chantierAddress || !contactInfo || !machineNumber) {
      setMessage('❌ Veuillez remplir tous les champs obligatoires');
      return;
    }

    if (new Date(dateDebut) > new Date(dateFin)) {
      setMessage('❌ La date de début doit être antérieure à la date de fin');
      return;
    }

    setLoading(true);
    try {
      const newEntry = {
        operateur_id: selectedOperateur,
        operateur_nom: operateurs.find(op => op.id === selectedOperateur)?.nom || 'Inconnu',
        operateur_telegram_id: operateurs.find(op => op.id === selectedOperateur)?.telegram_id || null,
        date_debut: dateDebut,
        date_fin: dateFin,
        equipe: selectedShift,
        chantier_name: chantierName,
        chantier_address: chantierAddress,
        contact_info: contactInfo,
        machine_number: machineNumber,
        statut: 'planifié',
        created_at: new Date().toISOString(),
        envoyé: false,
        envoyé_telegram: false,
        confirmé: false
      };

      await addDoc(collection(db, 'planning'), newEntry);
      
      setMessage('✅ Planning ajouté avec succès');
      
      // Réinitialiser les champs
      setSelectedOperateur('');
      setDateDebut('');
      setDateFin('');
      setSelectedShift('');
      setChantierName('');
      setChantierAddress('');
      setContactInfo('');
      setMachineNumber('');
      
      loadPlanning(); // Recharger le planning
    } catch (error) {
      setMessage('❌ Erreur lors de l\'ajout du planning');
      console.error('Erreur ajout planning:', error);
    } finally {
      setLoading(false);
    }
  };

  const generatePDF = async (planningEntry) => {
    setLoading(true);
    try {
      const pdfData = {
        operateur: planningEntry.operateur_nom,
        date_debut: planningEntry.date_debut,
        date_fin: planningEntry.date_fin,
        equipe: planningEntry.equipe,
        chantier: planningEntry.chantier_name,
        address: planningEntry.chantier_address,
        contact: planningEntry.contact_info,
        machine: planningEntry.machine_number,
        horaires: equipes.find(eq => eq.id === planningEntry.equipe)?.horaires || '',
        instructions: generateInstructions(planningEntry.chantier_name)
      };

      const pdfDoc = await generatePlanningPDF(pdfData);
      const emailResult = await sendPlanningPDF(pdfDoc, pdfData);
      
      if (emailResult.success) {
        await updateDoc(doc(db, 'planning', planningEntry.id), {
          envoyé: true,
          envoyé_le: new Date().toISOString(),
          pdf_generated: true
        });

        setMessage('✅ PDF généré et envoyé à l\'opérateur');
        pdfDoc.save(`planning_${planningEntry.operateur_nom}_${planningEntry.date_debut}.pdf`);
        await notifySupervisor(pdfData);
      } else {
        setMessage('❌ Erreur lors de l\'envoi du PDF');
      }
      loadPlanning();
    } catch (error) {
      setMessage('❌ Erreur lors de la génération du PDF');
      console.error('Erreur génération PDF:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendTelegram = async (planningEntry) => {
    setLoading(true);
    try {
      // Debug: afficher les données du planning
      console.log('🔍 Planning entry:', planningEntry);
      
      // Chercher l'opérateur dans la liste chargée
      const operateur = operateurs.find(op => op.id === planningEntry.operateur_id);
      console.log('🔍 Opérateur trouvé:', operateur);
      
      // Essayer différentes façons de récupérer telegram_id
      const telegramId = planningEntry.operateur_telegram_id || 
                        operateur?.telegram_id || 
                        operateur?.telegramUserId ||
                        operateur?.id; // Parfois l'ID du document est le telegram_id
      
      console.log('🔍 Telegram ID trouvé:', telegramId);
      
      if (!telegramId) {
        setMessage('❌ Aucun ID Telegram trouvé pour cet opérateur. Vérifiez la base de données.');
        return;
      }

      const telegramData = {
        operateur: planningEntry.operateur_nom,
        telegram_id: telegramId,
        date_debut: planningEntry.date_debut,
        date_fin: planningEntry.date_fin,
        equipe: planningEntry.equipe,
        chantier: planningEntry.chantier_name,
        address: planningEntry.chantier_address,
        contact: planningEntry.contact_info,
        machine: planningEntry.machine_number,
        horaires: equipes.find(eq => eq.id === planningEntry.equipe)?.horaires || '',
        instructions: generateInstructions(planningEntry.chantier_name)
      };

      console.log('🔍 Données Telegram préparées:', telegramData);

      const telegramResult = await sendTelegramMessage(telegramData);
      
      if (telegramResult.success) {
        await updateDoc(doc(db, 'planning', planningEntry.id), {
          envoyé_telegram: true,
          envoyé_telegram_le: new Date().toISOString(),
          telegram_message_id: telegramResult.messageId,
          telegram_id_utilisé: telegramId
        });

        setMessage('✅ Planning envoyé sur Telegram');
      } else {
        setMessage('❌ Erreur lors de l\'envoi Telegram');
      }
      loadPlanning();
    } catch (error) {
      setMessage('❌ Erreur lors de l\'envoi Telegram');
      console.error('Erreur envoi Telegram:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendPDFFile = async (planningEntry) => {
    setLoading(true);
    try {
      console.log('📄 Envoi du fichier PDF via Telegram:', planningEntry);
      
      // Chercher l'opérateur dans la liste chargée
      const operateur = operateurs.find(op => op.id === planningEntry.operateur_id);
      const telegramId = planningEntry.operateur_telegram_id || 
                        operateur?.telegram_id || 
                        operateur?.telegramUserId ||
                        operateur?.id;
      
      if (!telegramId) {
        setMessage('❌ Aucun ID Telegram trouvé pour cet opérateur.');
        return;
      }

      // Générer le PDF
      const pdfDoc = await generatePlanningPDF({
        operateur: planningEntry.operateur_nom,
        date_debut: planningEntry.date_debut,
        date_fin: planningEntry.date_fin,
        equipe: planningEntry.equipe,
        chantier: planningEntry.chantier_name,
        address: planningEntry.chantier_address,
        contact: planningEntry.contact_info,
        machine: planningEntry.machine_number,
        horaires: equipes.find(eq => eq.id === planningEntry.equipe)?.horaires || '',
        instructions: generateInstructions(planningEntry.chantier_name)
      });

      // Convertir le PDF en Blob
      const pdfBlob = pdfDoc.output('blob');
      
      // Validation du Blob généré
      if (!pdfBlob || !(pdfBlob instanceof Blob)) {
        console.error('❌ Erreur: PDF Blob invalide');
        setMessage('❌ Erreur lors de la génération du PDF');
        return;
      }

      console.log('📄 PDF Blob généré:', {
        size: pdfBlob.size,
        type: pdfBlob.type,
        valid: pdfBlob instanceof Blob
      });

      // Préparer les données pour l'envoi
      const telegramData = {
        operateur: planningEntry.operateur_nom,
        telegram_id: telegramId,
        date_debut: planningEntry.date_debut,
        date_fin: planningEntry.date_fin,
        equipe: planningEntry.equipe,
        chantier: planningEntry.chantier_name,
        address: planningEntry.chantier_address,
        contact: planningEntry.contact_info,
        machine: planningEntry.machine_number,
        horaires: equipes.find(eq => eq.id === planningEntry.equipe)?.horaires || '',
        instructions: generateInstructions(planningEntry.chantier_name)
      };

      // Envoyer le fichier PDF via Telegram
      const fileResult = await sendTelegramFile(telegramData, pdfBlob);
      
      if (fileResult.success) {
        await updateDoc(doc(db, 'planning', planningEntry.id), {
          envoyé_pdf_telegram: true,
          envoyé_pdf_telegram_le: new Date().toISOString(),
          telegram_file_id: fileResult.documentId,
          telegram_id_utilisé: telegramId
        });

        setMessage('✅ Fichier PDF envoyé sur Telegram !');
      } else {
        setMessage('❌ Erreur lors de l\'envoi du fichier PDF');
      }
      loadPlanning();
    } catch (error) {
      setMessage('❌ Erreur lors de l\'envoi du fichier PDF');
      console.error('Erreur envoi fichier PDF:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendReminder = async (planningEntry) => {
    setLoading(true);
    try {
      const reminderData = {
        operateur: planningEntry.operateur_nom,
        date_debut: planningEntry.date_debut,
        date_fin: planningEntry.date_fin,
        equipe: planningEntry.equipe,
        chantier: planningEntry.chantier_name,
        address: planningEntry.chantier_address,
        contact: planningEntry.contact_info,
        machine: planningEntry.machine_number,
        horaires: equipes.find(eq => eq.id === planningEntry.equipe)?.horaires || ''
      };

      await sendPlanningReminder(reminderData);
      
      await updateDoc(doc(db, 'planning', planningEntry.id), {
        rappel_envoyé: true,
        rappel_envoyé_le: new Date().toISOString()
      });

      setMessage('✅ Rappel envoyé à l\'opérateur');
      loadPlanning();
    } catch (error) {
      setMessage('❌ Erreur lors de l\'envoi du rappel');
      console.error('Erreur envoi rappel:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateInstructions = (chantier) => {
    const instructions = {
      'EIFFAGE-PROLIX': 'Maintenance préventive - Vérification des équipements de sécurité',
      'WILBUILD-ANDERS': 'Installation de nouvelles infrastructures - Respect des normes',
      'SPIE-THERON': 'Inspection technique - Contrôle qualité renforcé',
      'SFERIS-COCCO': 'Maintenance corrective - Intervention urgente',
      'COLAS-SOULAH': 'Travaux de terrassement - Sécurité renforcée',
      'COLAS-KOLAGINSKO': 'Installation signalisation - Coordination avec la circulation',
      'CDG': 'Travaux aéroportuaires - Respect des horaires de vol',
      'SPIE-ANDRIEU': 'Maintenance électrique - Consignes de sécurité strictes'
    };

    for (const [key, instruction] of Object.entries(instructions)) {
      if (chantier.includes(key)) {
        return instruction;
      }
    }
    return 'Suivre les consignes de sécurité standard et les procédures ENCO';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getStatusColor = (statut) => {
    switch (statut) {
      case 'planifié': return '#007bff';
      case 'confirmé': return '#28a745';
      case 'en_cours': return '#ffc107';
      case 'terminé': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const getDateRange = (debut, fin) => {
    const debutDate = new Date(debut);
    const finDate = new Date(fin);
    const diffTime = Math.abs(finDate - debutDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return `${formatDate(debut)} - ${formatDate(fin)} (${diffDays} jour${diffDays > 1 ? 's' : ''})`;
  };

  return (
    <div className="planning-pro">
      <div className="planning-header">
        <h2>📅 Planning Professionnel ENCO</h2>
        <p>Gestion des équipes et envoi de planning aux opérateurs</p>
      </div>

      {message && (
        <div className={`message ${message.includes('❌') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="planning-container">
        {/* Formulaire d'ajout */}
        <div className="planning-form">
          <h3>➕ Ajouter une affectation</h3>
          
          <div className="form-group">
            <label>👤 Opérateur *</label>
            <select 
              value={selectedOperateur} 
              onChange={(e) => setSelectedOperateur(e.target.value)}
            >
              <option value="">Sélectionner un opérateur</option>
              {operateurs.map(op => (
                <option key={op.id} value={op.id}>
                  {op.nom} ({op.operateur_id}) 
                  {op.telegram_id ? '📱' : ''} 
                  {op.telegramUserId ? '📱' : ''} 
                  {op.id === op.telegram_id ? '📱' : ''}
                  {!op.telegram_id && !op.telegramUserId && op.id !== op.telegram_id ? '❌' : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>📅 Date de début *</label>
            <input 
              type="date" 
              value={dateDebut}
              onChange={(e) => setDateDebut(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>📅 Date de fin *</label>
            <input 
              type="date" 
              value={dateFin}
              onChange={(e) => setDateFin(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>⏰ Équipe *</label>
            <select 
              value={selectedShift} 
              onChange={(e) => setSelectedShift(e.target.value)}
            >
              <option value="">Sélectionner une équipe</option>
              {equipes.map(equipe => (
                <option key={equipe.id} value={equipe.id}>
                  {equipe.nom} ({equipe.horaires})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>🏗️ Nom du chantier *</label>
            <input 
              type="text" 
              value={chantierName}
              onChange={(e) => setChantierName(e.target.value)}
              placeholder="Ex: EIFFAGE-PROLIX A900-135406"
            />
            <div className="examples">
              <small>Exemples: {chantiersExamples.slice(0, 3).join(', ')}</small>
            </div>
          </div>

          <div className="form-group">
            <label>📍 Adresse du chantier *</label>
            <input 
              type="text" 
              value={chantierAddress}
              onChange={(e) => setChantierAddress(e.target.value)}
              placeholder="Ex: VILLENEUVE ST GEORGES"
            />
          </div>

          <div className="form-group">
            <label>📞 Contact *</label>
            <input 
              type="text" 
              value={contactInfo}
              onChange={(e) => setContactInfo(e.target.value)}
              placeholder="Ex: Chef de chantier - 01 23 45 67 89"
            />
          </div>

          <div className="form-group">
            <label>🚜 Numéro de machine *</label>
            <input 
              type="text" 
              value={machineNumber}
              onChange={(e) => setMachineNumber(e.target.value)}
              placeholder="Ex: CATM323F"
            />
            <div className="examples">
              <small>Exemples: {machinesExamples.slice(0, 4).join(', ')}</small>
            </div>
          </div>

          <button 
            onClick={addPlanningEntry}
            disabled={loading}
            className="add-btn"
          >
            {loading ? '🔄 Ajout en cours...' : '➕ Ajouter au planning'}
          </button>
        </div>

        {/* Liste du planning */}
        <div className="planning-list">
          <h3>📋 Planning actuel</h3>
          
          {planning.length === 0 ? (
            <div className="empty-state">
              <p>📭 Aucun planning enregistré</p>
              <p>Ajoutez des affectations pour commencer</p>
            </div>
          ) : (
            <div className="planning-entries">
              {planning.map((entry) => (
                <div key={entry.id} className="planning-entry">
                  <div className="entry-header">
                    <h4>{entry.operateur_nom}</h4>
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(entry.statut) }}
                    >
                      {entry.statut}
                    </span>
                  </div>
                  
                  <div className="entry-details">
                    <div className="detail-row">
                      <span className="label">📅 Période:</span>
                      <span>{getDateRange(entry.date_debut, entry.date_fin)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">⏰ Équipe:</span>
                      <span>{equipes.find(eq => eq.id === entry.equipe)?.nom || entry.equipe}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">🏗️ Chantier:</span>
                      <span>{entry.chantier_name}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">📍 Adresse:</span>
                      <span>{entry.chantier_address}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">📞 Contact:</span>
                      <span>{entry.contact_info}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">🚜 Machine:</span>
                      <span>{entry.machine_number}</span>
                    </div>
                  </div>

                  <div className="entry-actions">
                    {!entry.envoyé && (
                      <button 
                        onClick={() => generatePDF(entry)}
                        disabled={loading}
                        className="action-btn primary"
                      >
                        📄 Générer PDF
                      </button>
                    )}
                    {!entry.envoyé_telegram && entry.operateur_telegram_id && (
                      <button 
                        onClick={() => sendTelegram(entry)}
                        disabled={loading}
                        className="action-btn telegram"
                      >
                        📱 Envoyer Telegram
                      </button>
                    )}
                    {!entry.envoyé_pdf_telegram && entry.operateur_telegram_id && (
                      <button 
                        onClick={() => sendPDFFile(entry)}
                        disabled={loading}
                        className="action-btn pdf-telegram"
                      >
                        📄📱 Envoyer PDF Telegram
                      </button>
                    )}
                    {entry.envoyé && !entry.rappel_envoyé && (
                      <button 
                        onClick={() => sendReminder(entry)}
                        disabled={loading}
                        className="action-btn secondary"
                      >
                        📧 Envoyer rappel
                      </button>
                    )}
                    {entry.envoyé && (
                      <span className="sent-badge">✅ PDF Envoyé</span>
                    )}
                    {entry.envoyé_telegram && (
                      <span className="sent-badge telegram">✅ Telegram</span>
                    )}
                    {entry.envoyé_pdf_telegram && (
                      <span className="sent-badge pdf-telegram">✅ PDF Telegram</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlanningPro;