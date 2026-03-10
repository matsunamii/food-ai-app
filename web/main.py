from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from ai_server import analyze

import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

#⓶ログイン管理システム
login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy()

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
db.init_app(app)

migrate = Migrate(app,db)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime,nullable=False,default=date.today())
    img_name = db.Column(db.String(100),nullable=True)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    meal_type = db.Column(db.String(10))
    foods = db.Column(db.String(500))
    calorie = db.Column(db.Float)
    protein = db.Column(db.Float)
    fat = db.Column(db.Float)
    carb = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=date.today())

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50),nullable=False, unique=True)
    password = db.Column(db.String(200),nullable=False)

#⓷現在のユーザを識別するための関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )

NUTRITION_MAP = {
    0: {"name":"ご飯","cal":234,"protein":4,"fat":0.3,"carb":55},
    1: {"name":"うな重","cal":800,"protein":30,"fat":25,"carb":100},
    2: {"name":"ピラフ","cal":550,"protein":12,"fat":18,"carb":80},
    3: {"name":"親子丼","cal":650,"protein":30,"fat":20,"carb":80},
    4: {"name":"カツ丼","cal":900,"protein":35,"fat":35,"carb":100},
    5: {"name":"ビーフカレー","cal":850,"protein":25,"fat":30,"carb":110},
    6: {"name":"寿司","cal":700,"protein":35,"fat":10,"carb":100},
    7: {"name":"チキンライス","cal":600,"protein":18,"fat":15,"carb":90},
    8: {"name":"チャーハン","cal":750,"protein":20,"fat":25,"carb":100},
    9: {"name":"天丼","cal":850,"protein":20,"fat":35,"carb":110},
    10: {"name":"ビビンバ","cal":700,"protein":22,"fat":20,"carb":95},
    11: {"name":"トースト","cal":180,"protein":6,"fat":3,"carb":30},
    12: {"name":"クロワッサン","cal":220,"protein":4,"fat":12,"carb":24},
    13: {"name":"ロールパン","cal":120,"protein":4,"fat":2,"carb":22},
    14: {"name":"レーズンパン","cal":180,"protein":5,"fat":2,"carb":35},
    15: {"name":"チップバティ","cal":500,"protein":10,"fat":20,"carb":70},
    16: {"name":"ハンバーガー","cal":295,"protein":17,"fat":13,"carb":30},
    17: {"name":"ピザ","cal":300,"protein":12,"fat":10,"carb":36},
    18: {"name":"サンドイッチ","cal":350,"protein":15,"fat":10,"carb":40},
    19: {"name":"うどん","cal":350,"protein":10,"fat":3,"carb":70},
    20: {"name":"天ぷらうどん","cal":500,"protein":15,"fat":15,"carb":75},
    21: {"name":"そば","cal":330,"protein":12,"fat":2,"carb":65},
    22: {"name":"ラーメン","cal":500,"protein":20,"fat":15,"carb":70},
    23: {"name":"牛肉麺","cal":550,"protein":25,"fat":18,"carb":70},
    24: {"name":"天津麺","cal":520,"protein":18,"fat":14,"carb":75},
    25: {"name":"焼きそば","cal":600,"protein":18,"fat":20,"carb":80},
    26: {"name":"スパゲッティ","cal":650,"protein":20,"fat":15,"carb":90},
    27: {"name":"お好み焼き","cal":700,"protein":25,"fat":25,"carb":80},
    28: {"name":"たこ焼き","cal":500,"protein":15,"fat":20,"carb":60},
    29: {"name":"グラタン","cal":600,"protein":20,"fat":25,"carb":65},
    30: {"name":"野菜炒め","cal":250,"protein":10,"fat":12,"carb":25},
    31: {"name":"コロッケ","cal":200,"protein":4,"fat":10,"carb":22},
    32: {"name":"焼きナス","cal":80,"protein":2,"fat":4,"carb":8},
    33: {"name":"ほうれん草ソテー","cal":120,"protein":5,"fat":8,"carb":7},
    34: {"name":"野菜天ぷら","cal":300,"protein":5,"fat":18,"carb":30},
    35: {"name":"味噌汁","cal":60,"protein":4,"fat":2,"carb":6},
    36: {"name":"ポタージュ","cal":150,"protein":4,"fat":7,"carb":18},
    37: {"name":"ソーセージ","cal":250,"protein":10,"fat":22,"carb":2},
    38: {"name":"おでん","cal":300,"protein":20,"fat":12,"carb":20},
    39: {"name":"オムレツ","cal":250,"protein":16,"fat":20,"carb":3},
    40: {"name":"がんもどき","cal":200,"protein":12,"fat":15,"carb":8},
    41: {"name":"餃子","cal":250,"protein":12,"fat":14,"carb":18},
    42: {"name":"シチュー","cal":350,"protein":15,"fat":18,"carb":30},
    43: {"name":"照り焼き魚","cal":250,"protein":25,"fat":10,"carb":10},
    44: {"name":"フライドフィッシュ","cal":300,"protein":20,"fat":18,"carb":15},
    45: {"name":"焼き鮭","cal":220,"protein":22,"fat":13,"carb":0},
    46: {"name":"サーモンムニエル","cal":320,"protein":24,"fat":20,"carb":3},
    47: {"name":"刺身","cal":180,"protein":30,"fat":5,"carb":0},
    48: {"name":"サンマ塩焼き","cal":350,"protein":22,"fat":25,"carb":0},
    49: {"name":"すき焼き","cal":700,"protein":35,"fat":35,"carb":50},
    50: {"name":"酢豚","cal":400,"protein":20,"fat":18,"carb":40},
    51: {"name": "魚の軽い炙り", "cal": 220, "protein": 24, "fat": 12, "carb": 2},
    52: {"name":"茶碗蒸し","cal":120,"protein":8,"fat":7,"carb":5},
    53: {"name":"天ぷら","cal":350,"protein":10,"fat":25,"carb":25},
    54: {"name":"唐揚げ","cal":350,"protein":25,"fat":20,"carb":10},
    55: {"name":"ヒレカツ","cal":400,"protein":30,"fat":25,"carb":10},
    56: {"name": "南蛮漬け", "cal": 250, "protein": 18, "fat": 12, "carb": 12},
    57: {"name": "煮魚", "cal": 220, "protein": 22, "fat": 10, "carb": 8},
    58: {"name":"肉じゃが","cal":350,"protein":15,"fat":15,"carb":40},
    59: {"name":"ハンバーグ","cal":450,"protein":25,"fat":30,"carb":10},
    60: {"name":"ビーフステーキ","cal":500,"protein":40,"fat":35,"carb":0},
    61: {"name": "干物", "cal": 200, "protein": 25, "fat": 8, "carb": 0},
    62: {"name":"豚の生姜焼き","cal":400,"protein":25,"fat":25,"carb":10},
    63: {"name":"麻婆豆腐","cal":350,"protein":18,"fat":25,"carb":10},
    64: {"name":"焼き鳥","cal":250,"protein":20,"fat":15,"carb":5},
    65: {"name":"ロールキャベツ","cal":300,"protein":18,"fat":15,"carb":20},
    66: {"name":"だし巻き卵","cal":180,"protein":12,"fat":12,"carb":5},
    67: {"name":"目玉焼き","cal":160,"protein":12,"fat":12,"carb":1},
    68: {"name":"納豆","cal":200,"protein":16,"fat":10,"carb":12},
    69: {"name":"冷奴","cal":120,"protein":10,"fat":7,"carb":4},
    70: {"name":"卵焼き","cal":200,"protein":14,"fat":14,"carb":5},
    71: {"name": "冷やし麺", "cal": 420, "protein": 14, "fat": 8, "carb": 70},
    72: {"name": "牛肉ピーマン炒め", "cal": 320, "protein": 20, "fat": 20, "carb": 10},
    73: {"name": "豚の角煮", "cal": 450, "protein": 20, "fat": 35, "carb": 8},
    74: {"name": "鶏と野菜の煮物", "cal": 280, "protein": 18, "fat": 12, "carb": 18},
    75: {"name": "刺身丼", "cal": 600, "protein": 30, "fat": 8, "carb": 85},
    76: {"name": "寿司丼", "cal": 650, "protein": 28, "fat": 10, "carb": 95},
    77: {"name": "たい焼き", "cal": 240, "protein": 5, "fat": 3, "carb": 50},
    78: {"name": "エビチリ", "cal": 320, "protein": 20, "fat": 15, "carb": 20},
    79: {"name": "ローストチキン", "cal": 350, "protein": 30, "fat": 22, "carb": 0},
    80: {"name": "焼売", "cal": 250, "protein": 12, "fat": 12, "carb": 20},
    81: {"name": "オムライス", "cal": 700, "protein": 20, "fat": 20, "carb": 90},
    82: {"name": "カツカレー", "cal": 1000, "protein": 35, "fat": 40, "carb": 120},
    83: {"name": "ミートソーススパゲッティ", "cal": 700, "protein": 25, "fat": 18, "carb": 95},
    84: {"name": "エビフライ", "cal": 300, "protein": 18, "fat": 18, "carb": 15},
    85: {"name": "ポテトサラダ", "cal": 200, "protein": 4, "fat": 10, "carb": 22},
    86: {"name": "グリーンサラダ", "cal": 100, "protein": 3, "fat": 5, "carb": 10},
    87: {"name": "マカロニサラダ", "cal": 250, "protein": 6, "fat": 14, "carb": 25},
    88: {"name": "けんちん汁", "cal": 120, "protein": 5, "fat": 4, "carb": 15},
    89: {"name": "豚汁", "cal": 200, "protein": 10, "fat": 10, "carb": 15},
    90: {"name": "中華スープ", "cal": 120, "protein": 5, "fat": 6, "carb": 10},
    91: {"name":"牛丼","cal":700,"protein":25,"fat":20,"carb":90},
    92: {"name": "きんぴらごぼう", "cal": 150, "protein": 3, "fat": 6, "carb": 22},
    93: {"name":"おにぎり","cal":180,"protein":3,"fat":1,"carb":40},
    94: {"name": "ピザトースト", "cal": 260, "protein": 10, "fat": 9, "carb": 34},
    95: {"name": "つけ麺", "cal": 550, "protein": 20, "fat": 12, "carb": 85},
    96: {"name":"ホットドッグ","cal":300,"protein":12,"fat":18,"carb":25},
    97: {"name":"フライドポテト","cal":350,"protein":4,"fat":17,"carb":48},
    98: {"name": "混ぜご飯", "cal": 280, "protein": 6, "fat": 3, "carb": 56},
    99: {"name": "ゴーヤチャンプルー", "cal": 300, "protein": 18, "fat": 18, "carb": 12},
}

