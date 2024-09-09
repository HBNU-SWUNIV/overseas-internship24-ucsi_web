from flask import Flask, render_template, redirect, url_for, request, session, flash
import smtplib
from email.mime.text import MIMEText
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 위한 시크릿 키 설정

# 임시 사용자 데이터베이스 (실제 애플리케이션에서는 데이터베이스를 사용하세요)
users = {'admin': 'admin', 'user': 'user'}

# 기본 라우트: 로그인 페이지
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 인증
        if username in users and users[username] == password:
            session['user'] = username
            if username == 'admin':
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('user_page'))
        else:
            flash("Invalid credentials")

    return render_template('login.html')

# 로그아웃 라우트
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Admin 페이지 라우트
@app.route('/admin')
def admin_page():
    if 'user' in session and session['user'] == 'admin':
        return render_template('admin.html')
    else:
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            flash("Username already exists")
        else:
            users[username] = password
            flash("Registration successful")
            return redirect(url_for('login'))

    return render_template('register.html')


# Application Approval 페이지 라우트 (Admin만 접근 가능)
@app.route('/approval')
def approval_page():
    if 'user' in session and session['user'] == 'admin':
        return render_approval_page()
    return redirect(url_for('login'))

def render_approval_page(msg=None):
    # OrderDB.csv 파일을 읽기
    order_df = pd.read_csv('OrderDB.csv')
    product_df = pd.read_csv('ProductDB.csv')
    user_df = pd.read_csv('UserDB.csv')

    # ProductDB에서 color 정보를 가져와 OrderDB에 추가
    order_df['color'] = order_df['product_id'].map(product_df.set_index('product_id')['color'])

    # OrderDB의 product_id를 ProductDB의 name으로 대체
    order_df['product_id'] = order_df['product_id'].map(product_df.set_index('product_id')['name'])

    # OrderDB의 user_id를 UserDB의 name으로 대체
    order_df['user_id'] = order_df['user_id'].map(user_df.set_index('user_id')['name'])

    # 데이터프레임을 HTML 표로 변환
    table_html = order_df.to_html(index=False)

    return render_template('approval.html', table_html=table_html, msg=msg)

@app.route("/send_mail", methods=['POST'])
def send_mail():
    msg = request.form['select']
    return render_approval_page(msg=msg)

@app.route("/approve", methods=['POST'])
def approve():
    msg = request.form['date']
    time = request.form['time']
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()

    # 보낼 계정
    smtp.login('20221095@edu.hanbat.ac.kr', 'ipxx qflq btpb mdgc')

    send_msg = MIMEText(f"승인 날짜 : {msg} 시간 : {time}")
    send_msg['Subject'] = "승인"
    smtp.sendmail('20221095@edu.hanbat.ac.kr', 'luonj@naver.com', send_msg.as_string())

    smtp.quit()

    return render_approval_page()

@app.route("/Defer", methods=['POST'])
def Defer():
    msg = request.form['Defer']
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()

    # 보낼 계정
    smtp.login('20221095@edu.hanbat.ac.kr', 'ipxx qflq btpb mdgc')

    send_msg = MIMEText(f"보류사유: {msg}")
    send_msg['Subject'] = "보류"
    smtp.sendmail('20221095@edu.hanbat.ac.kr', 'luonj@naver.com', send_msg.as_string())

    smtp.quit()

    return render_approval_page()

@app.route("/reject", methods=['POST'])
def reject():
    msg = request.form['reject']
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()

    # 보낼 계정
    smtp.login('20221095@edu.hanbat.ac.kr', 'ipxx qflq btpb mdgc')

    send_msg = MIMEText(f"거절사유: {msg}")
    send_msg['Subject'] = "거절"
    smtp.sendmail('20221095@edu.hanbat.ac.kr', 'luonj@naver.com', send_msg.as_string())

    smtp.quit()

    return render_approval_page()

if __name__ == '__main__':
    app.run(debug=True)
