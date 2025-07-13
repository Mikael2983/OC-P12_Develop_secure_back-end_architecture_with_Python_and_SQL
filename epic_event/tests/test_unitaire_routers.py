import io
import pytest
from unittest.mock import Mock
from router import MyHandler


def fake_socket():
    mock = Mock()
    mock.makefile.return_value = io.BytesIO()
    return mock


def make_handler(path="/", method="GET", headers=None):
    headers = headers or {}
    handler = MyHandler(fake_socket(), ("127.0.0.1", 0), None)
    handler.path = path
    handler.headers = headers
    handler.rfile = io.BytesIO()
    handler.wfile = io.BytesIO()
    return handler


def test_redirect_sets_location_header():
    handler = make_handler()
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()

    handler._redirect("/test")

    handler.send_response.assert_called_once_with(302)
    handler.send_header.assert_any_call("Location", "/test")


def test_send_html_sets_content_type():
    handler = make_handler()
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()

    handler._send_html("<h1>Hello</h1>")

    handler.send_response.assert_called_once_with(200)
    handler.send_header.assert_any_call("Content-type", "text/html; charset=utf-8")