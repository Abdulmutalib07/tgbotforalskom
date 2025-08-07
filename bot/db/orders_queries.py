from db.connection import connection

def get_today_orders():
    query = """
        SELECT R.ID, R.DATE_RASPOR, R.AMOUNT, R.TYPE
        FROM RASPOR R
        WHERE TRUNC(R.DATE_RASPOR) = TRUNC(SYSDATE)
          AND NOT EXISTS (
              SELECT 1 FROM BOT_LOGS B
              WHERE B.ENTITY_ID = R.ID AND B.TYPE = 'RASPOR'
          )
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def get_order_votes(order_id):
    query = """
        SELECT U.FULL_NAME, V.VOTE
        FROM RASPOR_VOTES V
        JOIN USERS U ON U.ID = V.USER_ID
        WHERE V.RASPOR_ID = :order_id
    """
    with connection.cursor() as cursor:
        cursor.execute(query, {'order_id': order_id})
        return cursor.fetchall()
