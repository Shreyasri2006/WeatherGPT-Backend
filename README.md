# WeatherGPT Backend — SIH26068

FastAPI backend for the **Safety-First Weather Decision Copilot** concept developed for SIH Problem Statement 26068.

## What is implemented

- Live current weather + 7/16-day forecast through Open-Meteo (prototype source)
- Real GFS and ECMWF model snapshots for a **model agreement score**
- Safety/risk layer with explicit distinction between official and derived alerts
- Optional IMD-warning adapter contract
- Persona/activity decision logic for citizen, farmer, fisherman, traveller, disaster officer, researcher and aviation modes
- Farmer examples: pesticide-spraying and irrigation advisories
- Historical-dataset hook for climate anomaly context
- Route-weather MVP
- Disaster replay scenarios
- Location search
- Hindi/Kannada prototype response templates
- FastAPI Swagger docs
- Tests, Dockerfile, Render blueprint and GitHub Actions CI

## Core safety rule

The language layer is **not** the meteorological source of truth. Numeric values come from structured weather sources. The system explains and acts on those values.

## Quick start

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements-dev.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux

uvicorn app.main:app --reload
```

Open:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Historical Kaggle dataset

The dataset is intentionally not bundled. Put the downloaded CSV in `data/` and set `HISTORICAL_DATASET_PATH` in `.env`. See `data/README.md`.

## Frontend connection

The separate frontend repo expects:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For deployment, set backend `CORS_ORIGINS` to your actual frontend origin(s).

## Production integration roadmap

1. Replace/augment prototype forecast source with authorized IMD feeds.
2. Normalize IMD district/cyclone/marine/lightning warnings into the adapter contract in `API.md`.
3. Add BharatFS/WRF feeds when accessible to the team.
4. Replace demo replay data with verified historical event records.
5. Add vulnerability/exposure datasets for true impact-based risk.
6. Add WIS2/MQTT ingestion worker when broker/topic details are available.
7. Calibrate model agreement against forecast-vs-observation history before calling it forecast confidence.

## Important terminology

The current percentage is named **model agreement**, not AI confidence. It measures similarity between available forecast-model outputs; it is not a calibrated probability of forecast correctness.

## Optional LLM communication layer

The backend works without an LLM. If you configure `LLM_ENDPOINT`, `LLM_MODEL` and optionally `LLM_API_KEY`, the deterministic verified answer may be rephrased through an OpenAI-compatible chat-completions endpoint. A numeric-token guard rejects LLM output that introduces new numeric values.

## Optional WIS2/MQTT scaffold

Install `requirements-wis2.txt`, configure the WIS2 broker/topic values and run `python scripts/wis2_subscriber.py`. The included worker is intentionally an ingestion scaffold; select and normalize the exact WIS2 collections required by your SIH prototype before production use.

## Run tests

```bash
pytest -q
ruff check app tests
```

## Docker

```bash
docker build -t weathergpt-backend .
docker run --rm -p 8000:8000 --env-file .env weathergpt-backend
```

## License
MIT
