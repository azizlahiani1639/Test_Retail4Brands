"""Return whether a product image URL contains explicit size information."""

import argparse
from pathlib import Path
import sys

# Allow running this script directly from the project root or another directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ex2.analyze_image import analyze_image

def has_size_info(image_url: str, prompt: str | None = None) -> bool:
    """Return a boolean for an image URL (or a local image used in tests)."""
    return analyze_image(image_url, prompt)["has_size_info"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a product image URL for size information.")
    parser.add_argument("-i", "--image-url", required=True, help="Direct HTTP(S) image URL")
    args = parser.parse_args(argv)
    if not args.image_url.startswith(("https://", "http://")):
        parser.error("Provide a direct HTTP(S) image URL, not an ASIN or local file.")
    try:
        print("true" if has_size_info(args.image_url) else "false")
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
