from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://insanecipher.github.io"],
    allow_methods=["GET"],
)

API_KEY = os.getenv("API_KEY")

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )

def verify_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

@app.get("/news")
@limiter.limit("30/minute")
def get_news(
    request: Request,
    source: Optional[str] = Query(None),
    limit: int = Query(200, le=1000)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    if source:
        cursor.execute("""
            SELECT source, title, url, snippet, date, epoch
            FROM articles
            WHERE source = %s
            ORDER BY epoch DESC LIMIT %s
        """, (source, limit))
    else:
        cursor.execute("""
            SELECT source, title, url, snippet, date, epoch
            FROM articles
            ORDER BY epoch DESC LIMIT %s
        """, (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {"source": r[0], "title": r[1], "url": r[2],
         "snippet": r[3], "date": r[4], "epoch": r[5]}
        for r in rows
    ]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/admin/stats")
def stats(x_api_key: str = Header(...)):
    verify_key(x_api_key)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
    sources = cursor.fetchone()[0]
    cursor.execute("SELECT MAX(scraped_at) FROM articles")
    last_scrape = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return {"total_articles": total, "sources": sources, "last_scrape": str(last_scrape)}