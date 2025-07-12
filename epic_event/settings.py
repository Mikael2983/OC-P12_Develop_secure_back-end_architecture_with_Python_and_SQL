import logging
import logging.config
from sentry_sdk.integrations.logging import LoggingIntegration


entities = {
    "collaborators": "Collaborator",
    "contracts": "Contract",
    "clients": "Client",
    "events": "Event"
}

DATABASES = {"main": "epic_events.db",
             "test": "test_database.db"}

PORT = {"main": 8000,
        "test": 5000}


SENTRY_DSN = "https://422a046974326b3d65c42157b707bdc2@o4509643092721664.ingest.de.sentry.io/4509643095146576"

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.EventHandler',
        },
    },
    'root': {
        'handlers': ['console', 'sentry'],
        'level': 'INFO',
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
