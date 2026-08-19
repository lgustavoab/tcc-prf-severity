import { access, stat } from "node:fs/promises";
import path from "node:path";

const outDir = path.resolve("out");
const routes = [
  "index.html",
  "exploracao.html",
  "geografia.html",
  "modelos.html",
  "validacao-temporal.html",
  "limiar.html",
  "interpretacao.html",
  "metodologia.html",
];
const assets = [
  "data/manifest.json",
  "data/meta.json",
  "data/overview/summary.json",
  "data/exploration/temporal.json",
  "data/models/model_comparison.json",
];

async function assertFile(relativePath) {
  const absolutePath = path.join(outDir, relativePath);
  await access(absolutePath);
  const details = await stat(absolutePath);
  if (!details.isFile()) {
    throw new Error(`O caminho exportado não é um arquivo: ${relativePath}`);
  }
}

await Promise.all([...routes, ...assets].map(assertFile));
console.log(`Static export verificado: ${routes.length} rotas e ${assets.length} assets essenciais.`);
