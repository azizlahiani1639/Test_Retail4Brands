# Exercise 3 — Return a boolean and test the prompt

`check_size.py` imports the existing analysis function from exercise 2.
There are no copied scripts or symlinks. Exercise 2 reads the shared prompt
from `test_suite_prompt/prompt.txt` in this folder. The runner can also pass
that prompt explicitly when testing the labeled images.

From the project root, with the shared environment activated:

```sh
python ex3/check_size.py -i "https://example.com/product.jpg"
python ex3/check_size.py --image-url "https://example.com/product.jpg"
python ex3/check_size.py -h
```

The command takes a direct image URL, not an ASIN or a local file, and uses
exercise 2 to analyze it. The output is `true` or `false`. Errors produce an error message
and exit code 1; they are never converted into false.

The function itself takes an image URL and returns a Python boolean:

```python
from ex3.check_size import has_size_info

result = has_size_info("https://example.com/product.jpg")
```

It also accepts local image paths so the test runner can use the same function.

## Test your prompt

```text
test_suite_prompt/
├── prompt.txt
├── test_prompt.py
└── test_images/
    ├── with_size/   # Images where the expected answer is true
    └── without/     # Images where the expected answer is false
```

Add your images to both folders, then run from the project root:

```sh
python ex3/test_suite_prompt/test_prompt.py
```

JPEG, PNG, WebP, HEIC, and HEIF files are tested; other files are ignored.
Each image makes a Gemini request using the root `.env` key. The runner starts
the next image immediately after the previous one finishes, with no fixed delay.
If Gemini returns HTTP 429, the shared analysis function waits 60 seconds
and retries the same image, with a maximum of three attempts. The model remains
`gemini-3-flash-preview`.

The runner prints PASS, FAIL, or ERROR for every image, then completion count
and prediction accuracy. Accuracy counts completed predictions only; API/file
errors mark the run INCOMPLETE and never let it pass, even with 100% accuracy
on the completed predictions. Exit code 0 means every image
passed; 1 means a prediction failed or a request errored; 2 means the prompt or
test folders are missing/empty. Both image folders must contain examples.

Waiting addresses temporary rate limits, not an exhausted daily quota or a
disabled API key. A daily-quota error stops the whole suite immediately and
reports the remaining images as not tested. Limits depend on the project's
current billing tier and are shared by the Google project, including requests
from other scripts. See [Google's rate-limit documentation](https://ai.google.dev/gemini-api/docs/rate-limits).

Edit `prompt.txt` and rerun to compare results. The exact same prompt is used
by the boolean function and the runner. Reaching 100% applies to the supplied
examples; it does not guarantee perfect predictions on other images.

Offline code checks (no API calls):

```sh
python -m unittest discover -s ex3/tests -v
```
