from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
    jsonify,
)
import os
import csv
import smtplib
from email.mime.text import MIMEText
import MySQLdb

# MySQL 서버에 연결
conn = MySQLdb.connect(
    host="localhost",  # 호스트 이름
    user="root",  # MySQL 사용자 이름
    passwd="ahWkfmxm@32",  # MySQL 사용자 비밀번호
    db="test_db3",  # 연결할 데이터베이스 이름
)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 세션을 위한 시크릿 키 설정

# CSV 파일 경로 설정 (SQL 설정 시 삭제)
user_csv_file_path = "mnt/data_dummy/UserDB.csv"
product_csv_file_path = "mnt/data_dummy/ProductDB.csv"
order_csv_file_path = "mnt/data_dummy/OrderDB.csv"


# CSV 파일에서 사용자 데이터를 읽어오는 함수 (SQL 설정 시 삭제)
def read_users_from_csv():
    users = {}
    with open(user_csv_file_path, mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            users[row["id"]] = {
                "user_id": row["user_id"],
                "id": row["id"],
                "password": row["password"],
                "email": row["email"],
                "department": row["department"],
            }
    return users


# CSV 파일에 새로운 사용자를 추가하는 함수 (SQL 설정 시 삭제)
def write_user_to_csv(user_id, id, password, email, department, name):
    with open(user_csv_file_path, mode="a", newline="") as file:
        fieldnames = ["user_id", "id", "password", "name", "email", "department"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow(
            {
                "user_id": user_id,
                "id": id,
                "password": password,
                "email": email,
                "department": department,
                "name": name,
            }
        )


# Users 테이블에 회원가입 정보 입력
def insert_user(data):
    cursor = conn.cursor()
    sql = "INSERT INTO Users (id, password, name, email, department) VALUES (%s, %s, %s, %s, %s)"
    values = (
        data["id"],
        data["password"],
        data["name"],
        data["email"],
        data["department"],
    )
    cursor.execute(sql, values)
    conn.commit()
    return cursor.lastrowid


def get_user_by_id_and_password(id, password):
    cursor = conn.cursor()
    sql = "SELECT * FROM Users WHERE id = %s AND password = %s"
    cursor.execute(sql, (id, password))
    result = cursor.fetchone()

    if result:
        # 컬럼 이름을 가져와서 튜플을 딕셔너리로 변환
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, result))
    return None


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        input_id = request.form["id"]  # 사용자가 입력한 로그인 ID
        password = request.form["password"]

        # 입력된 ID와 비밀번호에 해당하는 사용자를 조회
        users = get_user_by_id_and_password(input_id, password)

        if users:
            session["user"] = users["id"]  # 세션에 user_id를 저장
            session["user_pk"] = users["user_id"]
            if users.get("department") == "admin":
                return redirect(url_for("admin_page"))
            else:
                return redirect(url_for("user_page"))

        flash("Invalid credentials")
    return render_template("login.html")


# 가입 시 PK 값 지정 (SQL 적용 시 삭제)
def generate_new_user_id():
    # CSV 파일에서 직접 user_id 값을 읽어옴
    with open(user_csv_file_path, mode="r") as file:
        csv_reader = csv.DictReader(file)
        ids = [int(row["user_id"]) for row in csv_reader if row["user_id"].isdigit()]

    if not ids:
        return 1  # 첫 번째 사용자의 ID는 1
    return max(ids) + 1  # 가장 큰 ID에 1을 더하여 새로운 ID 생성


def get_user_by_id(user_id):
    cursor = conn.cursor()
    sql = "SELECT * FROM Users WHERE id = %s LIMIT 1"
    cursor.execute(sql, (user_id,))
    user = cursor.fetchone()  # 결과가 없으면 None 반환
    return user


@app.route("/create_account", methods=["GET", "POST"])
def register():
    # users = read_users_from_csv()
    if request.method == "POST":
        name = request.form["username"]
        id = request.form["id"]  # 사용자가 입력한 'username'을 받아옴
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        email = request.form["email"]
        department = request.form["department"]

        # 사용자 ID가 이미 존재하는지 확인하는 SQL 쿼리
        existing_user = get_user_by_id(id)

        # id가 이미 존재하는지 확인
        if existing_user:
            flash("Username already exists")
        elif password != confirm_password:
            flash("Passwords do not match")
        else:
            user_data = {
                "id": id,
                "password": password,
                "name": name,
                "email": email,
                "department": department,
            }

            # 사용자 정보를 MySQL에 삽입
            insert_user(user_data)
            flash("Registration successful", category="success")
            return redirect(url_for("login"))

    return render_template("register.html")


