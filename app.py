from __future__ import annotations
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from decimal import Decimal
import math
import os

app = Flask(__name__)
app.secret_key = os.environ.get("CANGROO_SECRET", "dev-secret-change-me")

# --------- Fake catalog (in-memory) ----------
# Note: image URLs are from Unsplash (royalty-free placeholders).
PRODUCTS = [
    {
        "id": "kang-001",
        "name": "Cangroo Canvas Tote",
        "price": Decimal("19.99"),
        "category": "Bags",
        "image": "https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1200&auto=format&fit=crop",
        "rating": 4.6,
        "description": "Eco‑friendly canvas tote with a springy Cangroo emblem. Folds flat, carries everything."
    },
    {
        "id": "kang-002",
        "name": "Cangroo Runner Sneakers",
        "price": Decimal("74.50"),
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?q=80&w=1200&auto=format&fit=crop",
        "rating": 4.8,
        "description": "Lightweight daily trainers with bounce. Mesh upper, comfy foam midsole."
    },
    {
        "id": "kang-003",
        "name": "Cangroo Thermal Bottle 1L",
        "price": Decimal("29.00"),
        "category": "Accessories",
        "image": "https://images.unsplash.com/photo-1542736667-069246bdbc74?q=80&w=1200&auto=format&fit=crop",
        "rating": 4.7,
        "description": "Keeps drinks icy for 24h and hot for 12h. Powder‑coated finish, leak‑proof cap."
    },
    {
        "id": "kang-004",
        "name": "Cangroo Hoodie (Unisex)",
        "price": Decimal("49.90"),
        "category": "Apparel",
        "image": "https://images.unsplash.com/photo-1503342217505-b0a15cf70489?q=80&w=1200&auto=format&fit=crop",
        "rating": 4.5,
        "description": "Mid‑weight fleece hoodie with soft hand‑feel and relaxed fit."
    },
    {
        "id": "kang-005",
        "name": "Cangroo Trail Backpack 22L",
        "price": Decimal("89.00"),
        "category": "Bags",
        "image": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=1200&auto=format&fit=crop",
        "rating": 4.9,
        "description": "All‑day pack with breathable back panel, laptop sleeve, and stretch pockets."
    },
    {
        "id": "kang-006",
        "name": "Cangroo Tee (Organic)",
        "price": Decimal("24.00"),
        "category": "Apparel",
        "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?q=80&w=1200&auto=format&fit=crop",
        "rating": 4.4,
        "description": "100% organic cotton tee. Silky smooth, pre‑shrunk, and durable."
    },
    {
        "id": "kang-007",
        "name": "Cangroo Sport Socks (3‑Pack)",
        "price": Decimal("12.00"),
        "category": "Accessories",
        "image": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=1200&auto=format&fit=crop",
        "rating": 4.3,
        "description": "Cushioned heel & toe, breathable mesh zones. Bounce with every hop."
    },
    {
        "id": "kang-008",
        "name": "Cangroo Daylight Sunglasses",
        "price": Decimal("39.50"),
        "category": "Accessories",
        "image": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?q=80&w=1200&auto=format&fit=crop",
        "rating": 4.6,
        "description": "Polarized lenses with UV400 protection. Matte finish frames."
    }
]

CATEGORIES = sorted({p["category"] for p in PRODUCTS})

# ---------- Helpers ----------
def find_product(pid: str):
    return next((p for p in PRODUCTS if p["id"] == pid), None)

def get_cart():
    cart = session.get("cart", {})
    # clean legacy types
    return {k: int(v) for k, v in cart.items()}

def save_cart(cart):
    session["cart"] = cart
    session.modified = True

