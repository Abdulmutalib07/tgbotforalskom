import oracledb
from bot.utils.config import ORACLE_CONFIG

def log_action(entity_id, type='RASPOR', message_id=None):
    query = """
        INSERT INTO BOT_LOGS (REQ_ID, ACTION_TYPE, ACTION_DATE, MESSAGE_ID)
    VALUES (:id, :type, :SYSDATE, :message_id)
    """
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute(query, {'id': entity_id, 'type': type, 'message_id': message_id})
    conn.commit()
    cursor.close()
    conn.close()
