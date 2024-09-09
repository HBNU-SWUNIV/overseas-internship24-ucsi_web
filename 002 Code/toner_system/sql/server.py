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
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_table
import pandas as pd
import plotly.express as px
import MySQLdb

# MySQL 서버에 연결
conn = MySQLdb.connect(
    host="localhost",  # 호스트 이름
    user="root",  # MySQL 사용자 이름
    passwd="0000",  # MySQL 사용자 비밀번호
    db="test_db4",  # 연결할 데이터베이스 이름
)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 세션을 위한 시크릿 키 설정

# CSV 파일 경로 설정 (SQL 설정 시 삭제)
user_csv_file_path = "mnt/data_dummy/UserDB.csv"
product_csv_file_path = "mnt/data_dummy/ProductDB.csv"
order_csv_file_path = "mnt/data_dummy/OrderDB.csv"

# Dash 애플리케이션 생성
dash_app = dash.Dash(__name__, server=app, url_base_pathname="/dashboard/")

# 데이터 로드
df = pd.read_csv(product_csv_file_path)

# 브랜드 목록과 해당 브랜드에 속한 토너 목록 생성
brand_options = [{"label": brand, "value": brand} for brand in df["maker"].unique()]

# Dash 레이아웃 설정
dash_app.layout = html.Div(
    children=[
        dcc.Dropdown(
            id="brand-dropdown",
            options=brand_options,
            placeholder="Select a brand",
        ),
        dcc.Dropdown(
            id="toner-dropdown",
            placeholder="Select a toner",
        ),
        dcc.Graph(id="stock-graph"),
        dash_table.DataTable(
            id="stock-table",
            columns=[
                {"name": "Color", "id": "color"},
                {"name": "Stock", "id": "stock"},
            ],
            style_table={"width": "80%", "margin": "auto"},
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
            style_cell={
                "textAlign": "center",
                "padding": "10px",
                "border": "1px solid black",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248)"}
            ],
        ),
        html.Div(id="output-container"),
    ]
)


def test_smtp_connection():
    try:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login("20221095@edu.hanbat.ac.kr", "ipxx qflq btpb mdgc")
        print("SMTP connection successful!")
        smtp.quit()
    except Exception as e:
        print(f"SMTP connection failed: {e}")


