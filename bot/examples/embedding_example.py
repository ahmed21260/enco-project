#!/usr/bin/env python3
"""
Exemple d'utilisation des embeddings OpenAI pour ENCO
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embeddings import (
    get_embedding, 
    semantic_search_docs, 
    categorize_document,
    embedding_service
)

def example_basic_embedding():
    """Exemple basique de création d'embedding"""
    print("🔍 Exemple 1: Création d'embedding basique")
    print("-" * 50)
    
    text = "Anomalie signalée sur la voie ferrée"
    embedding = get_embedding(text)
    
    if embedding:
        print(f"✅ Embedding créé avec {len(embedding)} dimensions")
        print(f"📊 Premières valeurs: {embedding[:5]}")
    else:
        print("❌ Impossible de créer l'embedding")
    print()

def example_semantic_search():
    """Exemple de recherche sémantique"""
    print("🔍 Exemple 2: Recherche sémantique")
    print("-" * 50)
    
    # Documents d'exemple (rapports d'anomalies)
    documents = [
        "Anomalie signalée sur la voie ferrée entre les kilomètres 45 et 47",
        "Problème de signalisation au niveau du passage à niveau",
        "Dégradation de l'infrastructure ferroviaire sur le tronçon principal",
        "Incident technique sur les équipements de sécurité",
        "Maintenance préventive programmée pour la semaine prochaine"
    ]
    
    # Requête de recherche
    query = "problème voie ferrée"
    
    print(f"🔎 Requête: '{query}'")
    print("📄 Documents disponibles:")
    for i, doc in enumerate(documents):
        print(f"   {i+1}. {doc}")
    
    # Recherche sémantique
    results = semantic_search_docs(query, documents, top_k=3)
    
    print("\n🎯 Résultats (triés par pertinence):")
    for rank, (doc_index, score) in enumerate(results, 1):
        print(f"   {rank}. Document {doc_index+1} (score: {score:.3f})")
        print(f"      {documents[doc_index]}")
    print()

def example_categorization():
    """Exemple de catégorisation automatique"""
    print("🏷️ Exemple 3: Catégorisation automatique")
    print("-" * 50)
    
    # Catégories d'anomalies
    categories = [
        "Infrastructure ferroviaire",
        "Signalisation",
        "Équipements de sécurité", 
        "Maintenance préventive",
        "Incident technique"
    ]
    
    # Textes à catégoriser
    texts_to_categorize = [
        "Voie ferrée endommagée sur 200 mètres",
        "Panneau de signalisation défaillant",
        "Système d'alarme en panne",
        "Inspection programmée des rails",
        "Défaut électrique sur le système de contrôle"
    ]
    
    print("📋 Catégories disponibles:")
    for i, cat in enumerate(categories, 1):
        print(f"   {i}. {cat}")
    
    print("\n📝 Catégorisation des textes:")
    for text in texts_to_categorize:
        category = categorize_document(text, categories)
        if category:
            print(f"   ✅ '{text}' → {category}")
        else:
            print(f"   ❓ '{text}' → Non catégorisé")
    print()

def example_similarity_comparison():
    """Exemple de comparaison de similarité"""
    print("📊 Exemple 4: Comparaison de similarité")
    print("-" * 50)
    
    # Paires de textes à comparer
    text_pairs = [
        ("Anomalie voie ferrée", "Problème sur les rails"),
        ("Signalisation défaillante", "Panneau de signal en panne"),
        ("Maintenance préventive", "Inspection programmée"),
        ("Anomalie voie ferrée", "Maintenance préventive"),  # Moins similaire
    ]
    
    for text1, text2 in text_pairs:
        embedding1 = get_embedding(text1)
        embedding2 = get_embedding(text2)
        
        if embedding1 and embedding2:
            similarity = embedding_service.cosine_similarity(embedding1, embedding2)
            print(f"   '{text1}' vs '{text2}' → {similarity:.3f}")
        else:
            print(f"   ❌ Impossible de comparer '{text1}' et '{text2}'")
    print()

def main():
    """Fonction principale avec tous les exemples"""
    print("🤖 Exemples d'utilisation des embeddings OpenAI pour ENCO")
    print("=" * 60)
    
    # Vérifier que le service est disponible
    if not embedding_service.client:
        print("❌ Service d'embeddings non disponible")
        print("   Assurez-vous que OPENAI_API_KEY est définie dans vos variables d'environnement")
        return
    
    # Exécuter les exemples
    example_basic_embedding()
    example_semantic_search()
    example_categorization()
    example_similarity_comparison()
    
    print("✅ Tous les exemples terminés !")
    print("\n💡 Utilisations possibles dans ENCO:")
    print("   • Recherche intelligente dans les rapports d'anomalies")
    print("   • Catégorisation automatique des incidents")
    print("   • Tri intelligent des documents par pertinence")
    print("   • Détection de similarité entre incidents")
    print("   • Suggestions de solutions basées sur l'historique")

if __name__ == "__main__":
    main() 