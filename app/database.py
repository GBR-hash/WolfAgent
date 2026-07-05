# -*- coding: utf-8 -*-
import pymysql, logging, json
from typing import Optional

log = logging.getLogger("wolfagent.db")

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "1234",
    "charset": "utf8mb4",
    "autocommit": True,
}

def _get_conn():
    return pymysql.connect(**DB_CONFIG)

def init_db():
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS wolfagent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.select_db("wolfagent")
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS game_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    game_id VARCHAR(8) NOT NULL,
                    human_role VARCHAR(20) NOT NULL,
                    winner VARCHAR(20),
                    total_rounds INT,
                    is_alive BOOLEAN,
                    players_json JSON,
                    game_log_json JSON,
                    speeches_json JSON,
                    votes_json JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
        log.info("Database tables ready")
    finally:
        conn.close()


def create_user(username: str, password_hash: str) -> Optional[int]:
    conn = _get_conn()
    conn.select_db("wolfagent")
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        user_id = cur.lastrowid
        log.info("User created: %s (id=%d)", username, user_id)
        return user_id
    except pymysql.IntegrityError:
        log.warning("Username already exists: %s", username)
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[dict]:
    conn = _get_conn()
    conn.select_db("wolfagent")
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT id, username, password_hash, created_at FROM users WHERE username = %s", (username,))
            return cur.fetchone()
    finally:
        conn.close()


def save_game_record(user_id: int, game_id: str, human_role: str, winner: Optional[str],
                     total_rounds: int, is_alive: bool, players: dict,
                     game_log: list, speeches: list, votes: dict) -> Optional[int]:
    conn = _get_conn()
    conn.select_db("wolfagent")
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO game_records (user_id, game_id, human_role, winner, total_rounds, is_alive, players_json, game_log_json, speeches_json, votes_json) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (user_id, game_id, human_role, winner, total_rounds, is_alive,
                 json.dumps(players, ensure_ascii=False, default=str),
                 json.dumps(game_log, ensure_ascii=False, default=str),
                 json.dumps(speeches, ensure_ascii=False, default=str),
                 json.dumps(votes, ensure_ascii=False, default=str)))
        rid = cur.lastrowid
        log.info("Game record saved: %s for user %d", game_id, user_id)
        return rid
    finally:
        conn.close()


def get_user_records(user_id: int, limit: int = 20) -> list:
    conn = _get_conn()
    conn.select_db("wolfagent")
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                "SELECT id, game_id, human_role, winner, total_rounds, is_alive, created_at FROM game_records WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                (user_id, limit))
            rows = cur.fetchall()
            for r in rows:
                if hasattr(r.get('created_at'), 'isoformat'):
                    r['created_at'] = r['created_at'].isoformat()
            return rows
    finally:
        conn.close()


def get_record_detail(user_id: int, game_id: str) -> Optional[dict]:
    conn = _get_conn()
    conn.select_db("wolfagent")
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                "SELECT * FROM game_records WHERE user_id = %s AND game_id = %s",
                (user_id, game_id))
            row = cur.fetchone()
            if row:
                if hasattr(row.get('created_at'), 'isoformat'):
                    row['created_at'] = row['created_at'].isoformat()
                for json_field in ('players_json', 'game_log_json', 'speeches_json', 'votes_json'):
                    if row.get(json_field):
                        try:
                            key = json_field.replace('_json', '')
                            val = row[json_field]
                            row[key] = json.loads(val) if isinstance(val, str) else val
                        except (json.JSONDecodeError, TypeError):
                            pass
            return row
    finally:
        conn.close()