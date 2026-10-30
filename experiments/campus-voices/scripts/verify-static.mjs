import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

async function filesBelow(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await filesBelow(target)));
    else files.push(target);
  }
  return files;
}

const files = await filesBelow(path.resolve("dist"));
const browserSource = (
  await Promise.all(files.map((file) => readFile(file, "utf8")))
).join("\n");
const forbiddenApis = [
  "OMLX_API_KEY",
  "speechSynthesis",
  "SpeechRecognition",
  "getUserMedia",
];
const leaked = forbiddenApis.filter((name) => browserSource.includes(name));
if (
  process.env.OMLX_API_KEY &&
  browserSource.includes(process.env.OMLX_API_KEY)
)
  leaked.push("configured server credential");
if (leaked.length) {
  console.error(
    `Browser bundle contains forbidden names or credentials: ${leaked.join(", ")}`,
  );
  process.exit(1);
}
if (!browserSource.includes("Dessa is a disabled future provider")) {
  console.error("The disabled Dessa provider label is missing.");
  process.exit(1);
}
console.log(
  "Browser bundle contains no oMLX credential, microphone capture, or cloud speech API references.",
);
