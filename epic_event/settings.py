"""
settings.py - Application configuration module.

Defines:
- Entity mappings for CRUD operations.
- Database configurations for different environments.
- Application port settings.
- Sentry DSN for error tracking.
- Logging configuration with console and Sentry handlers.

Provides:
- setup_logging() function to initialize logging.
"""

import logging
import logging.config

entities = {
    "collaborators": "Collaborator",
    "contracts": "Contract",
    "clients": "Client",
    "events": "Event"
}

DATABASES = {
    "main": "epic_events.db",
    "demo": "demo_epic_event.db",
    "test": "test_database.db"
}

PORT = {
    "main": 8000,
    "demo": 8000,
    "test": 8000
}

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
            'level': 'INFO',
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
