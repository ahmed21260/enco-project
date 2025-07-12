import React, { useState, useEffect } from 'react';
import { collection, query, orderBy, onSnapshot, where, addDoc } from 'firebase/firestore';
import { db } from '../firebaseConfig';
import './Planning.css';

const Planning = () => {
    const [consultations, setConsultations] = useState([]);
    const [envois, setEnvois] = useState([]);
    const [operateurs, setOperateurs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [activeTab, setActiveTab] = useState('consultations');

    useEffect(() => {
        const unsubscribeConsultations = onSnapshot(
            query(
                collection(db, 'consultations_planning'),
                where('date_planning', '==', selectedDate),
                orderBy('timestamp', 'desc')
            ),
            (snapshot) => {
                const consultationsData = snapshot.docs.map(doc => ({
                    id: doc.id,
                    ...doc.data()
                }));
                setConsultations(consultationsData);
            }
        );

        const unsubscribeEnvois = onSnapshot(
            query(
                collection(db, 'envois_planning'),
                orderBy('timestamp', 'desc')
            ),
            (snapshot) => {
                const envoisData = snapshot.docs.map(doc => ({
                    id: doc.id,
                    ...doc.data()
                }));
                setEnvois(envoisData);
            }
        );

        const unsubscribeOperateurs = onSnapshot(
            collection(db, 'operateurs'),
            (snapshot) => {
                const operateursData = snapshot.docs.map(doc => ({
                    id: doc.id,
                    ...doc.data()
                }));
                setOperateurs(operateursData);
                setLoading(false);
            }
        );

        return () => {
            unsubscribeConsultations();
            unsubscribeEnvois();
            unsubscribeOperateurs();
        };
    }, [selectedDate]);

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const sendPlanningToOperateurs = async () => {
        try {
            const envoiData = {
                timestamp: new Date().toISOString(),
                admin_id: 'admin_dashboard',
                admin_name: 'Admin Dashboard',
                operateurs_contactes: operateurs.length,
                type: 'envoi_planning',
                date_envoi: selectedDate
            };

            await addDoc(collection(db, 'envois_planning'), envoiData);
            alert('Planning envoyé aux opérateurs !');
        } catch (error) {
            console.error('Erreur lors de l\'envoi:', error);
            alert('Erreur lors de l\'envoi du planning');
        }
    };

    const renderConsultations = () => (
        <div className="consultations-section">
            <div className="section-header">
                <h3>📋 Consultations de Planning</h3>
                <span className="count">{consultations.length} consultation(s)</span>
            </div>
            
            {consultations.length === 0 ? (
                <div className="no-data">
                    <p>Aucune consultation de planning pour cette date</p>
                </div>
            ) : (
                <div className="consultations-list">
                    {consultations.map((consultation) => (
                        <div key={consultation.id} className="consultation-card">
                            <div className="consultation-header">
                                <h4>👤 {consultation.operatorName}</h4>
                                <span className="consultation-time">
                                    {formatDate(consultation.timestamp)}
                                </span>
                            </div>
                            <div className="consultation-details">
                                <p><strong>Opérateur ID:</strong> {consultation.operatorId}</p>
                                <p><strong>Date consultée:</strong> {consultation.date_planning}</p>
                                <p><strong>Type:</strong> {consultation.type}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );

    const renderEnvois = () => (
        <div className="envois-section">
            <div className="section-header">
                <h3>📤 Envois de Planning</h3>
                <button onClick={sendPlanningToOperateurs} className="btn-primary">
                    📤 Envoyer Planning
                </button>
            </div>
            
            {envois.length === 0 ? (
                <div className="no-data">
                    <p>Aucun envoi de planning enregistré</p>
                </div>
            ) : (
                <div className="envois-list">
                    {envois.map((envoi) => (
                        <div key={envoi.id} className="envoi-card">
                            <div className="envoi-header">
                                <h4>📤 Envoi Planning</h4>
                                <span className="envoi-time">
                                    {formatDate(envoi.timestamp)}
                                </span>
                            </div>
                            <div className="envoi-details">
                                <p><strong>Admin:</strong> {envoi.admin_name}</p>
                                <p><strong>Opérateurs contactés:</strong> {envoi.operateurs_contactes}</p>
                                <p><strong>Type:</strong> {envoi.type}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );

    const renderOperateurs = () => (
        <div className="operateurs-section">
            <div className="section-header">
                <h3>👥 Opérateurs ({operateurs.length})</h3>
            </div>
            
            <div className="operateurs-grid">
                {operateurs.map((operateur) => (
                    <div key={operateur.id} className="operateur-card">
                        <div className="operateur-header">
                            <h4>👤 {operateur.nom || 'Opérateur'}</h4>
                            <span className="operateur-status">
                                {operateur.telegram_id ? '🟢 Connecté' : '🔴 Déconnecté'}
                            </span>
                        </div>
                        <div className="operateur-details">
                            <p><strong>ID:</strong> {operateur.telegram_id || 'Non défini'}</p>
                            <p><strong>Machine:</strong> {operateur.machine || 'Non définie'}</p>
                            <p><strong>Équipe:</strong> {operateur.equipe || 'Non définie'}</p>
                        </div>
                        <div className="operateur-actions">
                            <button className="btn-secondary">📋 Voir Planning</button>
                            <button className="btn-secondary">📤 Envoyer Planning</button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    if (loading) {
        return (
            <div className="planning-container">
                <div className="planning-header">
                    <h2>🗓️ Outil Planning Ferroviaire</h2>
                    <input
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        className="date-picker"
                    />
                </div>
                <div className="loading">Chargement de l'outil planning...</div>
            </div>
        );
    }

    return (
        <div className="planning-container">
            <div className="planning-header">
                <h2>🗓️ Outil Planning Ferroviaire</h2>
                <div className="header-controls">
                    <input
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        className="date-picker"
                    />
                    <button onClick={sendPlanningToOperateurs} className="btn-primary">
                        📤 Envoyer Planning
                    </button>
                </div>
            </div>

            <div className="planning-stats">
                <div className="stat-card">
                    <h3>Consultations du jour</h3>
                    <div className="stat-number">{consultations.length}</div>
                </div>
                <div className="stat-card">
                    <h3>Envois effectués</h3>
                    <div className="stat-number">{envois.length}</div>
                </div>
                <div className="stat-card">
                    <h3>Opérateurs actifs</h3>
                    <div className="stat-number">{operateurs.length}</div>
                </div>
            </div>

            <div className="planning-tabs">
                <button 
                    className={`tab-btn ${activeTab === 'consultations' ? 'active' : ''}`}
                    onClick={() => setActiveTab('consultations')}
                >
                    📋 Consultations
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'envois' ? 'active' : ''}`}
                    onClick={() => setActiveTab('envois')}
                >
                    📤 Envois
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'operateurs' ? 'active' : ''}`}
                    onClick={() => setActiveTab('operateurs')}
                >
                    👥 Opérateurs
                </button>
            </div>

            <div className="planning-content">
                {activeTab === 'consultations' && renderConsultations()}
                {activeTab === 'envois' && renderEnvois()}
                {activeTab === 'operateurs' && renderOperateurs()}
            </div>
        </div>
    );
};

export default Planning; 