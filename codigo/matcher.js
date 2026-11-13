// Misma lógica que matcheador.py, para la pantalla. Si cambiás reglas, cambialas en los dos (test_matcher.js lo verifica).
const OK_MIN = 0.9, REVISAR_MIN = 0.6, EMPATE = 0.03, BONO_PEDIDOYA = 0.1;
const SINONIMOS = { BROASTER: "BROSTER", MUZLO: "MUSLO", MARIANADA: "MARINADA", MOZTAZA: "MOSTAZA",
  MOZTASA: "MOSTAZA", CHEDAR: "CHEDDAR", GR: "G", REFRESCO: "COCA", REFRESCOS: "COCA",
  COCAS: "COCA", COKBO: "COMBO", DOS: "2", TRES: "3" };
const RELLENO = new Set(["MAS", "Y", "CON", "DE", "LA", "EL", "O", "X", "PARA", "COLA", "ORIGINAL", "ML", "PERSONAS", "PERSONS"]);

function normalizar(texto) {
  let t = String(texto ?? "").normalize("NFKD").replace(/[^\x00-\x7F]/g, "").toUpperCase();
  // Medidas aparte, como "=600": si las dos tienen y no coinciden, no es el mismo artículo
  const medidas = [...t.matchAll(/(\d+(?:[.,]\d+)?)\s*(?:G|GR|GRS|ML|CC|L|LT|LTS)\b/g)].map(m => "=" + m[1].replace(",", "."));
  t = t.replace(/\d+([.,]\d+)?\s*(G|GR|GRS|ML|CC|L|LT|LTS)\b/g, " ");
  t = t.replace(/(\d)([A-Z])|([A-Z])(\d)/g, (m, a, b, c, d) => a ? `${a} ${b}` : `${c} ${d}`);
  const palabras = (t.match(/[A-Z0-9]+/g) || []).map(p => SINONIMOS[p] || p).filter(p => !RELLENO.has(p));
  return [...new Set([...palabras, ...medidas])];
}

// Caracteres en común al estilo difflib.SequenceMatcher
function enComun(a, b) {
  let mejor = 0, ai = 0, bj = 0;
  for (let i = 0; i < a.length; i++) for (let j = 0; j < b.length; j++) {
    let k = 0;
    while (i + k < a.length && j + k < b.length && a[i + k] === b[j + k]) k++;
    if (k > mejor) { mejor = k; ai = i; bj = j; }
  }
  return mejor && mejor + enComun(a.slice(0, ai), b.slice(0, bj)) + enComun(a.slice(ai + mejor), b.slice(bj + mejor));
}

function iguales(a, b) {
  if (/^\d+$/.test(a) || /^\d+$/.test(b)) return a === b;
  return 2 * enComun(a, b) / (a.length + b.length) >= 0.8;
}

function similitud(a, b) {
  const ma = a.filter(p => p[0] === "="), mb = b.filter(p => p[0] === "=");
  if (ma.length && mb.length && !ma.some(p => mb.includes(p))) return 0;
  a = a.filter(p => p[0] !== "="); b = b.filter(p => p[0] !== "=");
  const libres = [...b];
  let comunes = 0;
  for (const p of a) {
    const i = libres.findIndex(q => iguales(p, q));
    if (i >= 0) { libres.splice(i, 1); comunes++; }
  }
  return a.length || b.length ? 2 * comunes / (a.length + b.length) : 0;
}

const numCod = h => parseInt(h.cod.split("-")[0], 10) || 0;

function ranking(nombre, hiopos) {
  const tok = normalizar(nombre);
  // El bonus PEDIDOYA ordena y desempata (p); el estado se decide con el parecido sin bonus (s)
  return hiopos.map(h => { const s = similitud(tok, h.tokens); return { h, s, p: s + (h.familia === "PEDIDOYA" ? BONO_PEDIDOYA : 0) }; })
    .sort((x, y) => y.p - x.p || numCod(x.h) - numCod(y.h));
}

function buscar(nombre, hiopos) {
  const r = ranking(nombre, hiopos);
  const a = r[0], b = r.find(x => x.h.cod !== a.h.cod);  // un código repetido no tapa un empate
  const empatado = b && a.p - b.p <= EMPATE;
  const estado = a.s >= OK_MIN && !empatado ? "ok" : a.s >= REVISAR_MIN ? "revisar" : "sin match";
  return { cod: estado === "sin match" ? null : a.h.cod, estado, candidatos: r.slice(0, 3) };
}

function prepararHiopos(filas) {
  const cab = filas[0].map(c => String(c ?? "").trim());
  const iCod = cab.indexOf("Cód. PedidosYa"), iNom = cab.indexOf("Artículo"), iFam = cab.indexOf("Familia"), iPre = cab.indexOf("Precio");
  if (iCod < 0 || iNom < 0) throw new Error("El listado HIOPOS no tiene las columnas 'Artículo' y 'Cód. PedidosYa'.");
  return filas.slice(1).filter(r => r[iCod]).map(r => ({
    cod: String(r[iCod]).trim(), nombre: String(r[iNom] ?? "").trim(), familia: r[iFam] || "",
    precio: r[iPre], tokens: normalizar(r[iNom]) }));
}

if (typeof module !== "undefined") module.exports = { normalizar, similitud, buscar, ranking, prepararHiopos };
