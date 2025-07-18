import logging
import uuid
from datetime import date, datetime, time
from typing import Any, Dict, Union

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# the import of Event is necessary. it appears indirectly by model = get_model(entity_name)
from epic_event.models import (SESSION_CONTEXT, Client, Collaborator, Contract,
                               Event)
from epic_event.permission import has_permission, login_required, user_can
from epic_event.render_engine import TemplateRenderer, make_query_string
from epic_event.settings import entities

logger = logging.getLogger(__name__)
renderer = TemplateRenderer()


def get_model(entity_name):
    """
        Retrieve the ORM model class associated with the given entity name.

        Args:
            entity_name (str): Name of the entity.

        Returns:
            Type: ORM model class corresponding to the entity name.
        """
    model = eval(entities.get(entity_name))
    return model


def home() -> str:
    """Render the home page."""
    return renderer.render_template(
        "index.html",
        {"error": ""})


def login(db: Session, data: Dict[str, list[str]]) -> dict:
    """
    Authenticate a user based on submitted login credentials.

    Args:
        db (Session): SQLAlchemy session instance.
        data (Dict[str, list[str]]): Dictionary containing form fields:
            - 'full_name': List with the full name as first element.
            - 'password': List with the password as first element.

    Returns:
        dict: A dictionary containing:
            - {'success': True, 'session_id': str} if authentication succeeds.
            - {'success': False, 'html': str} if authentication fails,
              with rendered login page including an error message.
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
def logout(**kwargs) -> str:
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
    """
    Render the password update form for a specific collaborator.

    Args:
        pk (int): Primary key of the collaborator.

    Kwargs:
        user: Current authenticated collaborator.
        session: SQLAlchemy session instance (optional, for consistency).

    Returns:
        str: Rendered HTML string of the password change form.
    """
    return renderer.render_template("password_change.html",
                                    {
                                        "user": kwargs.get("user", {}),
                                        "error": "",
                                        "success": ""
                                    })


@login_required
@has_permission("password")
def user_password_post_view(pk, data: Dict[str, str], **kwargs) -> str:
    """
    Update the authenticated user's password after validating input.

    Args:
        pk (int): Primary key of the user whose password is being updated.
        data (Dict[str, str]): Dictionary containing the following keys:
            - 'current_password': User's current password.
            - 'new_password': Desired new password.
            - 'Confirm_password': Confirmation of the new password.

    Kwargs:
        session: SQLAlchemy session instance.
        user: Current authenticated collaborator.

    Returns:
        str: Rendered HTML string of the password change page,
             showing success or error messages.
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
    """
    Render a list view for the specified entity with sorting and archive filtering.

    Args:
        query_params (Dict[str, list[str]]): HTTP GET query parameters for sorting
            (e.g., 'sort' and 'order').

    Kwargs:
        session: SQLAlchemy session instance.
        entity_name (str): Name of the entity type to list.
        session_id: Contextual session identifier for archive filtering.
        user: Current authenticated collaborator.

    Returns:
        str: Rendered HTML string of the entity list page or error page.
    """
    session_id = kwargs.get("session_id")
    entity_name = kwargs.get("entity_name", "")
    user = kwargs.get("user")
    session = kwargs.get("session")
    model = get_model(entity_name)

    if not model:
        logger.exception("Entité inconnue: %s", entity_name)
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
    except (AttributeError, ValueError) as e:
        logger.warning("Erreur de tri : %s", e)
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": f"Champ de tri invalide : {e}"
            })

    except SQLAlchemyError as e:
        logger.error("Erreur SQL : %s", e)
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": "Erreur base de données lors du tri"
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
            "with_sorting": True,
            # on template, allows the display of sorting links
            "user_can": user_can,
            "error": "",
        })


