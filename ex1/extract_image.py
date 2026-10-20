"""Find and download the main image of an Amazon.fr product."""

import argparse
import math
import mimetypes
from pathlib import Path
import re
import sys

import requests
from bs4 import BeautifulSoup

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "test_images"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AmazonImageExercise/1.0)",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def get_main_image_url(asin: str, timeout: float = 15) -> str:
    """Fetch the product page and return its main image URL."""
    asin = asin.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{10}", asin):
        raise ValueError("An ASIN must contain exactly 10 letters or digits.")

    response = requests.get(
        f"https://www.amazon.fr/dp/{asin}", headers=HEADERS, timeout=timeout,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    if soup.select_one('form[action*="validateCaptcha"], #captchacharacters'):
        raise ValueError("Amazon returned a CAPTCHA. Try again later.")

    # The first ID is for standard products; the others are for book covers.
    image = soup.select_one("img#landingImage, img#imgBlkFront, img#ebooksImgBlkFront")
    if image is None:
        raise ValueError("Main image not found. Amazon may have blocked the request or changed its page.")

    # Prefer the high-resolution version; otherwise use the displayed image.
    image_url = image.get("data-old-hires") or image.get("src")
    if not image_url or not image_url.startswith(("https://", "http://")):
        raise ValueError("The main image does not have a usable URL.")
    return image_url


def download_image(image_url: str, asin: str, output_dir: Path, timeout: float = 15) -> Path:
    """Download the image and save it as ASIN.extension in the output folder."""
    response = requests.get(image_url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()

    # Use the actual image format for the filename, e.g. image/jpeg -> .jpg.
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    extension = mimetypes.guess_extension(content_type)
    if not content_type.startswith("image/") or not extension:
        raise ValueError("The image server did not return a recognized image format.")
    if not response.content:
        raise ValueError("The image server returned an empty file.")

    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"{asin}{extension}"
    image_path.write_bytes(response.content)
    return image_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download an Amazon.fr product's main image.")
    parser.add_argument("-i", "--asin", required=True, help="Product ASIN, e.g. B07N7WT6J8")
    parser.add_argument(
        "-o", "--output", type=Path, default=DEFAULT_OUTPUT,
        help="Output folder (default: test_images next to this script)",
    )
    parser.add_argument("--timeout", type=float, default=15, help="Request timeout in seconds (default: 15)")
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a positive, finite number.")
    asin = args.asin.strip().upper()

    try:
        image_url = get_main_image_url(asin, args.timeout)
        image_path = download_image(image_url, asin, args.output, args.timeout)
    except (requests.RequestException, ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Image URL: {image_url}")
    print(f"Saved to: {image_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
