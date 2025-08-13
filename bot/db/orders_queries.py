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
        ORDER BY CASE M.USER_ID
            WHEN 56   THEN 1
            WHEN 2003 THEN 2
            WHEN 26   THEN 3
            WHEN 1771 THEN 4
            ELSE 5
          END 
    """,{"order_id": order_id})

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_vote_status(order_id, telegram_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT VOTE
        FROM INS_COST_ORDER_MEMBER
        WHERE ORD_ID = :ORDER_ID
          AND USER_ID = (SELECT TB_ID FROM TB_USERS WHERE TELEGRAM_ID = :TG_ID)
    """, {"ORDER_ID": order_id, "TG_ID": str(telegram_id)})
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None


def set_vote(order_id, telegram_id, vote):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()

    # 1. Ставим голос
    cursor.execute("""
        UPDATE INS_COST_ORDER_MEMBER
        SET VOTE = :VOTE
        WHERE ORD_ID = :ORDER_ID
          AND USER_ID = (SELECT TB_ID FROM TB_USERS WHERE TELEGRAM_ID = :TG_ID)
    """, {
        "VOTE": vote,
        "ORDER_ID": order_id,
        "TG_ID": str(telegram_id)
    })
    updated = cur.rowcount
    conn.commit()

    # после updated/commit
    conn2 = oracledb.connect(**ORACLE_CONFIG)
    c2 = conn2.cursor()
    c2.execute("SELECT COUNT(*) FROM INS_COST_ORDER_MEMBER WHERE ORD_ID=:ORDER_ID AND VOTE=0",
               {"ORDER_ID": order_id})
    left, = c2.fetchone()
    if left == 0:
        c2.execute(
            "INSERT INTO BOT_LOGS (REQ_ID, ACTION_TYPE, DETAILS) VALUES "
            "(:id, 'RASPOR_DONE', 'Все участники одобрили')",
            {"id": str(order_id)})
        conn2.commit()
    c2.close();
    conn2.close()
    # 2. Проверяем — остались ли те, кто не проголосовал
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INS_COST_ORDER_MEMBER
        WHERE ORD_ID = :ORDER_ID AND VOTE = 0
    """, {"ORDER_ID": order_id})

    left_cnt, = cursor.fetchone()

    # 3. Если все проголосовали — пишем в BOT_LOGS
    if left_cnt == 0:
        cursor.execute("""
            INSERT INTO BOT_LOGS (REQ_ID, ACTION_TYPE, DETAILS)
            VALUES (:id, 'RASPOR_DONE', 'Все участники одобрили')
        """, {"id": order_id})
        conn.commit()

    cursor.close()
    conn.close()

    return left_cnt  # можно вернуть, чтобы обработчик понимал



def get_pending_orders():
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT b.REQ_ID, b.MESSAGE_ID, b.CHAT_ID
        FROM BOT_LOGS b
        JOIN INS_COST_ORDER o ON o.INS_ID = b.REQ_ID
        WHERE o.ORDER_TYPE = 5
        AND NOT EXISTS (
            SELECT 1 FROM BOT_LOGS b2
                WHERE b2.REQ_ID = b.REQ_ID AND b2.ACTION_TYPE = 'RASPOR_DONE'
  )
        AND EXISTS (
            SELECT 1 FROM INS_COST_ORDER_MEMBER m
            WHERE m.ORD_ID = o.INS_ID AND m.VOTE = 0
        )
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_order_by_id(order_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT INS_ID, CREATED_DATE, ORDER_SUM, ORDER_TYPE
        FROM INS_COST_ORDER
        WHERE INS_ID = :ORDER_ID
    """, {"ORDER_ID": order_id})
    row = cur.fetchone()
    cur.close(); conn.close()
    return row  # (INS_ID, CREATED_DATE, ORDER_SUM, ORDER_TYPE)