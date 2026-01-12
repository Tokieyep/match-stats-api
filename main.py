from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import Literal
from pydantic import Field
from fastapi import HTTPException
import aiosqlite
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request


templates = Jinja2Templates(directory="templates")

class MatchCreate(BaseModel):
    game: str
    map: str
    result: Literal["win", "loss"]
    kills: int = Field(ge=0, le=100)
    deaths: int = Field(ge=0, le=100)
    notes: Optional[str] = None

DB_PATH = "match_stats.db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT NOT NULL,
                map TEXT NOT NULL,
                result TEXT NOT NULL,
                kills INTEGER NOT NULL,
                deaths INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """)
        await db.commit()
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def read_root():
    return {"ok": True}

@app.get("/")
async def root():
    return {"msg": "Match Stats API is running"}


@app.post("/matches")
async def create_match(payload: MatchCreate):
    created_at = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO matches (game, map, result, kills, deaths, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, 
            (payload.game, payload.map, payload.result, payload.kills, payload.deaths, payload.notes, created_at)
        )
        await db.commit()
        match_id = cursor.lastrowid

    return {
        "id": match_id,
        "game": payload.game,
        "map": payload.map,
        "result": payload.result,
        "kills": payload.kills,
        "deaths": payload.deaths,
        "notes": payload.notes,
        "created_at": created_at
    }

@app.get("/matches")
async def get_matches():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM matches ORDER BY id DESC")
        rows = await cursor.fetchall()

    return [dict(r) for r in rows]


@app.get("/matches/{match_id}")
async def get_match(match_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Match not found")

    return dict(row)


@app.delete("/matches/{match_id}")
async def delete_match(match_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM matches WHERE id = ?", (match_id,))
        await db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Match not found")
    return {"deleted": True, "match_id": match_id}

@app.get("/stats")
async def stats():
    async with aiosqlite.connect(DB_PATH) as db:
        # total m
        cursor = await db.execute("SELECT COUNT(*) FROM matches")
        (total,) = await cursor.fetchone()

        # total w
        cursor = await db.execute("SELECT COUNT(*) FROM matches WHERE result = 'win'")
        (wins,) = await cursor.fetchone()

        # sums for kd
        cursor = await db.execute("SELECT COALESCE(SUM(kills), 0), COALESCE(SUM(deaths), 0) FROM matches")
        kills, deaths = await cursor.fetchone()

    losses = total - wins
    winrate = round((wins / total) * 100, 1) if total > 0 else 0.0
    kd = round((kills / deaths), 2) if deaths > 0 else None



    return {
        "total_matches": total,
        "wins": wins,
        "losses": total - wins,
        "winrate": winrate,
        "total_kills": kills,
        "total_deaths": deaths,
        "over_all_kd": kd
    }



@app.get("/hud", response_class=HTMLResponse)
async def hub(request: Request):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute("SELECT COUNT(*) FROM matches")
        (total,) = await cursor.fetchone()

        cursor = await db.execute("SELECT COUNT(*) FROM matches WHERE result = 'win'")
        (wins,) = await cursor.fetchone()

        cursor = await db.execute("SELECT COALESCE(SUM(kills), 0), COALESCE(SUM(deaths), 0) FROM matches")
        kills, deaths = await cursor.fetchone()

        cursor = await db.execute("""
            SELECT id, game, map, result, kills, deaths, notes, created_at
            FROM matches
            ORDER BY id DESC
            LIMIT 10
        """)
        recent = await cursor.fetchall()

    losses = total - wins
    winrate = round((wins / total) * 100, 1) if total > 0 else 0.0
    kd = round((kills / deaths), 2) if deaths > 0 else None
    kd_display = kd if kd is not None else "-"
   

    return templates.TemplateResponse(
        "hud.html",
        {
            "request": request,
            "total": total,
            "wins": wins,
            "losses": losses,
            "winrate": winrate,
            "kills": kills,
            "deaths": deaths,
            "kd_display": kd_display,
            "recent": recent,
        },
    )