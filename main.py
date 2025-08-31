from flask import Flask, render_template, request, redirect, url_for, flash
import json, os, uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "secret")

# ================== ĐƯỜNG DẪN ==================
ITEMS_FILE = "data/items.json"
ORDERS_FILE = "data/orders.json"
UPLOAD_FOLDER = "static/uploads"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

os.makedirs("data", exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================== HÀM XỬ LÝ FILE ==================
def load_json(file):
    if not os.path.exists(file):
        return []
    with open(file, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ================== TRANG CHÍNH ==================
@app.route("/")
def index():
    items = load_json(ITEMS_FILE)
    return render_template("index.html", items=items)

# ================== GIỎ HÀNG ==================
@app.route("/checkout", methods=["POST"])
def checkout():
    items = load_json(ITEMS_FILE)
    orders = load_json(ORDERS_FILE)

    cart = []
    total = 0

    for item in items:
        qty = request.form.get(f"qty_{item['id']}", "0")
        try:
            qty = int(qty)
        except:
            qty = 0
        if qty > 0 and qty <= item["quantity"]:
            subtotal = qty * item["price"]
            total += subtotal
            cart.append({
                "id": item["id"],
                "name": item["name"],
                "qty": qty,
                "price": item["price"],
                "subtotal": subtotal
            })
            item["quantity"] -= qty

    if not cart:
        flash("Bạn chưa chọn món hàng nào!", "error")
        return redirect(url_for("index"))

    order = {
        "id": str(uuid.uuid4()),
        "items": cart,
        "total": total,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    orders.append(order)
    save_json(ORDERS_FILE, orders)
    save_json(ITEMS_FILE, items)

    flash("Thanh toán thành công!", "success")
    return redirect(url_for("index"))

# ================== ADMIN ==================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        if password != ADMIN_PASSWORD:
            flash("Sai mật khẩu!", "error")
            return redirect(url_for("admin"))
        items = load_json(ITEMS_FILE)
        return render_template("admin.html", items=items)

    return render_template("admin_login.html")

@app.route("/admin/add", methods=["POST"])
def admin_add():
    password = request.form.get("password")
    if password != ADMIN_PASSWORD:
        flash("Sai mật khẩu!", "error")
        return redirect(url_for("admin"))

    items = load_json(ITEMS_FILE)

    name = request.form.get("name")
    price = float(request.form.get("price", 0))
    quantity = int(request.form.get("quantity", 0))

    image = request.files.get("image")
    if image and image.filename != "":
        filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
        path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(path)
        image_url = f"uploads/{filename}"
    else:
        image_url = "placeholder.png"

    new_item = {
        "id": str(uuid.uuid4()),
        "name": name,
        "price": price,
        "quantity": quantity,
        "image": image_url
    }

    items.append(new_item)
    save_json(ITEMS_FILE, items)

    flash("Đã thêm sản phẩm!", "success")
    return redirect(url_for("admin"))

# ================== CHẠY APP ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True)
