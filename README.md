# Match Stats APi

simple REST API for tracking match results and basic stats.

## Features
- Create and list matches
- Get match by Id
- Input Validation
- Aggregated stats endpoint
- Auto docs via Swagger UI

What it is: Match Stats API (FastAPI + SQLite + HUD)

How it was built: guided + AI-assisted learning project

What I learned: CRUD, validation, DB queries, templating, deployment

Pushed with Render: 
Hud: https://matchstats-dfm5.onrender.com/hud
Create/Get matches: https://matchstats-dfm5.onrender.com/docs

## Run locally
```bash
python -m venv .venv
# activate venv...
pip install fastapi uvicorn
uvicorn main:app --reload
