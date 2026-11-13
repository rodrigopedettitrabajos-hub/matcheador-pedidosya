"""Arma "Para tecnicos/Matcheador.html": un solo archivo con todo adentro, para pasar a los técnicos.
Correr después de cambiar matcheador.html o matcher.js:  python empaquetar.py"""
import re
from pathlib import Path

BASE = Path(__file__).parent
html = (BASE / "matcheador.html").read_text(encoding="utf-8")


def incrustar(m):
    codigo = (BASE / m.group(1)).read_text(encoding="utf-8").replace("</script", "<\\/script")
    return f"<script>\n{codigo}\n</script>"


html, n = re.subn(r'<script src="([^"]+)"></script>', incrustar, html)
assert n == 2, f"Esperaba 2 scripts locales (SheetJS y matcher.js), encontré {n}"
salida = BASE / "Para tecnicos" / "Matcheador.html"
salida.parent.mkdir(exist_ok=True)
salida.write_text(html, encoding="utf-8")
print(f"Listo -> {salida} ({salida.stat().st_size // 1024} KB)")
