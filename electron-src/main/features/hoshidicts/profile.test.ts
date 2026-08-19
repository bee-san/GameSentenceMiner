import { describe, expect, it } from 'vitest';

import {
    cloneHoshidictsMiningProfile,
    hoshidictsMiningProfilesEqual,
} from '../../../shared/features/hoshidicts.js';
import {
    DEFAULT_HOSHIDICTS_ANKI_BUTTON_ID,
    defaultHoshidictsMiningProfile,
    normalizeHoshidictsMiningProfile,
} from './profile.js';

function buttonConfig(overrides: Record<string, unknown> = {}) {
    return {
        ...defaultHoshidictsMiningProfile().buttons[0],
        id: DEFAULT_HOSHIDICTS_ANKI_BUTTON_ID,
        enabled: true,
        label: 'Add to Anki',
        icon: 'anki',
        ...overrides,
    };
}

describe('Hoshidicts Anki button profiles', () => {
    it('migrates the legacy mining profile and Add to Anki visibility without data loss', () => {
        const migrated = normalizeHoshidictsMiningProfile(
            {
                version: 3,
                enabled: false,
                deck: ' Mining ',
                model: ' Japanese ',
                fields: {
                    expression: ' Front ',
                    reading: ' Kana ',
                },
                disabledFields: ['pitch'],
                tags: [' hoshidicts ', 'custom'],
                checkForDuplicates: false,
                duplicateScope: 'deck',
                duplicateScopeCheckAllModels: true,
                duplicateBehavior: 'overwrite',
                fieldOverwriteModes: { expression: 'overwrite' },
                fieldTemplates: {
                    Front: {
                        value: '{expression}',
                        overwriteMode: 'overwrite',
                    },
                },
            },
            false
        );

        expect(migrated).toEqual({
            version: 4,
            enabled: false,
            buttons: [
                {
                    id: DEFAULT_HOSHIDICTS_ANKI_BUTTON_ID,
                    enabled: false,
                    label: 'Add to Anki',
                    icon: 'anki',
                    deck: 'Mining',
                    model: 'Japanese',
                    fields: {
                        expression: 'Front',
                        reading: 'Kana',
                        definition: '',
                        sentence: '',
                        frequency: '',
                        pitch: '',
                        audio: '',
                    },
                    disabledFields: ['pitch'],
                    tags: ['hoshidicts', 'custom'],
                    checkForDuplicates: false,
                    duplicateScope: 'deck',
                    duplicateScopeCheckAllModels: true,
                    duplicateBehavior: 'overwrite',
                    fieldOverwriteModes: {
                        expression: 'overwrite',
                        reading: 'coalesce',
                        definition: 'coalesce',
                        sentence: 'coalesce',
                        frequency: 'coalesce',
                        pitch: 'coalesce',
                        audio: 'coalesce',
                    },
                    fieldTemplates: {
                        Front: {
                            value: '{expression}',
                            overwriteMode: 'overwrite',
                        },
                    },
                },
            ],
        });
    });

    it('normalizes and round-trips multiple ordered buttons with stable ids', () => {
        const profile = normalizeHoshidictsMiningProfile({
            version: 4,
            enabled: true,
            buttons: [
                buttonConfig({
                    id: 'recognition',
                    label: ' Recognition ',
                    deck: ' Mining::Recognition ',
                }),
                buttonConfig({
                    id: 'production',
                    label: 'Production',
                    icon: 'sparkles',
                    deck: 'Mining::Production',
                    model: 'Production',
                    tags: ['production'],
                    fieldTemplates: {
                        Answer: {
                            value: '{reading}<br>{definition}',
                            overwriteMode: 'coalesce',
                        },
                    },
                }),
            ],
        });

        expect(profile.buttons.map(({ id }) => id)).toEqual([
            'recognition',
            'production',
        ]);
        expect(profile.buttons[0]).toMatchObject({
            label: 'Recognition',
            deck: 'Mining::Recognition',
        });
        expect(normalizeHoshidictsMiningProfile(JSON.parse(JSON.stringify(profile)))).toEqual(
            profile
        );
    });

    it.each([
        ['a non-array button collection', { version: 4, enabled: true, buttons: {} }],
        ['a non-boolean legacy enabled value', { version: 3, enabled: 'yes' }],
        [
            'duplicate ids',
            {
                version: 4,
                enabled: true,
                buttons: [
                    buttonConfig({ id: 'same' }),
                    buttonConfig({ id: 'same' }),
                ],
            },
        ],
        [
            'an unsafe id',
            {
                version: 4,
                enabled: true,
                buttons: [buttonConfig({ id: '../unsafe' })],
            },
        ],
        [
            'a malformed entry',
            { version: 4, enabled: true, buttons: [null] },
        ],
    ])('rejects %s', (_case, profile) => {
        expect(() => normalizeHoshidictsMiningProfile(profile)).toThrow();
    });

    it('clones nested button state and compares every persisted value', () => {
        const profile = defaultHoshidictsMiningProfile();
        const clone = cloneHoshidictsMiningProfile(profile);

        expect(hoshidictsMiningProfilesEqual(profile, clone)).toBe(true);
        clone.buttons[0].tags.push('changed');
        clone.buttons[0].fieldOverwriteModes.expression = 'overwrite';

        expect(profile.buttons[0].tags).toEqual(['hoshidicts']);
        expect(profile.buttons[0].fieldOverwriteModes.expression).toBe('coalesce');
        expect(hoshidictsMiningProfilesEqual(profile, clone)).toBe(false);
    });
});
