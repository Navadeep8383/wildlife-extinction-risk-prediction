"""
EcoGuard AI - Species Image Service
On-demand retrieval and caching of verified species imagery from Wikimedia Commons
and GBIF, with graceful taxonomic vector silhouette fallback for unphotographed taxa.
"""

import json
import logging
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("ecoguard.species_image_service")


class SpeciesImageService:
    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            self.cache_dir = Path(__file__).resolve().parent.parent / "data" / "cache" / "species_images"
        else:
            self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = "EcoGuardAI/1.0 (Biodiversity Intelligence Platform; mailto:research@ecoguard.ai)"

    def sanitize_name(self, scientific_name: str) -> str:
        return re.sub(r"[^\w\-.]", "_", scientific_name)

    def get_species_image(self, scientific_name: str, class_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve verified species image on-demand.
        Checks local cache first; if not found, queries Wikimedia Commons and GBIF,
        caches image file and metadata locally, and returns metadata.
        """
        sanitized = self.sanitize_name(scientific_name)
        meta_file = self.cache_dir / f"{sanitized}.json"

        # 1. Check local cache
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                img_path = self.cache_dir / f"{sanitized}.jpg"
                if cached.get("has_image") and img_path.exists():
                    return cached
                if not cached.get("has_image"):
                    # Cached silhouette fallback
                    if class_name and not cached.get("silhouette_class"):
                        cached["silhouette_class"] = class_name
                    return cached
            except Exception as e:
                logger.warning(f"Error reading image cache for {scientific_name}: {e}")

        # 2. Query Wikimedia Commons / Wikipedia API
        wiki_result = self._fetch_wikimedia(scientific_name)
        if wiki_result and wiki_result.get("image_url"):
            cached_data = self._cache_image(sanitized, scientific_name, wiki_result, class_name)
            if cached_data:
                return cached_data

        # 3. Fallback to GBIF Occurrence Media API
        gbif_result = self._fetch_gbif(scientific_name)
        if gbif_result and gbif_result.get("image_url"):
            cached_data = self._cache_image(sanitized, scientific_name, gbif_result, class_name)
            if cached_data:
                return cached_data

        # 4. Fallback: Consistent Taxonomic Vector Silhouette
        fallback = {
            "scientific_name": scientific_name,
            "has_image": False,
            "image_url": None,
            "external_url": None,
            "source": "Taxonomic Vector Silhouette",
            "attribution": "EcoGuard AI Silhouette System",
            "license": "Public Domain",
            "description": f"Standardized vector silhouette for {scientific_name.replace('_', ' ')}",
            "silhouette_class": class_name or "Tetrapod",
        }

        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(fallback, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache fallback metadata for {scientific_name}: {e}")

        return fallback

    def _fetch_wikimedia(self, scientific_name: str) -> Optional[Dict[str, Any]]:
        clean_name = scientific_name.replace("_", " ")
        encoded = urllib.parse.quote(clean_name)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"

        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status != 200:
                    return None
                data = json.loads(resp.read().decode("utf-8"))

                # Ensure image exists
                orig_img = data.get("originalimage", {}).get("source")
                thumb_img = data.get("thumbnail", {}).get("source")
                chosen_url = thumb_img or orig_img
                if not chosen_url:
                    return None

                # Exclude obvious non-organism SVG maps
                lower_url = chosen_url.lower()
                if "range" in lower_url and lower_url.endswith(".svg.png"):
                    return None

                desc = data.get("description") or f"Specimen photo of {clean_name}"
                title = data.get("title") or clean_name
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page")

                return {
                    "image_url": chosen_url,
                    "external_url": page_url or chosen_url,
                    "source": "Wikimedia Commons",
                    "attribution": f"{title} / Wikimedia Commons",
                    "license": "Creative Commons / Public Domain",
                    "description": desc,
                }
        except Exception:
            return None

    def _fetch_gbif(self, scientific_name: str) -> Optional[Dict[str, Any]]:
        clean_name = scientific_name.replace("_", " ")
        encoded = urllib.parse.quote(clean_name)
        match_url = f"https://api.gbif.org/v1/species/match?name={encoded}&strict=true"

        req = urllib.request.Request(match_url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status != 200:
                    return None
                match_data = json.loads(resp.read().decode("utf-8"))
                usage_key = match_data.get("usageKey")
                if not usage_key:
                    return None

            occ_url = f"https://api.gbif.org/v1/occurrence/search?taxonKey={usage_key}&mediaType=StillImage&limit=1"
            req2 = urllib.request.Request(occ_url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req2, timeout=4) as resp2:
                if resp2.status != 200:
                    return None
                occ_data = json.loads(resp2.read().decode("utf-8"))
                results = occ_data.get("results", [])
                if not results or not results[0].get("media"):
                    return None

                media = results[0]["media"][0]
                img_url = media.get("identifier")
                if not img_url:
                    return None

                rights = media.get("rightsHolder") or results[0].get("rightsHolder") or "GBIF Contributor"
                license_str = media.get("license") or "CC BY-NC 4.0"
                publisher = results[0].get("publisher") or "GBIF"

                return {
                    "image_url": img_url,
                    "external_url": img_url,
                    "source": "GBIF Occurrence Media",
                    "attribution": f"Photo © {rights} via {publisher}",
                    "license": license_str,
                    "description": f"Verified specimen occurrence of {clean_name}",
                }
        except Exception:
            return None

    def _cache_image(
        self, sanitized: str, scientific_name: str, info: Dict[str, Any], class_name: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        img_target = self.cache_dir / f"{sanitized}.jpg"
        meta_target = self.cache_dir / f"{sanitized}.json"

        # Download image bytes
        req = urllib.request.Request(info["image_url"], headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status != 200:
                    return None
                img_bytes = resp.read()

            with open(img_target, "wb") as f:
                f.write(img_bytes)

            result = {
                "scientific_name": scientific_name,
                "has_image": True,
                "image_url": f"/cache/species_images/{sanitized}.jpg",
                "external_url": info.get("external_url"),
                "source": info.get("source"),
                "attribution": info.get("attribution"),
                "license": info.get("license"),
                "description": info.get("description"),
                "silhouette_class": class_name or "Tetrapod",
            }

            with open(meta_target, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            return result
        except Exception as e:
            logger.warning(f"Failed downloading or caching image for {scientific_name}: {e}")
            return None


# Global singleton instance
_image_service_instance: Optional[SpeciesImageService] = None


def get_species_image_service() -> SpeciesImageService:
    global _image_service_instance
    if _image_service_instance is None:
        _image_service_instance = SpeciesImageService()
    return _image_service_instance
