"""Name parsing and reading generation for Japanese character names."""

from typing import Dict
import jaconv


class NameParser:
    """
    Handles parsing and reading generation for Japanese character names.

    This class manages:
    - Splitting Japanese names by space (family/given name separation)
    - Converting romanized names to hiragana readings
    - Handling mixed kanji/kana names with per-part logic
    - Generating honorific suffix variants
    """

    # Japanese honorific suffixes: (kanji/kana form, hiragana reading)
    HONORIFIC_SUFFIXES = [
        # Respectful/Formal
        ("さん", "さん"),
        ("様", "さま"),
        ("先生", "せんせい"),
        ("先輩", "せんぱい"),
        ("後輩", "こうはい"),
        ("氏", "し"),
        # Casual/Friendly
        ("君", "くん"),
        ("くん", "くん"),
        ("ちゃん", "ちゃん"),
        ("たん", "たん"),
        ("坊", "ぼう"),
        # Old-fashioned/Archaic
        ("殿", "どの"),
        ("博士", "はかせ"),
        # Occupational/Specific
        ("社長", "しゃちょう"),
        ("部長", "ぶちょう"),
    ]

    def contains_kanji(self, text: str) -> bool:
        if not text:
            return False
        for char in text:
            code = ord(char)
            if (0x4E00 <= code <= 0x9FFF) or (0x3400 <= code <= 0x4DBF):
                return True
        return False

    def split_japanese_name(self, name_original: str) -> Dict[str, str | bool]:
        if not name_original or ' ' not in name_original:
            return {
                'has_space': False,
                'original': name_original or '',
                'combined': name_original or '',
                'family': None,
                'given': None
            }

        parts = name_original.split(' ', 1)
        family = parts[0]
        given = parts[1] if len(parts) > 1 else ''
        combined = family + given

        return {
            'has_space': True,
            'original': name_original,
            'combined': combined,
            'family': family,
            'given': given
        }

    def split_romanized_name_to_hiragana(self, romanized_name: str) -> Dict[str, str | bool]:
        if not romanized_name:
            return {
                'has_space': False,
                'original': '',
                'full': '',
                'family': '',
                'given': ''
            }

        if ' ' not in romanized_name:
            full_hiragana = jaconv.alphabet2kana(romanized_name.lower())
            return {
                'has_space': False,
                'original': romanized_name,
                'full': full_hiragana,
                'family': full_hiragana,
                'given': full_hiragana
            }

        parts = romanized_name.split(' ', 1)
        given_romaji = parts[0]
        family_romaji = parts[1] if len(parts) > 1 else ''

        given_hiragana = jaconv.alphabet2kana(given_romaji.lower())
        family_hiragana = jaconv.alphabet2kana(family_romaji.lower()) if family_romaji else ''

        full_hiragana = family_hiragana + given_hiragana

        return {
            'has_space': True,
            'original': romanized_name,
            'full': full_hiragana,
            'family': family_hiragana,
            'given': given_hiragana
        }

    def generate_kana_readings(self, name_original: str) -> Dict[str, str | bool]:
        if not name_original:
            return {
                'has_space': False,
                'original': '',
                'full': '',
                'family': '',
                'given': ''
            }

        full_hiragana = jaconv.kata2hira(name_original.replace(' ', ''))

        if ' ' not in name_original:
            return {
                'has_space': False,
                'original': name_original,
                'full': full_hiragana,
                'family': full_hiragana,
                'given': full_hiragana
            }

        parts = name_original.split(' ', 1)
        family_kana = parts[0]
        given_kana = parts[1] if len(parts) > 1 else ''

        family_hiragana = jaconv.kata2hira(family_kana)
        given_hiragana = jaconv.kata2hira(given_kana) if given_kana else ''

        return {
            'has_space': True,
            'original': name_original,
            'full': full_hiragana,
            'family': family_hiragana,
            'given': given_hiragana
        }

    def generate_mixed_name_readings(self, name_original: str, romanized_name: str) -> Dict[str, str | bool]:
        if not name_original:
            return {
                'has_space': False,
                'original': '',
                'full': '',
                'family': '',
                'given': ''
            }

        jp_parts = self.split_japanese_name(name_original)

        if not jp_parts['has_space']:
            if self.contains_kanji(name_original):
                full_hiragana = jaconv.alphabet2kana(romanized_name.lower())
                return {
                    'has_space': False,
                    'original': name_original,
                    'full': full_hiragana,
                    'family': full_hiragana,
                    'given': full_hiragana
                }
            else:
                return self.generate_kana_readings(name_original)

        family_jp = jp_parts['family'] or ''
        given_jp = jp_parts['given'] or ''

        family_has_kanji = self.contains_kanji(family_jp) if family_jp else False
        given_has_kanji = self.contains_kanji(given_jp) if given_jp else False

        romanized_parts = romanized_name.split(' ', 1) if romanized_name else ['', '']
        given_romaji = romanized_parts[0] if romanized_parts else ''
        family_romaji = romanized_parts[1] if len(romanized_parts) > 1 else ''

        if family_has_kanji:
            family_reading = jaconv.alphabet2kana(given_romaji.lower()) if given_romaji else ''
        else:
            family_reading = jaconv.kata2hira(family_jp) if family_jp else ''

        if given_has_kanji:
            given_reading = jaconv.alphabet2kana(family_romaji.lower()) if family_romaji else ''
        else:
            given_reading = jaconv.kata2hira(given_jp) if given_jp else ''

        full_reading = family_reading + given_reading

        return {
            'has_space': True,
            'original': name_original,
            'full': full_reading,
            'family': family_reading,
            'given': given_reading
        }