@app.route("/")
def user():
    return redirect('/signup')

@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pass = generate_password_hash(password)
        user = User(username=username, password=hashed_pass)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    elif request.method == 'GET':
        return render_template('signup.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #　ユーザー名とパスワードの受け取り
        username = request.form.get('username')
        password = request.form.get('password')
        #　ユーザー名をもとにデータベースから情報を取得
        user = User.query.filter_by(username=username).first()
        #　入力パスワードとデータベースのパスワードが一致しているか確認
        if check_password_hash(user.password, password=password):
            #　一致していれば，ログインさせて，管理画面へリダイレクトされる
            login_user(user)
            return redirect('/dashboard')
        else:
            #　間違っている場合，エラー文と共にログイン画面へリダイレクトさせる
            return redirect('/login',msg='ユーザー名/パスワードが違います')
    elif request.method == 'GET':
        return render_template('login.html', msg='')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route("/dashboard")
@login_required
def dashboard():

    today = date.today()

    meals = Meal.query.filter(
    Meal.user_id == current_user.id,
    db.func.date(Meal.created_at) == today
    ).all()

    breakfast = []
    lunch = []
    dinner = []

    total_cal = 0
    total_protein = 0
    total_fat = 0
    total_carb = 0

    for m in meals:
        if m.meal_type == "朝":
            breakfast.append(m)
        elif m.meal_type == "昼":
            lunch.append(m)
        elif m.meal_type == "夜":
            dinner.append(m)

        # 合計栄養
        total_cal += m.calorie or 0
        total_protein += m.protein or 0
        total_fat += m.fat or 0
        total_carb += m.carb or 0

    return render_template(
        "dashboard.html",
        breakfast=breakfast,
        lunch=lunch,
        dinner=dinner,
        total_cal=total_cal,
        total_protein=total_protein,
        total_fat=total_fat,
        total_carb=total_carb
    )

@app.route("/meal/delete/<int:id>")
@login_required
def meal_delete(id):

    meal = Meal.query.filter_by(
    id=id,
    user_id=current_user.id
    ).first()

    if meal:
        db.session.delete(meal)
        db.session.commit()

    return redirect("/dashboard")

@app.route("/dashboard/log")
@login_required
def meal_log():

    meals = Meal.query.filter_by(user_id=current_user.id)\
        .order_by(Meal.created_at.desc())\
        .all()
    
    return render_template("log.html", meals=meals)

@app.route("/dashboard/create", methods=['GET','POST'])
@login_required
def meal_create():

    if request.method == "POST":

        meal_type = request.form.get("meal_type")
        foods = request.form.getlist("foods[]")

        calorie = request.form.get("calorie")
        protein = request.form.get("protein")
        fat = request.form.get("fat")
        carb = request.form.get("carb")

        meal = Meal(
            user_id=current_user.id,
            meal_type = meal_type,
            foods = ",".join(foods),
            calorie = calorie,
            protein = protein,
            fat = fat,
            carb = carb
        )

        db.session.add(meal)
        db.session.commit()

        return redirect("/dashboard")

    return render_template(
    "create.html",
    nutrition_map=NUTRITION_MAP
)

@app.route("/classify", methods=["POST"])
@login_required
def classify():

    if "img" not in request.files:
        return jsonify({"ok": False, "error": "image not found"})

    file = request.files["img"]

    try:

        detections = analyze(file)

        foods = []

        for d in detections:

            cid = d["class_id"]
            food = NUTRITION_MAP.get(cid, {
            "name": "不明",
            "cal": 0,
            "protein": 0,
            "fat": 0,
            "carb": 0
            })

            foods.append({
                "food101": food["name"],
                "score": d["score"],
                "bbox": d["bbox"],
                "calorie": food["cal"],
                "protein": food["protein"],
                "fat": food["fat"],
                "carb": food["carb"]
            })

        return jsonify({
            "ok": True,
            "foods": foods
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        })
port = int(os.environ.get("PORT", 8080))
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=port)