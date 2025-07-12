#!/usr/bin/env python3
"""
Service d'embeddings OpenAI pour ENCO
Utilisé pour la recherche sémantique et le tri intelligent des données
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI

# Configuration OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.warning("⚠️ OPENAI_API_KEY non définie - les embeddings seront désactivés")

class EmbeddingService:
    """Service pour gérer les embeddings OpenAI"""
    
    def __init__(self):
        self.client = None
        if OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=OPENAI_API_KEY)
                logging.info("✅ Service d'embeddings OpenAI initialisé")
            except Exception as e:
                logging.error(f"❌ Erreur initialisation OpenAI: {e}")
                self.client = None
        else:
            logging.warning("⚠️ Service d'embeddings désactivé (pas d'API key)")
    
    def create_embedding(self, text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
        """
        Crée un embedding pour un texte donné
        
        Args:
            text: Le texte à encoder
            model: Le modèle d'embedding à utiliser
            
        Returns:
            Liste de floats représentant l'embedding ou None si erreur
        """
        if not self.client or not text.strip():
            return None
            
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text.strip()
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"❌ Erreur création embedding: {e}")
            return None
    
    def create_embeddings_batch(self, texts: List[str], model: str = "text-embedding-3-small") -> List[Optional[List[float]]]:
        """
        Crée des embeddings pour une liste de textes
        
        Args:
            texts: Liste des textes à encoder
            model: Le modèle d'embedding à utiliser
            
        Returns:
            Liste d'embeddings (None pour les textes qui ont échoué)
        """
        if not self.client:
            return [None] * len(texts)
            
        embeddings = []
        for text in texts:
            embedding = self.create_embedding(text, model)
            embeddings.append(embedding)
        
        return embeddings
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings
        
        Args:
            embedding1: Premier embedding
            embedding2: Deuxième embedding
            
        Returns:
            Score de similarité entre 0 et 1
        """
        if not embedding1 or not embedding2:
            return 0.0
            
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Normalisation
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            # Similarité cosinus
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logging.error(f"❌ Erreur calcul similarité: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[tuple]:
        """
        Trouve les embeddings les plus similaires à une requête
        
        Args:
            query_embedding: Embedding de la requête
            candidate_embeddings: Liste des embeddings candidats
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste de tuples (index, score_similarité) triés par similarité décroissante
        """
        if not query_embedding:
            return []
            
        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            if candidate:
                score = self.cosine_similarity(query_embedding, candidate)
                similarities.append((i, score))
        
        # Tri par score décroissant
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def semantic_search(self, query: str, documents: List[str], top_k: int = 5) -> List[tuple]:
        """
        Recherche sémantique dans une liste de documents
        
        Args:
            query: Texte de la requête
            documents: Liste des documents à rechercher
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste de tuples (index_document, score_similarité) triés par similarité
        """
        if not self.client:
            return []
            
        # Créer l'embedding de la requête
        query_embedding = self.create_embedding(query)
        if not query_embedding:
            return []
        
        # Créer les embeddings des documents
        document_embeddings = self.create_embeddings_batch(documents)
        
        # Trouver les plus similaires
        return self.find_most_similar(query_embedding, document_embeddings, top_k)
    
    def categorize_text(self, text: str, categories: List[str]) -> Optional[str]:
        """
        Catégorise un texte selon les catégories données
        
        Args:
            text: Le texte à catégoriser
            categories: Liste des catégories possibles
            
        Returns:
            La catégorie la plus appropriée ou None si erreur
        """
        if not self.client:
            return None
            
        # Créer l'embedding du texte
        text_embedding = self.create_embedding(text)
        if not text_embedding:
            return None
        
        # Créer les embeddings des catégories
        category_embeddings = self.create_embeddings_batch(categories)
        
        # Trouver la catégorie la plus similaire
        similarities = self.find_most_similar(text_embedding, category_embeddings, top_k=1)
        
        if similarities:
            best_index, best_score = similarities[0]
            if best_score > 0.7:  # Seuil de confiance
                return categories[best_index]
        
        return None

# Instance globale du service
embedding_service = EmbeddingService()

# Fonctions utilitaires pour faciliter l'utilisation
def get_embedding(text: str) -> Optional[List[float]]:
    """Raccourci pour créer un embedding"""
    return embedding_service.create_embedding(text)

def semantic_search_docs(query: str, documents: List[str], top_k: int = 5) -> List[tuple]:
    """Raccourci pour la recherche sémantique"""
    return embedding_service.semantic_search(query, documents, top_k)

def categorize_document(text: str, categories: List[str]) -> Optional[str]:
    """Raccourci pour la catégorisation"""
    return embedding_service.categorize_text(text, categories) 