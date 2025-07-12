from datetime import datetime, date
import uuid
from typing import Any, Dict, Union

import logging
from sqlalchemy.orm import Session

from epic_event.models import Collaborator, Client, Contract, Event, Database
from epic_event.models import SESSION_CONTEXT
from epic_event.permission import login_required, has_permission, user_can
from .render_engine import TemplateRenderer, make_query_string
from .settings import entities

logger = logging.getLogger(__name__)
renderer = TemplateRenderer()


def get_model(entity_name):
    model = eval(entities.get(entity_name))
    return model


def home() -> str:
    """Render the home page."""
    return renderer.render_template("index.html", {"error": ""})


def login(db: Session, data: Dict[str, list[str]]) -> dict:
    """Authenticate user with provided login form data.

    Args:
        db (Session): SQLAlchemy session.
        data: Form data including full_name and password.

    Returns:
        HTML or session ID string if login succeeds.
    """
    full_name = data.get("full_name", [""])[0]
    password = data.get("password", [""])[0]
    users = Collaborator.filter_by_fields(
        db,
        full_name=full_name
    )

    if users:
        user = users[0]
        if user.check_password(password):
            session_id = str(uuid.uuid4())
            SESSION_CONTEXT[session_id] = {
                "user": user,
                "Display_archive": False
            }

            return {"success": True, "session_id": session_id}

    html = renderer.render_template(
        "index.html",
        {"error": "Identifiants invalides."}
    )
    return {"success": False, "html": html}


@login_required
def logout(*args, **kwargs) -> str:
    """Log out the current user by deleting session ID from cookie.

    Returns:
        Rendered index page with logout state.
    """
    session_id = kwargs.get("session_id", {})
    if session_id:
        SESSION_CONTEXT.pop(session_id, None)

    return renderer.render_template("index.html",
                                    {"error": ""})


@login_required
@has_permission("password")
def collaborator_password_view(pk, **kwargs) -> str:
    """Render form for updating collaborator password."""
    return renderer.render_template("password_change.html",
                                    {
                                        "user": kwargs.get("user", {}),
                                        "error": "",
                                        "success": ""
                                    })


@login_required
@has_permission("password")
def user_password_post_view(pk, data: Dict[str, str], **kwargs) -> str:
    """Update user's password based on provided input.

    Args:
        pk: user's primary key
        data: Dictionary with password fields.

    Returns:
        Rendered page showing success or error messages.

    """
    user = kwargs.get("user")
    session = kwargs.get("session")
    current_password = data.get("current_password")
    new = data.get("new_password", "")
    confirm = data.get("confirm_password", "")

    if not user.check_password(current_password):
        return renderer.render_template(
            "password_change.html",
            {
                "user": user,
                "error": "Mot de passe actuel incorrect.",
                "success": ""
            })

    if new != confirm:
        return renderer.render_template(
            "password_change.html",
            {
                "user": user,
                "error": "Les mots de passe ne correspondent pas.",
                "success": ""
            })

    if len(new) < 6:
        return renderer.render_template(
            "password_change.html",
            {
                "user": user,
                "error": "Le mot de passe doit faire au moins 6 caractères.",
                "success": ""
            })

    user.set_password(new)
    user.save(session)
    return renderer.render_template(
        "password_change.html",
        {
            "user": user,
            "error": "",
            "success": "Mot de passe mis à jour avec succès."
        })


@login_required
def entity_list_view(query_params: Dict[str, list[str]],
                     **kwargs) -> str:
    """Render a list view for the specified entity.

    Args:
        query_params: HTTP GET query parameters for sorting.

    Returns:
        Rendered HTML page of the entity list.
    """
    headers = kwargs.get("headers")
    session_id = kwargs.get("session_id")
    entity_name = kwargs.get("entity_name", "")
    user = kwargs.get("user")
    session = kwargs.get("session")
    model = get_model(entity_name)

    if not model:
        logger.exception(f"Entité inconnue: {entity_name}")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": "Entité inconnue"
            })

    sort_field = query_params.get("sort", ["id"])[0]
    order = query_params.get("order", ["asc"])[0]
    descending = order == "desc"
    show_archived = SESSION_CONTEXT[session_id].get("Display_archive", False)
    query_strings = make_query_string(query_params)

    try:
        items = model.order_by_fields(session, sort_field, descending,
                                      archived=show_archived)
        if entity_name == "collaborators":
            items = [item for item in items if item.role != "admin"]
    except Exception as e:
        logger.exception(f"Erreur de Tri: {e}")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": f"Erreur de tri : {e}"
            })

    return renderer.render_template(
        f"{entity_name}.html",
        {
            "user": user,
            entity_name: items,
            "sort": sort_field,
            "order": order,
            "show_archived": show_archived,
            "sort_links": query_strings,
            "user_can": user_can,
            "error": "",
        })