# 로그아웃 라우트
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# 사용자 존재 여부를 확인하는 함수
def user_exists(user_id):
    cursor = conn.cursor()
    try:
        sql = "SELECT 1 FROM Users WHERE id = %s LIMIT 1"
        cursor.execute(sql, (user_id,))
        exists = cursor.fetchone() is not None  # 결과가 있으면 True, 없으면 False 반환
    finally:
        cursor.close()
    return exists


# User 페이지 라우트
@app.route("/user", methods=["GET", "POST"])
def user_page():
    if "user" in session and user_exists(session["user"]) :

        
        if request.method == "POST":
            user_id = session.get("user_pk")  # 현재 로그인된 사용자 ID
            maker = request.form["brand"]
            toner = request.form["toner"]
            color = request.form["color"]
            quantity = request.form["amount"]



            if maker and toner and color and quantity:
                product_id = find_product_id_sql(maker, toner, color)
                if product_id:
                    #order db추가
                    add_order_to_db(user_id, product_id, quantity)
                    flash("Order successfully submitted!")
                else:
                    flash("Product not found.")
                return redirect(url_for("user_page"))
            else:
                flash("Please fill in all fields.")

        return render_template("user.html")
    else:
        return redirect(url_for("login"))


# 제품 목록을 CSV 파일에서 불러오는 함수

# def get_toner_by_maker(maker):
#     toners = set()  # Set을 사용하여 중복 제거
#     with open(product_csv_file_path, mode="r") as file:
#         csv_reader = csv.DictReader(file)
#         for row in csv_reader:
#             if row["maker"].lower() == maker.lower():
#                 toners.add(row["name"])  # 'name' 필드 사용

#     return sorted(toners)  # Set을 리스트로 변환 후 정렬하여 반환


# 제품목록을 sql에서 불러오는 함수
def get_toner_by_maker(maker):
    cursor = conn.cursor()
    try:
        # SQL 쿼리 작성
        sql_query = """
        SELECT DISTINCT name
        FROM Products
        WHERE brand = %s
        """
        # 쿼리 실행
        cursor.execute(sql_query, (maker,))
        results = cursor.fetchall()
        
        # 결과를 리스트로 변환 및 정렬
        toners = set(row[0] for row in results)  # 중복 제거를 위해 set 사용
        return sorted(toners)  # 리스트로 변환 후 정렬
    finally:
        cursor.close()




# 프린터 제조사에 따라 토너 목록을 반환하는 라우트
@app.route("/get_toners", methods=["POST"])
def get_toners():
    maker = request.form.get("brand")  # 클라이언트에서 'brand'로 전달되는 값을 받음
    if not maker:
        return jsonify({"error": "No maker provided"}), 400

    toners = get_toner_by_maker(maker)
    return jsonify({"toners": toners})
#ok 

