#!/usr/bin/env python3
"""
Build a Yomitan dictionary from VNDB character data.

Features:
- Fetches all Japanese visual novels from VNDB
- Fetches characters for each VN
- Respects API rate limits (800 requests/hour ~= 4.5s between requests)
- Supports resume/restart functionality via state file
- Generates Yomitan-compatible dictionary ZIP

Usage:
    python build_vndb_yomitan_dict.py [--resume] [--max-vns N] [--output path]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from GameSentenceMiner.util.vndb_api_client import VNDBAPIClient
from GameSentenceMiner.util.yomitan_dict import YomitanDictBuilder


class VNDBDictionaryBuilder:
    """Builds Yomitan dictionary from VNDB with resumability."""

    def __init__(
        self,
        output_path: str = "./vndb_yomitan_dict.zip",
        state_file: str = "./vndb_dict_state.json",
        download_images: bool = True,
        spoiler_level: int = 0
    ):
        """
        Initialize dictionary builder.

        Args:
            output_path: Path for final dictionary ZIP
            state_file: Path to state file for resuming
            download_images: Whether to download character images
            spoiler_level: Maximum spoiler level (0=None, 1=Minor, 2=Major)
        """
        self.output_path = output_path
        self.state_file = state_file
        self.download_images = download_images
        self.spoiler_level = spoiler_level

        self.api_client = VNDBAPIClient()
        self.dict_builder = YomitanDictBuilder(
            dict_name="VNDB Visual Novel Characters (Japanese)",
            dict_revision=datetime.now().strftime("%Y-%m-%d"),
            author="GameSentenceMiner",
            description="Character dictionary from Japanese visual novels on VNDB",
            spoiler_level=spoiler_level
        )

        self.state = {
            "vn_ids": [],
            "current_vn_index": 0,
            "vns_processed": 0,
            "characters_added": 0,
            "terms_added": 0,
            "started_at": None,
            "last_updated_at": None,
            "completed": False
        }

    def load_state(self) -> bool:
        """
        Load state from file.

        Returns:
            True if state loaded, False if no state file exists
        """
        if not os.path.exists(self.state_file):
            return False

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                self.state = json.load(f)

            if self.state.get("completed"):
                print("Previous run was completed. Use --force to start fresh.")
                return True

            print(f"Loaded state: {self.state['vns_processed']} VNs processed, "
                  f"{self.state['characters_added']} characters, "
                  f"{self.state['terms_added']} terms")
            return True
        except Exception as e:
            print(f"Error loading state: {e}")
            return False

    def save_state(self):
        """Save current state to file."""
        self.state["last_updated_at"] = datetime.now().isoformat()

        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            print(f"State saved: {self.state['vns_processed']} VNs processed")
        except Exception as e:
            print(f"Error saving state: {e}")

    def fetch_vn_ids(self, max_vns: Optional[int] = None):
        """
        Fetch all VN IDs and save to state.

        Args:
            max_vns: Maximum number of VN IDs to fetch (None for all)
        """
        print("Fetching VN IDs from VNDB...")
        print("This may take a while due to rate limiting.")
        print("")

        vn_ids = []
        count = 0

        for vn_id in self.api_client.get_all_vn_ids(
            filters=["olang", "=", "ja"],
            start_page=1,
            max_vns=max_vns
        ):
            vn_ids.append(vn_id)
            count += 1

            if count % 100 == 0:
                print(f"Fetched {count} VN IDs...")

        self.state["vn_ids"] = vn_ids
        print(f"\nTotal VN IDs fetched: {len(vn_ids)}")
        self.save_state()

    def build_dictionary(
        self,
        resume: bool = False,
        max_vns: Optional[int] = None,
        force: bool = False
    ):
        """
        Build the Yomitan dictionary.

        Args:
            resume: Whether to resume from saved state
            max_vns: Maximum number of VNs to process (None for all)
            force: Force rebuild even if completed
        """
        # Load or initialize state
        if resume and self.load_state():
            if self.state.get("completed") and not force:
                print("Dictionary build was already completed.")
                print("Use --force to rebuild from scratch.")
                return False

            if not self.state.get("vn_ids"):
                print("No VN IDs found in state. Fetching...")
                self.fetch_vn_ids(max_vns)

            print("Resuming from previous state...")
        else:
            print("Starting fresh build...")
            self.state["started_at"] = datetime.now().isoformat()

            # Fetch VN IDs
            self.fetch_vn_ids(max_vns)

        # Process VNs
        vn_ids = self.state["vn_ids"]
        start_index = self.state["current_vn_index"]
        total_vns = len(vn_ids)

        if max_vns:
            vn_ids = vn_ids[:max_vns]
            total_vns = min(total_vns, max_vns)

        print(f"\nProcessing VNs: {start_index + 1} to {total_vns}")
        print(f"Rate limit: {self.api_client.MIN_REQUEST_INTERVAL}s between API requests")
        print("Press Ctrl+C to stop and save progress\n")

        try:
            for i in range(start_index, total_vns):
                vn_id = vn_ids[i]

                print(f"[{i + 1}/{total_vns}] Processing {vn_id}...")

                try:
                    # Fetch VN metadata
                    vn_metadata = self.api_client.fetch_vn_metadata(vn_id)
                    game_title = vn_metadata.get("title", vn_id)

                    # Fetch characters
                    characters = self.api_client.process_vn_characters(
                        vn_id,
                        download_images=self.download_images
                    )

                    if characters:
                        # Add to dictionary
                        stats = self.dict_builder.add_game_characters(characters, game_title)

                        self.state["characters_added"] += stats["characters"]
                        self.state["terms_added"] += stats["terms"]

                        print(f"  Added {stats['characters']} characters, {stats['terms']} terms")
                    else:
                        print(f"  No characters found")

                except Exception as e:
                    print(f"  Error processing {vn_id}: {e}")
                    # Continue to next VN

                # Update state
                self.state["current_vn_index"] = i + 1
                self.state["vns_processed"] += 1

                # Save state every 10 VNs
                if (i + 1) % 10 == 0:
                    self.save_state()

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Saving progress...")
            self.save_state()
            print("Progress saved. You can resume with --resume flag.")
            return False

        except Exception as e:
            print(f"\n\nError during processing: {e}")
            self.save_state()
            print("Progress saved. You can resume with --resume flag.")
            raise

        # Mark as completed
        self.state["completed"] = True
        self.save_state()

        print("\n" + "=" * 60)
        print("Processing complete!")
        print(f"VNs processed: {self.state['vns_processed']}")
        print(f"Characters added: {self.state['characters_added']}")
        print(f"Terms added: {self.state['terms_added']}")
        print(f"API requests: {self.api_client.request_count}")
        print("=" * 60 + "\n")

        return True

    def export_dictionary(self):
        """Export the dictionary to ZIP file."""
        stats = self.dict_builder.get_stats()
        print(f"\nDictionary statistics:")
        print(f"  Characters: {stats['characters']}")
        print(f"  Total terms: {stats['terms']}")
        print(f"  Unique terms: {stats['unique_terms']}")
        print(f"  Images: {stats['images']}")

        print(f"\nExporting dictionary to: {self.output_path}")
        self.dict_builder.export(self.output_path)

        print("\nDictionary generation complete!")
        print(f"Import {self.output_path} into Yomitan to use it.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build a Yomitan dictionary from VNDB character data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start fresh build (fetch all Japanese VNs)
  python build_vndb_yomitan_dict.py

  # Resume from previous state
  python build_vndb_yomitan_dict.py --resume

  # Build dictionary from first 100 VNs only
  python build_vndb_yomitan_dict.py --max-vns 100

  # Skip image downloads (faster)
  python build_vndb_yomitan_dict.py --no-images

  # Include minor spoilers
  python build_vndb_yomitan_dict.py --spoiler-level 1
        """
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous state"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild even if previous run completed"
    )

    parser.add_argument(
        "--max-vns",
        type=int,
        default=None,
        help="Maximum number of VNs to process (default: all)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./vndb_yomitan_dict.zip",
        help="Output ZIP file path (default: ./vndb_yomitan_dict.zip)"
    )

    parser.add_argument(
        "--state-file",
        type=str,
        default="./vndb_dict_state.json",
        help="State file path (default: ./vndb_dict_state.json)"
    )

    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip downloading character images (faster)"
    )

    parser.add_argument(
        "--spoiler-level",
        type=int,
        choices=[0, 1, 2],
        default=0,
        help="Maximum spoiler level: 0=None, 1=Minor, 2=Major (default: 0)"
    )

    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Skip fetching, only export dictionary from saved state"
    )

    args = parser.parse_args()

    # Create builder
    builder = VNDBDictionaryBuilder(
        output_path=args.output,
        state_file=args.state_file,
        download_images=not args.no_images,
        spoiler_level=args.spoiler_level
    )

    # Build dictionary
    if not args.export_only:
        success = builder.build_dictionary(
            resume=args.resume,
            max_vns=args.max_vns,
            force=args.force
        )

        if not success:
            sys.exit(1)
    else:
        print("Skipping fetch, exporting from saved state...")
        if not builder.load_state():
            print("Error: No saved state found. Cannot export.")
            sys.exit(1)

    # Export dictionary
    builder.export_dictionary()


if __name__ == "__main__":
    main()
