"""Custom template rendering engine supporting tags and inheritance syntax.

Supported features:
- {{ expression }} for inline variable rendering.
- {% if %} / {% else %} / {% endif %} for conditional rendering.
- {% for %} / {% endfor %} for iteration.
- {% include 'file.html' var %} for partial inclusion.
- {% extends 'base.html' %} and {% block name %}...{% endblock %} for inheritance.
"""
import logging
import os
import re
from collections.abc import Iterable
from typing import Any, Dict, List, Optional, Tuple, Union


TemplatePart = Union[str, Any]
Context = Dict[str, Any]
logger = logging.getLogger(__name__)


def safe_eval(expr: str, context: Context) -> Any:
    """Safely evaluates a Python expression using a restricted context.

    Args:
        expr: The string containing the Python expression.
        context: A dictionary providing variables for evaluation.

    Returns:
        The result of the evaluated expression, or an error message.
    """
    try:
        return eval(expr, {"__builtins__": {}}, context)
    except (SyntaxError, NameError, TypeError, ZeroDivisionError,
            AttributeError, KeyError, ValueError) as e:
        logger.exception(e)
        return f"[Error evaluating '{expr}': {e}]"


class TemplateRenderer:
    """Template rendering engine using custom tag syntax."""

    def __init__(self, template_dir: str = "epic_event/templates",
                 tag_dir: str = "epic_event/templates/templates_tag"):
        """Initializes the renderer with template and tag directories.

        Args:
            template_dir: Base directory for main templates.
            tag_dir: Directory for partials or included templates.
        """
        self.template_dir = template_dir
        self.tag_dir = tag_dir

    def read_template(self, template_name: str) -> Optional[str]:
        """Reads the content of a template file by name.

        Args:
            template_name: File name of the template.

        Returns:
            The file content as a string, or None if file is not found.
        """
        path = os.path.join(self.template_dir, template_name)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _split_template(code: str) -> List[str]:
        """Splits a raw template string into parts (text, expressions, tags).

        Args:
            code: The raw template string.

        Returns:
            A list of strings representing segments of the template.
        """
        return [part for part in re.split(r"({{.*?}}|{%.*?%})", code) if
                part.strip()]

    def render_template(self, template_name: str, context: Context) -> str:
        """Renders a template with the provided context.

        Args:
            template_name: Entry-point template filename.
            context: Variables to inject into the template.

        Returns:
            A fully rendered HTML string.
        """
        code = self.read_template(template_name)
        if code is None:
            return f"<h1>Template '{template_name}' not found</h1>"

        parsed = self._split_template(code)
        blocks_context = self._extract_blocks(parsed)

        if "mother_template" in blocks_context:
            base = blocks_context.pop("mother_template")
            base_code = self.read_template(base)
            if base_code is None:
                return f"<h1>Mother template '{base}' not found</h1>"
            parsed = self._split_template(base_code)
            parsed = self._replace_blocks(parsed, blocks_context)

        return ''.join(self._render_blocks(parsed, context))

    def _render_blocks(self, parts: List[TemplatePart], context: Context) -> \
            List[str]:
        """Renders the list of template parts into final output.

        Args:
            parts: A list of raw strings and tag blocks.
            context: Variable context to evaluate expressions.

        Returns:
            List of strings representing rendered output.
        """
        output = []
        i = 0
        while i < len(parts):
            part = parts[i]
            if isinstance(part, str) and part.strip().startswith("{%"):
                tag = part.strip()[2:-2].strip()
                if tag.startswith("if "):
                    block, i = self._handle_if(tag[3:], parts, context, i)
                    output.extend(block)
                elif tag.startswith("for "):
                    block, i = self._handle_for(tag[4:], parts, context, i)
                    output.extend(block)
                elif tag.startswith("include"):
                    output.extend(self._handle_include(tag.split(), context))
                    i += 1
                    continue
                i += 1
            elif isinstance(part, str):
                output.append(re.sub(r"{{\s*(.*?)\s*}}", lambda m: str(
                    safe_eval(m.group(1), context)), part))
                i += 1
            else:
                output.append(str(part))
                i += 1
        return output

    def _handle_if(self, condition: str, parts: List[TemplatePart],
                   context: Context, i: int) -> Tuple[List[str], int]:
        """Processes an {% if %}...{% else %}...{% endif %} block.

        Args:
            condition: Condition expression for the if.
            parts: The full list of template parts.
            context: Variable dictionary.
            i: Current index in parts.

        Returns:
            A tuple of rendered content and updated index.
        """
        true_block, false_block = [], []
        depth = 1
        i += 1
        while i < len(parts):
            part = parts[i]
            if isinstance(part, str) and part.strip().startswith("{%"):
                tag_inner = part.strip()[2:-2].strip()
                if tag_inner.startswith("if "):
                    depth += 1
                elif tag_inner == "endif":
                    depth -= 1
                    if depth == 0:
                        break
                elif tag_inner == "else" and depth == 1:
                    i += 1
                    while i < len(parts) and parts[i].strip() != "{% endif %}":
                        false_block.append(parts[i])
                        i += 1
                    break
            true_block.append(part)
            i += 1

        block = true_block if safe_eval(condition, context) else false_block
        return self._render_blocks(block, context), i

    def _handle_for(self, condition: str, parts: List[TemplatePart],
                    context: Context, i: int) -> Tuple[List[str], int]:
        """Processes a {% for %}...{% endfor %} block.

        Args:
            condition: The loop declaration (e.g., "item in items").
            parts: Template parts.
            context: Context for rendering.
            i: Index in parts.

        Returns:
            Tuple of rendered loop content and new index.
        """
        loop_block = []
        depth = 1
        i += 1
        while i < len(parts):
            part = parts[i]
            if isinstance(part, str) and part.strip().startswith("{%"):
                tag_inner = part.strip()[2:-2].strip()
                if tag_inner.startswith("for "):
                    depth += 1
                elif tag_inner == "endfor":
                    depth -= 1
                    if depth == 0:
                        break
            loop_block.append(part)
            i += 1

        match = re.match(r"(\w+)\s+in\s+(.+)", condition)
        if not match:
            return [f"[Error: malformed for loop: '{condition}']"], i

        var_name, iterable_expr = match.groups()
        iterable = safe_eval(iterable_expr, context)

        if not isinstance(iterable, Iterable) or isinstance(iterable,
                                                            (str, bytes,
                                                             dict)):
            return [f"[Error: '{iterable_expr}' is not iterable]"], i

        result = []
        for item in iterable:
            new_ctx = context.copy()
            new_ctx[var_name] = item
            result.extend(self._render_blocks(loop_block, new_ctx))
        return result, i

    def _handle_include(self, tag_parts: List[str], context: Context) -> \
            List[str]:
        """Handles {% include 'template.html' var %} directives.

        Args:
            tag_parts: List of strings from the include tag.
            context: Current rendering context.

        Returns:
            Rendered content of the included template.
        """
        if len(tag_parts) < 2:
            return ["[Error: malformed include tag]"]

        template_name = tag_parts[1].strip("'\"")
        sub_context = context.copy()

        if len(tag_parts) >= 3:
            var_expr = tag_parts[2]
            var_value = safe_eval(var_expr, context)

            # Add evaluated variable to subcontext
            sub_context[var_expr] = (
                list(var_value)
                if isinstance(var_value, Iterable) and not isinstance(
                    var_value, (str, bytes, dict))
                else var_value
            )
            sub_context["with_sorting"] = False

        if len(tag_parts) == 4:
            # Optional boolean for display sorting menu on template
            sub_context["with_sorting"] = True

        tag_path = os.path.join(self.tag_dir, template_name)
        if not os.path.exists(tag_path):
            return [f"<h1>Template '{template_name}' not found</h1>"]

        with open(tag_path, "r", encoding="utf-8") as f:
            tag_code = f.read()

        return self._render_blocks(self._split_template(tag_code), sub_context)

    @staticmethod
    def _extract_blocks(parsed: List[str]) -> Context:
        """Extracts {% block %} definitions and base inheritance.

        Args:
            parsed: Parsed parts of a template.

        Returns:
            Context dictionary with blocks and optional mother_template.
        """
        context: Context = {}
        if not parsed or not parsed[0].startswith("{% extends"):
            return context

        base_html = re.split(r"['\"]", parsed[0])
        context["mother_template"] = base_html[1]
        block_content, write, block_name = [], False, None

        for part in parsed:
            if "{% block" in part:
                block_name = part.split()[2]
                block_content, write = [], True
            elif "endblock" in part:
                if block_name:
                    context[block_name] = block_content[:]
                    write = False
            elif write:
                block_content.append(part)
        return context

    @staticmethod
    def _replace_blocks(parsed: List[str], context: Context) -> List[str]:
        """Replaces block placeholders in a base template with child overrides.

        Args:
            parsed: Parsed parts from base template.
            context: Block content from child template.

        Returns:
            A list of parts with replaced blocks.
        """
        result = []
        i = 0
        while i < len(parsed):
            part = parsed[i]
            if "{% block" in part:
                block_name = part.split()[2]
                i += 1
                while i < len(parsed) and "endblock" not in parsed[i]:
                    i += 1
                i += 1  # skip endblock
                if block_name in context:
                    result.extend(context[block_name])
                continue
            result.append(part)
            i += 1
        return result


