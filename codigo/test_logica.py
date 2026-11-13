"""Pruebas de la lógica de matcheo de matcheador.py con datos inventados (no necesita planillas de clientes).

Uso: python -m unittest test_logica -v
"""
import tempfile, unittest
from pathlib import Path
import openpyxl
import matcheador as m

LEYENDA = "Se recomienda crearlo en HIOPOS e importar las planillas nuevamente."

# Listado HIOPOS de ejemplo: (Cód. PedidosYa, Artículo, Familia)
HIOPOS = [
    ("101", "PIERNA BROSTER + COCA", "PEDIDOYA"),
    ("102", "SALCHIPAPA CLASICA", "PEDIDOYA"),
    ("103", "ALITAS X 6", "POLLO"),
    ("104", "HAMBURGUESA DOBLE CHEDDAR", "PEDIDOYA"),
    ("201", "PAPAS FRITAS", "GUARNICION"),
    ("202", "SALSA MOSTAZA", "SALSAS"),
    ("203", "SALSA BBQ", "SALSAS"),
    ("301", "EMPANADA CARNE", "COCINA"),
    ("302", "EMPANADA CARNE", "PEDIDOYA"),
    ("401", "MILANESA POLLO", "COCINA"),
    ("402", "MILANESA POLLO", "COCINA"),
]


def hiopos(filas=HIOPOS):
    return [{"cod": c, "nombre": n, "familia": f, "tokens": m.normalizar(n)} for c, n, f in filas]


def libro(ruta, cabecera, filas):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(cabecera)
    for fila in filas:
        ws.append(fila)
    wb.save(ruta)


class NombresDistintos(unittest.TestCase):
    """El mismo artículo escrito distinto en PedidosYa y en HIOPOS."""

    def assertOk(self, nombre, cod):
        got, estado, _ = m.buscar(nombre, hiopos())
        self.assertEqual((got, estado), (cod, "ok"), nombre)

    def test_acentos_mayusculas_y_relleno(self):
        self.assertOk("Salchipapa clásica", "102")

    def test_medidas_ignoradas(self):
        self.assertOk("Salchipapa Clásica 600 g", "102")

    def test_sinonimos_y_relleno(self):
        self.assertOk("Pierna broaster más coca cola", "101")
        self.assertOk("Pierna Broster con Refresco", "101")

    def test_numero_pegado(self):
        self.assertOk("Alitas x6", "103")

    def test_falta_de_ortografia(self):
        self.assertOk("Hamburguesa dobel chedar", "104")

    def test_orden_de_palabras(self):
        self.assertOk("Mostaza salsa", "202")

    def test_otra_medida_no_es_el_mismo(self):
        filas = [("601", "COCA 600", "BEBIDAS"), ("602", "COCA 1.5 LTS", "BEBIDAS")]
        self.assertNotEqual(m.buscar("Coca-Cola 600 ml", hiopos(filas))[:2], ("602", "ok"))
        self.assertEqual(m.buscar("Coca-Cola 1,5 L", hiopos(filas))[:2], ("602", "ok"))

    def test_bonus_pedidoya_no_aprueba_un_match_a_medias(self):
        # 2 de 3 palabras (80%) + bonus PEDIDOYA no alcanza para verde: es otro producto
        self.assertEqual(m.buscar("Hamburguesa doble", hiopos())[1], "revisar")

    def test_numeros_deben_ser_iguales(self):
        # "ALITAS X 12" no es "ALITAS X 6": el número no se tolera como falta de ortografía
        self.assertNotEqual(m.buscar("Alitas x12", hiopos())[1], "ok")


