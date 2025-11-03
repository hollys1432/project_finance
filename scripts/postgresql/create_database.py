import psycopg2
from psycopg2 import sql


from psycopg2 import sql, OperationalError

def create_database(db_name, user, password, host="localhost", port=5432, template_db="postgres"):
    """
    PostgreSQL에서 새로운 데이터베이스를 생성하는 함수

    Args:
        db_name (str): 생성할 데이터베이스 이름
        user (str): PostgreSQL 사용자 이름
        password (str): PostgreSQL 비밀번호
        host (str): DB 서버 주소 (기본값: localhost)
        port (int): DB 포트 (기본값: 5432)
        template_db (str): 연결할 기본 데이터베이스 (기본값: postgres)

    Returns:
        bool: 생성 성공 시 True, 실패 시 False
    """
    try:
        # 기본 DB에 접속
        conn = psycopg2.connect(
            dbname=template_db,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True  # CREATE DATABASE는 트랜잭션 외부에서 실행

        with conn.cursor() as cur:
            # SQL 안전하게 작성 (SQL Injection 방지)
            cur.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            ))
        print(f"✅ 데이터베이스 '{db_name}' 생성 완료.")
        return True

    except OperationalError as e:
        print(f"❌ 데이터베이스 생성 실패: {e}")
        return False

    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    create_database(db_name="finance", user="postgres", password="1234", template_db="postgres")
