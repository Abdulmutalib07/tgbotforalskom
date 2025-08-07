from db.connection import connection

def log_action(entity_id, type='RASPOR'):
    query = """
        INSERT INTO BOT_LOGS (ENTITY_ID, TYPE, SENT_AT)
        VALUES (:id, :type, SYSDATE)
    """
    with connection.cursor() as cursor:
        cursor.execute(query, {'id': entity_id, 'type': type})
        connection.commit()
