import os
import uuid
from datetime import date, datetime
from decimal import Decimal
from functools import wraps
from pathlib import Path
from urllib.parse import quote

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-development-secret-before-deployment")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("RENDER", "").lower() == "true"
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


def db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "frigdex"),
        autocommit=False,
    )


def query(sql, params=(), one=False):
    conn = db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        result = cur.fetchone() if one else cur.fetchall()
        conn.commit()
        return result
    finally:
        cur.close()
        conn.close()


def execute(sql, params=()):
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    if not file or not file.filename:
        return None
    if not allowed_image(file.filename):
        raise ValueError("Use a PNG, JPG, JPEG or WEBP image.")
    ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    file.save(UPLOAD_DIR / name)
    return f"/static/uploads/{name}"


def money(value):
    try:
        return f"₹{Decimal(str(value or 0)):,.2f}"
    except Exception:
        return "₹0.00"


@app.context_processor
def inject_helpers():
    return {"money": money, "current_year": datetime.now().year}


@app.get("/")
def home():
    featured = query("SELECT * FROM products WHERE is_active=1 ORDER BY created_at DESC LIMIT 6")
    return render_template("home.html", products=featured)


@app.get("/products")
def products():
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()
    sql = "SELECT * FROM products WHERE is_active=1"
    params = []
    if category:
        sql += " AND category=%s"
        params.append(category)
    if search:
        sql += " AND (name LIKE %s OR brand LIKE %s OR model LIKE %s)"
        like = f"%{search}%"
        params.extend([like, like, like])
    sql += " ORDER BY name"
    items = query(sql, tuple(params))
    categories = query("SELECT DISTINCT category FROM products WHERE is_active=1 AND category<>'' ORDER BY category")
    return render_template("products.html", products=items, categories=categories, selected=category, search=search)


@app.get("/product/<int:product_id>")
def product_detail(product_id):
    product = query("SELECT * FROM products WHERE id=%s AND is_active=1", (product_id,), one=True)
    if not product:
        abort(404)
    return render_template("product.html", product=product)


@app.get("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        product_interest = request.form.get("product_interest", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not message:
            flash("Please provide your name and requirement.", "error")
        else:
            enquiry_id = execute("""INSERT INTO enquiries (customer_name, phone, product_interest, message, status)
                       VALUES (%s,%s,%s,%s,'New')""",
                    (name, phone, product_interest, message))
            # Configure WHATSAPP_NUMBER in Render as digits only, including country code (India: 91...).
            whatsapp_number = "".join(ch for ch in os.getenv("WHATSAPP_NUMBER", "") if ch.isdigit())
            if whatsapp_number:
                whatsapp_message = (
                    "Hello Frigdex Industries, I would like to make an enquiry.\n\n"
                    f"Enquiry ID: {enquiry_id}\n"
                    f"Name: {name}\n"
                    f"Phone: {phone or 'Not provided'}\n"
                    f"Product of interest: {product_interest or 'Not specified'}\n"
                    f"Requirement: {message}"
                )
                return redirect(f"https://wa.me/{whatsapp_number}?text={quote(whatsapp_message)}")
            flash("Your enquiry was saved, but WhatsApp is not configured yet. Please contact the website administrator.", "error")
            return redirect(url_for("contact"))
    return render_template("contact.html")


@app.get("/admin/login")
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))
    return render_template("login.html")


@app.post("/admin/login")
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    admin = query("SELECT id, username, password_hash FROM admin_users WHERE username=%s AND is_active=1",
                  (username,), one=True)
    if admin and check_password_hash(admin["password_hash"], password):
        session.clear()
        session["admin_id"] = admin["id"]
        session["admin_username"] = admin["username"]
        execute("UPDATE admin_users SET last_login=NOW() WHERE id=%s", (admin["id"],))
        return redirect(request.args.get("next") or url_for("admin_dashboard"))
    flash("Username or password is incorrect.", "error")
    return redirect(url_for("login"))


