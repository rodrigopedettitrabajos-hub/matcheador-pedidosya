"""Rellena los SKU de las planillas de PedidosYa con los códigos del listado HIOPOS.

Uso: python codigo/matcheador.py  (o doble clic en ejecutar.bat)
Lee "planillas/Recibidos PYA/productos-*.xlsx" y "opcionales-*.xlsx", el primer archivo de "planillas/Listado HIOPOS"
y escribe las planillas completas en "planillas/Salida/".
Celdas amarillas = revisar (match dudoso o con varios candidatos, ver comentario). Rojas = sin match.
"""
import re, sys, unicodedata
from difflib import SequenceMatcher
from pathlib import Path
import openpyxl
from openpyxl.comments import Comment
from openpyxl.styles import PatternFill

BASE = Path(__file__).parent.parent / "planillas"  # Recibidos PYA, Listado HIOPOS, Salida, Enviados PYA
AMARILLO = PatternFill("solid", fgColor="FFFF00")
ROJO = PatternFill("solid", fgColor="FF8080")
OK_MIN, REVISAR_MIN, EMPATE, BONO_PEDIDOYA = 0.9, 0.6, 0.03, 0.1
LEYENDA = "Se recomienda crearlo en HIOPOS e importar las planillas nuevamente."

# Variantes de escritura que se ven en PedidosYa / HIOPOS
SINONIMOS = {"BROASTER": "BROSTER", "MUZLO": "MUSLO", "MARIANADA": "MARINADA", "MOZTAZA": "MOSTAZA",
             "MOZTASA": "MOSTAZA", "CHEDAR": "CHEDDAR", "GR": "G", "REFRESCO": "COCA", "REFRESCOS": "COCA",
             "COCAS": "COCA", "COKBO": "COMBO", "DOS": "2", "TRES": "3"}
RELLENO = {"MAS", "Y", "CON", "DE", "LA", "EL", "O", "X", "PARA", "COLA", "ORIGINAL", "ML", "PERSONAS", "PERSONS"}


def normalizar(texto):
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode().upper()
    # Medidas aparte, como "=600": HIOPOS casi nunca las tiene, pero si las dos tienen y no coinciden, no es el mismo
    medidas = ["=" + m.replace(",", ".") for m in re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:G|GR|GRS|ML|CC|L|LT|LTS)\b", t)]
    t = re.sub(r"\d+([.,]\d+)?\s*(G|GR|GRS|ML|CC|L|LT|LTS)\b", " ", t)
    t = re.sub(r"(\d)([A-Z])|([A-Z])(\d)", r"\1\3 \2\4", t)  # X6 -> X 6
    palabras = [SINONIMOS.get(p, p) for p in re.findall(r"[A-Z0-9]+", t)]
    return list(dict.fromkeys([p for p in palabras if p not in RELLENO] + medidas))


def iguales(a, b):
    return a == b if a.isdigit() or b.isdigit() else SequenceMatcher(None, a, b).ratio() >= 0.8  # tolera faltas de ortografía


def similitud(a, b):
    """Palabras en común (con tolerancia a errores) sobre el total: 1.0 = mismas palabras. Medidas distintas = 0."""
    ma, mb = {p for p in a if p[0] == "="}, {p for p in b if p[0] == "="}
    if ma and mb and not ma & mb:
        return 0
    a, b = [p for p in a if p[0] != "="], [p for p in b if p[0] != "="]
    libres, comunes = list(b), 0
    for p in a:
        par = next((q for q in libres if iguales(p, q)), None)
        if par:
            libres.remove(par)
            comunes += 1
    return 2 * comunes / (len(a) + len(b)) if a or b else 0


def leer_hiopos(ruta):
    with open(ruta, "rb") as f:  # el .xls de HIOPOS es en realidad un .xlsx; abrir por stream evita el chequeo de extensión
        filas = list(openpyxl.load_workbook(f, data_only=True).worksheets[0].iter_rows(values_only=True))
    cab = [str(c).strip() for c in filas[0]]
    i_cod, i_nom, i_fam = cab.index("Cód. PedidosYa"), cab.index("Artículo"), cab.index("Familia")
    return [{"cod": str(r[i_cod]).strip(), "nombre": str(r[i_nom]).strip(), "familia": r[i_fam] or "",
             "tokens": normalizar(r[i_nom])} for r in filas[1:] if r[i_cod]]


def num_cod(cod):
    """Número del código para desempatar, como parseInt de matcher.js: '12A-3' -> 12."""
    m = re.match(r"\d+", cod)
    return int(m[0]) if m else 0


