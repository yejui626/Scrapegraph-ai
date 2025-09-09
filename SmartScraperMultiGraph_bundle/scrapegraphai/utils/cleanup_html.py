"""
Module for minimizing the code
"""

import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment
from minify_html import minify


def extract_from_script_tags(soup):
    script_content = []

    for script in soup.find_all("script"):
        content = script.string
        if content:
            try:
                json_pattern = r"(?:const|let|var)?\s*\w+\s*=\s*({[\s\S]*?});?$"
                json_matches = re.findall(json_pattern, content)

                for potential_json in json_matches:
                    try:
                        parsed = json.loads(potential_json)
                        if parsed:
                            script_content.append(
                                f"JSON data from script: {json.dumps(parsed, indent=2)}"
                            )
                    except json.JSONDecodeError:
                        pass

                if "window." in content or "document." in content:
                    data_pattern = r"(?:window|document)\.(\w+)\s*=\s*([^;]+);"
                    data_matches = re.findall(data_pattern, content)

                    for var_name, var_value in data_matches:
                        script_content.append(
                            f"Dynamic data - {var_name}: {var_value.strip()}"
                        )
            except Exception:
                if len(content) < 1000:
                    script_content.append(f"Script content: {content.strip()}")

    return "\n\n".join(script_content)


def cleanup_html(html_content: str, base_url: str) -> str:
    """
    Processes HTML content by removing unnecessary tags,
    minifying the HTML, and extracting the title and body content.

    Args:
        html_content (str): The HTML content to be processed.

    Returns:
        str: A string combining the parsed title and the minified body content.
        If no body content is found, it indicates so.

    Example:
        >>> html_content = "<html><head><title>Example</title></head><body><p>Hello World!</p></body></html>"
        >>> remover(html_content)
        'Title: Example, Body: <body><p>Hello World!</p></body>'

    This function is particularly useful for preparing HTML content for
    environments where bandwidth usage needs to be minimized.
    """

    soup = BeautifulSoup(html_content, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text() if title_tag else ""

    script_content = extract_from_script_tags(soup)

    for tag in soup.find_all("style"):
        tag.extract()

    link_urls = [
        urljoin(base_url, link["href"]) for link in soup.find_all("a", href=True)
    ]

    images = soup.find_all("img")
    image_urls = []
    for image in images:
        if "src" in image.attrs:
            if "http" not in image["src"]:
                image_urls.append(urljoin(base_url, image["src"]))
            else:
                image_urls.append(image["src"])

    body_content = soup.find("body")
    if body_content:
        minimized_body = minify(str(body_content))
        return title, minimized_body, link_urls, image_urls, script_content

    else:
        raise ValueError(
            f"""No HTML body content found, please try setting the 'headless'
                         flag to False in the graph configuration. HTML content: {html_content}"""
        )


def minify_html(html):
    """
    minify_html function
    """
    # Combine multiple regex operations into one for better performance
    patterns = [
        (r"<!--.*?-->", "", re.DOTALL),
        (r">\s+<", "><", 0),
        (r"\s+>", ">", 0),
        (r"<\s+", "<", 0),
        (r"\s+", " ", 0),
        (r"\s*=\s*", "=", 0),
    ]

    for pattern, repl, flags in patterns:
        html = re.sub(pattern, repl, html, flags=flags)

    return html.strip()


def reduce_html(html, reduction):
    """
    Reduces the size of the HTML content based on the specified level of reduction.

    Args:
        html (str): The HTML content to reduce.
        reduction (int): The level of reduction to apply to the HTML content.
            0: minification only,
            1: minification and removig unnecessary tags and attributes,
            2: minification, removig unnecessary tags and attributes,
            simplifying text content, removing of the head tag

    Returns:
        str: The reduced HTML content based on the specified reduction level.
    """
    if reduction == 0:
        return minify_html(html)

    soup = BeautifulSoup(html, "html.parser")

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag in soup(["style"]):
        tag.string = ""

    attrs_to_keep = ["class", "id", "href", "src", "type"]
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr not in attrs_to_keep:
                del tag[attr]

    if reduction == 1:
        return minify_html(str(soup))

    for tag in soup(["style"]):
        tag.decompose()

    body = soup.body
    if not body:
        return "No <body> tag found in the HTML"

    for tag in body.find_all(string=True):
        if tag.parent.name not in ["script"]:
            tag.replace_with(re.sub(r"\s+", " ", tag.strip())[:20])

    reduced_html = str(body)

    reduced_html = minify_html(reduced_html)

    return reduced_html