@app.post("/admin/logout")
@admin_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/admin")
@admin_required
def admin_dashboard():
    stats = query("""SELECT
        (SELECT COUNT(*) FROM products) AS products_count,
        (SELECT COUNT(*) FROM products WHERE is_active=1) AS active_products,
        (SELECT COUNT(*) FROM enquiries WHERE status IN ('New','Contacted','Quoted')) AS open_enquiries,
        (SELECT COUNT(*) FROM orders WHERE status NOT IN ('Completed','Cancelled')) AS open_orders,
        (SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE status='Completed') AS completed_sales""", one=True)
    recent_orders = query("""SELECT o.*, c.name AS customer_name FROM orders o
                             LEFT JOIN customers c ON c.id=o.customer_id
                             ORDER BY o.created_at DESC LIMIT 7""")
    recent_enquiries = query("SELECT * FROM enquiries ORDER BY created_at DESC LIMIT 6")
    monthly = query("""
                        SELECT
                            DATE_FORMAT(MIN(created_at), '%b %Y') AS month_label,
                            SUM(total_amount) AS total
                        FROM orders
                        WHERE status = 'Completed'
                        AND created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                        GROUP BY YEAR(created_at), MONTH(created_at)
                        ORDER BY YEAR(created_at), MONTH(created_at)
                    """)
    return render_template("admin_dashboard.html", stats=stats, orders=recent_orders,
                           enquiries=recent_enquiries, monthly=monthly)


@app.get("/admin/products")
@admin_required
def admin_products():
    items = query("SELECT * FROM products ORDER BY created_at DESC")
    return render_template("admin_products.html", products=items)


