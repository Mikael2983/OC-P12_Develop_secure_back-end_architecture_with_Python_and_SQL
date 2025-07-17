import argparse
from http.server import HTTPServer
import logging.config
import os
from pathlib import Path
import subprocess
import sys

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from epic_event.models import Database, load_data_in_database
from epic_event.models.utils import load_test_data_in_database, load_super_user
from epic_event.router import MyHandler
from epic_event.settings import DATABASES, PORT, SENTRY_DSN, setup_logging


sentry_logging = LoggingIntegration(level=logging.INFO,
                                    event_level=logging.INFO)
sentry_sdk.init(dsn=SENTRY_DSN, integrations=[sentry_logging])

setup_logging()
logger = logging.getLogger(__name__)
logger.info("Serveur lancé avec journalisation.")

parser = argparse.ArgumentParser(
    description="Lancer le serveur en mode normal ou test.")
parser.add_argument("mode", nargs="?", default="main",
                    choices=["main", "test", "demo"])

args = parser.parse_args()
operating_mode = args.mode

if operating_mode == "demo":
    path = Path(DATABASES[operating_mode])
    if path.exists():
        os.remove(path)

database = Database(DATABASES[operating_mode])
database.initialize_database()

session = database.get_session()

if operating_mode == "test":
    load_test_data_in_database(session)
elif operating_mode == "demo":
    load_data_in_database(session)
else:
    load_super_user(session)

MyHandler.session = session
MyHandler.database = database

if __name__ == "__main__":
    port = PORT[operating_mode]
    server_address = ("", port)
    httpd = HTTPServer(server_address, MyHandler)

    if operating_mode == "demo":

        print("Choisissez le mode de démarrage :")
        print("1. Manuel (ouvrir le serveur seulement)")
        print("2. Automatique (ouvrir le serveur et lancer la démo)")
        choice = input("Entrez 1 ou 2 : ").strip()

        if choice == "1":
            print(
                f"Serveur actif en mode manuel sur http://localhost:{port}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                httpd.server_close()

        elif choice == "2":
            print("Démarrage automatique : serveur + démo Selenium")
            selenium_process = subprocess.Popen(
                [sys.executable, "epic_event/demo_selenium.py"])
            print(f"Serveur actif sur http://localhost:{port}")

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                httpd.server_close()
                selenium_process.terminate()
                os.remove(path)
        else:
            print("Choix invalide. Arrêt.")

    else:
        print(f"Serveur actif sur http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
