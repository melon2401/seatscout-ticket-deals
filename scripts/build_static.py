from __future__ import annotations

import shutil
import sys
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.data import EVENTS, OFFERS, PRICE_HISTORY, ZONES

DIST = ROOT / "dist"
env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape())

DIST.mkdir(exist_ok=True)
html = env.get_template("index.html").render(events=EVENTS, offers=OFFERS, history=PRICE_HISTORY, zones=ZONES, static_prefix=".", api_base=os.getenv("PUBLIC_API_BASE_URL", ""))
(DIST / "index.html").write_text(html, encoding="utf-8")
shutil.copy2(ROOT / "static" / "app.css", DIST / "app.css")
shutil.copy2(ROOT / "static" / "app.js", DIST / "app.js")
print(DIST)