@app.route("/admin/products/new", methods=["GET", "POST"])
@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_form(product_id=None):
    item = query("SELECT * FROM products WHERE id=%s", (product_id,), one=True) if product_id else None
    if product_id and not item:
        abort(404)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Product name is required.", "error")
            return redirect(request.url)
        try:
            price = Decimal(request.form.get("price") or "0")
            stock = int(request.form.get("stock") or 0)
            if price < 0 or stock < 0:
                raise ValueError
        except Exception:
            flash("Enter a valid non-negative price and stock quantity.", "error")
            return redirect(request.url)
        image_url = request.form.get("image_url", "").strip() or None
        try:
            uploaded = save_image(request.files.get("image"))
            if uploaded:
                image_url = uploaded
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(request.url)
        values = (
            name, request.form.get("brand", "").strip(), request.form.get("model", "").strip(),
            request.form.get("category", "Freezer").strip(), request.form.get("description", "").strip(),
            price, stock, request.form.get("capacity", "").strip(), request.form.get("refrigerant", "").strip(),
            request.form.get("temperature_range", "").strip(), request.form.get("power_consumption", "").strip(),
            request.form.get("door_type", "").strip(), request.form.get("color", "").strip(),
            image_url, 1 if request.form.get("is_active") == "on" else 0
        )
        if item:
            execute("""UPDATE products SET name=%s,brand=%s,model=%s,category=%s,description=%s,price=%s,
                stock=%s,capacity=%s,refrigerant=%s,temperature_range=%s,power_consumption=%s,door_type=%s,
                color=%s,image_url=%s,is_active=%s WHERE id=%s""", values + (product_id,))
            flash("Product updated successfully.", "success")
        else:
            execute("""INSERT INTO products (name,brand,model,category,description,price,stock,capacity,refrigerant,
                temperature_range,power_consumption,door_type,color,image_url,is_active)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", values)
            flash("Product added successfully.", "success")
        return redirect(url_for("admin_products"))
    return render_template("product_form.html", product=item)


@app.post("/admin/products/<int:product_id>/toggle")
@admin_required
def product_toggle(product_id):
    execute("UPDATE products SET is_active=IF(is_active=1,0,1) WHERE id=%s", (product_id,))
    flash("Product visibility updated.", "success")
    return redirect(url_for("admin_products"))


@app.get("/admin/enquiries")
@admin_required
def admin_enquiries():
    items = query("SELECT * FROM enquiries ORDER BY created_at DESC")
    return render_template("admin_enquiries.html", enquiries=items)


@app.post("/admin/enquiries/<int:enquiry_id>/status")
@admin_required
def enquiry_status(enquiry_id):
    status = request.form.get("status", "New")
    allowed = {"New", "Contacted", "Quoted", "Converted", "Closed"}
    if status not in allowed:
        abort(400)
    execute("UPDATE enquiries SET status=%s WHERE id=%s", (status, enquiry_id))
    flash("Enquiry status updated.", "success")
    return redirect(url_for("admin_enquiries"))


@app.get("/admin/orders")
@admin_required
def admin_orders():
    orders = query("""SELECT o.*, c.name AS customer_name FROM orders o
                      LEFT JOIN customers c ON c.id=o.customer_id ORDER BY o.created_at DESC""")
    return render_template("admin_orders.html", orders=orders)


@app.route("/admin/orders/new", methods=["GET", "POST"])
@admin_required
def new_order():
    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        product_id = request.form.get("product_id", type=int)
        quantity = request.form.get("quantity", type=int)
        status = request.form.get("status", "Pending")
        if not name or not product_id or not quantity or quantity < 1:
            flash("Customer, product and quantity are required.", "error")
            return redirect(url_for("new_order"))
        product = query("SELECT * FROM products WHERE id=%s", (product_id,), one=True)
        if not product:
            flash("Choose a valid product.", "error")
            return redirect(url_for("new_order"))
        customer = query("SELECT id FROM customers WHERE phone=%s", (phone,), one=True) if phone else None
        if customer:
            customer_id = customer["id"]
            execute("UPDATE customers SET name=%s WHERE id=%s", (name, customer_id))
        else:
            customer_id = execute("INSERT INTO customers (name,phone) VALUES (%s,%s)", (name, phone or None))
        total = Decimal(str(product["price"])) * quantity
        order_id = execute("INSERT INTO orders (customer_id,status,total_amount,notes) VALUES (%s,%s,%s,%s)",
                           (customer_id, status, total, request.form.get("notes", "").strip()))
        execute("INSERT INTO order_items (order_id,product_id,product_name,quantity,unit_price,line_total) VALUES (%s,%s,%s,%s,%s,%s)",
                (order_id, product_id, product["name"], quantity, product["price"], total))
        if status == "Completed":
            execute("UPDATE products SET stock=GREATEST(stock-%s,0) WHERE id=%s", (quantity, product_id))
        flash(f"Order #{order_id} created.", "success")
        return redirect(url_for("admin_orders"))
    products_list = query("SELECT id,name,brand,price,stock FROM products WHERE is_active=1 ORDER BY name")
    return render_template("order_form.html", products=products_list)


@app.post("/admin/orders/<int:order_id>/status")
@admin_required
def order_status(order_id):
    status = request.form.get("status", "Pending")
    allowed = {"Pending", "Confirmed", "Dispatched", "Completed", "Cancelled"}
    if status not in allowed:
        abort(400)
    old = query("SELECT status FROM orders WHERE id=%s", (order_id,), one=True)
    if not old:
        abort(404)
    execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
    flash("Order status updated. Review stock manually if changing a completed order.", "success")
    return redirect(url_for("admin_orders"))


@app.get("/admin/reports")
@admin_required
def reports():
    daily = query("""SELECT DATE(created_at) AS day, COUNT(*) AS order_count, SUM(total_amount) AS total
                     FROM orders WHERE status='Completed' AND created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                     GROUP BY DATE(created_at) ORDER BY day DESC""")
    by_brand = query("""SELECT p.brand, SUM(oi.quantity) AS units, SUM(oi.line_total) AS total
                        FROM order_items oi JOIN orders o ON o.id=oi.order_id
                        LEFT JOIN products p ON p.id=oi.product_id
                        WHERE o.status='Completed' GROUP BY p.brand ORDER BY total DESC""")
    return render_template("reports.html", daily=daily, by_brand=by_brand)


@app.errorhandler(500)
def server_error(error):
    return render_template("error.html", message="Something went wrong. Check the terminal for the detailed error."), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
