"""Arma "Para tecnicos/Matcheador.html": un solo archivo con todo adentro, para pasar a los técnicos.
Correr después de cambiar matcheador.html o matcher.js:  python codigo/empaquetar.py"""
import html as h
import re
from pathlib import Path

BASE = Path(__file__).parent
RAIZ = BASE.parent
html = (BASE / "matcheador.html").read_text(encoding="utf-8")


def incrustar(m):
    codigo = (BASE / m.group(1)).read_text(encoding="utf-8").replace("</script", "<\\/script")
    return f"<script>\n{codigo}\n</script>"




def novedades():
    """Panel de Novedades desde CHANGELOG.md: cada '## X.Y.Z — fecha' es una versión, cada '- ' un cambio."""
    partes, version = [], None
    for linea in (RAIZ / "CHANGELOG.md").read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            version = version or linea[3:].split()[0]
            partes.append(("</ul>" if len(partes) else "") + f"<h3>{h.escape(linea[3:])}</h3><ul>")
        elif linea.startswith("- ") and partes:
            partes.append(f"<li>{h.escape(linea[2:])}</li>")
    assert version, "CHANGELOG.md no tiene ninguna versión '## X.Y.Z'"
    return version, f'<details class="novedades"><summary>v{version} · Novedades</summary><div>{"".join(partes)}</ul></div></details>'


version, panel = novedades()
assert "<!--NOVEDADES-->" in html, "Falta <!--NOVEDADES--> en matcheador.html"
html = html.replace("<!--NOVEDADES-->", panel)
html, n = re.subn(r'<script src="([^"]+)"></script>', incrustar, html)
assert n == 2, f"Esperaba 2 scripts locales (SheetJS y matcher.js), encontré {n}"
salida = RAIZ / "Para tecnicos" / "Matcheador.html"
salida.parent.mkdir(exist_ok=True)
salida.write_text(html, encoding="utf-8")
print(f"Listo v{version} -> {salida} ({salida.stat().st_size // 1024} KB)")
