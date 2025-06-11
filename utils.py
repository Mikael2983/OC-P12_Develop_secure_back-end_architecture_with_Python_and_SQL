import mimetypes
from http.server import BaseHTTPRequestHandler
import urllib.parse
import os
import re

from views import routes, entities, entity_list_view, entity_detail_view, \
    login, entity_create_view, entity_create_post_view


class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/static/"):
            return self.serve_static_file()

        if self.path == "/":
            return self.handle_home()

        if self.path in routes:
            return self.handle_route()

        if match := re.match(r"^/(\w+)/?$", self.path):
            return self.handle_entity_list(match)

        if match := re.match(r"^/(\w+)/(\d+)/?$", self.path):
            return self.handle_entity_detail(match)

        elif match := re.match(r"^/(\w+)/create/?$", self.path):
            return self.handle_entity_create(match)

        return self.send_error(404, "Page non trouvée")

    def do_POST(self):
        if self.path == "/login":
            return self.handle_login()
        elif match := re.match(r"^/(\w+)/create/?$", self.path):
            return self.handle_entity_create_post(match)

        return self.send_error(404, "Page non trouvée")

    def handle_home(self):
        content = routes["/"]()
        self._send_html(content)

    def handle_route(self):
        view = routes[self.path]
        content = view(self.headers) if self._view_accepts_headers(
            view) else view()
        self._send_html(content)

    def handle_entity_list(self, match):
        entity = match.group(1)
        if entity in entities:
            content = entity_list_view(self.headers, entity)
            self._send_html(content)
        else:
            self.send_error(404, f"Entité inconnue : {entity}")

    def handle_entity_detail(self, match):
        entity, pk = match.group(1), int(match.group(2))
        if entity in entities:
            content = entity_detail_view(self.headers, entity, pk)
            self._send_html(content)
        else:
            self.send_error(404, f"Entité inconnue : {entity}")

    def handle_entity_create(self, match):
        entity = match.group(1)
        if entity in entities:
            content = entity_create_view(self.headers, entity)
            self._send_html(content)

    def handle_entity_create_post(self, match):
        entity_name = match.group(1)
        if entity_name not in entities:
            return self.send_error(404, f"Entité inconnue : {entity_name}")

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))

        cleaned_data = {k: v[0] for k, v in form_data.items()}

        try:
            content = entity_create_post_view(self.headers, entity_name,
                                              cleaned_data)
            self._send_html(content)
        except Exception as e:
            self.send_error(400, f"Erreur : {e}")

    def handle_login(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        post_params = urllib.parse.parse_qs(post_data.decode('utf-8'))

        result = login(post_params)
        if isinstance(result, tuple):
            html, session_id = result
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Set-Cookie",
                             f"session_id={session_id}; HttpOnly; Path=/")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self._send_html(result)

    def _send_html(self, content):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _view_accepts_headers(self, view_func):
        return view_func.__code__.co_argcount >= 1

    def serve_static_file(self):
        file_path = os.path.join(os.getcwd(), self.path.lstrip("/"))
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
