/// <reference types="node" />

import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import vm from "node:vm";

import { beforeAll, describe, expect, it } from "vitest";

const root = process.cwd();
const syncScript = path.resolve(
  root,
  "electron-src/renderer/scripts/sync-legacy-assets.mjs"
);
const previewDirectory = path.resolve(
  root,
  "electron-src/renderer/public/hoshidicts-preview"
);

beforeAll(() => {
  execFileSync(process.execPath, [syncScript], { cwd: root });
});

describe("Hoshidicts popup preview assets", () => {
  it("generates every reader dependency in browser load order", () => {
    const html = readFileSync(path.join(previewDirectory, "index.html"), "utf8");
    const scripts = Array.from(
      html.matchAll(/<script\s+defer\s+src="\.\/(.*?)"><\/script>/g),
      (match) => match[1]
    );

    expect(scripts).toEqual([
      "constants.js",
      "audio.js",
      "popup.js",
      "reader.js",
      "preview-fixture.js",
      "preview.js"
    ]);
    for (const fileName of scripts) {
      expect(() =>
        readFileSync(path.join(previewDirectory, fileName), "utf8")
      ).not.toThrow();
    }
  });

  it("initializes the browser reader API from the generated runtime", () => {
    const browserWindow: Record<string, unknown> = {};
    const context = vm.createContext({
      window: browserWindow,
      URL,
      AbortController,
      TextDecoder,
      TextEncoder,
      setTimeout,
      clearTimeout
    });

    for (const fileName of [
      "constants.js",
      "audio.js",
      "popup.js",
      "reader.js"
    ]) {
      vm.runInContext(
        readFileSync(path.join(previewDirectory, fileName), "utf8"),
        context,
        { filename: fileName }
      );
    }

    const reader = browserWindow.GSMHoshidictsReader as
      | { createHoshidictsReader?: unknown }
      | undefined;
    expect(reader?.createHoshidictsReader).toBeTypeOf("function");
  });

  it("adds the bee illustration only to the dictionary used by the preview summary", () => {
    const browserWindow: Record<string, unknown> = {};
    const context = vm.createContext({ window: browserWindow });
    vm.runInContext(
      readFileSync(path.join(previewDirectory, "preview-fixture.js"), "utf8"),
      context,
      { filename: "preview-fixture.js" }
    );
    const fixture = browserWindow.GSMHoshidictsPreviewFixture as {
      decorateLookupPayload(payload: unknown, dictionary: string | null): void;
    };
    const payload = {
      type: "hoshidicts_lookup_result",
      success: true,
      results: [{
        term: {
          glossaries: [
            { dictionary: "JMdict", glossary: "bee" },
            { dictionary: "Illustrated", glossary: "honey-making insect" }
          ]
        }
      }]
    };

    fixture.decorateLookupPayload(payload, "Illustrated");

    expect(payload.results[0].term.glossaries).toHaveLength(3);
    expect(payload.results[0].term.glossaries[0]).toEqual({
      dictionary: "JMdict",
      glossary: "bee"
    });
    expect(payload.results[0].term.glossaries[1]).toEqual(
      expect.objectContaining({
        dictionary: "Illustrated",
        glossary: expect.stringContaining('"path":"preview/bee.png"')
      })
    );
    expect(payload.results[0].term.glossaries[2]).toEqual({
      dictionary: "Illustrated",
      glossary: "honey-making insect"
    });
  });

  it("ships a real PNG for the live bee example", () => {
    const image = readFileSync(path.join(previewDirectory, "bee.png"));
    expect(image.subarray(0, 8)).toEqual(
      Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
    );
    expect(image.byteLength).toBeGreaterThan(1_000);
  });
});