def update_stock(product_id, quantity, operation="subtract"):
    """
    product_id: 업데이트할 제품의 ID
    quantity: 변경할 수량
    operation: 'subtract' 또는 'add', 재고를 차감할지 추가할지 결정
    """
    updated_rows = []
    stock_updated = False

    with open(product_csv_file_path, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["product_id"] == product_id:
                current_stock = int(row["stock"])

                if operation == "subtract":
                    if current_stock >= quantity:
                        row["stock"] = str(current_stock - quantity)
                        stock_updated = True
                    else:
                        print(f"Insufficient stock for product {product_id}.")
                elif operation == "add":
                    row["stock"] = str(current_stock + quantity)
                    stock_updated = True

            updated_rows.append(row)

    if stock_updated:
        with open(product_csv_file_path, mode="w", newline="") as file:
            fieldnames = ["product_id", "maker", "name", "color", "stock"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)
        print(f"Stock for product {product_id} updated successfully.")
    else:
        print(f"No changes made to the stock for product {product_id}.")


# CSV 파일에서 사용자 데이터를 읽어오는 함수 (SQL 설정 시 삭제)
def read_users_from_csv():
    users = {}
    with open(user_csv_file_path, mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            users[row["id"]] = {
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


# 기본 라우트: 로그인 페이지
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
    if "user" in session and user_exists(session["user"]):

        if request.method == "POST":
            user_id = session.get("user_pk")  # 현재 로그인된 사용자 ID
            maker = request.form["brand"]
            toner = request.form["toner"]
            color = request.form["color"]
            quantity = request.form["amount"]

            if maker and toner and color and quantity:
                product_id = find_product_id(maker, toner, color)
                if product_id:
                    # 주문 정보를 MySQL에 삽입
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


# 제품 목록을 불러오는 함수
def get_toner_by_maker(maker):
    toners = set()  # Set을 사용하여 중복 제거
    cursor = conn.cursor()
    try:
        query = "SELECT name FROM Products WHERE brand = %s"
        cursor.execute(query, (maker,))
        rows = cursor.fetchall()

        for row in rows:
            toners.add(row[0])  # 'name' 필드 사용

    finally:
        cursor.close()

    return sorted(toners)  # Set을 리스트로 변환 후 정렬하여 반환


# 프린터 제조사에 따라 토너 목록을 반환하는 라우트
@app.route("/get_toners", methods=["POST"])
def get_toners():
    maker = request.form.get("brand")  # 클라이언트에서 'brand'로 전달되는 값을 받음
    if not maker:
        return jsonify({"error": "No maker provided"}), 400

    toners = get_toner_by_maker(maker)
    return jsonify({"toners": toners})


def find_product_id(brand, name, color):
    cursor = conn.cursor()
    try:
        sql = "SELECT product_id FROM Products WHERE brand = %s AND name = %s AND color = %s"
        cursor.execute(sql, (brand, name, color))
        result = cursor.fetchone()

        # 수동으로 딕셔너리로 변환
        if result:
            return result[0]
        else:
            return None

    finally:
        cursor.close()


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


# Admin 페이지 라우트
@app.route("/admin")
def admin_page():
    if "user" in session and user_exists(session["user"]):
        cursor = conn.cursor()
        try:
            sql = "SELECT department FROM Users WHERE id = %s LIMIT 1"
            cursor.execute(sql, (session["user"],))
            department = cursor.fetchone()
            if department and department[0] == "admin":
                return render_template("admin.html")
        finally:
            cursor.close()
    else:
        return redirect(url_for("login"))


# Dashboard 페이지 라우트 (Admin만 접근 가능)
# @app.route('/dashboard')
# def dashboard():
#     if 'user' in session and session['user'] in read_users_from_csv():
#         user_data = read_users_from_csv()[session['user']]
#         if user_data.get('department') == 'admin':
#             return render_template('dashboard.html')
#     else:
#         return redirect(url_for('login'))


# 브랜드 선택에 따라 토너 목록 업데이트
@dash_app.callback(
    Output("toner-dropdown", "options"), [Input("brand-dropdown", "value")]
)
def set_toner_options(selected_brand):
    filtered_df = df[df["maker"] == selected_brand]
    return [{"label": toner, "value": toner} for toner in filtered_df["name"].unique()]


# 토너 선택에 따라 재고량 표시 및 막대 그래프 생성
@dash_app.callback(
    Output("stock-table", "data"),
    Output("stock-graph", "figure"),
    [Input("toner-dropdown", "value")],
)
def update_output(selected_toner):
    if selected_toner:
        toner_info = df[df["name"] == selected_toner]

        # 색상별 재고량을 계산 및 순서 지정
        stock_by_color = toner_info.groupby("color")["stock"].sum().reset_index()
        stock_by_color["color"] = pd.Categorical(
            stock_by_color["color"],
            categories=["black", "red", "green", "blue"],
            ordered=True,
        )
        stock_by_color = stock_by_color.sort_values("color")

        # 막대 그래프 생성
        fig = px.bar(
            stock_by_color,
            x="color",
            y="stock",
            title=f"{selected_toner} Stock by Color",
            color="color",
            color_discrete_map={
                "black": "black",
                "red": "red",
                "green": "green",
                "blue": "blue",
            },
        )

        # DataTable에 표시할 데이터 설정
        table_data = stock_by_color.to_dict("records")

        return table_data, fig

    return [], {}


@app.route("/dashboard/")
def dashboard():
    return dash_app.index()


# 함수에서 쿼리 결과를 딕셔너리로 변환
def fetch_as_dict(cursor, query, params=None):
    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    results = cursor.fetchall()
    return [dict(zip(columns, row)) for row in results]


# Application Approval 페이지 라우트 (Admin만 접근 가능)
@app.route("/approval")
def approval_page():
    if "user" in session and user_exists(session["user"]):
        cursor = conn.cursor()
        try:
            sql = "SELECT department FROM Users WHERE id = %s LIMIT 1"
            cursor.execute(sql, (session["user"],))
            department = cursor.fetchone()
            if department and department[0] == "admin":
                return render_approval_page()  # 이곳에서 render_approval_page 호출
                # return render_template("approval.html")
        finally:
            cursor.close()
    else:
        return redirect(url_for("login"))


def render_approval_page(msg=None, selected_order=None):
    order_data = []
    product_data = {}
    user_data = {}

    cursor = conn.cursor()  # 기본 커서 사용

    # Products 테이블에서 데이터 조회
    product_query = "SELECT product_id, name, color FROM Products"
    product_rows = fetch_as_dict(cursor, product_query)
    product_data = {
        row["product_id"]: {"name": row["name"], "color": row["color"]}
        for row in product_rows
    }

    # Users 테이블에서 데이터 조회
    user_query = "SELECT user_id, name, department, email FROM Users"
    user_rows = fetch_as_dict(cursor, user_query)
    user_data = {
        row["user_id"]: {
            "name": row["name"],
            "department": row.get("department", "N/A"),
            "email": row.get("email", "N/A"),
        }
        for row in user_rows
    }

    # Orders 테이블에서 데이터 조회
    order_query = "SELECT order_id, toner_id, user_id, quantity, Done FROM Orders"
    order_rows = fetch_as_dict(cursor, order_query)
    order_data = [
        {
            "order_id": row["order_id"],
            "user_name": user_data[row["user_id"]]["name"],
            "department": user_data[row["user_id"]]["department"],
            "product_name": product_data[row["toner_id"]]["name"],
            "color": product_data[row["toner_id"]]["color"],
            "quantity": row["quantity"],
            "user_id": row["user_id"],
            "email": user_data[row["user_id"]]["email"],
        }
        for row in order_rows
        if not row.get("Done")
    ]

    # 연결 종료
    cursor.close()

    # HTML 표를 생성
    table_html = '<form method="POST" action="/process_orders" id="orderForm">'
    table_html += '<table border="1">'
    table_html += "<tr><th>Select</th><th>User Name</th><th>Department</th><th>Product Name</th><th>Color</th><th>Quantity</th></tr>"

    if not order_data:
        print("No data found for rendering the table.")
    else:
        for order in order_data:
            table_html += (
                f"<tr>"
                f"<td><input type='radio' name='order_id' value='{order['order_id']}' onchange='showActionButtons(\"{order['order_id']} - {order['user_name']} - {order['department']} - {order['product_name']} ({order['color']})\", \"{order['user_id']}\")'></td>"
                f"<td>{order['user_name']}</td>"
                f"<td>{order['department']}</td>"
                f"<td>{order['product_name']}</td>"
                f"<td>{order['color']}</td>"
                f"<td>{order['quantity']}</td>"
                f"</tr>"
            )

    table_html += "</table>"
    table_html += """
        <div id="actionButtons" style="display: none; margin-top: 20px;">
            <label for="select_action">Action:</label>
            <select id="select_action" name="select_action" required>
                <option value="">Select Action</option>
                <option value="approve">Approve</option>
                <option value="defer">Defer</option>
                <option value="reject">Reject</option>
            </select>
            <input type="hidden" name="user_id" id="hidden_user_id">
        </div>
    """
    table_html += "</form>"

    return render_template(
        "approval.html", table_html=table_html, msg=msg, selected_order=selected_order
    )


@app.route("/process_orders", methods=["POST"])
def process_orders():
    user_id = request.form.get("user_id", type=int)
    selected_order = request.form.get("order_id")

    order_id = int(selected_order.split(" - ")[0])

    print(f"Selected Order ID: {selected_order}")
    print(f"User ID: {user_id}")

    if not selected_order or not user_id:
        flash("No orders selected or User ID missing.", category="error")
        return redirect(url_for("approval_page"))

    # user_id에 해당하는 email을 가져옴
    email = get_email_by_user_id(user_id)

    if not email:
        flash("Email address not found.", category="error")
        return redirect(url_for("approval_page"))

    # 세션에 user_id와 email 저장
    session["apply_user_id"] = user_id
    session["apply_user_email"] = email
    session["apply_order_id"] = order_id

    action = request.form.get("select_action")

    if action == "approve":
        return render_approval_page(msg="approve", selected_order=selected_order)
    elif action == "defer":
        return render_approval_page(msg="defer", selected_order=selected_order)
    elif action == "reject":
        return render_approval_page(msg="reject", selected_order=selected_order)
    else:
        flash("No valid action selected.", category="error")
        return redirect(url_for("approval_page"))


def get_email_by_user_id(user_id, file_path=user_csv_file_path):
    with open(file_path, mode="r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row["user_id"] == str(user_id):  # user_id를 문자열로 비교
                return row["email"]  # 이메일을 반환
    return None  # 이메일을 찾지 못한 경우 None 반환


@app.route("/approve", methods=["POST"])
def approve():
    user_id = session.get("apply_user_id")
    order_id = session.get("apply_order_id")
    email = session.get("apply_user_email")
    date = request.form["date"]
    time = request.form["time"]

    print(f"Order ID from session: {order_id}")

    if not email:
        flash("Email address not found.", category="error")
        return redirect(url_for("approval_page"))

    try:
        product_id = None
        quantity = 0
        rows = []  # 전체 데이터를 저장할 리스트

        # OrderDB.csv에서 선택된 주문의 제품 ID와 수량을 가져옴
        with open(order_csv_file_path, mode="r", newline="") as file:
            csv_reader = csv.DictReader(file)
            rows = list(csv_reader)  # 전체 데이터를 리스트에 저장
            for row in rows:
                print(
                    f"Checking row: {row['order_id']}, {row['product_id']}, {row['quantity']}"
                )
                if row["order_id"] == str(
                    order_id
                ):  # order_id를 문자열로 변환하여 비교
                    product_id = row["product_id"]
                    quantity = int(row["quantity"])
                    break

        print(f"Product ID: {product_id}, Quantity: {quantity}")
        if product_id:
            # Stock 업데이트 함수 호출
            update_stock(product_id, quantity)

            # 이메일 발송 과정 (기존 코드 사용)
            smtp = smtplib.SMTP("smtp.gmail.com", 587)
            smtp.ehlo()
            smtp.starttls()

            # 보낼 계정
            smtp.login("20221095@edu.hanbat.ac.kr", "ipxx qflq btpb mdgc")

            send_msg = MIMEText(f"승인 날짜 : {date} 시간 : {time}")
            send_msg["Subject"] = "승인"
            smtp.sendmail("20221095@edu.hanbat.ac.kr", email, send_msg.as_string())

            smtp.quit()

            flash(f"Selected Order approved and stock updated.", category="success")

            # OrderDB.csv 파일의 Done 열에 'O' 추가
            print("Updating Done column in OrderDB.csv")
            with open(order_csv_file_path, mode="w", newline="") as file:
                fieldnames = rows[
                    0
                ].keys()  # 첫 번째 행의 키를 사용하여 필드 이름 가져옴
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    if row["order_id"] == str(
                        order_id
                    ):  # order_id를 문자열로 변환하여 비교
                        print(f"Updating order_id {order_id} to Done")
                        row["Done"] = "O"  # Done 열에 'O' 추가
                    writer.writerow(row)
                print("OrderDB.csv update complete.")

        else:
            flash("Product ID not found for the selected order.", category="error")

    except Exception as e:
        flash(f"Failed to send email: {e}", category="error")

    return render_approval_page()


@app.route("/Defer", methods=["POST"])
def Defer():
    user_id = session.get("apply_user_id")
    order_id = session.get("apply_order_id")
    email = session.get("apply_user_email")
    reason = request.form["Defer"]

    if not email:
        flash("Email address not found.", category="error")
        return redirect(url_for("approval_page"))

    try:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login("20221095@edu.hanbat.ac.kr", "ipxx qflq btpb mdgc")

        send_msg = MIMEText(f"보류 사유: {reason}")
        send_msg["Subject"] = "보류"
        smtp.sendmail("20221095@edu.hanbat.ac.kr", email, send_msg.as_string())

        smtp.quit()
        flash("Email sent successfully!", category="success")

        # OrderDB.csv에서 선택된 주문의 제품 ID와 수량을 가져옴
        with open(order_csv_file_path, mode="r", newline="") as file:
            csv_reader = csv.DictReader(file)
            rows = list(csv_reader)  # 전체 데이터를 리스트에 저장
            for row in rows:
                print(
                    f"Checking row: {row['order_id']}, {row['product_id']}, {row['quantity']}"
                )
                if row["order_id"] == str(
                    order_id
                ):  # order_id를 문자열로 변환하여 비교
                    product_id = row["product_id"]
                    quantity = int(row["quantity"])
                    break

        # OrderDB.csv 파일의 Done 열에 'O' 추가
        print("Updating Done column in OrderDB.csv")
        with open(order_csv_file_path, mode="w", newline="") as file:
            fieldnames = rows[0].keys()  # 첫 번째 행의 키를 사용하여 필드 이름 가져옴
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                if row["order_id"] == str(
                    order_id
                ):  # order_id를 문자열로 변환하여 비교
                    print(f"Updating order_id {order_id} to Done")
                    row["Done"] = "O"  # Done 열에 'O' 추가
                writer.writerow(row)
            print("OrderDB.csv update complete.")

    except Exception as e:
        flash(f"Failed to send email: {e}", category="error")

    return render_approval_page()


# 일단은 reject대충 함
@app.route("/reject", methods=["POST"])
def reject():
    user_id = session.get("apply_user_id")
    order_id = session.get("apply_order_id")
    email = session.get("apply_user_email")
    reason = request.form["reject"]

    if not email:
        flash("Email address not found.", category="error")
        return redirect(url_for("approval_page"))

    try:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login("20221095@edu.hanbat.ac.kr", "ipxx qflq btpb mdgc")

        send_msg = MIMEText(f"거절 사유: {reason}")
        send_msg["Subject"] = "거절"
        smtp.sendmail("20221095@edu.hanbat.ac.kr", email, send_msg.as_string())

        smtp.quit()
        flash("Email sent successfully!", category="success")
        # 이메일 보내는 코드

        # OrderDB.csv에서 선택된 주문의 제품 ID와 수량을 가져옴
        with open(order_csv_file_path, mode="r", newline="") as file:
            csv_reader = csv.DictReader(file)
            rows = list(csv_reader)  # 전체 데이터를 리스트에 저장
            for row in rows:
                print(
                    f"Checking row: {row['order_id']}, {row['product_id']}, {row['quantity']}"
                )
                if row["order_id"] == str(
                    order_id
                ):  # order_id를 문자열로 변환하여 비교
                    product_id = row["product_id"]
                    quantity = int(row["quantity"])
                    break

        # 위의거 sql버전

        cursor = conn.cursor()

        try:
            sql = "SELECT product_id, quantity FROM OrderDB WHERE order_id = %s"
            cursor.execute(sql, (order_id,))
            result = cursor.fetchone()

            if result:
                product_id, quantity = result
                print(f"Retrieved product_id: {product_id}, quantity: {quantity}")
            else:
                flash("Order not found in the database.", category="error")
                return redirect(url_for("approval_page"))
        finally:
            cursor.close()

        # OrderDB.csv 파일의 Done 열에 'O' 추가
        cursor = conn.cursor()
        try:
            sql_update = "UPDATE OrderDB SET Done = 1 WHERE order_id = %s"
            cursor.execute(sql_update, (order_id,))
            conn.commit()
            print(f"Order ID {order_id} updated to Done in the database.")
        finally:
            cursor.close()

    except Exception as e:
        flash(f"Failed to send email or update database: {e}", category="error")

    return render_approval_page()


if __name__ == "__main__":
    test_smtp_connection()
    app.run(debug=True)
