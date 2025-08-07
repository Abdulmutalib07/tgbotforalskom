import oracledb
from config import ORACLE_CONFIG

async def check_auth(telegram_id):
    conn = oracledb.connect(**ORACLE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ID, TB_COMMITTEE, dec_user2(tb_id) as FULL_NAME
        FROM TB_USERS
        WHERE TELEGRAM_ID = :1
    """, [str(telegram_id)])

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        user_id, role, full_name = row
        return {
            "user_id": user_id,
            "role": role,
            "full_name": full_name
        }
    else:
        return None