@login_required
def entity_detail_view(pk: int, **kwargs) -> str:
    """Render detail view of a single entity item.

    Args:
        pk: Primary key of the item.
    kwargs:
        session: SQLAlchemy Session.
        entity_name: Type of entity.

    Returns:
        Rendered detail page.
    """
    session_id = kwargs.get("session_id")

    entity_name = kwargs.get("entity_name", "")
    user = kwargs.get("user", None)
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception(f"Entité inconnue: {entity_name}")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": "Entité inconnue"
            })

    items = model.filter_by_fields(session,
                                   archived=SESSION_CONTEXT[session_id].get(
                                       "Display_archive",
                                       False),
                                   id=pk
                                   )
    if not items:
        logger.exception(
            f"L'entité {entity_name} avec l'id={pk} est introuvable")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": f"{entity_name.capitalize()} introuvable"
            })

    item = items[0]
    context = {
        "user": user,
        "user_can": user_can,
        entity_name: [item],
        entity_name[:-1]: item
    }

    if entity_name == "collaborators":
        context.update(events=list(item.events), clients=list(item.clients))
    elif entity_name == "clients":
        context.update(collaborators=[item.commercial],
                       contracts=list(item.contracts))
    elif entity_name == "contracts":
        context.update(clients=[item.client], events=[item.event])
    elif entity_name == "events":
        context.update(clients=[item.contract.client],
                       contracts=[item.contract])

    return renderer.render_template(
        f"{entity_name}_detail.html",
        context)


@login_required
@has_permission("create")
def entity_create_view(query_params: [Dict[str, list[str]]] = None,
                       **kwargs) -> str:
    """Render a creation form for the specified entity.

    Args:
        query_params: query parameters.

    Kwargs:
        session: SQLAlchemy session.
        entity_name: Type of entity.
        headers
    Returns:
        Rendered creation form template.
    """
    user = kwargs.get("user")
    entity_name = kwargs.get("entity_name")
    session = kwargs.get("session")

    context: Dict[str, Any] = {"user": user, "error": ""}

    if entity_name == "contracts":
        context["clients"] = Client.filter_by_fields(session)

    if entity_name == "events":
        contract_id = query_params.get("contract_id", [None])[
            0] if query_params else None
        context["contract_id"] = int(contract_id) if contract_id else None

    return renderer.render_template(
        f"{entity_name}_create.html",
        context)


@login_required
@has_permission("create")
def entity_create_post_view(data: Dict[str, Any], **kwargs) -> Union[
    str, bool]:
    """Handle submission of entity creation form.

    Args:
        data: Form data.

    Returns:
        True if successful, or rendered template with error.
    """
    session = kwargs.get("session")
    user = kwargs.get("user")
    entity_name = kwargs.get("entity_name")
    model = get_model(entity_name)
    db = kwargs.get("session")
    if not model:
        logger.exception(f"Entité inconnue: {entity_name}")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": "Entité inconnue"})

    try:
        if entity_name == "collaborators":
            instance = Collaborator(
                full_name=data["full_name"],
                email=data["email"],
                role=data["role"]
            )
            instance.set_password(data["password"])

        elif entity_name == "contracts":
            print(data["signed"], type(data["signed"]))
            data["signed"] = Contract.normalize_signed(data["signed"])
            print(data["signed"], type(data["signed"]))
            data["created_date"] = datetime.today()
            instance = model(**data)

        elif entity_name == "clients":
            data["id_commercial"] = user.id
            data["created_date"] = datetime.today()
            data['last_contact_date'] = date.fromisoformat(
                data['last_contact_date'])
            instance = model(**data)

        elif entity_name == "events":
            data["start_date"] = date.fromisoformat(data["start_date"])
            data["end_date"] = date.fromisoformat(data["end_date"])
            data["participants"] = int(data["participants"])
            data["contract_id"] = int(data["contract_id"])
            instance = model(**data)

        else:
            instance = model(**data)

        instance.validate_all(db)

    except Exception as e:
        session.rollback()
        session.refresh(instance)
        return renderer.render_template(
            f"{entity_name}_create.html",
            {"user": user, "error": f"Erreur : {str(e)}"}
        )
    instance.save(db)
    logger.info(f"Entité créé: {instance}")
    return True

@login_required
@has_permission("update")
def entity_update_view(pk: int, **kwargs) -> str:
    """Render form to update entity identified by pk."""
    session_id = kwargs.get("session_id")
    user = kwargs.get("user")
    entity_name = kwargs.get("entity_name")
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception(f"Entité inconnue: {entity_name}")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": "Entité inconnue"})

    items = model.filter_by_fields(session,
                                   archived=SESSION_CONTEXT[session_id].get(
                                       "Display_archive",
                                       False),
                                   id=pk
                                   )
    context = {
        "user": user,
        entity_name[:-1]: items[0],
        "error": ""
    }
    if not items:
        logger.exception(
            f"L'entité {entity_name} avec l'id={pk} est introuvable")
        context["error"] = f"{entity_name.capitalize()} introuvable"

        return renderer.render_template("index.html",
                                        context)

    if entity_name == "events":
        supports = Collaborator.filter_by_fields(session,
                                                 archived=False,
                                                 role="support")
        context["supports"] = supports

    if entity_name == "contracts":
        context["clients"] = Client.filter_by_fields(session,
                                                     archived=False)

    return renderer.render_template(f"{entity_name}_update.html",
                                    context)


