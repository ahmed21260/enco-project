#!/usr/bin/env python3
"""
Démonstration pratique de l'IA ENCO
Montre comment l'IA aide dans la logique métier réelle
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enco_ai_assistant import (
    ai_assistant,
    analyze_similar_anomalies,
    suggest_resolution,
    get_operator_help,
    analyze_system_trends
)

def demo_anomalie_analysis():
    """Démonstration de l'analyse d'anomalies"""
    print("🔍 DÉMONSTRATION : Analyse d'anomalies")
    print("=" * 60)
    
    # Cas d'usage réels d'ENCO
    anomalies_test = [
        "Bruit anormal dans le moteur de la machine de pose de voies",
        "Fuite d'huile hydraulique sur le vérin principal",
        "Signalisation défaillante au passage à niveau",
        "Voie ferrée endommagée sur 50 mètres",
        "Système de freinage qui répond lentement"
    ]
    
    for i, anomalie in enumerate(anomalies_test, 1):
        print(f"\n📝 Anomalie {i}: {anomalie}")
        
        # Catégorisation automatique
        category = ai_assistant.categorize_anomalie(anomalie)
        print(f"   🏷️ Catégorie: {category or 'Non catégorisée'}")
        
        # Évaluation priorité
        priority = ai_assistant.prioritize_urgence(anomalie)
        print(f"   ⚠️ Priorité: {priority['priority'].upper()}")
        print(f"   📋 Raison: {priority['reason']}")
        
        # Suggestion de résolution
        resolution = suggest_resolution(anomalie)
        if resolution:
            print(f"   💡 Suggestion: {resolution}")
        
        # Recherche d'anomalies similaires
        similar = analyze_similar_anomalies(anomalie)
        if similar:
            print(f"   📊 Anomalies similaires: {len(similar)} trouvées")
            for j, sim in enumerate(similar[:2], 1):
                print(f"      {j}. Score {sim['similarity_score']:.2f}: {sim['description'][:60]}...")

def demo_operator_assistance():
    """Démonstration de l'assistance opérateur"""
    print("\n💡 DÉMONSTRATION : Assistance opérateur")
    print("=" * 60)
    
    questions_test = [
        "Comment vérifier les niveaux d'huile hydraulique ?",
        "Procédure en cas de panne de freinage",
        "Normes de sécurité pour le travail sur voie",
        "Comment signaler un problème de signalisation ?",
        "Vérification des équipements avant démarrage"
    ]
    
    for i, question in enumerate(questions_test, 1):
        print(f"\n❓ Question {i}: {question}")
        
        # Contexte opérateur simulé
        context = {
            "machine": "Machine de pose de voies",
            "location": "Chantier ferroviaire",
            "activity_type": "Maintenance préventive"
        }
        
        # Obtenir l'aide
        help_response = get_operator_help(question, context)
        if help_response:
            print(f"   🤖 Réponse: {help_response}")
        else:
            print("   ❌ Pas de réponse disponible")

def demo_trend_analysis():
    """Démonstration de l'analyse de tendances"""
    print("\n📊 DÉMONSTRATION : Analyse de tendances")
    print("=" * 60)
    
    # Simuler une analyse de tendances
    print("Analyse des 30 derniers jours...")
    
    # En production, cela analyserait les vraies données Firestore
    trends = analyze_system_trends(30)
    
    if "error" in trends:
        print(f"   ❌ Erreur: {trends['error']}")
    else:
        print(f"   📅 Période: {trends['period']}")
        print(f"   🚨 Total anomalies: {trends['total_anomalies']}")
        print(f"   ⚠️ Total urgences: {trends['total_urgences']}")
        
        if trends['categories_distribution']:
            print("   📋 Distribution par catégorie:")
            for category, count in trends['categories_distribution'].items():
                print(f"      • {category}: {count}")
        
        if trends['recommendations']:
            print("   💡 Recommandations:")
            for rec in trends['recommendations']:
                print(f"      • {rec}")

def demo_smart_categorization():
    """Démonstration de la catégorisation intelligente"""
    print("\n🏷️ DÉMONSTRATION : Catégorisation intelligente")
    print("=" * 60)
    
    # Textes d'anomalies variés
    textes_anomalies = [
        "Le moteur diesel fait un bruit métallique anormal",
        "Panneau de signalisation ne s'allume pas",
        "Fissure visible sur le rail principal",
        "Système de communication radio défaillant",
        "Passage à niveau bloqué en position ouverte",
        "Équipement de sécurité incendie manquant",
        "Voie ferrée inondée sur 100 mètres",
        "Éclairage de chantier défaillant"
    ]
    
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
    
    print("Catégorisation automatique des anomalies:")
    for i, texte in enumerate(textes_anomalies, 1):
        category = ai_assistant.categorize_anomalie(texte)
        print(f"   {i}. {texte[:50]}... → {category or 'Non catégorisée'}")

def demo_priority_assessment():
    """Démonstration de l'évaluation de priorité"""
    print("\n⚠️ DÉMONSTRATION : Évaluation de priorité")
    print("=" * 60)
    
    # Cas d'urgences variés
    urgences_test = [
        "Déraillement d'un train de marchandises",
        "Personne blessée sur le chantier",
        "Incendie dans la cabine de conduite",
        "Voie coupée par un arbre tombé",
        "Signalisation complètement défaillante",
        "Fuite de carburant importante",
        "Équipement de sécurité endommagé",
        "Bruit anormal dans le moteur"
    ]
    
    for i, urgence in enumerate(urgences_test, 1):
        print(f"\n🚨 Urgence {i}: {urgence}")
        
        priority_info = ai_assistant.prioritize_urgence(urgence)
        print(f"   ⚠️ Priorité: {priority_info['priority'].upper()}")
        print(f"   📋 Raison: {priority_info['reason']}")
        
        if priority_info.get('immediate_action'):
            print("   🚨 ACTION IMMÉDIATE REQUISE")

def main():
    """Fonction principale de démonstration"""
    print("🤖 DÉMONSTRATION ENCO AI ASSISTANT")
    print("=" * 60)
    print("Cette démonstration montre comment l'IA aide dans la logique métier ENCO")
    print()
    
    # Vérifier que l'assistant est disponible
    if not ai_assistant.client:
        print("❌ Assistant AI non disponible")
        print("   Assurez-vous que OPENAI_API_KEY est définie")
        return
    
    # Exécuter les démonstrations
    demo_anomalie_analysis()
    demo_operator_assistance()
    demo_trend_analysis()
    demo_smart_categorization()
    demo_priority_assessment()
    
    print("\n" + "=" * 60)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("\n💡 AVANTAGES DE L'IA POUR ENCO:")
    print("   • 🔍 Analyse automatique des anomalies")
    print("   • 🏷️ Catégorisation intelligente")
    print("   • ⚠️ Évaluation de priorité en temps réel")
    print("   • 💡 Suggestions de résolution basées sur l'historique")
    print("   • 📊 Analyse de tendances pour l'encadrement")
    print("   • 🤖 Assistance technique pour les opérateurs")
    print("   • 🔄 Amélioration continue grâce aux données")

if __name__ == "__main__":
    main() 