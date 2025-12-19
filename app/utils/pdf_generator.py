import os
import uuid
import asyncio
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright


TEMPLATE_DIR = "app/templates"
OUTPUT_DIR = "generated_reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)


env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    auto_reload=True
)
env.cache = {}


def render_html(template_name: str, data: dict) -> str:
    print("Rendering HTML with template:", template_name)
    template = env.get_template(template_name)
    return template.render(**data)


def _generate_pdf_sync(html_content: str) -> str:
    pdf_filename = f"{uuid.uuid4()}.pdf"
    pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)

    print("Generating PDF:", pdf_filename)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()

        page.set_content(html_content, wait_until="networkidle")

        page.pdf(
            path=pdf_path,
            format="A4",
            margin={
                "top": "20mm",
                "bottom": "20mm",
                "left": "10mm",
                "right": "10mm"
            },
            print_background=True
        )

        browser.close()

    return pdf_path


async def generate_pdf_from_html(html_content: str) -> str:
    return await asyncio.to_thread(_generate_pdf_sync, html_content)
