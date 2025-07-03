from __future__ import annotations

import os
import logging

# --- Third-party imports with graceful degradation ---------------------------------
try:
    from dotenv import load_dotenv  # type: ignore[import]
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "python-dotenv est requis. Installez-le via 'pip install python-dotenv'."
    ) from exc

# Attempt firebase_admin import for Firestore operations
try:
    from firebase_admin import firestore  # type: ignore[import]
except ModuleNotFoundError:
    firestore = None  # type: ignore

load_dotenv()

try:
    from telegram.error import BadRequest, Forbidden  # type: ignore[import]
    from telegram import Bot  # type: ignore[import]
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "python-telegram-bot est requis. Installez-le via 'pip install python-telegram-bot[webhooks]'."
    ) from exc

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

"""Utility script to purge invalid `telegram_id` fields from the `operateurs` collection.

It checks each stored chat id with Telegram's `get_chat` endpoint. If the chat
does not exist ( `BadRequest` or `Forbidden` is raised ) the ``telegram_id``
field is cleared and the corresponding operator document is marked as
``actif=False``.

Usage (against Firestore):
    python cleanup_invalid_telegram_ids.py          # dry-run, no writes
    python cleanup_invalid_telegram_ids.py --apply  # perform updates

Usage with local sample data:
    python cleanup_invalid_telegram_ids.py \
        --sample-file bot/tests/sample_operateurs.json

The sample JSON must contain an array of documents with at minimum an ``id``
and a ``telegram_id`` field. In sample-file mode the script never performs any
write operations to Firestore.
"""

from typing import List, Dict, Any, Optional, Iterator, Tuple

def _stream_firestore_docs() -> Iterator[Tuple[str, Dict[str, Any]]]:
    """Yield ``(document_id, document_data)`` from Firestore.

    Relies on the global ``db`` instance provided by ``utils.firestore``.
    When Firebase is disabled this function is never called.
    """
    for doc in db.collection(COLLECTION).stream():  # type: ignore[attr-defined]
        yield doc.id, doc.to_dict()


def _stream_sample_file(path: str) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """Load sample documents from *path* for local / CI testing."""
    import json

    with open(path, "r", encoding="utf-8") as fp:
        arr: List[Dict[str, Any]] = json.load(fp)

    for obj in arr:
        yield str(obj.get("id", "sample")), obj


def cleanup_invalid_ids(*, dry_run: bool = True, sample_file: Optional[str] = None) -> None:
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
            if not dry_run and not sample_file and firestore is not None:
                db.collection(COLLECTION).document(doc_id).update({FIELD: firestore.DELETE_FIELD, "actif": False})  # type: ignore[attr-defined]
            elif not dry_run and firestore is None:
                logging.error("Impossible de mettre à jour Firestore : firebase-admin manquant.")
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