def buscar(nombre, hiopos):
    """Devuelve (codigo o None, estado 'ok'|'revisar'|'sin match', texto de candidatos)."""
    tok = normalizar(nombre)
    # Los artículos armados para la integración viven en la familia PEDIDOYA: el bonus ordena y desempata,
    # pero el estado se decide con el parecido sin bonus. A igualdad, el código más bajo.
    filas = [(h, s, s + (BONO_PEDIDOYA if h["familia"] == "PEDIDOYA" else 0)) for h in hiopos for s in [similitud(tok, h["tokens"])]]
    filas.sort(key=lambda f: (-f[2], num_cod(f[0]["cod"])))
    candidatos = "\n".join(f"{h['cod']} {h['nombre']} [{h['familia']}] {p:.0%}" for h, _, p in filas[:3])
    mejor, parecido, puntaje = filas[0]
    otro = next((f for f in filas if f[0]["cod"] != mejor["cod"]), None)  # un código repetido no tapa un empate
    empatado = otro is not None and puntaje - otro[2] <= EMPATE
    if parecido >= OK_MIN and not empatado:
        return mejor["cod"], "ok", candidatos
    if parecido >= REVISAR_MIN:
        return mejor["cod"], "revisar", candidatos
    return None, "sin match", candidatos


def completar(celda, nombre, hiopos, codigos, cache):
    """Rellena una celda SKU. Si ya trae un código válido de HIOPOS lo respeta."""
    actual = str(celda.value).strip() if celda.value else ""
    if actual in codigos:
        return "ok"
    if nombre not in cache:
        cache[nombre] = buscar(nombre, hiopos)
    cod, estado, candidatos = cache[nombre]
    celda.value = cod
    if estado != "ok":
        celda.fill = AMARILLO if cod else ROJO
        previo = f"Tenía '{actual}' (no existe en HIOPOS).\n" if actual else ""
        if not cod:
            previo += LEYENDA + "\n"
        celda.comment = Comment(f"{previo}Candidatos:\n{candidatos}", "matcheador", width=320, height=110)
    return estado


def columnas(ws):
    return {str(c.value).strip(): c.column for c in ws[1] if c.value}


def procesar(hiopos, ruta_prod, ruta_opc, salida):
    codigos = {h["cod"] for h in hiopos}
    cache, resumen = {}, {}

    wb = openpyxl.load_workbook(ruta_prod)
    ws = wb.worksheets[0]
    c = columnas(ws)
    sku_por_id = {}
    for fila in range(2, ws.max_row + 1):
        nombre = ws.cell(fila, c["Nombre"]).value
        if not nombre:
            continue
        celda = ws.cell(fila, c["SKU"])
        estado = completar(celda, nombre, hiopos, codigos, cache)
        resumen.setdefault(("productos", estado), []).append(nombre)
        sku_por_id[ws.cell(fila, c["ID"]).value] = (celda.value, estado)
    wb.save(salida / ruta_prod.name)

    wb = openpyxl.load_workbook(ruta_opc)
    ws = wb.worksheets[0]
    c = columnas(ws)
    for fila in range(2, ws.max_row + 1):
        nombre = ws.cell(fila, c["Nombre Opción"]).value
        if not nombre:
            continue
        sku_prod, estado_prod = sku_por_id.get(ws.cell(fila, c["ID Producto"]).value, (None, "sin match"))
        celda_prod = ws.cell(fila, c["SKU Producto"])
        celda_prod.value = sku_prod
        if estado_prod != "ok":  # hereda la duda del producto
            celda_prod.fill = AMARILLO if sku_prod else ROJO
            if not sku_prod:
                celda_prod.comment = Comment(f"El producto no tiene artículo de HIOPOS. {LEYENDA}", "matcheador", width=320, height=60)
        estado = completar(ws.cell(fila, c["SKU"]), nombre, hiopos, codigos, cache)
        resumen.setdefault(("opcionales", estado), []).append(nombre)
    wb.save(salida / ruta_opc.name)
    return resumen


def uno(carpeta, patron):
    """El único archivo de la carpeta que cumple el patrón; si hay 0 o varios, avisa y sale."""
    archivos = sorted(carpeta.glob(patron))
    if len(archivos) != 1:
        hay = ", ".join(a.name for a in archivos) or "ninguno"
        sys.exit(f"En '{carpeta}' tiene que haber un solo archivo {patron} (hay: {hay}).")
    return archivos[0]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    recibidos = BASE / "Recibidos PYA"
    hiopos = leer_hiopos(uno(BASE / "Listado HIOPOS", "*.xls*"))
    salida = BASE / "Salida"
    salida.mkdir(exist_ok=True)
    resumen = procesar(hiopos, uno(recibidos, "productos-*.xlsx"), uno(recibidos, "opcionales-*.xlsx"), salida)
    for (hoja, estado), nombres in sorted(resumen.items()):
        print(f"{hoja:10} {estado:9} {len(nombres):3}" + ("" if estado == "ok" else "  " + ", ".join(sorted(set(nombres)))))
    if any(estado == "sin match" for _, estado in resumen):
        print(f"\nSin match: {LEYENDA}")
    print(f"\nListo -> {salida}")


if __name__ == "__main__":
    main()
