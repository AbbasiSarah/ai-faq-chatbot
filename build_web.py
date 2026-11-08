"""Builds web/index.html: one self-contained page with the bot code and the FAQ inside it."""
from pathlib import Path
here = Path(__file__).parent
html = (here / "web/template.html").read_text(encoding="utf-8")
html = html.replace("/*BOT*/", (here / "web/bot.js").read_text(encoding="utf-8"))
html = html.replace("/*FAQ*/", (here / "faq.json").read_text(encoding="utf-8"))
(here / "web/index.html").write_text(html, encoding="utf-8")
print("built web/index.html")
