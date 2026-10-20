# Exercise 5 — Package the API with Docker

The Dockerfile starts from Python 3.13, installs the root requirements, copies
the five Python modules, the prompt, and the HTML tester, and runs Uvicorn.
The API listens on port 8000 inside the container. The build context is the
project root because the code is shared across exercises.

Docker must be installed and running. On macOS, you can use
[Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/).
You do not need to activate the local Python virtual environment for Docker.

## Build

Run from `Test_Retail4Brands`:

```sh
docker build -f ex5/Dockerfile -t retail4brands-api .
```

The final `.` supplies the project root as the build context.
The root `.dockerignore` excludes local secrets, the virtual environment,
test images, tests, and the Word document. The Dockerfile copies only the
runtime files explicitly.

## Run

Keep `GEMINI_API_KEY=your_key` in the root `.env`, without quotes around the key:

```sh
docker run --rm --name retail4brands-api --env-file .env -p 127.0.0.1:8001:8000 retail4brands-api
```

`--env-file` passes the key to the running container. The `.env` file is not
copied into the image. `8001:8000` maps port 8001 on your computer to port 8000
inside the container.

Open http://127.0.0.1:8001 for the visual tester. Enter an ASIN, click Analyze,
and see the product image and result. The API documentation remains at `/docs`.

Or use another terminal:

```sh
curl http://127.0.0.1:8001/analyze/B0FHL12F97
```

Stop the foreground container with Ctrl+C. `--rm` removes it after it exits;
the built image remains available for the next run.

## Share the result

The repository with the Dockerfile is sufficient for the brief: a reviewer can
build the image and provide their own Gemini key. The Dockerfile also includes
the apple-pie recipe required by the brief, as comments.

To export a built image instead:

```sh
docker save -o retail4brands-api.tar retail4brands-api
```

On a machine with the same CPU architecture, load the archive with
`docker load -i retail4brands-api.tar`, then run the same `docker run` command
with that machine's `.env`. Rebuilding from the repository lets Docker choose
the appropriate image architecture for the reviewer's machine.

## Verification status

The image was built and a container was started successfully with the root
`.env` supplied at runtime. `/docs` returned HTTP 200. Live requests returned
HTTP 200 with `has_size_info: true` for `B09DCX42VV` and false for `B0FHL12F97`.
Invalid ASINs returned HTTP 422.
The visual tester was checked on desktop and mobile, including a live analysis
from its ASIN form.
The container runs as a non-root user, contains the prompt, and has no `.env`
file in the image. The temporary validation container was removed afterward.

References: [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/)
and [Docker build contexts](https://docs.docker.com/build/concepts/context/).
