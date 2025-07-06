from init_firestore import db

def import_sample():
    # Exemple d'import d'une machine
    db.collection("machines").add({
        "nom": "CAT 323 M",
        "etat": "Disponible",
        "documents": ["VGP.pdf", "carte_grise.pdf"]
    })
    print("Donnée exemple importée.")

if __name__ == "__main__":
    import_sample() 