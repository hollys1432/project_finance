import psycopg2

# 슈퍼유저로 DB 접속
conn = psycopg2.connect(
    dbname="finance",
    user="postgres",
    password="1234",
    host="localhost",  # 또는 원격 서버 IP
    port=5432
)
conn.autocommit = True  # CREATE USER 등 DDL 명령어에는 autocommit이 필요

cur = conn.cursor()

# 유저 생성
try:
    cur.execute("CREATE USER user_fin WITH PASSWORD 'deskjet930';")
    print("User created successfully.")
except psycopg2.errors.DuplicateObject:
    print("User already exists.")

# 권한 부여
# 특정 데이터베이스에 연결
cur.execute("GRANT CONNECT ON DATABASE finance TO user_fin;")
# 테이블 생성 권한
cur.execute("GRANT CREATE ON DATABASE finance TO user_fin;")

cur.execute("GRANT ALL PRIVILEGES ON DATABASE finance TO user_fin;")
cur.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO user_fin;")
cur.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO user_fin;")
cur.execute("GRANT USAGE ON SCHEMA public TO user_fin;")
cur.execute("GRANT CREATE ON SCHEMA public TO user_fin;")
print("hihi")

cur.close()
conn.close()