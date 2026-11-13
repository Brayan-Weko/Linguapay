import { build } from "esbuild";
import { cpSync, mkdirSync, rmSync } from "node:fs";
import { resolve } from "node:path";

const distDir = resolve("dist");
rmSync(distDir, { recursive: true, force: true });
mkdirSync(distDir, { recursive: true });

await Promise.all([
  build({
    entryPoints: ["src/content/index.ts"],
    bundle: true,
    format: "iife",
    target: "chrome120",
    outfile: "dist/content.js",
    minify: false,
    sourcemap: false,
  }),
  build({
    entryPoints: ["src/background/service-worker.ts"],
    bundle: true,
    format: "esm",
    target: "chrome120",
    outfile: "dist/service-worker.js",
    minify: false,
    sourcemap: false,
  }),
  build({
    entryPoints: ["src/popup/popup.ts"],
    bundle: true,
    format: "iife",
    target: "chrome120",
    outfile: "dist/popup.js",
    minify: false,
    sourcemap: false,
  }),
]);

cpSync("manifest.json", "dist/manifest.json");
cpSync("src/popup/popup.html", "dist/popup.html");
console.log("LinguaPay MV3 extension built cleanly into extension/dist/");