@login_required
def entity_detail_view(pk: int, **kwargs) -> str:
    """
    Render the detail page of a specific entity instance.

    Args:
        pk (int): Primary key of the entity instance to retrieve.

    Kwargs:
        session: SQLAlchemy session instance.
        entity_name (str): Name of the entity to display.
        session_id: Contextual session identifier for archive filtering.
        user: Current authenticated collaborator.

    Returns:
        str: Rendered HTML string of the entity detail page or error page.
    """
    session_id = kwargs.get("session_id")

    entity_name = kwargs.get("entity_name", "")
    user = kwargs.get("user", None)
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception("Entité inconnue: %s", entity_name)
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
            "L'entité %s avec l'id=%s est introuvable", entity_name, pk)
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": f"{entity_name.capitalize()} introuvable"
            })

    item = items[0]
    context = {
        "user": user,
        "with_sorting": False,
        # on template, prevents the display of sorting links
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

    This view handles the rendering of a creation form for a given entity.
    It processes query parameters and context-specific data such as user
    session, entity type, and optional HTTP headers.

    Args:
        query_params (Optional[List[Dict[str, List[str]]]]):
            A dictionary of query parameters, typically from the URL.
            For example: {"contract_id": ["123"]}.

    Kwargs:
        session (Session):
            An SQLAlchemy session instance for database interactions.

        entity_name (str):
            The name of the entity for which the form is rendered.
            Example: "contracts" or "events".

        headers (Optional[Dict[str, str]]):
            A dictionary of HTTP headers passed from the request context.

        user (Any):
            The currently authenticated collaborator.

    Returns:
        str: The rendered HTML template as a string.
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
    """Handle submission of an entity creation form.

    Args:
        data (Dict[str, Any]): Form data.

    Kwargs:
        session: SQLAlchemy session.
        entity_name (str): Name of the entity to create.
        user: Current authenticated collaborator.
        headers (Optional[Dict[str, str]]):
            A dictionary of HTTP headers passed from the request context.

    Returns:
        bool or str: True if successful, otherwise the rendered error template.
    """
    session = kwargs.get("session")
    user = kwargs.get("user")
    entity_name = kwargs.get("entity_name")
    model = get_model(entity_name)

    if not model:
        logger.exception("Entité inconnue: %s", entity_name)
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": "Entité inconnue"})

    if entity_name == "collaborators":
        instance = Collaborator(
            full_name=data["full_name"],
            email=data["email"],
            role=data["role"]
        )
        instance.set_password(data["password"])

    elif entity_name == "contracts":
        data["signed"] = Contract.normalize_signed(data["signed"])
        data["created_date"] = datetime.today()
        instance = model(**data)

    elif entity_name == "clients":
        data["id_commercial"] = user.id
        data["created_date"] = date.today()
        data['last_contact_date'] = date.fromisoformat(
            data['last_contact_date'])
        instance = model(**data)

    elif entity_name == "events":
        start_date = date.fromisoformat(data["start_date"])
        start_time = time.fromisoformat(data["start_time"])
        end_date = date.fromisoformat(data["end_date"])
        end_time = time.fromisoformat(data["end_time"])

        data["start_date"] = datetime.combine(start_date, start_time)
        data["end_date"] = datetime.combine(end_date, end_time)
        data["participants"] = int(data["participants"])
        data["contract_id"] = int(data["contract_id"])
        instance = model(**data)

    else:
        instance = model(**data)

    try:
        instance.validate_all(session)
        instance.save(session)

    except (ValueError, TypeError, SQLAlchemyError) as e:
        session.rollback()
        logger.warning(
            "Erreur lors de la création d’un %s : %s.", entity_name, e)
        return renderer.render_template(
            f"{entity_name}_create.html",
            {"user": user, "error": str(e)}
        )

    logger.info("Entité créée : %s.", instance)
    return True


@login_required
@has_permission("update")
def entity_update_view(pk: int, **kwargs) -> str:
    """
    Render an update form for the entity identified by pk.

    Args:
        pk (int): Primary key of the entity to update.

    Kwargs:
        session: SQLAlchemy session.
        entity_name (str): Name of the entity to update.
        session_id: Current session context ID.
        user: Current authenticated collaborator.
        headers (Optional[Dict[str, str]]): A dictionary of HTTP headers passed
         from the request context.

    Returns:
        str: Rendered update form template.

    """

    session_id = kwargs.get("session_id")
    user = kwargs.get("user")
    entity_name = kwargs.get("entity_name")
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception("Entité inconnue: %s.", entity_name)
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
            "L'entité %s entity_name avec l'id= %s pk est introuvable",
            entity_name, pk)
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
    """Handle update form submission for an entity.

    Args:
        pk (int): Primary key of the entity to update.
        data (Dict[str, Any]): Updated form data.

    Kwargs:
        session: SQLAlchemy session.
        entity_name (str): Name of the entity.
        session_id: Current session context ID.
        user: Current authenticated collaborator.

    Returns:
        bool or str: True if successful, otherwise the rendered error template.

    Raises:
        ValueError: If the business data is invalid during the update.
        TypeError: If incorrect type is provided in update data.
        SQLAlchemyError: If a database error occurs during the commit.
    """

    session_id = kwargs.get("session_id")
    user = kwargs.get("user")
    entity_name = kwargs.get("entity_name")
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception("Entité inconnue: %s.", entity_name)
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
            "L'entité %s avec l'id=%s est introuvable",
            entity_name, pk)
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": f"{entity_name.capitalize()} introuvable"
            })

    instance = items[0]

    try:
        instance.update(session, **data)
        instance.save(session)
        logger.info("L'entité %s avec l'id=%s est mis à jour",
                    entity_name, pk)
        return True

    except (ValueError, TypeError) as e:
        session.rollback()
        logger.warning(
            "Erreur métier lors de la mise à jour de %s id=%s: %s",
            entity_name, pk, e)
        return renderer.render_template(
            f"{entity_name}_update.html",
            {
                "user": user,
                entity_name[:-1]: instance,
                "error": f"Erreur : {e}"
            }
        )


