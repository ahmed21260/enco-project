import os
import logging
from dotenv import load_dotenv
from firebase_admin import firestore

load_dotenv()

from telegram.error import BadRequest, Forbidden
from telegram import Bot

# Import db if Firestore enabled; otherwise create a stub list
try:
    from utils.firestore import db, USE_FIRESTORE
except ImportError:
    USE_FIRESTORE = False
    db = None  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN/TELEGRAM_TOKEN manquant dans l'environnement.")

bot = Bot(token=str(BOT_TOKEN))

COLLECTION = "operateurs"
FIELD = "telegram_id"

"""Script de nettoyage des telegram_id invalides dans Firestore.

Utilisation :
    python cleanup_invalid_telegram_ids.py          # Dry-run (aucune modification)
    python cleanup_invalid_telegram_ids.py --apply  # Supprime telegram_id invalides
"""
from typing import List, Dict, Any, Optional

def _stream_firestore_docs():
    """Retourne un iterable de tuples (id, data) depuis Firestore."""
    for doc in db.collection(COLLECTION).stream():  # type: ignore
        yield doc.id, doc.to_dict()


def _stream_sample_file(path: str):
    """Charge un fichier JSON (liste de docs) pour test local."""
    import json, pathlib
    with open(path, "r", encoding="utf-8") as fp:
        arr: List[Dict[str, Any]] = json.load(fp)
    for obj in arr:
        yield str(obj.get("id", "sample")), obj


def cleanup_invalid_ids(dry_run: bool = True, sample_file: Optional[str] = None):
    if sample_file:
        doc_iter = _stream_sample_file(sample_file)
    else:
        if not USE_FIRESTORE or db is None:
            logging.error("Firestore n'est pas activé (ENCO_USE_FIRESTORE != 1). Abandon nettoyage.")
            return
        doc_iter = _stream_firestore_docs()

    invalid_docs = []
    for doc_id, data in doc_iter:
        chat_id = data.get(FIELD)
        if not chat_id:
            continue
        try:
            bot.get_chat(chat_id)  # type: ignore
        except (BadRequest, Forbidden) as e:
            # Chat inexistant ou bot bloqué
            logging.warning("Chat introuvable pour %s: %s", chat_id, e)
            invalid_docs.append(doc_id)
            if not dry_run and not sample_file:
                db.collection(COLLECTION).document(doc_id).update({FIELD: firestore.DELETE_FIELD, "actif": False})  # type: ignore
    logging.info("Documents invalides trouvés: %s", invalid_docs)
    if dry_run:
        logging.info("Mode dry-run : aucun document modifié. Relancez avec dry_run=False pour appliquer la suppression.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Nettoie les telegram_id invalides dans Firestore")
    parser.add_argument("--apply", action="store_true", help="Appliquer les changements (par défaut dry-run)")
    parser.add_argument("--sample-file", help="Fichier JSON contenant des opérateurs factices pour test")
    args = parser.parse_args()

    cleanup_invalid_ids(dry_run=not args.apply, sample_file=args.sample_file)