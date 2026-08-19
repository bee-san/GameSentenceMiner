import { describe, expect, it } from "vitest";

import {
  addMiningButton,
  DEFAULT_MINING_PROFILE,
  deleteMiningButton,
  duplicateSelectedMiningButton,
  draftToProfile,
  moveMiningButton,
  profileToDraft,
  selectMiningButton,
  setMiningButtonEnabled
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

  it("preserves the prior valid button label when a rename draft is blank", () => {
    const draft = profileToDraft({
      version: 4,
      enabled: true,
      buttons: [
        {
          ...DEFAULT_MINING_PROFILE.buttons[0],
          id: "recognition",
          label: "Recognition"
        }
      ]
    });

    const saved = draftToProfile({ ...draft, label: " \t " });

    expect(saved.buttons[0].label).toBe("Recognition");
  });

  it("selects another button without losing edits to the current button", () => {
    const defaultButton = DEFAULT_MINING_PROFILE.buttons[0];
    const draft = profileToDraft({
      version: 4,
      enabled: true,
      buttons: [
        { ...defaultButton, id: "recognition", deck: "Recognition" },
        { ...defaultButton, deck: "Production" }
      ]
    });

    const selected = selectMiningButton(
      { ...draft, deck: "Edited Production" },
      "recognition"
    );

    expect(selected.selectedButtonId).toBe("recognition");
    expect(selected.deck).toBe("Recognition");
    expect(selected.buttons[1].deck).toBe("Edited Production");
  });

  it("adds and selects a fresh button with a unique stable id", () => {
    const first = addMiningButton(
      profileToDraft(DEFAULT_MINING_PROFILE),
      "New Anki button"
    );
    const second = addMiningButton(first, "New Anki button");

    expect(first.selectedButtonId).toBe("anki-button");
    expect(second.selectedButtonId).toBe("anki-button-2");
    expect(second.buttons.map(({ id }) => id)).toEqual([
      "add-to-anki",
      "anki-button",
      "anki-button-2"
    ]);
    expect(second.label).toBe("New Anki button");
    expect(second.icon).toBe("anki");
  });

  it("duplicates the selected button beside its source", () => {
    const defaultButton = DEFAULT_MINING_PROFILE.buttons[0];
    const draft = profileToDraft({
      version: 4,
      enabled: true,
      buttons: [
        { ...defaultButton, deck: "Production" },
        { ...defaultButton, id: "recognition", deck: "Recognition" }
      ]
    });

    const duplicate = duplicateSelectedMiningButton(
      { ...draft, model: "Mining" },
      "Add to Anki copy"
    );

    expect(duplicate.selectedButtonId).toBe("anki-button");
    expect(duplicate.buttons.map(({ id }) => id)).toEqual([
      "add-to-anki",
      "anki-button",
      "recognition"
    ]);
    expect(duplicate.label).toBe("Add to Anki copy");
    expect(duplicate.deck).toBe("Production");
    expect(duplicate.model).toBe("Mining");
  });

  it("reorders a button while preserving its selection and edits", () => {
    const defaultButton = DEFAULT_MINING_PROFILE.buttons[0];
    const draft = selectMiningButton(
      profileToDraft({
        version: 4,
        enabled: true,
        buttons: [
          defaultButton,
          { ...defaultButton, id: "recognition", label: "Recognition" }
        ]
      }),
      "recognition"
    );

    const reordered = moveMiningButton(
      { ...draft, deck: "Edited Recognition" },
      "recognition",
      -1
    );

    expect(reordered.buttons.map(({ id }) => id)).toEqual([
      "recognition",
      "add-to-anki"
    ]);
    expect(reordered.selectedButtonId).toBe("recognition");
    expect(reordered.deck).toBe("Edited Recognition");
  });

  it("enables or disables one button independently", () => {
    const defaultButton = DEFAULT_MINING_PROFILE.buttons[0];
    const draft = profileToDraft({
      version: 4,
      enabled: true,
      buttons: [
        defaultButton,
        { ...defaultButton, id: "recognition", enabled: true }
      ]
    });

    const updated = setMiningButtonEnabled(draft, "recognition", false);

    expect(updated.buttons.map(({ enabled }) => enabled)).toEqual([true, false]);
    expect(updated.selectedButtonId).toBe("add-to-anki");
  });

  it("deletes a button and selects its nearest remaining neighbour", () => {
    const defaultButton = DEFAULT_MINING_PROFILE.buttons[0];
    const draft = profileToDraft({
      version: 4,
      enabled: true,
      buttons: [
        defaultButton,
        { ...defaultButton, id: "recognition", label: "Recognition" }
      ]
    });

    const remaining = deleteMiningButton(draft, "add-to-anki");
    const empty = deleteMiningButton(remaining, "recognition");

    expect(remaining.buttons.map(({ id }) => id)).toEqual(["recognition"]);
    expect(remaining.selectedButtonId).toBe("recognition");
    expect(empty.buttons).toEqual([]);
    expect(empty.selectedButtonId).toBeNull();
  });
});
