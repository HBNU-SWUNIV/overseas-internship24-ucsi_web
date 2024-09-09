import mysql.connector

# MySQL 서버에 연결
conn = MySQLdb.connect(
    host="localhost",  # 호스트 이름
    user="root",  # MySQL 사용자 이름
    passwd="0000",  # MySQL 사용자 비밀번호
    db="test_db3",  # 연결할 데이터베이스 이름
)

# 커서 생성
cursor = conn.cursor()

# 쿼리 실행 예시

# 신청서 주문 정보 가져오기
# sql_query = "SELECT * FROM orders"

# 재고 가져오기
sql_query = "SELECT * from products"

#
cursor.execute(sql_query)


# 쿼리 결과 가져오기
result = cursor.fetchall()

# 결과 출력
for row in result:
    print(row)

# 연결과 커서 닫기
cursor.close()
conn.close()
