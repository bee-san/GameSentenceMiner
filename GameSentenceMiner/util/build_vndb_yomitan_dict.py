#!/usr/bin/env python3
"""
Build a Yomitan dictionary from VNDB data.

Features:
- Fetches Japanese visual novels from VNDB
- Respects API rate limits (800 requests/hour)
- Supports resume/restart functionality
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

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GameSentenceMiner.util.vndb_api_client import VNDBAPIClient
from GameSentenceMiner.util.yomitan_dict_generator import YomitanDictGenerator


class VNDBDictionaryBuilder:
    """Builds Yomitan dictionary from VNDB with resumability."""

    def __init__(
        self,
        output_dir: str = "./vndb_yomitan_dict",
        state_file: str = "./vndb_dict_state.json",
        checkpoint_interval: int = 100
    ):
        """
        Initialize dictionary builder.

        Args:
            output_dir: Directory for dictionary files
            state_file: Path to state file for resuming
            checkpoint_interval: Save state every N VNs
        """
        self.output_dir = output_dir
        self.state_file = state_file
        self.checkpoint_interval = checkpoint_interval

        self.api_client = VNDBAPIClient()
        self.dict_generator = YomitanDictGenerator(
            dict_name="VNDB Visual Novels (Japanese)",
            dict_revision=datetime.now().strftime("%Y-%m-%d"),
            author="GameSentenceMiner",
            description="Japanese visual novel database from VNDB for sentence mining"
        )

        self.state = {
            "last_page": 1,
            "total_vns_fetched": 0,
            "total_vns_added": 0,
            "last_vn_id": None,
            "started_at": None,
            "last_updated_at": None
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
            print(f"Loaded state: Page {self.state['last_page']}, "
                  f"{self.state['total_vns_fetched']} VNs fetched, "
                  f"{self.state['total_vns_added']} VNs added to dictionary")
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
            print(f"State saved: Page {self.state['last_page']}, "
                  f"{self.state['total_vns_fetched']} VNs fetched")
        except Exception as e:
            print(f"Error saving state: {e}")

    def save_checkpoint(self, vns_batch: list):
        """
        Save a checkpoint with accumulated VN data.

        Args:
            vns_batch: List of VNs to save
        """
        checkpoint_file = os.path.join(self.output_dir, f"checkpoint_{self.state['last_page']}.json")
        os.makedirs(self.output_dir, exist_ok=True)

        try:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(vns_batch, f, ensure_ascii=False)
            print(f"Checkpoint saved: {checkpoint_file}")
        except Exception as e:
            print(f"Error saving checkpoint: {e}")

    def load_checkpoints(self):
        """Load all checkpoint files into the dictionary generator."""
        if not os.path.exists(self.output_dir):
            return

        checkpoint_files = sorted([
            f for f in os.listdir(self.output_dir)
            if f.startswith("checkpoint_") and f.endswith(".json")
        ])

        for checkpoint_file in checkpoint_files:
            checkpoint_path = os.path.join(self.output_dir, checkpoint_file)
            try:
                with open(checkpoint_path, "r", encoding="utf-8") as f:
                    vns_batch = json.load(f)
                added = self.dict_generator.add_vns(vns_batch)
                print(f"Loaded checkpoint {checkpoint_file}: {added} VNs added")
            except Exception as e:
                print(f"Error loading checkpoint {checkpoint_file}: {e}")

    def build_dictionary(
        self,
        resume: bool = False,
        max_vns: Optional[int] = None
    ):
        """
        Build the Yomitan dictionary.

        Args:
            resume: Whether to resume from saved state
            max_vns: Maximum number of VNs to fetch (None for all)
        """
        # Initialize state
        if resume and self.load_state():
            print("Resuming from previous state...")
            self.load_checkpoints()
            start_page = self.state["last_page"] + 1
        else:
            print("Starting fresh build...")
            start_page = 1
            self.state["started_at"] = datetime.now().isoformat()

        # Fetch VNs
        vns_batch = []

        try:
            print(f"\nFetching Japanese VNs from VNDB (starting at page {start_page})...")
            print(f"Rate limit: {self.api_client.MIN_REQUEST_INTERVAL}s between requests")
            print(f"Estimated time per page: ~{self.api_client.MIN_REQUEST_INTERVAL}s")
            print("Press Ctrl+C to stop and save progress\n")

            for vn in self.api_client.get_all_japanese_vns(
                fields=["id", "title", "alttitle", "titles", "description", "released", "languages", "olang"],
                start_page=start_page,
                max_vns=max_vns
            ):
                self.state["total_vns_fetched"] += 1
                self.state["last_vn_id"] = vn.get("id")

                # Add to batch
                vns_batch.append(vn)

                # Add to dictionary
                if self.dict_generator.add_vn(vn):
                    self.state["total_vns_added"] += 1

                # Checkpoint every N VNs
                if len(vns_batch) >= self.checkpoint_interval:
                    self.save_checkpoint(vns_batch)
                    vns_batch = []
                    self.state["last_page"] = start_page + (self.state["total_vns_fetched"] // 100)
                    self.save_state()

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Saving progress...")
            if vns_batch:
                self.save_checkpoint(vns_batch)
            self.save_state()
            print("Progress saved. You can resume with --resume flag.")
            return False

        except Exception as e:
            print(f"\n\nError during fetch: {e}")
            if vns_batch:
                self.save_checkpoint(vns_batch)
            self.save_state()
            print("Progress saved. You can resume with --resume flag.")
            raise

        # Save any remaining VNs
        if vns_batch:
            self.save_checkpoint(vns_batch)

        # Final state save
        self.save_state()

        print("\n" + "=" * 60)
        print(f"Fetch complete!")
        print(f"Total VNs fetched: {self.state['total_vns_fetched']}")
        print(f"Total VNs added to dictionary: {self.state['total_vns_added']}")
        print(f"API requests made: {self.api_client.request_count}")
        print("=" * 60 + "\n")

        return True

    def generate_output(self, output_format: str = "zip"):
        """
        Generate final dictionary output.

        Args:
            output_format: "zip" or "directory"
        """
        stats = self.dict_generator.get_stats()
        print(f"\nDictionary statistics:")
        print(f"  Total terms: {stats['total_terms']}")
        print(f"  Unique terms: {stats['unique_terms']}")

        if output_format == "zip":
            output_path = self.output_dir.rstrip("/") + ".zip"
            print(f"\nGenerating Yomitan dictionary ZIP: {output_path}")
            self.dict_generator.save_to_zip(output_path)
        else:
            print(f"\nGenerating Yomitan dictionary directory: {self.output_dir}")
            self.dict_generator.save_to_directory(self.output_dir)

        print("\nDictionary generation complete!")
        print(f"Import this into Yomitan to use it for sentence mining.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build a Yomitan dictionary from VNDB",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous state"
    )

    parser.add_argument(
        "--max-vns",
        type=int,
        default=None,
        help="Maximum number of VNs to fetch (default: all)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./vndb_yomitan_dict",
        help="Output directory/file path (default: ./vndb_yomitan_dict)"
    )

    parser.add_argument(
        "--state-file",
        type=str,
        default="./vndb_dict_state.json",
        help="State file path (default: ./vndb_dict_state.json)"
    )

    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=100,
        help="Save checkpoint every N VNs (default: 100)"
    )

    parser.add_argument(
        "--format",
        choices=["zip", "directory"],
        default="zip",
        help="Output format (default: zip)"
    )

    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip fetching, only generate dictionary from checkpoints"
    )

    args = parser.parse_args()

    # Create builder
    builder = VNDBDictionaryBuilder(
        output_dir=args.output,
        state_file=args.state_file,
        checkpoint_interval=args.checkpoint_interval
    )

    # Build dictionary
    if not args.skip_fetch:
        success = builder.build_dictionary(
            resume=args.resume,
            max_vns=args.max_vns
        )

        if not success:
            sys.exit(1)
    else:
        print("Skipping fetch, loading from checkpoints...")
        builder.load_checkpoints()

    # Generate output
    builder.generate_output(output_format=args.format)


if __name__ == "__main__":
    main()
