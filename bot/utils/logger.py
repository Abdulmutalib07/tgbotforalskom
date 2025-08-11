import oracledb
from bot.utils.config import ORACLE_CONFIG

def log_action(entity_id, action_type='RASPOR', message_id=None, chat_id=   None):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO BOT_LOGS (REQ_ID, ACTION_TYPE, ACTION_DATE, MESSAGE_ID, CHAT_ID)
    VALUES (:1, :2, SYSDATE, :3, :4)
    """,[str(entity_id), action_type, message_id, chat_id])
    conn.commit()
    cur.close()
    conn.close()

def upsert_message_id(order_id, message_id, chat_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        UPDATE BOT_LOGS
           SET MESSAGE_ID = :mid, CHAT_ID = :cid
         WHERE REQ_ID = :rid
           AND ACTION_TYPE = 'RASPOR'
    """, {"mid": int(message_id), "cid": int(chat_id), "rid": str(order_id)})
    conn.commit()
    cur.close(); conn.close()