def make_sort_url(field: str, current_sort: str, current_order: str) -> str:
    """
    assembles the fields and the order to form the query string
    Args:
        field: Orm field use to sort
        current_sort: Orm currently used sorting field
        current_order : sort order currently used
    returns :
        a string use to make query string in links
    """
    if field == current_sort and current_order == "asc":
        order = "desc"
    else:
        order = "asc"

    base = f"?sort={field}&order={order}"

    return base


def make_query_string(query_params):
    """
    Generates a query string dictionary for multi-field sorting.

    Args:
        query_params (Optional[Dict[str, List[str]]]):
            HTTP GET query parameters for sorting
    Returns:
        Dict[str, str]:
            A dictionary where each key is a field name on which one can sort,
            and the associated value is a query string formed to sort
            according to this field.
    """
    sort_field = query_params.get("sort", ["id"])[0]
    order = query_params.get("order", ["asc"])[0]

    return {
        "email": make_sort_url("email", sort_field, order),
        "id": make_sort_url("id", sort_field, order),
        "client": make_sort_url("contract.client.company_name", sort_field, order),
        "total_amount": make_sort_url("total_amount", sort_field, order),
        "amount_due": make_sort_url("amount_due", sort_field, order),
        "created_date": make_sort_url("created_date", sort_field, order),
        "signed": make_sort_url("signed", sort_field, order),
        "event": make_sort_url("event.title", sort_field, order),
        "full_name": make_sort_url("full_name", sort_field, order),
        "role": make_sort_url("role", sort_field, order),
        "company_name": make_sort_url("company_name", sort_field, order),
        "last_contact": make_sort_url("last_contact_date", sort_field, order),
        "commercial": make_sort_url("commercial.full_name", sort_field, order),
        "title": make_sort_url("title", sort_field, order),
        "support": make_sort_url("support.full_name", sort_field, order),
        "start_date": make_sort_url("start_date", sort_field, order),
        "end_date": make_sort_url("end_date", sort_field, order),
        "location": make_sort_url("location", sort_field, order),
        "participants": make_sort_url("participants", sort_field, order),
    }