def find_product_id(maker, name, color):
    with open(product_csv_file_path, mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if (
                row["maker"].lower() == maker.lower()
                and row["name"].lower() == name.lower()
                and row["color"].lower() == color.lower()
            ):
                return row["product_id"]
    return None  # 해당 조건에 맞는 제품이 없을 경우 None 반환

#위에거 sql로 바꿈 ↓

def find_product_id_sql(maker, name, color):
    cursor = conn.cursor()
    try:
        # SQL 쿼리 작성
        sql_query = """
        SELECT product_id
        FROM Products
        WHERE brand = %s
          AND name = %s
          AND color = %s
        LIMIT 1
        """
        # 쿼리 실행
        cursor.execute(sql_query, (maker, name, color))
        result = cursor.fetchone()
        
        # 결과가 있으면 product_id 반환, 없으면 None 반환
        if result:
            return result[0]
        else:
            return None
    finally:
        cursor.close()





def add_order_to_csv(user_id, product_id, quantity):
    order_id = generate_new_order_id()  # 새로운 주문 ID 생성

    with open(order_csv_file_path, mode="a", newline="") as file:
        fieldnames = ["order_id", "product_id", "user_id", "quantity"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow(
            {
                "order_id": order_id,
                "user_id": user_id,
                "product_id": product_id,
                "quantity": quantity,
            }
        )

def add_order_to_db(user_id, product_id, quantity):
    cursor = conn.cursor()
    try:
        # 새로운 주문 ID 생성 (자동 증가되는 PK를 사용하면 이 부분은 생략 가능)
        sql_query = """
        INSERT INTO Orders (user_id, toner_id, quantity)
        VALUES (%s, %s, %s)
        """
        # 쿼리 실행
        cursor.execute(sql_query, (user_id, product_id, quantity))
        # 변경사항 커밋
        conn.commit()

        # 마지막으로 삽입된 ID를 가져옴 (자동 증가 PK 사용 시)
        order_id = cursor.lastrowid
        return order_id
    except MySQLdb.Error as e:
        # 에러 발생 시 롤백
        conn.rollback()
        print(f"Error: {e}")
        return None
    finally:
        cursor.close()

# 새로운 주문 ID 생성 함수
def generate_new_order_id():
    with open(order_csv_file_path, mode="r") as file:
        csv_reader = csv.DictReader(file)
        order_ids = [
            int(row["order_id"]) for row in csv_reader if row["order_id"].isdigit()
        ]

    if not order_ids:
        return 1
    return max(order_ids) + 1


# Admin 페이지 라우트
@app.route("/admin")
def admin_page():
    if "user" in session and session["user"] in read_users_from_csv():
        user_data = read_users_from_csv()[session["user"]]
        if user_data.get("department") == "admin":
            return render_template("admin.html")
    else:
        return redirect(url_for("login"))


# Dashboard 페이지 라우트 (Admin만 접근 가능)
@app.route("/dashboard")
def dashboard():
    if "user" in session and session["user"] in read_users_from_csv():
        user_data = read_users_from_csv()[session["user"]]
        if user_data.get("department") == "admin":
            return render_template("dashboard.html")
    else:
        return redirect(url_for("login"))


# Application Approval 페이지 라우트 (Admin만 접근 가능)
@app.route("/approval")
def approval_page():
    if "user" in session and session["user"] in read_users_from_csv():
        user_data = read_users_from_csv()[session["user"]]
        if user_data.get("department") == "admin":
            return render_template("approval.html")
    else:
        return redirect(url_for("login"))


@app.route("/send_mail", methods=["POST"])
def send_mail():
    msg = request.form["select"]
    return render_template("approval.html", msg=msg)


@app.route("/approve", methods=["POST"])
def approve():
    msg = request.form["date"]
    time = request.form["time"]
    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.ehlo()
    smtp.starttls()

    # 보낼 계정
    smtp.login("20221095@edu.hanbat.ac.kr", "ipxx qflq btpb mdgc")

    send_msg = MIMEText(f"승인 날짜 : {msg} 시간 : {time}")
    send_msg["Subject"] = "승인"
    smtp.sendmail("20221095@edu.hanbat.ac.kr", "luonj@naver.com", send_msg.as_string())

    smtp.quit()

    return render_template("approval.html")


@app.route("/Defer", methods=["POST"])
def Defer():
    msg = request.form["Defer"]
    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.ehlo()
    smtp.starttls()

    # 보낼 계정
    smtp.login("20221095@edu.hanbat.ac.kr", "ipxx qflq btpb mdgc")

    send_msg = MIMEText(f"보류사유: {msg}")
    send_msg["Subject"] = "보류"
    smtp.sendmail("20221095@edu.hanbat.ac.kr", "luonj@naver.com", send_msg.as_string())

    smtp.quit()

    return render_template("approval.html")


@app.route("/reject", methods=["POST"])
def reject():
    msg = request.form["reject"]
    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.ehlo()
    smtp.starttls()

    # 보낼 계정
    smtp.login("20221095@edu.hanbat.ac.kr", "ipxx qflq btpb mdgc")

    send_msg = MIMEText(f"거절사유: {msg}")
    send_msg["Subject"] = "거절"
    smtp.sendmail("20221095@edu.hanbat.ac.kr", "luonj@naver.com", send_msg.as_string())

    smtp.quit()
    return render_template("approval.html")


if __name__ == "__main__":
    app.run(debug=True)
