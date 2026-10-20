# Exercise 4 — An API taking an ASIN

One API file, `app.py`, and one visual tester, `index.html`. The API reuses
`get_main_image_url` from exercise 1 and
`has_size_info` from exercise 3, which calls the analysis code in exercise 2.
The prompt remains in `ex3/test_suite_prompt/prompt.txt`; no scraping or
analysis code is copied into this folder.

## Run

From `Test_Retail4Brands`:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn ex4.app:app --reload
```

Open http://127.0.0.1:8000 to enter an ASIN and see the product image with its
size-information result. The page calls the same `/analyze/{asin}` endpoint.

Open http://127.0.0.1:8000/docs to try the endpoint through the API documentation.
Use **GET /analyze/{asin}**, click **Try it out**, enter an ASIN, then **Execute**.

Or use a terminal:

```sh
curl http://127.0.0.1:8000/analyze/B07N7WT6J8
```

The request fetches the Amazon.fr page, extracts its main image URL, and sends
that image to Gemini. It uses the shared virtual environment and root `.env`.
Lowercase ASINs are normalized to uppercase. Each successful analysis uses a
Gemini request; results are not cached.

Example response (the image URL below is illustrative):

```json
{
  "asin": "B07N7WT6J8",
  "image_url": "https://example.com/product.jpg",
  "has_size_info": false
}
```

`ProductAnalysis` describes these three response fields and gives FastAPI
the schema for its interactive documentation. `has_size_info` is a JSON boolean.

FastAPI validates the 10-letter/digit ASIN format and returns HTTP 422 for invalid input.
Amazon/image/Gemini request timeouts return 504;
other fetching or Gemini response failures return 502. Exhausted daily Gemini
quota returns 503. Errors never become a false result. Amazon can still block
requests. Existing Gemini rate-limit retries can make a request take longer.

## Offline checks

```sh
python -m unittest discover -s ex4/tests -v
```

These use FastAPI's test client and mock Amazon and Gemini calls. They do not
consume API quota.

Reference: [FastAPI's documentation](https://fastapi.tiangolo.com/tutorial/).
