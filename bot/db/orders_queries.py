import oracledb

from bot.utils.config import ORACLE_CONFIG
oracledb.init_oracle_client(lib_dir="/Users/abdulmutalib_007/oracle_client/instantclient_23_3")


def get_today_orders():
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT R.INS_ID, R.CREATED_DATE, R.ORDER_SUM, R.ORDER_TYPE
        FROM INS_COST_ORDER R
        WHERE TRUNC(R.CREATED_DATE) = TRUNC(SYSDATE) AND R.ORDER_TYPE = 5
          AND NOT EXISTS (
              SELECT 1 FROM BOT_LOGS B
              WHERE B.req_ID = R.INS_ID
          )
    """)

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_order_votes(order_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dec_user2(M.USER_ID) as FULL_NAME, M.VOTE
        FROM INS_COST_ORDER_MEMBER M
        JOIN TB_USERS U ON U.tb_ID = M.USER_ID
        WHERE M.ORD_ID = :order_id
    """,{"order_id": order_id})

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