@login_required
@has_permission("update")
def entity_delete_view(pk, **kwargs) -> bool:
    """
    Soft-delete an entity by setting its archived flag.

    Args:
        pk (int): Primary key of the entity to delete.

    Kwargs:
        session: SQLAlchemy session.
        entity_name (str): Name of the entity.
        session_id: Current session context ID.

    Returns:
        bool: True if deletion is successful, False otherwise.
    """

    session_id = kwargs.get("session_id")
    entity_name = kwargs.get("entity_name")
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception("Entité inconnue: %s.", entity_name)
        return False

    items = model.filter_by_fields(session,
                                   archived=SESSION_CONTEXT[session_id].get(
                                       "Display_archive",
                                       False),
                                   id=pk
                                   )

    if not items:
        logger.exception(
            "L'entité %s avec l'id=%s est introuvable",
            entity_name, pk)
        return False

    instance = items[0]
    instance.archived = True
    instance.save(session)
    return True


@login_required
@has_permission("delete")
def entity_delete_post_view(pk: int, **kwargs) -> \
        Union[bool, str]:
    """
    Process the soft deletion of an entity and return result.

    Args:
        pk (int): Primary key of the entity to delete.

    Kwargs:
        session: SQLAlchemy session instance.
        user: Current authenticated collaborator.
        entity_name (str): Name of the entity to delete.

    Returns:
        Union[bool, str]:
            - True if the deletion was successful.
            - Rendered template string with error message otherwise.

    Raises:
        ValueError: If the entity does not have the 'archived' field or
            a business error occurs in `soft_delete`.
        TypeError: If the data is mistyped in the call to `soft_delete`.
        SQLAlchemyError: If a database error occurs during the deletion.
    """
    user = kwargs.get("user")
    entity_name = kwargs.get("entity_name")
    session = kwargs.get("session")

    model = get_model(entity_name)
    if not model:
        logger.exception("Entité inconnue: %s.", entity_name)
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": "Entité inconnue"
            })

    items = model.filter_by_fields(session, id=pk)

    if not items:
        logger.exception(
            "L'entité %s avec l'id=%s est introuvable",
            entity_name, pk)
        return renderer.render_template(
            "index.html",
            {
                "user": user,
                "error": f"{entity_name.capitalize()} introuvable"
            })

    item = items[0]

    try:
        model.soft_delete(session, pk)
        logger.info(
            "L'entité %s avec l'id=%s est supprimé",
            entity_name, pk)
        return True
    except (ValueError, TypeError) as e:
        session.rollback()
        logger.warning(
            "Erreur métier lors de la suppression de %s id=%s: %s",
            entity_name, pk, e)
        return renderer.render_template(
            f"{entity_name}_delete.html",
            {"user": user, "error": str(e), entity_name[:-1]: item}
        )

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(
            "Erreur SQL lors de la suppression de %s id=%s: %s",
            entity_name, pk, e)
        return renderer.render_template(
            f"{entity_name}_delete.html",
            {"user": user, "error": "Erreur technique en base de données",
             entity_name[:-1]: item}
        )


@login_required
@has_permission("update")
def client_contact_view(client_id: int, **kwargs) -> Union[bool, str]:
    """
    Mark a client as contacted by updating its `last_contact_date`.

    Args:
        client_id (int): ID of the client to update.

    Kwargs:
        session: SQLAlchemy session instance.
        user: Current authenticated collaborator.

    Returns:
        Union[bool, str]:
            - True if the update is successful.
            - Rendered template string with error message otherwise.

    Raises:
        ValueError: If the client does not exist or if the business data is invalid.
        TypeError: If the data has an incorrect type (ex: wrong date).
        SQLAlchemyError: If a database error occurs during the commit.
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
        client.validate_all(session)
        client.save(session)
        return True
    except (ValueError, TypeError) as e:
        logger.warning("Erreur de validation : %s.",e)
        return renderer.render_template(
            "clients_detail.html",
            {
                "user": user,
                "with_sorting": False,
                "user_can": user_can,
                "client": client,
                "clients": [client],
                "error": f"Erreur de validation : {str(e)}"
            })

    except SQLAlchemyError as e:
        logger.error("Erreur base de données : %s.", e)
        session.rollback()
        return renderer.render_template(
            "clients_detail.html",
            {
                "user": user,
                "with_sorting": False,
                "user_can": user_can,
                "client": client,
                "clients": [client],
                "error": "Erreur technique lors de la sauvegarde."
            })


routes = {
    "/": home,
}
