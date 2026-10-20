"""Evaluate prompt.txt against the images labeled by their folder."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ex3.check_size import has_size_info
from ex2.analyze_image import DailyQuotaError, MODEL

SUITE_DIR = Path(__file__).resolve().parent
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


def main() -> int:
    try:
        prompt = (SUITE_DIR / "prompt.txt").read_text(encoding="utf-8")
        if not prompt.strip():
            raise ValueError("prompt.txt is empty.")
        cases = []
        for folder, expected in (("with_size", True), ("without", False)):
            directory = SUITE_DIR / "test_images" / folder
            images = sorted(path for path in directory.iterdir()
                            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)
            if not images:
                raise ValueError(f"Add at least one image to {directory} before testing.")
            cases.extend((image, expected) for image in images)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    correct = 0
    errors = 0
    not_tested = 0
    total = len(cases)
    print(f"Model: {MODEL} | Images: {total}", flush=True)
    for index, (image, expected) in enumerate(cases):
        name = f"{image.parent.name}/{image.name}"
        try:
            actual = has_size_info(str(image), prompt)
            passed = actual is expected
            correct += passed
            print(f"{'PASS' if passed else 'FAIL'} {name}: expected={expected}, actual={actual}", flush=True)
        except DailyQuotaError as error:
            errors += 1
            not_tested = total - index - 1
            print(f"STOP {name}: {error}", flush=True)
            break
        except Exception as error:
            errors += 1
            print(f"ERROR {name}: {error}", flush=True)

    completed = total - errors - not_tested
    print(f"\nCompleted: {completed}/{total} | API/file errors: {errors} | Not tested: {not_tested}")
    if completed:
        print(f"Prediction accuracy: {correct}/{completed} ({correct / completed:.1%})")
    else:
        print("Prediction accuracy: unavailable (no completed predictions)")
    status = "INCOMPLETE" if errors else ("PASS" if correct == total else "FAIL")
    print(f"Target 100%: {status}")
    return 0 if correct == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
