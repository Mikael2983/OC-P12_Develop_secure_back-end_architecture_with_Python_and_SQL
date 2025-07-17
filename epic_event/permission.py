from functools import wraps
import re
from typing import TypeAlias, Union

from epic_event.models import SESSION_CONTEXT, Contract, Collaborator, Client, \
    Event
from epic_event.render_engine import TemplateRenderer
from epic_event.settings import entities

Entity: TypeAlias = Union[Collaborator, Client, Contract, Event]

PERMISSIONS = {
    "create": {
        "admin": {"collaborators", "clients", "events", "contracts"},
        "gestion": {"collaborators", "contracts"},
        "support": {},
        "commercial": {"clients", "events"}
    },
    "update": {
        "admin": {"collaborators", "clients", "events", "contracts"},
        "gestion": {"collaborators", "events", "contracts"},
        "support": {"events"},
        "commercial": {"clients"}
    },
    "delete": {
        "admin": {"collaborators", "clients", "events", "contracts"},
        "gestion": {"collaborators", "contracts"},
        "support": {"events"},
        "commercial": {"clients"}
    },
    "password": {
        "admin": {},
        "gestion": {},
        "support": {},
        "commercial": {}
    }
}

renderer = TemplateRenderer()


def login_required(func):
    def wrapper(*args, **kwargs):
        headers = kwargs.get("headers", {})
        cookie = headers.get("Cookie", "")
        match = re.search(r"session_id=([a-f0-9\-]+)", cookie)

        if not match:
            return renderer.render_template(
                "index.html",
                {"error": "Non authentifié"})

        session_id = match.group(1)

        current_session = SESSION_CONTEXT.get(session_id, None)
        if not current_session:
            return renderer.render_template("index.html", {
                "error": "veuillez vous identifier"})

        user = SESSION_CONTEXT.get(session_id).get("user", None)

        if not user:
            return renderer.render_template("index.html", {
                "error": "veuillez vous identifier"})
        kwargs["user"] = user
        kwargs["session_id"] = session_id
        return func(*args, **kwargs)

    return wrapper


def _has_object_permission(action: str,
                           user: Collaborator,
                           entity_name: str,
                           item: Entity) -> bool:
    """
    Checks if the user has permission to act on the given object according to
    business rules.
    Args:
        user: The user.
        action: The requested action ('create', 'update', 'delete').
        entity_name: Name of the entity.
        item: Object (optional) to which the action relates.

    Returns:
        bool: True if user has permission, False otherwise.
    """

    if user.role == "admin":
        return True

    if entity_name == "collaborators":
        return (getattr(item, "id", None) == getattr(user, "id", None)
                or user.role == "gestion")

    if entity_name == "clients":
        return getattr(item, "commercial", None) == user

    if entity_name == "contracts":
        return user.role == "gestion"

    if entity_name == "events":
        if getattr(item, "support", None) == user:
            return True
        return user.role == "gestion" and action == "update"

    return False


def has_permission(action):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):

            session = kwargs.get("session", None)
            user = kwargs.get("user")
            entity_name = kwargs.get("entity_name", "")

            allowed_entities = PERMISSIONS.get(action, {}).get(user.role,
                                                               set())
            can_access_entity = entity_name in allowed_entities

            pk = args[0] if args and isinstance(args[0], int) else None

            item = None

            if pk is not None:
                model = eval(entities.get(entity_name))
                results = model.filter_by_fields(session, id=pk)
                item = results[0] if results else None

            if item:

                if action == "password" and user != item:
                    return renderer.render_template(
                        "unauthorized.html",
                        {
                            "user": user,
                            "error": "Vous en pouvez pas modifier le mot de "
                                     "passe d'un autre utilisateur"
                        })

                if _has_object_permission(action, user, entity_name, item):
                    return view_func(*args, **kwargs)

            else:
                if entity_name == "events" and user.role != "admin":
                    data = args[0] if (
                            args and isinstance(args[0], dict)) else None
                    if data:
                        contract_id = int(data["contract_id"][0])
                        with session.no_autoflush:
                            contract = Contract.filter_by_fields(
                                session,
                                id=contract_id)[0]
                            if contract.client.commercial != user:
                                error = ("Vous ne pouvez créer que les "
                                         "événements de vos clients")
                                return _unauthorized(
                                    user,
                                    action,
                                    entity_name,
                                    error)
                    else:
                        return False
                if can_access_entity:
                    return view_func(*args, **kwargs)

            return _unauthorized(user, action, entity_name)

        return wrapper

    return decorator


def _unauthorized(user, action, entity_name, message=None):
    """
     Generate an HTML response displaying a custom denied access message.

    This function is used when a user attempts to perform a
    unauthorized action on an entity. It translates the type of action and
    the entity in French, then displays an error message in the template
    "unauthorized.html".

    Args:
        user (Collaborator): The current user attempting to perform the action.
        action (str): The action (for example "create", "update", "delete").
        entity_name (str): The name of the entity concerned ("collaborators",
            "clients", etc.).
        message (str, optional): A custom message to display. If None,
            a default message is generated from the action and the entity.

    Returns:
        str: The HTML content rendered with the error message.

    """
    translate = {
        "create": "créer",
        "update": "mettre à jour",
        "delete": "supprimer",
        "collaborators": "collaborateurs",
        "clients": "clients",
        "contracts": "contrats",
        "events": "événements"
    }
    error_msg = (message
                 or f"Accès refusé : un membre de l'équipe {user.role} n’a pas"
                    f" le droit de {translate[action]} des "
                    f"{translate[entity_name]}.")
    return renderer.render_template("unauthorized.html", {
        "user": user,
        "error": error_msg
    })


def user_can(user, action, entity_name, item=None):
    """
    Utility function to check a user’s permissions on a given entity/action.

    Args:
        user: The user.
        action: The requested action ('create', 'update', 'delete').
        entity_name: Name of the entity.
        item: Object (optional) to which the action relates.

    Returns:
        bool: True if user has permission, False otherwise.
    """
    role = getattr(user, "role", None)
    if not role:
        return False

    allowed = PERMISSIONS.get(action, {}).get(role, set())
    can_access_entity = entity_name in allowed

    if item:
        return _has_object_permission(action, user, entity_name, item)

    return can_access_entity
