"""Compara la salida del matcheador contra lo que se envió a mano en "Enviados PYA".
Regla clave: ningún SKU marcado como 'ok' (sin color) puede diferir de lo enviado."""
import sys, tempfile
from pathlib import Path
import openpyxl
import matcheador as m

sys.stdout.reconfigure(encoding="utf-8")
B = m.BASE
hiopos = m.leer_hiopos(next((B / "Listado HIOPOS").glob("*.xls*")))
salida = Path(tempfile.mkdtemp())
prod, opc = next((B / "Recibidos PYA").glob("productos-*.xlsx")), next((B / "Recibidos PYA").glob("opcionales-*.xlsx"))
m.procesar(hiopos, prod, opc, salida)

errores = 0
for nombre, enviado in [(prod.name, next((B / "Enviados PYA").glob("productos-*.xlsx"))), (opc.name, next((B / "Enviados PYA").glob("opcionales-*.xlsx")))]:
    ws_out, ws_env = openpyxl.load_workbook(salida / nombre).worksheets[0], openpyxl.load_workbook(enviado).worksheets[0]
    for col in ["SKU Producto", "SKU"]:
        if col not in m.columnas(ws_out):
            continue
        ci, ce = m.columnas(ws_out)[col], m.columnas(ws_env)[col]
        for f in range(2, ws_out.max_row + 1):
            got, exp = ws_out.cell(f, ci), ws_env.cell(f, ce).value
            marcado = got.fill.fgColor.rgb in ("00FFFF00", "00FF8080")
            if got.value != exp:
                tag = "revisar" if marcado else "ERROR (marcado ok)"
                errores += not marcado
                print(f"{nombre} fila {f} {col}: sale {got.value!r}, se envió {exp!r} -> {tag}")
assert errores == 0, f"{errores} SKU confirmados automáticamente difieren de lo enviado"
print("OK: todo lo que el matcheador da por bueno coincide con lo enviado")
