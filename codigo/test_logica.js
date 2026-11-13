// node codigo/test_logica.js — las reglas de matcher.js (lo que usa la pantalla) con datos inventados, sin planillas de clientes.
// Mismos casos que test_logica.py.
const assert = require("assert");
const m = require("./matcher.js");

const HIOPOS = [
  ["101", "PIERNA BROSTER + COCA", "PEDIDOYA"], ["102", "SALCHIPAPA CLASICA", "PEDIDOYA"], ["103", "ALITAS X 6", "POLLO"],
  ["104", "HAMBURGUESA DOBLE CHEDDAR", "PEDIDOYA"], ["201", "PAPAS FRITAS", "GUARNICION"], ["202", "SALSA MOSTAZA", "SALSAS"],
  ["203", "SALSA BBQ", "SALSAS"], ["301", "EMPANADA CARNE", "COCINA"], ["302", "EMPANADA CARNE", "PEDIDOYA"],
  ["401", "MILANESA POLLO", "COCINA"], ["402", "MILANESA POLLO", "COCINA"],
];
const lista = (filas = HIOPOS) => m.prepararHiopos([["Cód. PedidosYa", "Artículo", "Familia"], ...filas]);
const da = (nombre, filas) => { const r = m.buscar(nombre, lista(filas)); return [r.cod, r.estado]; };

const casos = [
  // Nombres escritos distinto en PedidosYa y en HIOPOS
  ["Salchipapa clásica", ["102", "ok"]],
  ["Salchipapa Clásica 600 g", ["102", "ok"]],
  ["Pierna broaster más coca cola", ["101", "ok"]],
  ["Pierna Broster con Refresco", ["101", "ok"]],
  ["Alitas x6", ["103", "ok"]],
  ["Hamburguesa dobel chedar", ["104", "ok"]],
  ["Mostaza salsa", ["202", "ok"]],
  // El bonus PEDIDOYA no aprueba un match a medias
  ["Hamburguesa doble", ["104", "revisar"]],
  // Repetidos en HIOPOS
  ["Empanada de carne", ["302", "ok"]],
  ["Milanesa de pollo", ["401", "revisar"]],
];
for (const [nombre, esperado] of casos) assert.deepStrictEqual(da(nombre), esperado, nombre);

assert.notStrictEqual(da("Alitas x12")[1], "ok", "el número no se tolera como falta de ortografía");
const cocas = [["601", "COCA 600", "BEBIDAS"], ["602", "COCA 1.5 LTS", "BEBIDAS"]];
assert.notDeepStrictEqual(da("Coca-Cola 600 ml", cocas), ["602", "ok"], "otra medida no es el mismo");
assert.deepStrictEqual(da("Coca-Cola 1,5 L", cocas), ["602", "ok"], "medida con coma");
const torta = [["501", "TORTA DE CHOCLO", "COCINA"], ["501", "TORTA DE CHOCLO", "COCINA"]];
assert.deepStrictEqual(da("Torta de choclo", torta), ["501", "ok"], "mismo código dos veces no es empate");
assert.deepStrictEqual(da("Torta de choclo", [...torta, ["502", "TORTA DE CHOCLO", "COCINA"]]), ["501", "revisar"], "código repetido no tapa un empate");

console.log(`OK: ${casos.length + 5} casos de matcher.js`);
