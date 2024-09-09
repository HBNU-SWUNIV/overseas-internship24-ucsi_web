import mysql.connector

# MySQL 연결 설정
cnn = mysql.connector.connect(
    host="localhost", user="root", password="0000", database="test_db3"
)


# Users 테이블에 회원가입 정보 입력
def insert_user(data, cb):
    cursor = cnn.cursor()
    sql = "INSERT INTO Users (id, password, name, email, department) VALUES (%s, %s, %s, %s, %s)"
    values = (
        data["id"],
        data["password"],
        data["name"],
        data["email"],
        data["department"],
    )

    cursor.execute(sql, values)
    cnn.commit()
    cb(cursor.lastrowid)


# Users 테이블에서 회원 정보 읽기
def select_user(id, cb):
    cursor = cnn.cursor(dictionary=True)
    sql = "SELECT * FROM Users WHERE id = %s LIMIT 1"

    cursor.execute(sql, (id,))
    row = cursor.fetchone()
    cb(row)


# test

# 사용자 데이터 생성
# user_data = {
#     "id": "testuser123",
#     "password": "password123",
#     "name": "John Doe",
#     "email": "johndoe@example.com",
#     "department": "Sales",
# }


# def user_insert_callback(user_id):
#     print(f"Inserted user with ID: {user_id}")


# # 사용자 삽입 함수 호출
# insert_user(user_data, user_insert_callback)


def user_select_callback(user):
    if user:
        print("User found:", user)
    else:
        print("User not found")


# 사용자 조회 함수 호출
select_user("testuser123", user_select_callback)
