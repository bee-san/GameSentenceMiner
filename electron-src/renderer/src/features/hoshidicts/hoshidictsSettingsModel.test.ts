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

  it("edits the first stable button without inventing a default button", () => {
    const defaultButton = DEFAULT_MINING_PROFILE.buttons[0];
    const profile = {
      version: 4 as const,
      enabled: true,
      buttons: [
        { ...defaultButton, id: "recognition", deck: "Recognition" },
        { ...defaultButton, id: "production", deck: "Production" }
      ]
    };

    const draft = profileToDraft(profile);
    const saved = draftToProfile({ ...draft, deck: "Edited Recognition" });

    expect(draft.id).toBe("recognition");
    expect(saved.buttons.map(({ id }) => id)).toEqual([
      "recognition",
      "production"
    ]);
    expect(saved.buttons[0].deck).toBe("Edited Recognition");
    expect(saved.buttons[1].deck).toBe("Production");
  });

  it("round-trips an empty button collection without inventing a preset", () => {
    const profile = {
      version: 4 as const,
      enabled: true,
      buttons: []
    };

    const draft = profileToDraft(profile);
    const saved = draftToProfile({ ...draft, enabled: false });

    expect(saved).toEqual({ ...profile, enabled: false });
  });
});
