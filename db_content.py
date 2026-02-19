# db_content.py
import asyncpg
import os
from typing import Dict, List, Any, Optional

DATABASE_URL = os.getenv('DATABASE_URL')

async def get_sections() -> List[Dict]:
    """Получить все разделы"""
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT id, key, name FROM sections ORDER BY id")
    await conn.close()
    return [dict(row) for row in rows]

async def get_topics(section_key: str) -> List[Dict]:
    """Получить темы раздела"""
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("""
        SELECT t.id, t.key, t.name, t.theory
        FROM topics t
        JOIN sections s ON t.section_id = s.id
        WHERE s.key = $1
        ORDER BY t.id
    """, section_key)
    await conn.close()
    return [dict(row) for row in rows]

async def get_formulas(topic_id: int) -> List[Dict]:
    """Получить формулы темы"""
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(
        "SELECT name, formula, description FROM formulas WHERE topic_id = $1",
        topic_id
    )
    await conn.close()
    return [dict(row) for row in rows]

async def get_examples(topic_id: int) -> List[Dict]:
    """Получить примеры темы"""
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(
        "SELECT question, answer FROM examples WHERE topic_id = $1",
        topic_id
    )
    await conn.close()
    return [dict(row) for row in rows]
