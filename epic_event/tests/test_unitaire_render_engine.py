import pytest

from epic_event.render_engine import TemplateRenderer, safe_eval


def test_safe_eval_valid_expression():
    context = {"a": 2, "b": 3}
    assert safe_eval("a + b", context) == 5


def test_safe_eval_invalid_expression():
    context = {"a": 2}
    result = safe_eval("a + unknown_var", context)
    assert "Error evaluating" in result


def test_split_template():
    renderer = TemplateRenderer()
    code = "Hello {{ name }} {% if condition %}Yes{% endif %}"
    parts = renderer._split_template(code)
    assert parts == [
        "Hello ", "{{ name }}", "{% if condition %}", "Yes", "{% endif %}"
    ]


def test_handle_include_invalid():
    renderer = TemplateRenderer()
    result = renderer._handle_include(["include"], {})
    assert result == ["[Error: malformed include tag]"]


def test_handle_for_invalid_loop():
    renderer = TemplateRenderer()
    parts = ["{% for x in %}", "Item", "{% endfor %}"]
    output, _ = renderer._handle_for("x in", parts, {}, 0)
    assert "malformed for loop" in output[0]


def test_handle_for_non_iterable():
    renderer = TemplateRenderer()
    parts = ["{% for x in y %}", "Item", "{% endfor %}"]
    context = {"y": 123}
    output, _ = renderer._handle_for("x in y", parts, context, 0)
    assert "not iterable" in output[0]
