# db_content.py
import asyncpg
import os
import logging
from typing import Dict, List, Any, Optional

DATABASE_URL = os.getenv('DATABASE_URL')
logger = logging.getLogger(__name__)

async def get_connection():
    """Получить соединение с БД"""
    return await asyncpg.connect(DATABASE_URL)

async def get_sections() -> List[Dict]:
    """Получить все разделы"""
    conn = None
    try:
        conn = await get_connection()
        rows = await conn.fetch("SELECT id, key, name FROM sections ORDER BY id")
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения разделов: {e}")
        return []
    finally:
        if conn:
            await conn.close()

async def get_section_by_key(key: str) -> Optional[Dict]:
    """Получить раздел по ключу"""
    conn = None
    try:
        conn = await get_connection()
        row = await conn.fetchrow("SELECT id, key, name FROM sections WHERE key = $1", key)
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Ошибка получения раздела {key}: {e}")
        return None
    finally:
        if conn:
            await conn.close()

async def get_section_by_id(section_id: int) -> Optional[Dict]:
    """Получить раздел по ID"""
    conn = None
    try:
        conn = await get_connection()
        row = await conn.fetchrow(
            "SELECT id, key, name FROM sections WHERE id = $1",
            section_id
        )
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Ошибка получения раздела {section_id}: {e}")
        return None
    finally:
        if conn:
            await conn.close()

async def get_topics(section_id: int) -> List[Dict]:
    """Получить темы раздела"""
    conn = None
    try:
        conn = await get_connection()
        rows = await conn.fetch(
            "SELECT id, key, name, theory FROM topics WHERE section_id = $1 ORDER BY id",
            section_id
        )
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения тем: {e}")
        return []
    finally:
        if conn:
            await conn.close()

async def get_topic_by_id(topic_id: int) -> Optional[Dict]:
    """Получить тему по ID"""
    conn = None
    try:
        conn = await get_connection()
        row = await conn.fetchrow(
            "SELECT id, key, name, theory, section_id FROM topics WHERE id = $1",
            topic_id
        )
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Ошибка получения темы {topic_id}: {e}")
        return None
    finally:
        if conn:
            await conn.close()

async def get_formulas(topic_id: int) -> List[Dict]:
    """Получить формулы темы"""
    conn = None
    try:
        conn = await get_connection()
        rows = await conn.fetch(
            "SELECT id, name, formula, description FROM formulas WHERE topic_id = $1 ORDER BY id",
            topic_id
        )
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения формул: {e}")
        return []
    finally:
        if conn:
            await conn.close()

async def get_examples(topic_id: int) -> List[Dict]:
    """Получить примеры темы"""
    conn = None
    try:
        conn = await get_connection()
        rows = await conn.fetch(
            "SELECT id, question, answer FROM examples WHERE topic_id = $1 ORDER BY id",
            topic_id
        )
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения примеров: {e}")
        return []
    finally:
        if conn:
            await conn.close()


async def add_user(user_id: int, username: str = None, first_name: str = None):
    """Добавить или обновить пользователя в БД"""
    conn = None
    try:
        conn = await get_connection()
        await conn.execute("""
            INSERT INTO users (user_id, username, first_name, registered_date, last_active)
            VALUES ($1, $2, $3, NOW(), NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET username = $2, first_name = $3, last_active = NOW()
        """, user_id, username, first_name)
        logger.info(f"✅ Пользователь {user_id} добавлен/обновлён")
    except Exception as e:
        logger.error(f"Ошибка добавления пользователя {user_id}: {e}")
    finally:
        if conn:
            await conn.close()