class ArticulosRepetidos(unittest.TestCase):
    """Artículos con el mismo nombre en HIOPOS o repetidos en la planilla de PedidosYa."""

    def test_repetido_en_hiopos_prefiere_familia_pedidoya(self):
        self.assertEqual(m.buscar("Empanada de carne", hiopos())[:2], ("302", "ok"))

    def test_repetido_en_hiopos_misma_familia_queda_para_revisar(self):
        cod, estado, candidatos = m.buscar("Milanesa de pollo", hiopos())
        self.assertEqual((cod, estado), ("401", "revisar"))  # a igualdad, el código más bajo
        self.assertIn("401", candidatos)
        self.assertIn("402", candidatos)

    def test_codigo_repetido_no_tapa_un_empate(self):
        filas = [("501", "TORTA DE CHOCLO", "COCINA"), ("501", "TORTA DE CHOCLO", "COCINA"), ("502", "TORTA DE CHOCLO", "COCINA")]
        self.assertEqual(m.buscar("Torta de choclo", hiopos(filas))[:2], ("501", "revisar"))

    def test_mismo_codigo_dos_veces_no_es_empate(self):
        filas = [("501", "TORTA DE CHOCLO", "COCINA"), ("501", "TORTA DE CHOCLO", "COCINA")]
        self.assertEqual(m.buscar("Torta de choclo", hiopos(filas))[:2], ("501", "ok"))


class Planillas(unittest.TestCase):
    """procesar() de punta a punta sobre planillas armadas en una carpeta temporal."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "Salida").mkdir()
        self.prod, self.opc = self.dir / "productos-1.xlsx", self.dir / "opcionales-1.xlsx"

    def correr(self, productos, opcionales):
        libro(self.prod, ["ID", "Nombre", "SKU"], productos)
        libro(self.opc, ["ID Producto", "Nombre Opción", "SKU Producto", "SKU"], opcionales)
        resumen = m.procesar(hiopos(), self.prod, self.opc, self.dir / "Salida")
        ws_p = openpyxl.load_workbook(self.dir / "Salida" / self.prod.name).worksheets[0]
        ws_o = openpyxl.load_workbook(self.dir / "Salida" / self.opc.name).worksheets[0]
        return resumen, ws_p, ws_o

    def color(self, celda):
        return {"00FFFF00": "amarillo", "00FF8080": "rojo"}.get(celda.fill.fgColor.rgb)

    def test_articulos_repetidos_en_pedidosya(self):
        resumen, ws, _ = self.correr(
            [(1, "Salchipapa clásica", None), (2, "Salchipapa clásica", None), (3, "SALCHIPAPA CLASICA 600 g", None)], [])
        self.assertEqual([ws.cell(f, 3).value for f in (2, 3, 4)], ["102"] * 3)
        self.assertTrue(all(self.color(ws.cell(f, 3)) is None for f in (2, 3, 4)))
        self.assertEqual(len(resumen[("productos", "ok")]), 3)

    def test_opcionales_repetidos(self):
        # La misma salsa como opcional de dos productos: mismo SKU y cada fila toma el SKU de su producto
        _, _, ws = self.correr(
            [(1, "Papas fritas", None), (2, "Alitas x6", None)],
            [(1, "Salsa mostaza", None, None), (2, "Salsa mostaza", None, None),
             (1, "Salsa BBQ", None, None), (2, "Salsa BBQ", None, None)])
        filas = [(ws.cell(f, 3).value, ws.cell(f, 4).value) for f in range(2, 6)]
        self.assertEqual(filas, [("201", "202"), ("103", "202"), ("201", "203"), ("103", "203")])
        self.assertTrue(all(self.color(ws.cell(f, c)) is None for f in range(2, 6) for c in (3, 4)))

    def test_sin_coincidencia_lleva_leyenda_hiopos(self):
        resumen, ws_p, ws_o = self.correr(
            [(1, "Sushi de salmón", None)], [(1, "Wasabi extra", None, None)])
        for celda in (ws_p.cell(2, 3), ws_o.cell(2, 4)):
            self.assertIsNone(celda.value)
            self.assertEqual(self.color(celda), "rojo")
            self.assertIn(LEYENDA, celda.comment.text)
        self.assertEqual(self.color(ws_o.cell(2, 3)), "rojo")  # SKU Producto hereda el sin match del producto
        self.assertEqual(resumen[("productos", "sin match")], ["Sushi de salmón"])

    def test_revisar_no_lleva_leyenda(self):
        _, ws, _ = self.correr([(1, "Milanesa de pollo", None)], [])
        celda = ws.cell(2, 3)
        self.assertEqual((celda.value, self.color(celda)), ("401", "amarillo"))
        self.assertNotIn(LEYENDA, celda.comment.text)


if __name__ == "__main__":
    unittest.main()
