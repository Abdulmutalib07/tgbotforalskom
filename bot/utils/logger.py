import oracledb
from bot.utils.config import ORACLE_CONFIG

def log_action(entity_id, type='RASPOR'):
    query = """
        INSERT INTO BOT_LOGS (REQ_ID, ACTION_TYPE)
    VALUES (:id, :type)
    """
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute(query, {'id': entity_id, 'type': type})
    conn.commit()
    cursor.close()
    conn.close()
