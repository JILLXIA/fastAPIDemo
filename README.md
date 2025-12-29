# Weekend Planner Agent API

This repo exposes the LangChain weekend-planner agent as a FastAPI service.

## API

### `POST /agent`

**Request**

```json
{
  "query": "Plan my weekend in San Jose. I like sushi and live music.",
  "verbose": false
}
```

**Response**

```json
{
  "output": "...final plan text...",
  "raw": null
}
```

## Logging

The server logs include:

- Request start/end with a `X-Request-ID` correlation id
- Agent start/end timings
- Tool calls (name + inputs; outputs are truncated by default)

Controls:

- `LOG_LEVEL` (default `INFO`). Use `DEBUG` for more verbose/truncated-less logs.
- `verbose` (request field): if `true`, the API response includes `raw` (the full LangChain result). Tool-call logs are still written to server logs either way.

Example (local):

```bash
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

## Environment variables

Required for full functionality:

- `OPENAI_API_KEY`
- `OPENWEATHERMAP_API_KEY` (weather tool)
- `TMDB_ACCESS_KEY` (movies tool)
- `TICKETMASTER_API_KEY` (events tool)

Optional:

- `OPENAI_MODEL` (default: `gpt-5-nano`)
- `OPENAI_TIMEOUT_S` (default: `30`)
- `OPENAI_TEMPERATURE` (default: `0.1`)
- `UVICORN_WORKERS` (default: `1`)

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://localhost:8000/docs

## Run with Docker

```bash
docker build -t weekend-planner-api .
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e OPENWEATHERMAP_API_KEY=$OPENWEATHERMAP_API_KEY \
  -e TMDB_ACCESS_KEY=$TMDB_ACCESS_KEY \
  -e TICKETMASTER_API_KEY=$TICKETMASTER_API_KEY \
  weekend-planner-api
```

## Run with Docker Compose

Create a `.env` file (not committed) and run:

```bash
docker compose up --build
```

## Tests

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```
