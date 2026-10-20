# Exercise 1 — Extract an Amazon product image

The implementation is in `extract_image.py`, with three functions:

1. `get_main_image_url`: validate the ASIN, fetch its Amazon.fr page with Requests,
   parse it with BeautifulSoup, and return the main image URL.
2. `download_image`: download that URL, create the output folder, and save the file.
3. `main`: read the command-line arguments and call the two functions.

The main image is located by its HTML ID (`landingImage`, with alternatives for
book covers). The script prefers `data-old-hires` for a high-resolution image,
then falls back to `src`, the displayed image URL. It does not select unrelated
images such as logos or recommendations.

## Setup and run

From `Test_Retail4Brands` (Python 3.10+):

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python ex1/extract_image.py -i B07N7WT6J8
python ex1/extract_image.py -i B07N7WT6J8 -o ./my_images
python ex1/extract_image.py -h
```

The environment and requirements are shared at the project root.
The default output folder is `ex1/test_images`, regardless of where you run the
command. `-o` accepts another folder, including `~/Pictures`. Filenames use the
ASIN and the image format, for example `B07N7WT6J8.jpg`. Repeating the command
replaces the file with the same name. `--timeout 30` changes the request timeout.

To reuse just the function from the project root:

```python
from ex1.extract_image import get_main_image_url

url = get_main_image_url("B07N7WT6J8")
```

Amazon can block requests or return a CAPTCHA, and its HTML may change.
The script reports an error when it cannot fetch the page or find the image.
It does not execute JavaScript. It downloads the image into memory before saving
it, which keeps this exercise simple and is suitable for typical product images.

## Offline tests

From the project root, with the environment activated:

```sh
python -m unittest discover -s ex1/tests -v
```

The tests use sample HTML and mocked HTTP responses, not live Amazon requests.
