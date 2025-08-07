import oracledb

from bot.utils.config import ORACLE_CONFIG
oracledb.init_oracle_client(lib_dir="/Users/abdulmutalib_007/oracle_client/instantclient_23_3")



def get_new_requests(status=None, status_gt=None):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()

    query = """
        SELECT 
            INS_ID, STATUS, OWNER,
            TO_CHAR(INS_DATEF, 'DD.MM.YYYY') AS INS_DATEF,
            TO_CHAR(INS_DATET, 'DD.MM.YYYY') AS INS_DATET,
            TO_CHAR(INS_PREM, 'FM999G999G999D00') AS INS_PREM,
            TO_CHAR(INS_OTV, 'FM999G999G999D00') AS INS_OTV,
            TO_CHAR(INS_PREM * 36500 / (INS_OTV * (INS_DATET - INS_DATEF)), 'FM999G999G999D00') AS KEF,
            REQ_NAME,
            dec_division(DIVISION_ID, 1) AS DIVISION_ID
        FROM INS_REQUEST
        WHERE CREATED_DATE BETWEEN SYSDATE - 3 AND SYSDATE
    """

    if status is not None:
        query += " AND STATUS = :1"
        cursor.execute(query, [status])
    elif status_gt is not None:
        query += " AND STATUS > :1"
        cursor.execute(query, [status_gt])
    else:
        cursor.execute(query)

    result = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return result



def update_request_status(ins_id, user_id, status):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE INS_REQUEST
        SET STATUS = :1
        WHERE INS_ID = :2
    """, [status, ins_id])
    print(f"[DEBUG] Обновление: ins_id={ins_id}, user_id={user_id}, status={status}")

    # логика добавления в INS_REQUEST_MEMBER
    cursor.execute("""
        MERGE INTO INS_REQUEST_MEMBER irm
        USING DUAL
        ON (irm.REQ_ID = :1 AND irm.USER_ID = :2)
        WHEN NOT MATCHED THEN
            INSERT (REQ_ID, USER_ID, VOTE_DATE)
            VALUES (:1, :2, SYSDATE)
    """, [ins_id, user_id])

    conn.commit()
    cursor.close()
    conn.close()

def log_action(telegram_id, action, ins_id, member_name, details):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO BOT_LOGS (TELEGRAM_ID, ACTION_TYPE, REQ_ID, USER_ID, DETAILS)
        VALUES (:tid, :act, :ins, :usr, :det)
    """, [str(telegram_id), action, ins_id, member_name, details])
    conn.commit()
    cursor.close()
    conn.close()

def get_participant_votes(req_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dec_user2(irm.USER_ID) as FULL_NAME, irm.USER_ID, irm.VOTE FROM INS_REQUEST_MEMBER irm
        JOIN TB_USERS u ON irm.USER_ID = u.TB_ID
        WHERE REQ_ID = :1
    """, [req_id])
    result =[
        {'FULL_NAME': row[0], 'VOTE': row[1]}
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()
    return result


def is_ready_for_closure(req_id):
    votes = get_participant_votes(req_id)
    return all(vote in (1, 2) for _, vote in votes)


def finalize_request(req_id):
    votes = get_participant_votes(req_id)
    final_status = 2 if all(v == 1 for _, v in votes) else 3  # 2 = одобрено, 3 = отказ
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE INS_REQUEST SET STATUS = :1 WHERE INS_ID = :2
    """, [final_status, req_id])
    conn.commit()
    cursor.close()
    conn.close()
    return final_status


def get_users_pending_vote(req_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT irm.USER_ID, dec_user2(tu.tb_id) as FULL_NAME
        FROM TB_USERS tu
        JOIN INS_REQUEST_MEMBER irm ON tu.TB_ID = irm.USER_ID
        WHERE irm.REQ_ID = :1 AND irm.VOTE = 0
    """, [req_id])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"ID": row[0], "FULL_NAME": row[1]} for row in rows]


def get_user_role(telegram_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TB_COMMITTEE FROM TB_USERS
        WHERE TELEGRAM_ID = :1
    """, [str(telegram_id)])
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result[0] if result else None


def is_user_admin(telegram_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT IS_ADMIN FROM TB_USERS
        WHERE TELEGRAM_ID = :1
    """, [str(telegram_id)])
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result and result[0] == 1


def get_all_users():
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TELEGRAM_ID, TB_COMMITTEE, IS_ADMIN, dec_user2(tb_id) as FULL_NAME
        FROM TB_USERS
        WHERE TELEGRAM_ID IS NOT NULL
    """)
    users = [
        {
            "TELEGRAM_ID": row[0],
            "TB_COMMITTEE": row[1],
            "IS_ADMIN": row[2],
            "FULL_NAME": row[3]
        }
        for row in cursor.fetchall()
    ]
    cursor.close()
    conn.close()
    return users

def get_accepted_outside_bot_requests():
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.INS_ID, r.OWNER, r.INS_DATEF, r.INS_DATET,
               TO_CHAR(r.INS_PREM, 'FM999G999G999D00') AS INS_PREM,
               TO_CHAR(r.INS_OTV, 'FM999G999G999D00') AS INS_OTV,
               TO_CHAR(r.INS_PREM * 36500 / (r.INS_OTV * (r.INS_DATET - r.INS_DATEF)), 'FM999G999G999D00') AS KEF,
               r.REQ_NAME, dec_division(r.DIVISION_ID, 1) AS DIVISION_ID
        FROM INS_REQUEST r
        WHERE r.STATUS = 1
          AND NOT EXISTS (
              SELECT 1 FROM BOT_LOGS b WHERE b.REQ_ID = r.INS_ID AND b.ACTION_TYPE = 'accept'
          )
          AND r.CREATED_DATE BETWEEN SYSDATE - 3 AND SYSDATE
    """)
    result = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return result


def get_all_votes_with_names(req_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            dec_user2(tu.tb_id) AS FULL_NAME,
            irm.VOTE,
            tu.TB_COMMITTEE,
            tu.IS_ADMIN
        FROM INS_REQUEST_MEMBER irm
        JOIN TB_USERS tu ON tu.TB_ID = irm.USER_ID
        WHERE irm.REQ_ID = :1
    """, [req_id])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {
            "FULL_NAME": row[0],
            "VOTE": row[1],
            "TB_COMMITTEE": row[2],
            "IS_ADMIN": row[3]
        }
        for row in rows
    ]


def is_fully_approved(ins_id, ins_otv):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) 
        FROM INS_REQUEST_MEMBER m
        JOIN TB_USERS u ON m.USER_ID = u.TB_ID
        WHERE m.REQ_ID = :1 
          AND m.VOTE != 1
          AND (
            m.USER_ID != 2003 
            OR TO_NUMBER(:2) >= 20000000000
          )
    """, [ins_id, ins_otv])
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    return count == 0  # True если все проголосовали за

def get_finalized_requests():
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.INS_ID, r.STATUS
        FROM INS_REQUEST r
        WHERE r.STATUS IN (2, 3)
          AND NOT EXISTS (
              SELECT 1 FROM BOT_LOGS b
              WHERE b.REQ_ID = r.INS_ID
                AND b.ACTION_TYPE = 'final'
          )
          AND r.CREATED_DATE > SYSDATE - 3
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"INS_ID": row[0], "STATUS": row[1]} for row in rows]
