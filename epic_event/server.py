import argparse
import logging.config
from http.server import HTTPServer

from epic_event.models import Database, load_data_in_database
from epic_event.models.utils import load_test_data_in_database, load_super_user
from epic_event.router import MyHandler
from epic_event.settings import DATABASES, PORT, SENTRY_DSN, setup_logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[sentry_logging]
)

setup_logging()
logger = logging.getLogger(__name__)
logger.info("Serveur lancé avec journalisation.")

parser = argparse.ArgumentParser(
    description="Lancer le serveur en mode normal ou test.")
parser.add_argument("mode", nargs="?", default="main",
                    choices=["main", "test"])

args = parser.parse_args()
operating_mode = args.mode

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
    print(f"Serveur actif sur http://localhost:{port}")
    httpd.serve_forever()
