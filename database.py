import sqlite3 as sq
import json
from datetime import datetime, timedelta

db = sq.connect('tg.db')
cur = db.cursor()
cur.execute(
    "CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, start_message_date TEXT, last_message_date TEXT, topic_id INTEGER, chat_history TEXT)")
db.commit()

db_topic = sq.connect('tg_topic.db')
cur_topic = db_topic.cursor()
cur_topic.execute("CREATE TABLE IF NOT EXISTS topics(topic_id INTEGER PRIMARY KEY, id INTEGER)")
db_topic.commit()

async def cmd_start_db(user_id: int):
    user = cur.execute("SELECT * FROM users WHERE id == ?", (user_id,)).fetchone()
    if not user:
        cur.execute("INSERT INTO users(id, start_message_date, chat_history) VALUES (?, ?, ?)",
                    (user_id, datetime.now().strftime("%d.%m.%Y %H:%M:%S"), json.dumps([])))
        db.commit()

async def add_message_to_db(user_id: int, message: str):
    info = json.loads(
        cur.execute("SELECT chat_history FROM users WHERE id == ?", (user_id,)).fetchone()[0])
    info.append(message)
    cur.execute("UPDATE users SET chat_history = ? WHERE id == ?",
                (json.dumps(info), user_id))
    db.commit()

async def clear_message_db(user_id: int):
    # Очищает историю чата пользователя.
    cur.execute("UPDATE users SET chat_history = ? WHERE id == ?",
                (json.dumps([]), user_id))
    db.commit()

async def get_message_history(user_id: int) -> list:
    info = json.loads(
        cur.execute("SELECT chat_history FROM users WHERE id == ?", (user_id,)).fetchone()[0])
    return info

def made_new_topic_db_adder(user_id: int, topic_id: int):
    cur.execute("UPDATE users SET topic_id = ?, last_message_date = ? WHERE id == ?",
                (topic_id, datetime.now().strftime("%d.%m.%Y %H:%M:%S"), user_id))
    db.commit()

def add_id_to_topic(user_id: int, topic_id: int):
    test_info = cur_topic.execute("SELECT * FROM topics WHERE topic_id == ?", (topic_id,)).fetchone()
    if not test_info:
        cur_topic.execute("INSERT INTO topics(topic_id, id) VALUES (?, ?)", (topic_id, user_id))
        db_topic.commit()
    else:
        cur_topic.execute("UPDATE topics SET id = ? WHERE topic_id == ?",
                          (user_id, topic_id))
        db_topic.commit()

async def checker_to_add_new_topic(user_id: int) -> bool:
    info = cur.execute("SELECT last_message_date FROM users WHERE id == ?", (user_id,)).fetchone()
    if info and info[0]:
        last_message_date = datetime.strptime(info[0], "%d.%m.%Y %H:%M:%S")
        return (last_message_date + timedelta(minutes=2)) <= datetime.now()
    return True