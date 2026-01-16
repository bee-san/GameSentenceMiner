"""
VNDB API Client for fetching visual novel and character data.

Uses VNDB API v2 with rate limiting and error handling.
Rate limit: 800 requests per hour (~4.5 seconds between requests)
"""

import base64
import json
import time
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any
from io import BytesIO


class VNDBAPIClient:
    """Client for interacting with VNDB API v2."""

    BASE_URL = "https://api.vndb.org/kana"
    USER_AGENT = "GameSentenceMiner/1.0"

    # Rate limiting: 800 requests per hour = 1 request per 4.5 seconds
    MIN_REQUEST_INTERVAL = 4.5

    def __init__(self, min_request_interval: float = MIN_REQUEST_INTERVAL):
        """
        Initialize VNDB API client.

        Args:
            min_request_interval: Minimum seconds between requests (default: 4.5)
        """
        self.min_request_interval = min_request_interval
        self.last_request_time = 0
        self.request_count = 0

    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limiting."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to VNDB API.

        Args:
            endpoint: API endpoint (e.g., "vn", "character")
            payload: JSON payload for the request

        Returns:
            Response data as dictionary

        Raises:
            urllib.error.HTTPError: If request fails
        """
        self._wait_for_rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': self.USER_AGENT
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                self.request_count += 1
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"HTTP Error {e.code}: {error_body}")
            raise
        except Exception as e:
            print(f"Request error: {e}")
            raise

    def get_all_vn_ids(
        self,
        filters: Optional[List] = None,
        start_page: int = 1,
        max_vns: Optional[int] = None
    ):
        """
        Get all VN IDs with pagination (generator).

        Args:
            filters: VNDB filter expression (e.g., ["olang", "=", "ja"])
            start_page: Page to start from (for resuming)
            max_vns: Maximum number of VNs to fetch (None for all)

        Yields:
            VN ID strings (e.g., "v17")
        """
        if filters is None:
            filters = ["olang", "=", "ja"]

        page = start_page
        total_fetched = 0

        while True:
            payload = {
                "filters": filters,
                "fields": "id, title",
                "sort": "id",
                "reverse": False,
                "results": 100,
                "page": page
            }

            try:
                result = self._make_request("vn", payload)
                vns = result.get("results", [])
                has_more = result.get("more", False)

                if not vns:
                    break

                for vn in vns:
                    vn_id = vn.get("id")
                    if vn_id:
                        yield vn_id
                        total_fetched += 1

                        if max_vns and total_fetched >= max_vns:
                            return

                if not has_more:
                    break

                page += 1

            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                raise

    def fetch_vn_metadata(self, vn_id: str) -> Dict[str, Any]:
        """
        Get comprehensive VN metadata.

        Args:
            vn_id: VNDB ID (e.g., "v17")

        Returns:
            Visual novel data with title, description, tags, etc.
        """
        payload = {
            "filters": ["id", "=", vn_id],
            "fields": "id, title, alttitle, titles, description, released, languages, olang, tags.name, tags.rating"
        }

        result = self._make_request("vn", payload)

        if result.get("results"):
            return result["results"][0]
        return {}

    def fetch_characters(
        self,
        vn_id: str,
        page: int = 1,
        results: int = 100
    ) -> Dict[str, Any]:
        """
        Fetch characters for a VN with pagination.

        Args:
            vn_id: VNDB ID (e.g., "v17")
            page: Page number (1-indexed)
            results: Results per page (max 100)

        Returns:
            Dictionary with 'results' (list of characters) and 'more' (boolean)
        """
        payload = {
            "filters": ["vn", "=", ["id", "=", vn_id]],
            "fields": "id, name, original, image.url, sex, age, birthday, vns.role, description, traits.id, traits.name, traits.spoiler, traits.group_name",
            "results": min(results, 100),
            "page": page
        }

        return self._make_request("character", payload)

    def process_vn_characters(self, vn_id: str, download_images: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch and process all characters for a VN.

        Args:
            vn_id: VNDB ID (e.g., "v17")
            download_images: Whether to download character images as base64

        Returns:
            List of processed character dictionaries
        """
        characters = []
        page = 1

        while True:
            result = self.fetch_characters(vn_id, page=page)
            chars = result.get("results", [])
            has_more = result.get("more", False)

            for char in chars:
                # Process character data
                processed = {
                    "id": char.get("id"),
                    "name": char.get("name"),
                    "name_original": char.get("original"),
                    "description": char.get("description", ""),
                    "sex": char.get("sex"),
                    "age": char.get("age"),
                    "birthday": char.get("birthday"),
                }

                # Get role for this VN
                vns = char.get("vns", [])
                role = "appears"
                for vn_entry in vns:
                    if vn_entry.get("id") == vn_id:
                        role = vn_entry.get("role", "appears")
                        break
                processed["role"] = role

                # Process traits
                traits = char.get("traits", [])
                personality = []
                roles = []
                engages_in = []
                subject_of = []

                for trait in traits:
                    trait_name = trait.get("name", "")
                    trait_group = trait.get("group_name", "")
                    trait_spoiler = trait.get("spoiler", 0)

                    trait_data = {
                        "name": trait_name,
                        "spoiler": trait_spoiler
                    }

                    # Categorize by group
                    if "Personality" in trait_group:
                        personality.append(trait_data)
                    elif "Role" in trait_group:
                        roles.append(trait_data)
                    elif "Engages in" in trait_group:
                        engages_in.append(trait_data)
                    elif "Subject of" in trait_group:
                        subject_of.append(trait_data)

                processed["personality"] = personality
                processed["roles"] = roles
                processed["engages_in"] = engages_in
                processed["subject_of"] = subject_of

                # Download image
                if download_images:
                    image_url = char.get("image", {}).get("url")
                    if image_url:
                        try:
                            image_base64 = self.fetch_image_as_base64(image_url)
                            processed["image_base64"] = image_base64
                        except Exception as e:
                            print(f"Error downloading image for character {char.get('id')}: {e}")

                characters.append(processed)

            if not has_more:
                break

            page += 1

        return characters

    def fetch_image_as_base64(self, url: str, max_size: tuple = (200, 300)) -> str:
        """
        Download an image and convert to base64 (with thumbnail).

        Args:
            url: Image URL
            max_size: Maximum dimensions (width, height) for thumbnail

        Returns:
            Base64-encoded image string with data URI prefix
        """
        self._wait_for_rate_limit()

        try:
            # Download image
            req = urllib.request.Request(url, headers={'User-Agent': self.USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as response:
                image_data = response.read()

            # Try to create thumbnail using PIL if available
            try:
                from PIL import Image
                img = Image.open(BytesIO(image_data))
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Convert to bytes
                output = BytesIO()
                img_format = img.format or 'PNG'
                img.save(output, format=img_format)
                image_data = output.getvalue()
            except ImportError:
                # PIL not available, use original image
                pass

            # Encode as base64
            base64_data = base64.b64encode(image_data).decode('utf-8')

            # Detect format
            if url.lower().endswith('.png'):
                mime = 'image/png'
            elif url.lower().endswith('.gif'):
                mime = 'image/gif'
            elif url.lower().endswith('.webp'):
                mime = 'image/webp'
            else:
                mime = 'image/jpeg'

            return f"data:{mime};base64,{base64_data}"

        except Exception as e:
            print(f"Error fetching image {url}: {e}")
            return ""
