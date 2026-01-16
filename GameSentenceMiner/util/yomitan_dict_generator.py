"""
Yomitan Dictionary Generator for VNDB data.

Converts VNDB visual novel data into Yomitan dictionary format.
"""

import json
import os
import zipfile
from typing import Dict, List, Any, Optional
from datetime import datetime


class YomitanDictGenerator:
    """Generator for Yomitan dictionary format."""

    def __init__(
        self,
        dict_name: str = "VNDB Visual Novels",
        dict_revision: str = None,
        author: str = "GameSentenceMiner",
        description: str = "Visual novel database from VNDB"
    ):
        """
        Initialize Yomitan dictionary generator.

        Args:
            dict_name: Name of the dictionary
            dict_revision: Revision/version (defaults to current date)
            author: Author name
            description: Dictionary description
        """
        self.dict_name = dict_name
        self.dict_revision = dict_revision or datetime.now().strftime("%Y-%m-%d")
        self.author = author
        self.description = description

        self.terms: List[List[Any]] = []
        self.tags: Dict[str, Any] = {}

    def _clean_text(self, text: Optional[str]) -> str:
        """Clean text for dictionary entry."""
        if not text:
            return ""

        # Remove excessive whitespace
        text = " ".join(text.split())
        return text

    def _extract_japanese_title(self, vn: Dict[str, Any]) -> Optional[str]:
        """
        Extract Japanese title from VN data.

        Args:
            vn: Visual novel data from VNDB

        Returns:
            Japanese title or None
        """
        # Try to get title from titles array
        titles = vn.get("titles", [])
        for title_obj in titles:
            if title_obj.get("lang") == "ja":
                return title_obj.get("title")

        # Fallback to main title if it's Japanese
        if vn.get("olang") == "ja":
            return vn.get("title")

        return None

    def _format_vn_entry(self, vn: Dict[str, Any]) -> Optional[List[Any]]:
        """
        Format a VN entry into Yomitan term format.

        Yomitan term format:
        [term, reading, definition_tags, rules, score, [definitions], sequence, term_tags]

        Args:
            vn: Visual novel data from VNDB

        Returns:
            Term entry or None if no Japanese title
        """
        japanese_title = self._extract_japanese_title(vn)

        if not japanese_title:
            return None

        # Get alternative titles for reading
        reading = ""
        titles = vn.get("titles", [])
        for title_obj in titles:
            lang = title_obj.get("lang")
            if lang in ["en", "ro"]:  # English or romanized
                reading = title_obj.get("title", "")
                break

        # Build definition
        definition_parts = []

        # Add English title if available
        title = vn.get("title", "")
        if title and title != japanese_title:
            definition_parts.append(f"**{title}**")

        # Add VNDB ID
        vn_id = vn.get("id", "")
        if vn_id:
            definition_parts.append(f"VNDB: [{vn_id}](https://vndb.org/{vn_id})")

        # Add release date
        released = vn.get("released")
        if released:
            definition_parts.append(f"Released: {released}")

        # Add languages
        languages = vn.get("languages", [])
        if languages:
            lang_str = ", ".join(languages)
            definition_parts.append(f"Languages: {lang_str}")

        # Add description
        description = self._clean_text(vn.get("description"))
        if description:
            # Truncate if too long
            if len(description) > 500:
                description = description[:497] + "..."
            definition_parts.append(f"\n{description}")

        # Combine definition
        full_definition = "\n".join(definition_parts)

        # Term format: [term, reading, definition_tags, rules, score, [definitions], sequence, term_tags]
        term_entry = [
            japanese_title,           # term
            reading,                  # reading
            "vndb",                   # definition_tags
            "",                       # rules
            0,                        # score
            [full_definition],        # definitions
            int(vn_id[1:]) if vn_id.startswith("v") else 0,  # sequence (numeric ID)
            "visual-novel"            # term_tags
        ]

        return term_entry

    def add_vn(self, vn: Dict[str, Any]) -> bool:
        """
        Add a visual novel to the dictionary.

        Args:
            vn: Visual novel data from VNDB

        Returns:
            True if added, False if skipped
        """
        term_entry = self._format_vn_entry(vn)

        if term_entry:
            self.terms.append(term_entry)
            return True

        return False

    def add_vns(self, vns: List[Dict[str, Any]]) -> int:
        """
        Add multiple visual novels to the dictionary.

        Args:
            vns: List of visual novel data from VNDB

        Returns:
            Number of VNs added
        """
        added = 0
        for vn in vns:
            if self.add_vn(vn):
                added += 1
        return added

    def _create_index(self) -> Dict[str, Any]:
        """Create index.json content."""
        return {
            "title": self.dict_name,
            "revision": self.dict_revision,
            "sequenced": True,
            "format": 3,
            "author": self.author,
            "url": "https://vndb.org",
            "description": self.description,
            "attribution": "Data from VNDB (https://vndb.org)",
        }

    def _create_tag_bank(self) -> List[List[Any]]:
        """Create tag bank content."""
        return [
            ["vndb", "freq", 0, "VNDB Entry", 0],
            ["visual-novel", "partOfSpeech", 0, "Visual Novel", 0]
        ]

    def save_to_directory(self, output_dir: str, terms_per_file: int = 10000):
        """
        Save dictionary files to a directory.

        Args:
            output_dir: Output directory path
            terms_per_file: Number of terms per term bank file
        """
        os.makedirs(output_dir, exist_ok=True)

        # Save index.json
        index_path = os.path.join(output_dir, "index.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(self._create_index(), f, ensure_ascii=False, indent=2)

        # Save tag_bank_1.json
        tag_bank_path = os.path.join(output_dir, "tag_bank_1.json")
        with open(tag_bank_path, "w", encoding="utf-8") as f:
            json.dump(self._create_tag_bank(), f, ensure_ascii=False)

        # Save term banks
        total_terms = len(self.terms)
        num_files = (total_terms + terms_per_file - 1) // terms_per_file

        for i in range(num_files):
            start_idx = i * terms_per_file
            end_idx = min((i + 1) * terms_per_file, total_terms)
            terms_subset = self.terms[start_idx:end_idx]

            term_bank_path = os.path.join(output_dir, f"term_bank_{i + 1}.json")
            with open(term_bank_path, "w", encoding="utf-8") as f:
                json.dump(terms_subset, f, ensure_ascii=False)

            print(f"Saved {len(terms_subset)} terms to term_bank_{i + 1}.json")

        print(f"Dictionary saved to {output_dir}")
        print(f"Total terms: {total_terms}")
        print(f"Total files: {num_files + 2} (1 index, 1 tag bank, {num_files} term banks)")

    def save_to_zip(self, output_path: str, terms_per_file: int = 10000):
        """
        Save dictionary as a ZIP file (Yomitan format).

        Args:
            output_path: Output ZIP file path
            terms_per_file: Number of terms per term bank file
        """
        # Create temporary directory for files
        temp_dir = output_path.replace(".zip", "_temp")
        self.save_to_directory(temp_dir, terms_per_file)

        # Create ZIP file
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)

        # Clean up temporary directory
        import shutil
        shutil.rmtree(temp_dir)

        print(f"Dictionary ZIP saved to {output_path}")

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the dictionary."""
        return {
            "total_terms": len(self.terms),
            "unique_terms": len(set(term[0] for term in self.terms))
        }
