import os
import logging
from dotenv import load_dotenv
from firebase_admin import firestore

load_dotenv()

from telegram.error import BadRequest, Forbidden
from telegram import Bot

from utils.firestore import db

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN/TELEGRAM_TOKEN manquant dans l'environnement.")

bot = Bot(token=str(BOT_TOKEN))

COLLECTION = "operateurs"
FIELD = "telegram_id"


def cleanup_invalid_ids(dry_run: bool = True):
    docs = db.collection(COLLECTION).stream()
    invalid_docs = []
    for doc in docs:
        data = doc.to_dict()
        chat_id = data.get(FIELD)
        if not chat_id:
            continue
        try:
            bot.get_chat(chat_id)  # type: ignore
        except (BadRequest, Forbidden) as e:
            # Chat inexistant ou bot bloqué
            logging.warning("Chat introuvable pour %s: %s", chat_id, e)
            invalid_docs.append(doc.id)
            if not dry_run:
                db.collection(COLLECTION).document(doc.id).update({FIELD: firestore.DELETE_FIELD, "actif": False})
    logging.info("Documents invalides trouvés: %s", invalid_docs)
    if dry_run:
        logging.info("Mode dry-run : aucun document modifié. Relancez avec dry_run=False pour appliquer la suppression.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Nettoie les telegram_id invalides dans Firestore")
    parser.add_argument("--apply", action="store_true", help="Appliquer les changements (par défaut dry-run)")
    args = parser.parse_args()

    cleanup_invalid_ids(dry_run=not args.apply)