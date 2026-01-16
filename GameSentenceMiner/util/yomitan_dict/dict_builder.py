"""Yomitan dictionary builder for VNDB character data."""

import json
import os
import zipfile
from io import BytesIO
from typing import Dict, List, Optional
from datetime import datetime

from .name_parser import NameParser
from .image_handler import ImageHandler
from .content_builder import ContentBuilder


class YomitanDictBuilder:
    """
    Builds Yomitan-compatible dictionaries from VNDB character data.

    This class orchestrates:
    - Name parsing and reading generation
    - Image handling
    - Structured content creation
    - Term entry generation (with variants)
    - ZIP export with proper Yomitan format
    """

    # Role-based score mapping (higher = more important)
    ROLE_SCORES = {
        "main": 100,
        "primary": 75,
        "side": 50,
        "appears": 25,
    }

    def __init__(
        self,
        dict_name: str = "VNDB Visual Novel Characters",
        dict_revision: str = None,
        author: str = "GameSentenceMiner",
        description: str = "Character dictionary from VNDB",
        spoiler_level: int = 0,
        download_url: Optional[str] = None
    ):
        """
        Initialize the dictionary builder.

        Args:
            dict_name: Name of the dictionary
            dict_revision: Revision/version (defaults to current date)
            author: Author name
            description: Dictionary description
            spoiler_level: Maximum spoiler level (0=None, 1=Minor, 2=Major)
            download_url: Optional URL for Yomitan auto-update
        """
        self.dict_name = dict_name
        self.dict_revision = dict_revision or datetime.now().strftime("%Y-%m-%d")
        self.author = author
        self.description = description
        self.download_url = download_url

        self.name_parser = NameParser()
        self.image_handler = ImageHandler()
        self.content_builder = ContentBuilder(spoiler_level=spoiler_level)

        self.terms: List[List] = []
        self.images: Dict[str, bytes] = {}  # filename -> image bytes
        self.character_count = 0

    def _get_role_score(self, role: str) -> int:
        """Get the priority score for a character role."""
        return self.ROLE_SCORES.get(role, 0)

    def add_character(self, char: dict, game_title: str) -> int:
        """
        Add a character to the dictionary, generating multiple searchable terms.

        Creates term entries for:
        - Full name (combined)
        - Family name (if name has space)
        - Given name (if name has space)
        - Honorific variants (さん, 様, etc.)

        Args:
            char: Character data dictionary with fields:
                - id: Character ID
                - name: Romanized name
                - name_original: Japanese name
                - role: main/primary/side/appears
                - image_base64: Base64 image (optional)
                - ... other character fields
            game_title: Name of the VN

        Returns:
            Number of term entries created
        """
        name_original = char.get("name_original", "")
        name_romaji = char.get("name", "")
        role = char.get("role", "appears")
        char_id = char.get("id", "")

        if not name_original:
            return 0

        # Get role-based score
        base_score = self._get_role_score(role)

        # Process image if available
        image_path = None
        image_base64 = char.get("image_base64")
        if image_base64 and self.image_handler.validate_image(image_base64):
            try:
                filename, image_bytes = self.image_handler.decode_image(image_base64, str(char_id))
                self.images[filename] = image_bytes
                image_path = f"img/{filename}"
            except Exception as e:
                print(f"Error processing image for character {char_id}: {e}")

        # Build structured content
        structured_content = self.content_builder.build_structured_content(
            char, image_path, game_title
        )

        # Parse name and generate readings
        name_parts = self.name_parser.split_japanese_name(name_original)
        has_space = name_parts['has_space']

        # Determine reading generation method
        has_kanji = self.name_parser.contains_kanji(name_original)

        if has_kanji and name_romaji:
            # Mixed name: use mixed reading generation
            readings = self.name_parser.generate_mixed_name_readings(name_original, name_romaji)
        elif has_kanji and not name_romaji:
            # Kanji without romaji: can't generate readings reliably
            readings = {
                'full': '',
                'family': '',
                'given': '',
                'has_space': has_space
            }
        elif name_romaji:
            # No kanji, have romaji: convert romaji to hiragana
            readings = self.name_parser.split_romanized_name_to_hiragana(name_romaji)
        else:
            # Pure kana: convert to hiragana
            readings = self.name_parser.generate_kana_readings(name_original)

        terms_added = 0

        # 1. Add full name (combined) - highest priority
        full_reading = readings.get('full', '')
        full_term = name_parts['combined']
        if full_term:
            term_entry = self.content_builder.create_term_entry(
                full_term, full_reading, role, base_score, structured_content
            )
            self.terms.append(term_entry)
            terms_added += 1

        # 2. Add family and given name entries (if name has space)
        if has_space:
            family_name = name_parts.get('family')
            given_name = name_parts.get('given')
            family_reading = readings.get('family', '')
            given_reading = readings.get('given', '')

            if family_name:
                # Family name - slightly lower priority
                term_entry = self.content_builder.create_term_entry(
                    family_name, family_reading, role, base_score - 5, structured_content
                )
                self.terms.append(term_entry)
                terms_added += 1

            if given_name:
                # Given name - even lower priority
                term_entry = self.content_builder.create_term_entry(
                    given_name, given_reading, role, base_score - 10, structured_content
                )
                self.terms.append(term_entry)
                terms_added += 1

        # 3. Add honorific variants
        for suffix, suffix_reading in self.name_parser.HONORIFIC_SUFFIXES:
            honorific_term = full_term + suffix
            honorific_reading = full_reading + suffix_reading

            term_entry = self.content_builder.create_term_entry(
                honorific_term, honorific_reading, role, base_score - 15, structured_content
            )
            self.terms.append(term_entry)
            terms_added += 1

            # Also add honorific variants for family/given if space exists
            if has_space:
                family_name = name_parts.get('family')
                given_name = name_parts.get('given')
                family_reading = readings.get('family', '')
                given_reading = readings.get('given', '')

                if family_name:
                    family_honorific = family_name + suffix
                    family_honorific_reading = family_reading + suffix_reading
                    term_entry = self.content_builder.create_term_entry(
                        family_honorific, family_honorific_reading, role,
                        base_score - 20, structured_content
                    )
                    self.terms.append(term_entry)
                    terms_added += 1

                if given_name:
                    given_honorific = given_name + suffix
                    given_honorific_reading = given_reading + suffix_reading
                    term_entry = self.content_builder.create_term_entry(
                        given_honorific, given_honorific_reading, role,
                        base_score - 20, structured_content
                    )
                    self.terms.append(term_entry)
                    terms_added += 1

        self.character_count += 1
        return terms_added

    def add_game_characters(self, characters: List[dict], game_title: str) -> Dict[str, int]:
        """
        Add all characters from a game.

        Args:
            characters: List of character dictionaries
            game_title: Name of the VN

        Returns:
            Dictionary with stats: {'characters': N, 'terms': M}
        """
        chars_added = 0
        terms_added = 0

        for char in characters:
            count = self.add_character(char, game_title)
            if count > 0:
                chars_added += 1
                terms_added += count

        return {
            'characters': chars_added,
            'terms': terms_added
        }

    def _create_index(self) -> dict:
        """Create index.json content."""
        index = {
            "title": self.dict_name,
            "revision": self.dict_revision,
            "sequenced": True,
            "format": 3,
            "author": self.author,
            "url": "https://vndb.org",
            "description": self.description,
            "attribution": "Data from VNDB (https://vndb.org)",
        }

        if self.download_url:
            index["downloadUrl"] = self.download_url

        return index

    def _create_tag_bank(self) -> List[List]:
        """Create tag bank content."""
        return [
            ["name", "partOfSpeech", 0, "Character Name", 0],
            ["main", "partOfSpeech", 0, "Protagonist", 0],
            ["primary", "partOfSpeech", 0, "Main Character", 0],
            ["side", "partOfSpeech", 0, "Side Character", 0],
            ["appears", "partOfSpeech", 0, "Minor Role", 0],
        ]

    def export_bytes(self, terms_per_file: int = 10000) -> bytes:
        """
        Export dictionary as ZIP file in memory.

        Args:
            terms_per_file: Number of terms per term bank file

        Returns:
            ZIP file as bytes
        """
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add index.json
            index_data = json.dumps(self._create_index(), ensure_ascii=False, indent=2)
            zipf.writestr("index.json", index_data)

            # Add tag_bank_1.json
            tag_bank_data = json.dumps(self._create_tag_bank(), ensure_ascii=False)
            zipf.writestr("tag_bank_1.json", tag_bank_data)

            # Add term banks (chunked)
            total_terms = len(self.terms)
            num_files = (total_terms + terms_per_file - 1) // terms_per_file

            for i in range(num_files):
                start_idx = i * terms_per_file
                end_idx = min((i + 1) * terms_per_file, total_terms)
                terms_subset = self.terms[start_idx:end_idx]

                term_bank_data = json.dumps(terms_subset, ensure_ascii=False)
                zipf.writestr(f"term_bank_{i + 1}.json", term_bank_data)

            # Add images
            for filename, image_bytes in self.images.items():
                zipf.writestr(f"img/{filename}", image_bytes)

        zip_buffer.seek(0)
        return zip_buffer.read()

    def export(self, output_path: str, terms_per_file: int = 10000):
        """
        Export dictionary as ZIP file.

        Args:
            output_path: Path to save ZIP file
            terms_per_file: Number of terms per term bank file
        """
        zip_bytes = self.export_bytes(terms_per_file)

        with open(output_path, 'wb') as f:
            f.write(zip_bytes)

        print(f"Dictionary exported to: {output_path}")
        print(f"  Characters: {self.character_count}")
        print(f"  Terms: {len(self.terms)}")
        print(f"  Images: {len(self.images)}")
        print(f"  Term banks: {(len(self.terms) + terms_per_file - 1) // terms_per_file}")

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the dictionary."""
        return {
            "characters": self.character_count,
            "terms": len(self.terms),
            "images": len(self.images),
            "unique_terms": len(set(term[0] for term in self.terms))
        }
