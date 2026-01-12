from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import Literal
from pydantic import Field
from fastapi import HTTPException

class MatchCreate(BaseModel):
    game: str
    map: str
    result: Literal["win", "loss"]
    kills: int = Field(ge=0, le=100)
    deaths: int = Field(ge=0, le=100)
    notes: Optional[str] = None

app = FastAPI()

MATCHES: list[dict] = []
NEXT_ID = 1

@app.get("/health")
async def read_root():
    return {"ok": True}

@app.get("/")
async def root():
    return {"msg": "Match Stats API is running"}


@app.post("/matches")
async def create_match(payload: MatchCreate):
    global NEXT_ID

    match = {
        "id": NEXT_ID,
        "game": payload.game,
        "map": payload.map,
        "result": payload.result,
        "kills": payload.kills,
        "deaths": payload.deaths,
        "notes": payload.notes,
        "created_at": datetime.utcnow().isoformat()
    }

    MATCHES.append(match)
    NEXT_ID += 1
    return match

@app.get("/matches")
async def get_matches():
    return list(reversed(MATCHES))


@app.get("/matches/{match_id}")
async def get_match(match_id: int):
    for m in MATCHES:
        if m["id"] == match_id:
            return m
        
    raise HTTPException(status_code=404, detail="Match not found")


@app.get("/stats")
async def stats():
    total = len(MATCHES)
    wins = sum(1 for m in MATCHES if m["result"] == "win")
    return {
        "total_matches": total,
        "wins": wins,
        "losses": total - wins
    }