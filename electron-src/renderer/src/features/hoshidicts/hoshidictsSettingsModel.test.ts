import { describe, expect, it } from "vitest";

import {
  DEFAULT_MINING_PROFILE,
  draftToProfile,
  profileToDraft
} from "./hoshidictsSettingsModel";

describe("Hoshidicts mining profile drafts", () => {
  it("edits the stable default button without reordering other buttons", () => {
    const defaultButton = DEFAULT_MINING_PROFILE.buttons[0];
    const profile = {
      version: 4 as const,
      enabled: true,
      buttons: [
        { ...defaultButton, id: "recognition", deck: "Recognition" },
        { ...defaultButton, deck: "Production" }
      ]
    };

    const draft = profileToDraft(profile);
    const saved = draftToProfile({ ...draft, deck: "Edited Production" });

    expect(draft.deck).toBe("Production");
    expect(saved.buttons.map(({ id }) => id)).toEqual([
      "recognition",
      "add-to-anki"
    ]);
    expect(saved.buttons[0].deck).toBe("Recognition");
    expect(saved.buttons[1].deck).toBe("Edited Production");
  });
});
