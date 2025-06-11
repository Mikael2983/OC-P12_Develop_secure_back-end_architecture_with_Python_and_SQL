import os
import re


def safe_eval(expr, context):
    try:
        return eval(expr, {}, context)
    except Exception as e:
        return f"[Error: {e}]"


def render_blocks(template_parts, context):
    output = []
    i = 0
    while i < len(template_parts):
        part = template_parts[i]
        if isinstance(part, str) and part.strip().startswith('{%') and part.strip().endswith('%}'):
            tag = part.strip()[2:-2].strip()

            if tag.startswith('if ') or tag.startswith('for '):
                tag_type, tag_expr = tag.split(None, 1)
                inner_block = []
                else_block = []
                i += 1
                depth = 1

                while i < len(template_parts):
                    inner_part = template_parts[i]
                    if isinstance(inner_part, str) and inner_part.strip().startswith('{%') and inner_part.strip().endswith('%}'):
                        inner_tag = inner_part.strip()[2:-2].strip()
                        if inner_tag.startswith('if ') or inner_tag.startswith('for '):
                            depth += 1
                        elif inner_tag in ['endif', 'endfor']:
                            depth -= 1
                            if depth == 0:
                                break
                        elif inner_tag == 'else' and depth == 1:
                            i += 1
                            while i < len(template_parts):
                                alt_part = template_parts[i]
                                if isinstance(alt_part, str) and alt_part.strip() == '{% endif %}':
                                    break
                                else_block.append(alt_part)
                                i += 1
                            break
                    inner_block.append(inner_part)
                    i += 1

                if tag_type == 'if':
                    if safe_eval(tag_expr, context):
                        output.extend(render_blocks(inner_block, context))
                    else:
                        output.extend(render_blocks(else_block, context))
                elif tag_type == 'for':
                    match = re.match(r'(\w+)\s+in\s+(.+)', tag_expr)
                    if match:
                        loop_var, iterable_expr = match.groups()
                        iterable = safe_eval(iterable_expr, context)
                        if isinstance(iterable, list):
                            for item in iterable:
                                new_context = context.copy()
                                new_context[loop_var] = item
                                output.extend(render_blocks(inner_block, new_context))
                        else:
                            output.append(f"[Error: {iterable_expr} is not iterable]")
                    else:
                        output.append(f"[Error: malformed for loop: '{tag_expr}']")
                i += 1
                continue
        elif isinstance(part, str):
            rendered = re.sub(r"{{\s*(.*?)\s*}}", lambda m: str(safe_eval(m.group(1), context)), part)
            output.append(rendered)
        else:
            output.append(str(part))
        i += 1
    return output


def read_template(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def split_template(template_code):
    return [part for part in re.split(r"({{.*?}}|{%.*?%})", template_code) if part.strip()]


def extract_blocks(parsed):
    context = {}
    if not parsed or not parsed[0].startswith("{% extends"):
        return context

    base_html = re.split(r"['\"]", parsed[0])
    context['mother_template'] = base_html[1]

    unwanted_data = ['{%', 'block', '%}']
    block_content = []
    write = False
    block_name = None

    for i, part in enumerate(parsed):
        if write:
            block_content.append(part)

        if "{% block" in part:
            block_split = part.split()
            block_name = next((p for p in block_split if p not in unwanted_data), None)
            block_content = []
            write = True

        elif "endblock" in part and block_name:
            write = False
            if block_content:
                block_content.pop()  # retire endblock
            context[block_name] = block_content.copy()
            block_content = []

    return context


def replace_blocks(parsed, context, context_keys):
    for block_name in context_keys:
        reconstituted_template = []
        i = 0
        while i < len(parsed):
            part = parsed[i]
            if "{% block" in part and block_name in part:
                # Sauter les parties du parent
                i += 1
                while i < len(parsed) and "endblock" not in parsed[i]:
                    i += 1
                i += 1  # skip endblock
                reconstituted_template.extend(context[block_name])
                continue
            reconstituted_template.append(part)
            i += 1
        parsed = reconstituted_template
    return parsed


def render_template(template_name, context):
    template_path = os.path.join("templates", template_name)
    template_code = read_template(template_path)
    if template_code is None:
        return "<h1>Template not found</h1>"

    parsed = split_template(template_code)
    blocks_context = extract_blocks(parsed)

    if 'mother_template' in blocks_context:
        context_keys = list(blocks_context.keys())
        context_keys.remove('mother_template')

        parent_path = os.path.join("templates", blocks_context['mother_template'])
        parent_code = read_template(parent_path)
        if parent_code is None:
            return "<h1>Mother template not found</h1>"

        parsed = split_template(parent_code)
        parsed = replace_blocks(parsed, blocks_context, context_keys)

    return ''.join(render_blocks(parsed, context))
