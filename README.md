# Amazon product image analysis

Checks whether an Amazon.fr product’s main image explicitly shows its size.
Enter an ASIN to get the image and a boolean result.

## Important: API key

Create a key in [Google AI Studio](https://aistudio.google.com/apikey).
From the project root, create your configuration file:

```sh
cp -n .env.example .env
```

Edit `.env` and replace the placeholder with your key, without quotes:

```dotenv
GEMINI_API_KEY=your_actual_key
```

Keep your key private. `.env` is excluded from Git and the Docker image.
Gemini requests use your Google project’s quota and billing.

## Run with Docker

Install and start Docker Desktop, then run these commands from the project root:

```sh
docker build -f ex5/Dockerfile -t retail4brands-api .
docker run --rm --env-file .env -p 127.0.0.1:8001:8000 retail4brands-api
```

Open [the visual tester](http://127.0.0.1:8001), enter an ASIN
such as `B09DCX42VV`, and click **Analyze**.

API documentation: [Swagger UI](http://127.0.0.1:8001/docs).
You can also call the API directly:

```sh
curl http://127.0.0.1:8001/analyze/B09DCX42VV
```

Press **Ctrl+C** in the running terminal to stop the container.
