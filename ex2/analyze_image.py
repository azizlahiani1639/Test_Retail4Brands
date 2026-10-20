"""Check whether a product image explicitly shows its size."""

import argparse
import json
import mimetypes
import os
from pathlib import Path
import sys
import time

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

MODEL = "gemini-3-flash-preview"
PROMPT_FILE = Path(__file__).resolve().parents[1] / "ex3/test_suite_prompt/prompt.txt"


class DailyQuotaError(RuntimeError):
    """The project's daily quota is exhausted; waiting a minute cannot fix it."""


def analyze_image(source: str, prompt: str | None = None) -> dict:
    """Load an image, ask Gemini, and return its answer."""
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in the root .env file.")
    if prompt is None:
        prompt = PROMPT_FILE.read_text(encoding="utf-8")
    if not prompt.strip():
        raise ValueError("The prompt file is empty.")

    # Read the image from a URL or a local file.
    if source.startswith(("https://", "http://")):
        response = requests.get(source, timeout=60)
        response.raise_for_status()
        image_bytes = response.content
        mime_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    else:
        path = Path(source).expanduser()
        image_bytes = path.read_bytes()
        mime_type = mimetypes.guess_type(path.name)[0]
    if not mime_type or not mime_type.startswith("image/") or not image_bytes:
        raise ValueError("Provide a non-empty image file or a direct image URL.")

    # The SDK handles the HTTP request and image encoding for us.
    options = {"timeout": 60000, "retry_options": {"attempts": 1}}
    with genai.Client(api_key=api_key, http_options=options) as client:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)],
                    config={"response_mime_type": "application/json"},
                )
                break
            except errors.APIError as error:
                if error.code != 429:
                    raise
                if "perday" in str(error.details).lower():
                    raise DailyQuotaError(
                        "Gemini's daily quota is exhausted. Wait for the daily reset "
                        "or check your project's quota in Google AI Studio."
                    ) from error
                if attempt == 2:
                    raise ValueError("Gemini quota is still exhausted after 3 attempts. "
                                     f"Google reports: {error.message}") from error
                print("Gemini rate limit reached. Waiting 60s before retrying the same image "
                      f"(attempt {attempt + 2}/3)...", file=sys.stderr, flush=True)
                time.sleep(60)
    result = json.loads(response.text or "{}")
    if (not isinstance(result, dict) or type(result.get("has_size_info")) is not bool
            or not isinstance(result.get("explanation"), str) or not result["explanation"].strip()):
        raise ValueError("Gemini did not return a boolean and an explanation.")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an image for explicit product size information.")
    parser.add_argument("-i", "--image", required=True, help="Local image path or direct image URL")
    args = parser.parse_args(argv)
    try:
        result = analyze_image(args.image)
    except Exception as error:
        # Report failures without turning them into a misleading false result.
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
