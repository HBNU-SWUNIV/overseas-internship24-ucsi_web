import MySQLdb

# MySQL 서버에 연결
conn = MySQLdb.connect(
    host="localhost",  # 호스트 이름
    user="root",  # MySQL 사용자 이름
    passwd="0000",  # MySQL 사용자 비밀번호
    db="test_db3",  # 연결할 데이터베이스 이름
)

# 커서 생성
cursor = conn.cursor()

# 1. `orders` 테이블에서 각 상품의 주문 수량을 조회
sql_query_orders = """
    SELECT toner_id, SUM(quantity) as total_count
    FROM Orders  -- 테이블 이름은 Orders임
    GROUP BY toner_id
"""
cursor.execute(sql_query_orders)
orders = cursor.fetchall()

# 2. `products` 테이블의 재고를 업데이트
for order in orders:
    toner_id, total_count = order  # 'toner_id'를 올바르게 매핑

    update_query = """
        UPDATE Products
        SET stock = stock - %s
        WHERE product_id = %s  -- Products 테이블의 기본 키인 product_id 사용
    """
    cursor.execute(update_query, (total_count, toner_id))

# 변경 사항 커밋
conn.commit()

# 재고 업데이트 결과 확인 (옵션)
sql_query_products = "SELECT * FROM Products"
cursor.execute(sql_query_products)
products = cursor.fetchall()

# 결과 출력
print("Updated products stock:")
for row in products:
    print(row)

# 연결과 커서 닫기
cursor.close()
conn.close()
