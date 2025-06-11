from functools import wraps
import re
import uuid

from models.collaborator import Collaborator
from models.client import Client
from models.contract import Contract
from models.event import Event
from models.db_model import Base, engine
from models.init_db import init_data_base
from render_engine import render_template

Base.metadata.create_all(bind=engine)
init_data_base()
SESSIONS = {}
entities = {
    "collaborators": Collaborator,
    "contracts": Contract,
    "clients": Client,
    "events": Event
}


def get_user_from_session(headers):
    cookie = headers.get("Cookie")
    if not cookie:
        return None
    match = re.search(r"session_id=([a-f0-9\\-]+)", cookie)
    if not match:
        return None
    session_id = match.group(1)
    return SESSIONS.get(session_id)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(headers, *args, **kwargs):
        user = get_user_from_session(headers)
        if not user:
            return "<h1>Accès refusé. Veuillez vous connecter.</h1>"
        return view_func(user, *args, **kwargs)

    return wrapper


def home():
    return render_template("index.html", {"error": ""})


def login(data):
    full_name = data.get("full_name", [""])[0]
    password = data.get("password", [""])[0]
    users = Collaborator.filter_by_fields(full_name=full_name)
    if users:
        user = users[0]
        if user.check_password(password):
            session_id = str(uuid.uuid4())
            SESSIONS[session_id] = user
            context = {
                "user": user,
                "collaborators": Collaborator.order_by_field("id"),

            }
            html = render_template("collaborators.html", context)
            return html, session_id
    return render_template("index.html", {"error": "Identifiants invalides."})


@login_required
def entity_list_view(user, entity_name):
    model = entities.get(entity_name)
    if not model:
        return "<h1>Entité inconnue</h1>"
    items = model.order_by_field("id")
    return render_template(f"{entity_name}.html", {
        "user": user,
        entity_name: items
    })


@login_required
def entity_detail_view(user, entity_name, pk):
    model = entities.get(entity_name)
    if not model:
        return "<h1>Entité inconnue</h1>"
    item = model.filter_by_fields(id=pk)
    if not item:
        return f"<h1>{entity_name.capitalize()} introuvable</h1>"

    print(f"{entity_name}_detail.html")
    entity = entity_name[:-1]
    print(entity_name, entity)

    return render_template(
        f"{entity_name}_detail.html",
        {
            "user": user,
            entity_name[:-1]: item[0]
        })


@login_required
def entity_create_view(user, entity_name):
    if entity_name not in entities:
        return f"<h1>Entité inconnue : {entity_name}</h1>"
    return render_template(
        f"{entity_name}_create.html",
        {"user": user, "error": ""}
    )


@login_required
def entity_create_post_view(user, entity_name, data):
    if entity_name not in entities:
        return f"<h1>Entité inconnue : {entity_name}</h1>"

    model = entities[entity_name]

    try:
        if entity_name == "collaborators":
            instance = model(
                full_name=data["full_name"],
                email=data["email"],
                role=data["role"]
            )
            instance.set_password(data["password"])
        else:
            instance = model(**data)

        instance.validate_all()
        instance.save()

    except Exception as e:
        return render_template(
            f"{entity_name}_create.html",
            {"user": user, "error": f"<h1>Erreur : {str(e)}</h1>"}
        )

    items = model.order_by_field("id")
    return render_template(f"{entity_name}.html", {
        "user": user,
        entity_name: items
    })


routes = {
    "/": home,

}
