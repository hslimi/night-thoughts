import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const stylesheet = readFileSync(resolve(process.cwd(), "src/styles.css"), "utf8");
const mutedMatch = stylesheet.match(/--muted:\s*(#[\da-f]{6})\s*;/i);

if (!mutedMatch) {
  throw new Error("Could not find a six-digit --muted color in src/styles.css");
}

const mutedColor = mutedMatch[1];
const backgrounds = [
  ["white", "#ffffff"],
  ["page background", "#f5f7f5"],
  ["category tile", "#f6f8f6"],
  ["page gradient endpoint", "#e8f2ed"],
] as const;

function relativeLuminance(color: string): number {
  const channels = color.slice(1).match(/.{2}/g);
  if (!channels || channels.length !== 3) {
    throw new Error(`Expected a six-digit hex color, received ${color}`);
  }

  const [red, green, blue] = channels.map((channel) => {
    const value = Number.parseInt(channel, 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });

  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

function contrastRatio(foreground: string, background: string): number {
  const luminances = [
    relativeLuminance(foreground),
    relativeLuminance(background),
  ].sort((a, b) => b - a);

  return (luminances[0] + 0.05) / (luminances[1] + 0.05);
}

describe("muted text contrast", () => {
  it.each(backgrounds)("meets normal-text contrast on %s", (_name, background) => {
    expect(contrastRatio(mutedColor, background)).toBeGreaterThanOrEqual(4.5);
  });
});
