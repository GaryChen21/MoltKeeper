"""MoltKeeper API — pencatat siklus molt (ganti kulit) tarantula.

Endpoint wajib UTS:
  GET  /health      -> cek status aplikasi + koneksi database
  GET  /baca-data   -> ambil semua catatan molt dari PostgreSQL
  POST /tulis-data  -> simpan satu catatan molt baru ke PostgreSQL
"""

import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/moltkeeper",
)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS catatan_molt (
    id            SERIAL PRIMARY KEY,
    nama_tarantula VARCHAR(100) NOT NULL,
    spesies        VARCHAR(150) NOT NULL,
    instar         VARCHAR(50),
    leg_span_cm    NUMERIC(4, 1),
    tanggal_molt   DATE,
    catatan        TEXT,
    dibuat_pada    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

COLUMNS = [
    "id",
    "nama_tarantula",
    "spesies",
    "instar",
    "leg_span_cm",
    "tanggal_molt",
    "catatan",
    "dibuat_pada",
]

pool: ConnectionPool | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global pool
    pool = ConnectionPool(conninfo=DATABASE_URL, min_size=1, max_size=5)
    with pool.connection() as conn:
        conn.execute(CREATE_TABLE_SQL)
    yield
    if pool is not None:
        pool.close()


app = FastAPI(title="MoltKeeper API", lifespan=lifespan)


class CatatanMolt(BaseModel):
    nama_tarantula: str = Field(min_length=1, max_length=100)
    spesies: str = Field(min_length=1, max_length=150)
    instar: str | None = Field(default=None, max_length=50)
    leg_span_cm: float | None = Field(default=None, ge=0, le=30)
    tanggal_molt: date | None = None
    catatan: str | None = None


@app.get("/health")
def health():
    try:
        with pool.connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "terhubung"}
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail=f"database tidak terhubung: {exc}")


@app.get("/baca-data")
def baca_data():
    with pool.connection() as conn:
        rows = conn.execute(
            f"SELECT {', '.join(COLUMNS)} FROM catatan_molt ORDER BY dibuat_pada DESC;"
        ).fetchall()
    return [dict(zip(COLUMNS, row)) for row in rows]


@app.post("/tulis-data", status_code=201)
def tulis_data(data: CatatanMolt):
    with pool.connection() as conn:
        row = conn.execute(
            """
            INSERT INTO catatan_molt
                (nama_tarantula, spesies, instar, leg_span_cm, tanggal_molt, catatan)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, nama_tarantula, spesies, instar, leg_span_cm,
                      tanggal_molt, catatan, dibuat_pada;
            """,
            (
                data.nama_tarantula,
                data.spesies,
                data.instar,
                data.leg_span_cm,
                data.tanggal_molt,
                data.catatan,
            ),
        ).fetchone()
    return dict(zip(COLUMNS, row))


static_dir = Path(__file__).parent / "static"
if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
