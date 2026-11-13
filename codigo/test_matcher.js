// node test_matcher.js (otra instalación de Python: PYTHON=ruta\python.exe) — verifica que matcher.js (pantalla) y matcheador.py den lo mismo con el listado HIOPOS actual.
const { execFileSync } = require("child_process");
const path = require("path"), assert = require("assert");
const m = require("./matcher.js");
const py = process.env.PYTHON || path.join(process.env.LOCALAPPDATA, "Programs", "Python", "Python311", "python.exe");
const out = execFileSync(py, ["-c", `
import json, sys, openpyxl, matcheador as m
f = next((m.BASE / "Listado HIOPOS").glob("*.xls*"))
h = m.leer_hiopos(f)
filas = [list(r) for r in openpyxl.load_workbook(open(f, "rb"), data_only=True).worksheets[0].iter_rows(values_only=True)]
nombres = [x["nombre"] for x in h] + ["Alitas x6", "Pierna broster mas coca cola", "Refresco Coca-Cola Original 600 ml", "Salchipapa clásica 600 g"]
sys.stdout.reconfigure(encoding="utf-8")
print(json.dumps({"filas": filas, "res": {n: m.buscar(n, h)[:2] for n in nombres}}, default=str, ensure_ascii=False))
`], { cwd: __dirname, encoding: "utf8", stdio: ["ignore", "pipe", "inherit"] });
const d = JSON.parse(out), h = m.prepararHiopos(d.filas);
for (const [nombre, [cod, estado]] of Object.entries(d.res)) {
  const r = m.buscar(nombre, h);
  assert.deepStrictEqual([r.cod, r.estado], [cod, estado], `Distinto para "${nombre}"`);
}
console.log(`OK: ${Object.keys(d.res).length} nombres iguales en JS y Python`);
