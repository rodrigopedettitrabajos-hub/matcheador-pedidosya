# Matcheador PedidosYa ↔ HIOPOS

Completa los SKU de las planillas que manda PedidosYa (productos y opcionales) con los códigos del listado HIOPOS (`Cód. PedidosYa`), para la integración PedidosYa–HIOPOS.

## Para técnicos

Abrí `Para tecnicos/Matcheador.html` con doble clic. Es un solo archivo, no necesita instalación ni internet (sin internet no se ven las fotos).

1. Arrastrá las 3 planillas: `productos-XXXX.xlsx`, `opcionales-XXXX.xlsx` y el listado HIOPOS.
2. Revisá lo que está en amarillo (Confirmar o Cambiar) y elegí a mano lo que está en rojo.
3. Descargá las planillas y enviáselas a PedidosYa.

Colores: verde = listo, amarillo = revisar, rojo = sin match, violeta = confirmado a mano.

## Cómo matchea

Compara nombres palabra por palabra, ignorando acentos, mayúsculas, medidas ("600 g") y relleno ("más", "con", "para"), y tolera faltas de ortografía. Ante empate prefiere la familia `PEDIDOYA` y después el código más bajo. Los SKU que ya existen en HIOPOS se respetan. El `SKU Producto` de los opcionales se toma del producto.

Para casos que no reconoce, agregar variantes en `SINONIMOS` / `RELLENO`.

## Archivos

| Archivo | Qué es |
|---|---|
| `matcheador.html` + `matcher.js` | Pantalla (fuente). |
| `empaquetar.py` | Arma `Para tecnicos/Matcheador.html` incrustando `matcher.js` y `vendor/xlsx.full.min.js` (SheetJS 0.18.5). Correrlo tras cada cambio. |
| `matcheador.py` + `ejecutar.bat` | Versión por consola: lee `Recibidos PYA/` y `Listado HIOPOS/`, escribe en `Salida/`. |
| `test_matcheador.py` | Compara la salida contra `Enviados PYA/` (lo que se envió a mano). |
| `test_matcher.js` | Verifica que `matcher.js` y `matcheador.py` den lo mismo. |
| `docs/Presentacion Matcheador.pdf` | Presentación de la herramienta. Se genera desde `docs/presentacion.html` imprimiéndolo con Edge/Chrome (`msedge --headless --print-to-pdf=... presentacion.html`). |

**Las reglas viven en dos lugares** (`matcher.js` y `matcheador.py`): si cambiás una, cambiá la otra y corré `node test_matcher.js`.

Las planillas de clientes no están en el repo (`.gitignore`). Para correr los tests, poné una tienda de ejemplo en `Recibidos PYA/`, `Enviados PYA/` y `Listado HIOPOS/`.

Requisitos para desarrollar: Python 3 con `openpyxl`, y Node.
