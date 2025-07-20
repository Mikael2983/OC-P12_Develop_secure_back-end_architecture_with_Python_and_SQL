"""
router.py - Custom HTTP request handler and router.

This module defines a custom handler class (`MyHandler`) based on Python's
`BaseHTTPRequestHandler`. It handles routing of HTTP GET and POST requests
to various view functions of the application.

Main Responsibilities:
- Dispatches requests to entity-specific CRUD views (list, detail, create,
    update, delete).
- Manages authentication routes (login, logout).
- Serves static files from the `/static/` directory.
- Handles collaborator password management and client contact marking.
- Manages session-based actions like archive display toggling.

Usage:
This module is used as the HTTP entry point of the application.
It connects HTTP requests to the relevant business logic in `views`.

"""
import logging
import mimetypes
import os
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from epic_event.models import SESSION_CONTEXT
from epic_event.settings import entities
from epic_event.views import (client_contact_view, collaborator_password_view,
                              entity_create_post_view, entity_create_view,
                              entity_delete_view, entity_detail_view,
                              entity_list_view, entity_update_post_view,
                              entity_update_view, login, logout, routes,
                              user_password_post_view)

logger = logging.getLogger(__name__)


class MyHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP handler for routing and processing application requests.
    Handles CRUD operations, authentication, and static files.
    """
    session = None
    database = None

    def log_message(self, format, *args):
        pass

    def log_request(self, code='-', size='-'):
        pass

    def parsed_url(self):
        """
            Analyze the request URL.

            Returns:
                tuple: The path of the URL and the query parameters as a dictionary.
            """
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def dispatch_route(self, method: str):
        """
        Dispatch HTTP request to the appropriate handler based on method and URL path.

        Args:
            method (str): HTTP method of the request (e.g., "GET", "POST").

        Returns:
            Any: The result of the matched handler function (typically an HTTP response).

        Behavior:
            - Routes GET requests for:
                - Home page
                - Logout
                - Entity list, detail, create form
                - Entity actions: update, delete, password
            - Routes POST requests for:
                - Login
                - Archive display toggle
                - Entity creation, update, delete
                - Collaborator password update
                - Client contact marking

            Returns a 403 error for direct GET access to /login.
            Returns a 404 error if no matching route is found.
        """
        path, query_params = self.parsed_url()
        segments = path.strip("/").split("/")

        if method == "GET":
            if path == "/":
                return self.handle_home()

            if path == "/logout":
                return self.handle_logout()

            if path == "/login":
                return self.send_error(403, "Accès direct interdit")

            if len(segments) == 1:
                entity = segments[0]
                return self.handle_entity_list(entity, query_params)

            if len(segments) == 2 and segments[1] == "create":
                return self.handle_entity_create(segments[0], query_params)

            if len(segments) == 2:
                entity, pk = segments
                return self.handle_entity_detail(entity, int(pk))

            if len(segments) == 3:
                entity, pk, action = segments
                if action == "delete":
                    return self.handle_entity_delete(entity, int(pk))
                if action == "update":
                    return self.handle_entity_update(entity, int(pk))
                if action == "password":
                    return self.handle_collaborator_password_get(int(pk))

        elif method == "POST":

            if path == "/login":
                return self.handle_login()

            if path == "/toggle_archive_display":
                return self.handle_toggle_archive_display()

            if len(segments) == 2 and segments[1] == "create":
                return self.handle_entity_create_post(segments[0])

            if len(segments) == 3:
                entity, pk, action = segments
                if action == "delete":
                    return self.handle_entity_delete_post(entity, int(pk))
                if action == "update":
                    return self.handle_entity_update_post(entity, int(pk))
                if action == "password":
                    return self.handle_collaborator_password_post(int(pk))

            if len(segments) == 3 and segments[0] == "clients" and segments[
                2] == "contact":
                return self.handle_client_contact(int(segments[1]))

            if path == "toggle_archive_display":
                return self.handle_toggle_archive_display()

        return self.send_error(404, "Page non trouvée")

    def do_GET(self):
        if self.path.startswith("/static/"):
            return self.serve_static_file()
        return self.dispatch_route("GET")

    def do_POST(self):
        return self.dispatch_route("POST")

    def _send_html(self, content, headers=None):
        """
            Sends an HTTP response with HTML content.

            Args:
                content (str): The HTML content to send.
                headers (dict, optional): Additional HTTP headers to be added.
            """
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        if headers:
            for name, value in headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _redirect(self, path="/", headers=None):
        """
            Sends an HTTP redirect (302) response to the specified URL.

            Args:
                path (str, optional): Destination path or URL. Default "/".
                headers (dict, optional): Additional HTTP headers to be added.
            """
        self.send_response(302)
        self.send_header("Location", path)
        if headers:
            for name, value in headers.items():
                self.send_header(name, value)
        self.end_headers()

    def serve_static_file(self):

        """
        Serves a static file from the 'static' directory.

        Sends the content of the requested file with the appropriate MIME type.
        If the file is missing, returns a 404 error.

        """

        static_dir = os.path.join(os.path.dirname(__file__), "static")
        relative_path = self.path[
                        len("/static/"):]
        file_path = os.path.join(static_dir, relative_path)
        if os.path.isfile(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"Fichier statique non trouvé : {self.path}")

    def handle_home(self):
        """
        Handles the request for the home page.

        Retrieve the content via the function associated with the route "/" and send it in HTML.
        """
        content = routes["/"]()
        self._send_html(content)

    def handle_login(self):
        """
        Processes the submission of the login form.

        Reads the POST data, tries to authenticate the user,
        then redirects to the collaborators page if success,
        or returns the login page with an error message otherwise.
        """
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        post_params = urllib.parse.parse_qs(post_data.decode('utf-8'))

        result = login(self.session, post_params)

        if result["success"]:
            session_id = result["session_id"]
            self._redirect(
                path="/collaborators",
                headers={"Set-Cookie": f"session_id={session_id};"
                                       f" HttpOnly; Path=/"}
            )
        else:
            self._send_html(result["html"])

    def handle_logout(self):
        """
        Handles user logout.

        Calls the logout function to clear the session, then redirects
        to the home page while deleting the session cookie.
        """
        logout(headers=self.headers)
        self._redirect(headers={
            "Set-Cookie": "session_id=deleted; Path=/; Max-Age=0"
        })

    def handle_collaborator_password_get(self, pk):
        """
        Handles GET request to display the password change form for a collaborator.

        Args:
            pk (int): The primary key (ID) of the collaborator.
        """
        content = collaborator_password_view(pk,
                                             entity_name="collaborators",
                                             session=self.session,
                                             headers=self.headers)
        self._send_html(content)

    def handle_entity_list(self, entity, query_params):
        """
        Handles the request to list entities.

        Args:
            entity (str): Name of the entity to list.
            query_params (dict): Query parameters from the URL.

        Sends the rendered HTML list if the entity is known,
        otherwise returns a 404 error.
        """
        if entity in entities:

            content = entity_list_view(query_params,
                                       session=self.session,
                                       entity_name=entity,
                                       headers=self.headers
                                       )
            self._send_html(content)
        else:
            self.send_error(404, f"Entité inconnue : {entity}")

    def handle_entity_detail(self, entity, pk):
        """
        Handles the request to display details of a specific entity item.

        Args:
            entity (str): Name of the entity.
            pk (int): Primary key (ID) of the entity item.

        Sends the rendered HTML detail view if the entity is known,
        otherwise returns a 404 error.
        """
        if entity in entities:

            content = entity_detail_view(pk,
                                         session=self.session,
                                         entity_name=entity,
                                         headers=self.headers)
            self._send_html(content)
        else:
            self.send_error(404, f"Entité inconnue : {entity}")

    def handle_entity_create(self, entity, query_params):
        """
        Handles the request to display the creation form for a new entity.

        Args:
            entity (str): Name of the entity to create.
            query_params (dict): Query parameters from the URL.

        Sends the rendered HTML form for entity creation if the entity is known.
        """
        if entity in entities:

            content = entity_create_view(query_params,
                                         session=self.session,
                                         entity_name=entity,
                                         headers=self.headers,
                                         )
            self._send_html(content)

    def handle_entity_delete(self, entity, pk):
        """
        Handles the deletion of a specific entity item.

        Args:
            entity (str): Name of the entity.
            pk (int): Primary key (ID) of the entity item.

        Redirects to the entity list page upon successful deletion.
        Returns a 404 error if the entity is unknown.
        """
        if entity in entities:

            content = entity_delete_view(pk,
                                         session=self.session,
                                         entity_name=entity,
                                         headers=self.headers)
            if content:
                self._redirect(path=f"/{entity}")
        else:
            self.send_error(404, f"Entité inconnue : {entity}")

    def handle_collaborator_password_post(self, pk):
        """
        Handles POST request to update a collaborator's password.

        Reads and parses form data from the request, processes the password
        update via the corresponding view, and sends back the resulting HTML.

        Args:
            pk (int): Primary key (ID) of the collaborator.
        """
        entity = "collaborators"
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        form_data = urllib.parse.parse_qs(post_data.decode("utf-8"))
        cleaned_data = {k: v[0] for k, v in form_data.items()}
        content = user_password_post_view(pk,
                                          cleaned_data,
                                          session=self.session,
                                          entity_name=entity,
                                          headers=self.headers)
        self._send_html(content)

    def handle_entity_create_post(self, entity):
        """
        Handles POST request to create a new entity.

        Args:
            entity (str): Name of the entity to create.

        Parses form data from the request and processes creation via the
        corresponding view. Redirects to the entity list on success,
        otherwise sends back the HTML with errors.

        """
        if entity not in entities:
            self.send_error(
                404,
                f"Entité inconnue : {entity}")

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))

        cleaned_data = {k: v[0] for k, v in form_data.items()}

        result = entity_create_post_view(cleaned_data,
                                         session=self.session,
                                         entity_name=entity,
                                         headers=self.headers)
        if result is True:
            self._redirect(path=f"/{entity}")
        else:
            self._send_html(result)

    def handle_client_contact(self, client_id):
        """
        Handles client contact updates.

        Args:
            client_id (int): The ID of the client.

        Calls the client contact view and redirects to the client detail page
        on success; otherwise, sends back the HTML response with errors.
        """
        result = client_contact_view(client_id,
                                     session=self.session,
                                     entity_name="clients",
                                     headers=self.headers)

        if result is True:
            self._redirect(f"/clients/{client_id}")

        else:
            self._send_html(result)

    def handle_entity_update(self, entity_name, pk):
        """
        Handles the request to display the update form for a specific entity item.

        Args:
            entity_name (str): Name of the entity.
            pk (int): Primary key (ID) of the entity item.

        Sends the rendered HTML update form if the entity is known,
        otherwise returns a 404 error.
        """
        if entity_name in entities:
            content = entity_update_view(pk,
                                         session=self.session,
                                         entity_name=entity_name,
                                         headers=self.headers)
            self._send_html(content)
        else:
            self.send_error(404, f"Entité inconnue : {entity_name}")

    def handle_entity_update_post(self, entity_name, pk):
        """
        Handles POST request to update a specific entity item.

        Args:
            entity_name (str): Name of the entity.
            pk (int): Primary key (ID) of the entity item.

        Parses form data and processes the update via the corresponding view.
        Redirects to the entity detail page on success,
        otherwise sends back the HTML response with errors.
        """
        if entity_name not in entities:
            self.send_error(
                404,
                f"Entité inconnue : {entity_name}")

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))

        cleaned_data = {k: v[0] for k, v in form_data.items()}

        result = entity_update_post_view(pk,
                                         cleaned_data,
                                         session=self.session,
                                         entity_name=entity_name,
                                         headers=self.headers)
        if result is True:
            self._redirect(path=f"/{entity_name}/{pk}")
        else:
            self._send_html(result)

    def handle_toggle_archive_display(self):
        """
        Toggles the display of archived items for the current user session.

        Reads the 'show_archived' parameter from the POST request body,
        updates the user's session setting accordingly,
        then redirects back to the referring page.
        """
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()
        params = urllib.parse.parse_qs(body)
        cookie = self.headers.get("Cookie", "")
        match = re.search(r"session_id=([a-f0-9\-]+)", cookie)
        session_id = match.group(1)

        SESSION_CONTEXT[session_id]["Display_archive"] = \
            params.get("show_archived", ["off"])[
                0] == "on"
        referer = self.headers.get('Referer', '/')
        self.send_response(303)
        self.send_header('Location', referer)
        self.end_headers()
