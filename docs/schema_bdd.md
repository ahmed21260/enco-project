# Schéma BDD Firestore ENCO

- **machines/**
  - nom: string
  - etat: string
  - documents: array
- **operateurs/**
  - nom: string
  - historique: array
- **prises_de_poste/**
  - operateur_id: ref
  - machine_id: ref
  - date: timestamp
  - checklist: array
- **anomalies/**
  - machine_id: ref
  - description: string
  - photo_url: string
  - gravite: string
  - date: timestamp 