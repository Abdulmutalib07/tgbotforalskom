import oracledb
from bot.utils.config import ORACLE_CONFIG

def log_action(entity_id, type='RASPOR', message_id=None, action_type=None):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO BOT_LOGS (REQ_ID, ACTION_TYPE, ACTION_DATE, MESSAGE_ID)
    VALUES (:id, :type, :SYSDATE, :message_id)
    """,{
        "p_req_id": str(entity_id),          # REQ_ID у тебя VARCHAR2(32)
        "p_action_type": action_type,
        "p_message_id": message_id
    })
    conn.commit()
    cur.close()
    conn.close()
