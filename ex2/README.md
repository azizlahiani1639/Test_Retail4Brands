# Exercise 2 — Check for size information

The code is in `analyze_image.py`:

- `analyze_image` loads the API key and image, sends the image with our prompt
  to Gemini 3 Flash, and returns a boolean with a short explanation.
- `main` reads `-i`, calls the function, and prints the answer.

From the project root:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python ex2/analyze_image.py -i ex1/test_images/B07N7WT6J8.jpg
python ex2/analyze_image.py -h
```

`-i` accepts a local image path or a direct image URL, not an ASIN. The key is
loaded from the root `.env` file. Google's SDK handles the Gemini request.
The model is set by `MODEL` near the top; the request timeout is 60 seconds.
HTTP 429 rate limits trigger a 60-second wait and retry, up to three attempts.
The script prints the wait so it is clear what is happening.
An exhausted daily quota raises a clear error immediately, without retries.

Edit `ex3/test_suite_prompt/prompt.txt` to refine what counts as size information.
That single prompt is shared by all exercises and the prompt runner. It counts
readable dimensions with units, explicit size labels, and rulers measuring
this product. It excludes guesses, clock times, model numbers, quantities,
weight, and capacity alone. Unreadable measurements count as absent.

Example answer:

```json
{
  "has_size_info": false,
  "explanation": "The image shows a clock but no explicit product dimensions."
}
```

Errors are reported separately from false results. Check the explanation against
the image: model responses can be wrong. Large or unsupported images may be
rejected by Gemini. Use the labeled image suite in exercise 3 to evaluate the
prompt. The final review results and limitations are recorded in the root README.

Offline checks, from the project root:

```sh
python -m unittest discover -s ex2/tests -v
```

Reference: [Google's Python SDK](https://googleapis.github.io/python-genai/).
