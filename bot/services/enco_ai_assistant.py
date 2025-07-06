#!/usr/bin/env python3
"""
Assistant AI spécialisé ENCO - Intégration métier des embeddings
Aide les opérateurs et l'encadrement avec l'intelligence artificielle
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from services.embeddings import (
    embedding_service, 
    semantic_search_docs, 
    categorize_document,
    get_embedding
)
from utils.firestore import db
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Configuration OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.warning("⚠️ OPENAI_API_KEY non définie - Assistant AI désactivé")

class ENCOAIAssistant:
    """Assistant AI spécialisé pour ENCO"""
    
    def __init__(self):
        self.client = None
        if OPENAI_API_KEY and OpenAI:
            try:
                self.client = OpenAI(api_key=OPENAI_API_KEY)
                logging.info("✅ Assistant AI ENCO initialisé")
            except Exception as e:
                logging.error(f"❌ Erreur initialisation OpenAI: {e}")
                self.client = None
        else:
            logging.warning("⚠️ Assistant AI désactivé (pas d'API key ou OpenAI non disponible)")
    
    # ===== CHATBOT FIRESTORE =====
    
    async def process_firestore_message(self, message_doc_ref, prompt: str) -> bool:
        """
        Traite un message Firestore et génère une réponse IA
        
        Args:
            message_doc_ref: Référence du document Firestore
            prompt: Le message de l'utilisateur
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Mettre à jour le statut en cours de traitement
            message_doc_ref.update({
                'status': {
                    'state': 'processing',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            })
            
            # Générer la réponse avec contexte ferroviaire
            response = await self.generate_railway_response(prompt)
            
            # Mettre à jour avec la réponse
            message_doc_ref.update({
                'response': response,
                'status': {
                    'state': 'completed',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            })
            
            logging.info(f"✅ Réponse générée pour: {prompt[:50]}...")
            return True
            
        except Exception as e:
            logging.error(f"❌ Erreur traitement message Firestore: {e}")
            try:
                message_doc_ref.update({
                    'status': {
                        'state': 'error',
                        'error': str(e),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                })
            except:
                pass
            return False
    
    async def generate_railway_response(self, prompt: str) -> str:
        """
        Génère une réponse IA avec contexte ferroviaire
        
        Args:
            prompt: Message de l'utilisateur
            
        Returns:
            Réponse générée
        """
        if not self.client:
            return "⚠️ Assistant AI non disponible (OpenAI non configuré)"
        
        try:
            # Contexte ferroviaire enrichi
            railway_context = """
            Tu es un assistant spécialisé dans le domaine ferroviaire pour ENCO.
            Tu peux aider avec :
            - Anomalies et incidents techniques
            - Maintenance préventive et curative
            - Sécurité et signalisation
            - Procédures opérationnelles
            - Équipements et matériel roulant
            - Réglementation ferroviaire
            - Optimisation des opérations
            
            Réponds de manière professionnelle et technique, adaptée aux opérateurs ferroviaires.
            """
            
            # Analyser le type de demande
            prompt_lower = prompt.lower()
            
            if any(word in prompt_lower for word in ['anomalie', 'problème', 'incident', 'erreur']):
                # Demande liée aux anomalies
                similar_anomalies = self.analyze_anomalie_similarity(prompt, days_back=30)
                if similar_anomalies:
                    context = f"\n\nAnomalies similaires récentes :\n"
                    for i, anomaly in enumerate(similar_anomalies[:3], 1):
                        context += f"{i}. {anomaly['description'][:100]}... (Score: {anomaly['similarity_score']:.2f})\n"
                else:
                    context = "\n\nAucune anomalie similaire trouvée dans l'historique récent."
                
                full_prompt = f"{railway_context}\n\nDemande utilisateur : {prompt}{context}\n\nAnalyse cette demande et fournis une réponse technique appropriée."
            
            elif any(word in prompt_lower for word in ['maintenance', 'réparation', 'entretien']):
                # Demande de maintenance
                full_prompt = f"{railway_context}\n\nDemande utilisateur : {prompt}\n\nFournis des conseils de maintenance et des procédures appropriées."
            
            elif any(word in prompt_lower for word in ['sécurité', 'signal', 'règlement']):
                # Demande de sécurité
                full_prompt = f"{railway_context}\n\nDemande utilisateur : {prompt}\n\nExplique les aspects de sécurité et les réglementations applicables."
            
            else:
                # Demande générale
                full_prompt = f"{railway_context}\n\nDemande utilisateur : {prompt}\n\nRéponds de manière utile et technique."
            
            # Appel à l'IA
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"❌ Erreur génération réponse: {e}")
            return f"❌ Erreur lors de la génération de la réponse : {str(e)}"
    
    def start_firestore_listener(self):
        """
        Démarre l'écouteur Firestore pour les nouveaux messages
        """
        if not db:
            logging.error("❌ Firestore non initialisé - impossible de démarrer l'écouteur")
            return
        
        try:
            # Écouter tous les messages dans la collection users/{uid}/messages
            messages_ref = db.collection_group('messages')
            
            def on_snapshot(doc_snapshot, changes, read_time):
                for change in changes:
                    if change.type.name == 'ADDED':
                        doc = change.document
                        data = doc.to_dict()
                        
                        # Vérifier si c'est un nouveau message sans réponse
                        if data.get('prompt') and not data.get('response'):
                            logging.info(f"🆕 Nouveau message détecté: {data['prompt'][:50]}...")
                            
                            # Correction asynchrone robuste
                            loop = None
                            try:
                                loop = asyncio.get_running_loop()
                            except RuntimeError:
                                try:
                                    loop = asyncio.get_event_loop()
                                except Exception:
                                    loop = None
                            if loop and loop.is_running():
                                asyncio.run_coroutine_threadsafe(
                                    self.process_firestore_message(doc.reference, data['prompt']),
                                    loop
                                )
                            else:
                                asyncio.run(self.process_firestore_message(doc.reference, data['prompt']))
            
            # Démarrer l'écouteur
            watch = messages_ref.on_snapshot(on_snapshot)
            logging.info("✅ Écouteur Firestore démarré pour les messages")
            
            return watch
            
        except Exception as e:
            logging.error(f"❌ Erreur démarrage écouteur Firestore: {e}")
            return None
    
    def add_test_message(self, uid: str, prompt: str) -> bool:
        """
        Ajoute un message de test dans Firestore
        
        Args:
            uid: ID de l'utilisateur
            prompt: Message à envoyer
            
        Returns:
            True si succès
        """
        if not db:
            logging.error("❌ Firestore non initialisé")
            return False
        
        try:
            # Ajouter le message
            message_ref = db.collection(f'users/{uid}/messages').add({
                'prompt': prompt,
                'timestamp': datetime.now().isoformat()
            })
            
            logging.info(f"✅ Message de test ajouté: {prompt[:50]}...")
            return True
            
        except Exception as e:
            logging.error(f"❌ Erreur ajout message test: {e}")
            return False

    # ===== ANALYSE D'ANOMALIES =====
    
    def analyze_anomalie_similarity(self, new_anomalie_description: str, days_back: int = 30) -> List[Dict]:
        """
        Trouve les anomalies similaires dans l'historique récent
        
        Args:
            new_anomalie_description: Description de la nouvelle anomalie
            days_back: Nombre de jours à analyser en arrière
            
        Returns:
            Liste des anomalies similaires avec scores
        """
        if not self.client or not db:
            return []
        
        try:
            # Récupérer les anomalies récentes
            cutoff_date = datetime.now() - timedelta(days=days_back)
            anomalies_ref = db.collection('anomalies')
            anomalies = anomalies_ref.where('timestamp', '>=', cutoff_date.isoformat()).stream()
            
            # Extraire les descriptions
            anomaly_descriptions = []
            anomaly_data = []
            
            for anomaly in anomalies:
                desc = anomaly.to_dict().get('description', '')
                if desc:
                    anomaly_descriptions.append(desc)
                    anomaly_data.append(anomaly.to_dict())
            
            if not anomaly_descriptions:
                return []
            
            # Recherche sémantique
            results = semantic_search_docs(new_anomalie_description, anomaly_descriptions, top_k=5)
            
            # Formater les résultats
            similar_anomalies = []
            for doc_index, score in results:
                if score > 0.6:  # Seuil de similarité
                    anomaly = anomaly_data[doc_index]
                    similar_anomalies.append({
                        'description': anomaly.get('description', ''),
                        'machine': anomaly.get('machine', ''),
                        'type_anomalie': anomaly.get('type_anomalie', ''),
                        'timestamp': anomaly.get('timestamp', ''),
                        'operator': anomaly.get('operatorName', ''),
                        'similarity_score': score,
                        'resolution': anomaly.get('resolution', ''),
                        'status': anomaly.get('handled', False)
                    })
            
            return similar_anomalies
            
        except Exception as e:
            logging.error(f"❌ Erreur analyse similarité anomalie: {e}")
            return []
    
    def suggest_anomalie_resolution(self, anomalie_description: str) -> Optional[str]:
        """
        Suggère une résolution basée sur l'historique des anomalies
        
        Args:
            anomalie_description: Description de l'anomalie
            
        Returns:
            Suggestion de résolution ou None
        """
        if not self.client:
            return None
        
        try:
            # Trouver des anomalies similaires résolues
            similar_anomalies = self.analyze_anomalie_similarity(anomalie_description, days_back=90)
            resolved_anomalies = [a for a in similar_anomalies if a.get('status') and a.get('resolution')]
            
            if not resolved_anomalies:
                return None
            
            # Créer un prompt pour l'IA
            prompt = f"""
            En tant qu'expert ferroviaire, analyse cette anomalie et suggère une résolution basée sur l'historique :

            NOUVELLE ANOMALIE : {anomalie_description}

            ANOMALIES SIMILAIRES RÉSOLUES :
            """
            
            for i, anomaly in enumerate(resolved_anomalies[:3], 1):
                prompt += f"""
                {i}. Description : {anomaly['description']}
                   Machine : {anomaly['machine']}
                   Résolution appliquée : {anomaly['resolution']}
                   Score de similarité : {anomaly['similarity_score']:.2f}
                """
            
            prompt += """
            Suggère une résolution courte et pratique pour la nouvelle anomalie, basée sur les solutions qui ont fonctionné.
            Réponse en 2-3 phrases maximum.
            """
            
            # Appel à l'IA
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"❌ Erreur suggestion résolution: {e}")
            return None
    
    # ===== CATÉGORISATION INTELLIGENTE =====
    
    def categorize_anomalie(self, description: str) -> Optional[str]:
        """
        Catégorise automatiquement une anomalie
        
        Args:
            description: Description de l'anomalie
            
        Returns:
            Catégorie suggérée ou None
        """
        categories = [
            "Infrastructure voie ferrée",
            "Signalisation et sécurité",
            "Équipements de traction",
            "Systèmes électriques",
            "Maintenance préventive",
            "Sécurité des passages",
            "Équipements de communication",
            "Problèmes environnementaux"
        ]
        
        return categorize_document(description, categories)
    
    def prioritize_urgence(self, description: str) -> Dict[str, Any]:
        """
        Évalue la priorité d'une urgence basée sur son contenu
        
        Args:
            description: Description de l'urgence
            
        Returns:
            Dict avec priorité et justification
        """
        if not self.client:
            return {"priority": "medium", "reason": "Assistant AI non disponible"}
        
        try:
            # Mots-clés critiques
            critical_keywords = [
                "déraillement", "collision", "incendie", "explosion", "personne blessée",
                "voie coupée", "signalisation défaillante", "freinage d'urgence"
            ]
            
            # Vérifier les mots-clés critiques
            desc_lower = description.lower()
            critical_found = [kw for kw in critical_keywords if kw in desc_lower]
            
            if critical_found:
                return {
                    "priority": "critical",
                    "reason": f"Mot-clé critique détecté : {', '.join(critical_found)}",
                    "immediate_action": True
                }
            
            # Analyse sémantique avec l'IA
            prompt = f"""
            Évalue la priorité de cette urgence ferroviaire :
            
            DESCRIPTION : {description}
            
            Réponds uniquement avec :
            - PRIORITY: high/medium/low
            - REASON: justification courte
            - IMMEDIATE_ACTION: true/false
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parser la réponse
            priority = "medium"
            reason = "Analyse automatique"
            immediate_action = False
            
            for line in result_text.split('\n'):
                if line.startswith('PRIORITY:'):
                    priority = line.split(':')[1].strip().lower()
                elif line.startswith('REASON:'):
                    reason = line.split(':')[1].strip()
                elif line.startswith('IMMEDIATE_ACTION:'):
                    immediate_action = line.split(':')[1].strip().lower() == 'true'
            
            return {
                "priority": priority,
                "reason": reason,
                "immediate_action": immediate_action
            }
            
        except Exception as e:
            logging.error(f"❌ Erreur évaluation priorité: {e}")
            return {"priority": "medium", "reason": "Erreur d'analyse"}
    
    # ===== ASSISTANT OPÉRATEUR =====
    
    def get_operator_assistance(self, question: str, operator_context: Dict = None) -> Optional[str]:
        """
        Assistant pour les opérateurs - répond aux questions techniques
        
        Args:
            question: Question de l'opérateur
            operator_context: Contexte de l'opérateur (position, machine, etc.)
            
        Returns:
            Réponse d'assistance ou None
        """
        if not self.client:
            return None
        
        try:
            # Contexte de base
            context = f"""
            Tu es un assistant technique spécialisé dans le domaine ferroviaire pour ENCO.
            Tu aides les opérateurs sur le terrain avec des conseils pratiques et techniques.
            """
            
            if operator_context:
                context += f"""
                Contexte opérateur :
                - Machine : {operator_context.get('machine', 'Non spécifiée')}
                - Position : {operator_context.get('location', 'Non spécifiée')}
                - Type d'activité : {operator_context.get('activity_type', 'Non spécifiée')}
                """
            
            prompt = f"""
            {context}
            
            QUESTION OPÉRATEUR : {question}
            
            Réponds de manière claire, concise et pratique. 
            Si tu ne sais pas, dis-le honnêtement.
            Réponse en 2-3 phrases maximum.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"❌ Erreur assistance opérateur: {e}")
            return None
    
    # ===== ANALYSE DE TENDANCES =====
    
    def analyze_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyse les tendances des anomalies et incidents
        
        Args:
            days_back: Nombre de jours à analyser
            
        Returns:
            Dict avec analyses et recommandations
        """
        if not db:
            return {"error": "Base de données non disponible"}
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Récupérer les données
            anomalies = db.collection('anomalies').where('timestamp', '>=', cutoff_date.isoformat()).stream()
            urgences = db.collection('urgences').where('timestamp', '>=', cutoff_date.isoformat()).stream()
            
            # Analyser les tendances
            anomaly_descriptions = []
            urgence_descriptions = []
            
            for anomaly in anomalies:
                desc = anomaly.to_dict().get('description', '')
                if desc:
                    anomaly_descriptions.append(desc)
            
            for urgence in urgences:
                desc = urgence.to_dict().get('description', '')
                if desc:
                    urgence_descriptions.append(desc)
            
            # Catégoriser les anomalies
            categories = {}
            for desc in anomaly_descriptions:
                category = self.categorize_anomalie(desc)
                if category:
                    categories[category] = categories.get(category, 0) + 1
            
            # Analyser les priorités d'urgence
            urgence_priorities = []
            for desc in urgence_descriptions:
                priority = self.prioritize_urgence(desc)
                urgence_priorities.append(priority['priority'])
            
            # Générer des recommandations
            recommendations = []
            
            if categories:
                most_common = max(categories.items(), key=lambda x: x[1])
                recommendations.append(f"Catégorie la plus fréquente : {most_common[0]} ({most_common[1]} incidents)")
            
            if urgence_priorities:
                critical_count = urgence_priorities.count('critical')
                if critical_count > 0:
                    recommendations.append(f"⚠️ {critical_count} urgence(s) critique(s) détectée(s)")
            
            return {
                "period": f"{days_back} derniers jours",
                "total_anomalies": len(anomaly_descriptions),
                "total_urgences": len(urgence_descriptions),
                "categories_distribution": categories,
                "urgence_priorities": urgence_priorities,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logging.error(f"❌ Erreur analyse tendances: {e}")
            return {"error": str(e)}

# Instance globale
ai_assistant = ENCOAIAssistant()

# Fonctions utilitaires pour faciliter l'utilisation
def analyze_similar_anomalies(description: str) -> List[Dict]:
    """Raccourci pour analyser les anomalies similaires"""
    return ai_assistant.analyze_anomalie_similarity(description)

def suggest_resolution(description: str) -> Optional[str]:
    """Raccourci pour suggérer une résolution"""
    return ai_assistant.suggest_anomalie_resolution(description)

def get_operator_help(question: str, context: Dict = None) -> Optional[str]:
    """Raccourci pour l'assistance opérateur"""
    return ai_assistant.get_operator_assistance(question, context)

def analyze_system_trends(days: int = 30) -> Dict[str, Any]:
    """Raccourci pour l'analyse des tendances"""
    return ai_assistant.analyze_trends(days) 