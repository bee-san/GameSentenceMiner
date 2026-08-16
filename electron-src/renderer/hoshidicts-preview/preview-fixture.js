(function () {
  "use strict";

  const BEE_PATH = "preview/bee.png";

  function isRecord(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
  }

  function lookupGlossaries(payload) {
    if (
      !isRecord(payload) ||
      payload.type !== "hoshidicts_lookup_result" ||
      payload.success !== true ||
      !Array.isArray(payload.results)
    ) {
      return null;
    }
    for (const result of payload.results) {
      if (isRecord(result?.term) && Array.isArray(result.term.glossaries)) {
        return result.term.glossaries;
      }
    }
    return null;
  }

  function decorateLookupPayload(payload, preferredDictionary) {
    const glossaries = lookupGlossaries(payload);
    if (!glossaries || glossaries.length === 0) return;
    const preferred = typeof preferredDictionary === "string"
      ? glossaries.find((glossary) => glossary?.dictionary === preferredDictionary)
      : null;
    const target = preferred || glossaries.find(
      (glossary) => typeof glossary?.dictionary === "string"
    );
    if (!target || glossaries.some(
      (glossary) => typeof glossary?.glossary === "string" &&
        glossary.glossary.includes(`\"path\":\"${BEE_PATH}\"`)
    )) {
      return;
    }
    const targetIndex = glossaries.indexOf(target);
    glossaries.splice(targetIndex, 0, {
      dictionary: target.dictionary,
      glossary: JSON.stringify({
        type: "structured-content",
        content: {
          tag: "img",
          path: BEE_PATH,
          width: 256,
          height: 256,
          data: { alt: "Honey bee" }
        }
      }),
      definitionTags: "",
      termTags: ""
    });
  }

  function isBeeMediaRequest(value) {
    return isRecord(value) &&
      value.type === "hoshidicts_media" &&
      value.path === BEE_PATH;
  }

  function bytesToBase64(bytes) {
    let binary = "";
    const chunkSize = 0x8000;
    for (let offset = 0; offset < bytes.length; offset += chunkSize) {
      binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
    }
    return window.btoa(binary);
  }

  async function createBeeMediaResponse(request) {
    try {
      const response = await window.fetch("./bee.png");
      if (!response.ok) throw new Error("bee_image_unavailable");
      const bytes = new Uint8Array(await response.arrayBuffer());
      return {
        type: "hoshidicts_media_result",
        requestId: request.requestId,
        success: true,
        generation: request.generation,
        dictionary: request.dictionary,
        path: request.path,
        mediaType: "image/png",
        byteLength: bytes.byteLength,
        dataBase64: bytesToBase64(bytes)
      };
    } catch {
      return {
        type: "hoshidicts_media_result",
        requestId: request.requestId,
        success: false,
        generation: request.generation,
        dictionary: request.dictionary,
        path: request.path,
        mediaType: null,
        byteLength: 0,
        dataBase64: null,
        error: "bee_image_unavailable"
      };
    }
  }

  window.GSMHoshidictsPreviewFixture = {
    decorateLookupPayload,
    isBeeMediaRequest,
    createBeeMediaResponse
  };
})();