@login_required
@has_permission("update")
def entity_update_post_view(pk: int,
                            data: Dict[str, Any],
                            **kwargs) -> Union[str, bool]:
    """Handle update form submission for entity."""
    headers = kwargs.get("headers")
    session_id = kwargs.get("session_id")
    user = kwargs.get("user")
    entity_name = kwargs.get("entity_name")
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception(f"Entité inconnue: {entity_name}")
        return renderer.render_template(
            "index.html",

            {
                "user": user,
                "error": "Entité inconnue"})

    items = model.filter_by_fields(session,
                                   archived=SESSION_CONTEXT[session_id].get(
                                       "Display_archive",
                                       False),
                                   id=pk
                                   )
    if not items:
        logger.exception(
            f"L'entité {entity_name} avec l'id={pk} est introuvable")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": f"{entity_name.capitalize()} introuvable"
            })

    instance = items[0]

    try:
        for k, v in data.items():
            if k == "signed":
                v = 'True' == v
            setattr(instance, k, v)
        instance.validate_all(session)

    except Exception as e:
        session.rollback()
        session.refresh(instance)
        return renderer.render_template(
            f"{entity_name}_update.html",
            {"user": user, entity_name[:-1]: instance,
             "error": f"Erreur : {e}"}
        )
    instance.save(session)
    logger.info(f"L'entité {entity_name} avec l'id={pk} est mis à jour")
    return True

@login_required
@has_permission("update")
def entity_delete_view(pk, **kwargs) -> bool:
    """Soft-delete an entity by setting archived flag."""

    session_id = kwargs.get("session_id")
    entity_name = kwargs.get("entity_name")
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception(f"Entité inconnue: {entity_name}")
        return False

    items = model.filter_by_fields(session,
                                   archived=SESSION_CONTEXT[session_id].get(
                                       "Display_archive",
                                       False),
                                   id=pk
                                   )

    if not items:
        logger.exception(
            f"L'entité {entity_name} avec l'id={pk} est introuvable")
        return False

    instance = items[0]
    instance.archived = True
    instance.save(session)
    return True


@login_required
@has_permission("delete")
def entity_delete_post_view(pk: int, **kwargs) -> \
        Union[bool, str]:
    """Process the deletion of an entity (soft delete).

    Args:
        db (Session): SQLAlchemy session.
        user: Authenticated user.
        entity_name: Type of entity.
        pk: Primary key.

    Returns:
        True if deleted, or form with error.
    """
    user = kwargs.get("user")
    entity_name = kwargs.get("entity_name")
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception(f"Entité inconnue: {entity_name}")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": "Entité inconnue"
            })

    item = model.filter_by_fields(session, id=pk)
    if not item:
        logger.exception(
            f"L'entité {entity_name} avec l'id={pk} est introuvable")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": f"{entity_name.capitalize()} introuvable"
            })

    try:
        model.soft_delete(session, pk)
        logger.info(
            f"L'entité {entity_name} avec l'id={pk} est supprimé")
        return True
    except Exception as e:
        session.rollback()
        session.refresh(item)
        logger.exception(e)
        return renderer.render_template(
            f"{entity_name}_delete.html",
            {
                "user": user,
                entity_name[:-1]: item[0],
                "error": f"Erreur lors de la suppression : {str(e)}"
            })


@login_required
@has_permission("update")
def client_contact_view(client_id: int, **kwargs) -> Union[bool, str]:
    """Mark a client as contacted (updates last_contact_date).

    Args:
        db (Session): SQLAlchemy session.
        user: Authenticated user.
        entity_name: Should be "clients".
        client_id: ID of the client.

    Returns:
        True if success, or detail page with error.
    """
    user = kwargs.get("user")
    session = kwargs.get("session")

    clients = Client.filter_by_fields(session, id=client_id)
    if not clients:
        logger.exception("Client introuvable")
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": "Client introuvable"
            })

    client = clients[0]
    try:
        client.last_contact_date = datetime.today().date()
        client.save(session)
        return True
    except Exception as e:
        logger.exception(e)
        return renderer.render_template(
            "clients_detail.html",
            {
                "user": user,
                "client": client,
                "clients": [client],
                "error": f"Erreur : {str(e)}"
            })

routes = {
    "/": home,
}