def cart_items_details():
    cart = get_cart()
    items = []
    subtotal = Decimal("0.00")
    for pid, qty in cart.items():
        product = find_product(pid)
        if not product:
            continue
        line_total = product["price"] * qty
        subtotal += line_total
        items.append({
            "product": product,
            "qty": qty,
            "line_total": line_total
        })
    shipping = Decimal("0.00") if subtotal >= Decimal("100.00") or subtotal == 0 else Decimal("6.95")
    tax = (subtotal * Decimal("0.08")).quantize(Decimal("0.01"))
    total = (subtotal + shipping + tax).quantize(Decimal("0.01"))
    return items, subtotal.quantize(Decimal("0.01")), shipping, tax, total

def cart_count():
    return sum(get_cart().values())

@app.context_processor
def inject_globals():
    return {"cart_count": cart_count(), "categories": CATEGORIES, "site_name": "cangroo"}

# ---------- Routes ----------
@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    cat = request.args.get("cat", "").strip()
    filtered = PRODUCTS
    if cat:
        filtered = [p for p in filtered if p["category"] == cat]
    if q:
        filtered = [p for p in filtered if q in p["name"].lower() or q in p["description"].lower()]
    return render_template("index.html", products=filtered, query=q, active_cat=cat)

@app.route("/product/<pid>")
def product_page(pid):
    product = find_product(pid)
    if not product:
        return render_template("product.html", product=None), 404
    # simple "related" by category
    related = [p for p in PRODUCTS if p["category"] == product["category"] and p["id"] != pid][:4]
    return render_template("product.html", product=product, related=related)

@app.route("/cart")
def cart_page():
    items, subtotal, shipping, tax, total = cart_items_details()
    return render_template("cart.html", items=items, subtotal=subtotal, shipping=shipping, tax=tax, total=total)

@app.post("/add-to-cart")
def add_to_cart():
    pid = request.form.get("pid")
    qty = int(request.form.get("qty", 1))
    product = find_product(pid)
    if not product:
        return jsonify({"ok": False, "message": "Product not found."}), 404
    cart = get_cart()
    cart[pid] = cart.get(pid, 0) + max(1, qty)
    save_cart(cart)
    return jsonify({"ok": True, "cart_count": cart_count(), "message": f"Added {product['name']}."})

@app.post("/update-cart")
def update_cart():
    pid = request.form.get("pid")
    qty = max(0, int(request.form.get("qty", 1)))
    cart = get_cart()
    if pid in cart:
        if qty == 0:
            cart.pop(pid)
        else:
            cart[pid] = qty
        save_cart(cart)
    items, subtotal, shipping, tax, total = cart_items_details()
    return jsonify({
        "ok": True,
        "cart_count": cart_count(),
        "summary": {
            "subtotal": f"{subtotal:.2f}",
            "shipping": f"{shipping:.2f}",
            "tax": f"{tax:.2f}",
            "total": f"{total:.2f}"
        }
    })

@app.post("/remove-from-cart")
def remove_from_cart():
    pid = request.form.get("pid")
    cart = get_cart()
    if pid in cart:
        cart.pop(pid)
        save_cart(cart)
    return jsonify({"ok": True, "cart_count": cart_count()})

@app.get("/search")
def search_api():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify([])
    results = []
    for p in PRODUCTS:
        hay = (p["name"] + " " + p["description"]).lower()
        if q in hay:
            results.append({"id": p["id"], "name": p["name"], "price": float(p["price"]), "image": p["image"]})
    return jsonify(results[:6])

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, subtotal, shipping, tax, total = cart_items_details()
    if request.method == "POST":
        # pretend to process order
        session["cart"] = {}
        flash("Order placed successfully! You’ll receive a confirmation email shortly.", "success")
        return redirect(url_for("index"))
    return render_template("checkout.html", items=items, subtotal=subtotal, shipping=shipping, tax=tax, total=total)

# ---- Small utilities ----
@app.template_filter("stars")
def stars_filter(value: float):
    # returns list of full/half/empty for simple star render
    whole = int(math.floor(value))
    half = 1 if (value - whole) >= 0.5 else 0
    empty = 5 - whole - half
    return ["full"] * whole + ["half"] * half + ["empty"] * empty

if __name__ == "__main__":
    app.run(debug=True)