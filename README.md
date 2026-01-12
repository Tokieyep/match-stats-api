# Match Stats APi

simple REST API for tracking match results and basic stats.

## Features
- Create and list matches
- Get match by Id
- Input Validation
- Aggregated stats endpoint
- Auto docs via Swagger UI

## Run locally
```bash
python -m venv .venv
# activate venv...
pip install fastapi uvicorn
uvicorn main:app --reload