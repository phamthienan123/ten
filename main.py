from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret-key"  # thay bằng key mạnh hơn

USERS_FILE = "users.json"
ITEMS_FILE = "items.json"


# ----------------- HÀM TIỆN ÍCH -----------------
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_items():
    if not os.path.exists(ITEMS_FILE):
        data = {
            "rank_bronze": {"buy": 50, "sell": 25},
            "rank_silver": {"buy": 100, "sell": 50},
            "rank_gold": {"buy": 200, "sell": 100},
            "rank_platinum": {"buy": 500, "sell": 250}
        }
        with open(ITEMS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    with open(ITEMS_FILE, "r") as f:
        return json.load(f)

def save_items(items):
    with open(ITEMS_FILE, "w") as f:
        json.dump(items, f, indent=4)


# ----------------- ROUTES -----------------
@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


# Đăng ký
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    users = load_users()
    if username in users:
        flash("Tài khoản đã tồn tại!")
        return redirect(url_for("home"))

    users[username] = {
        "password": password,
        "diamonds": 0,
        "inventory": [],
        "rank": "",
        "last_login": "",
        "quests": []
    }
    save_users(users)
    flash("Đăng ký thành công, hãy đăng nhập!")
    return redirect(url_for("home"))


# Đăng nhập
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    users = load_users()
    if username in users and users[username]["password"] == password:
        session["username"] = username
        return redirect(url_for("dashboard"))
    flash("Sai tài khoản hoặc mật khẩu!")
    return redirect(url_for("home"))


# Đăng xuất
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))


# Dashboard
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("home"))

    users = load_users()
    username = session["username"]
    user = users[username]

    # thưởng đăng nhập mỗi ngày
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_login"] != today:
        user["diamonds"] += 5
        user["last_login"] = today
        save_users(users)
        flash("Bạn nhận được 5 💎 thưởng đăng nhập hôm nay!")

    # lấy rank cao nhất
    ranks_order = ["rank_bronze", "rank_silver", "rank_gold", "rank_platinum"]
    user_rank = ""
    for r in reversed(ranks_order):
        if r in user["inventory"]:
            user_rank = r
            break

    return render_template("dashboard.html", user=user, rank=user_rank)


# Shop
@app.route("/shop")
def shop():
    if "username" not in session:
        return redirect(url_for("home"))

    items = load_items()
    return render_template("shop.html", items=items)


@app.route("/buy/<item>")
def buy(item):
    if "username" not in session:
        return redirect(url_for("home"))

    users = load_users()
    items = load_items()
    username = session["username"]
    user = users[username]

    if item in items and user["diamonds"] >= items[item]["buy"]:
        user["diamonds"] -= items[item]["buy"]
        user["inventory"].append(item)
        save_users(users)
        flash(f"Mua {item} thành công!")
    else:
        flash("Không đủ kim cương!")

    return redirect(url_for("shop"))


@app.route("/sell/<item>")
def sell(item):
    if "username" not in session:
        return redirect(url_for("home"))

    users = load_users()
    items = load_items()
    username = session["username"]
    user = users[username]

    if item in user["inventory"]:
        user["inventory"].remove(item)
        user["diamonds"] += items[item]["sell"]
        save_users(users)
        flash(f"Bán {item} thành công!")
    else:
        flash("Bạn không sở hữu vật phẩm này!")

    return redirect(url_for("shop"))


# Admin
@app.route("/admin")
def admin():
    if "username" not in session or session["username"] != "admin":
        flash("Chỉ admin mới vào được!")
        return redirect(url_for("home"))

    users = load_users()
    items = load_items()
    return render_template("admin.html", users=users, items=items)


@app.route("/admin/delete/<username>")
def delete_user(username):
    if "username" not in session or session["username"] != "admin":
        return redirect(url_for("home"))

    users = load_users()
    if username in users:
        users.pop(username)
        save_users(users)
        flash(f"Đã xóa tài khoản {username}")
    return redirect(url_for("admin"))


@app.route("/admin/give/<username>/<int:amount>")
def give_diamonds(username, amount):
    if "username" not in session or session["username"] != "admin":
        return redirect(url_for("home"))

    users = load_users()
    if username in users:
        users[username]["diamonds"] += amount
        save_users(users)
        flash(f"Đã tặng {amount} 💎 cho {username}")
    return redirect(url_for("admin"))


@app.route("/admin/update_price/<item>", methods=["POST"])
def update_price(item):
    if "username" not in session or session["username"] != "admin":
        return redirect(url_for("home"))

    items = load_items()
    if item in items:
        buy_price = int(request.form["buy"])
        sell_price = int(request.form["sell"])
        items[item]["buy"] = buy_price
        items[item]["sell"] = sell_price
        save_items(items)
        flash(f"Cập nhật giá {item} thành công!")
    return redirect(url_for("admin"))


# ----------------- RUN -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

