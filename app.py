from flask import Flask, request, jsonify, session, render_template
from db import init_db, get_db
import hashlib, os
from datetime import datetime
from functools import wraps

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.urandom(32)

ADMIN_USER = "admin"
ADMIN_PASS = hashlib.sha256("freitas2024".encode()).hexdigest()

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return jsonify({'error': 'Não autorizado'}), 401
        return f(*args, **kwargs)
    return decorated

@app.before_request
def setup():
    init_db()

# ── Páginas ──────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

# ── Auth ─────────────────────────────────────────────────
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    user = data.get('username', '')
    pw   = hashlib.sha256(data.get('password', '').encode()).hexdigest()
    if user == ADMIN_USER and pw == ADMIN_PASS:
        session['admin'] = True
        return jsonify({'ok': True})
    return jsonify({'error': 'Credenciais inválidas'}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin', None)
    return jsonify({'ok': True})

@app.route('/api/admin/check')
def admin_check():
    return jsonify({'logged': bool(session.get('admin'))})

# ── Produtos ─────────────────────────────────────────────
@app.route('/api/products', methods=['GET'])
def get_products():
    db  = get_db()
    cat = request.args.get('category', '')
    if cat:
        rows = db.execute('SELECT * FROM products WHERE active=1 AND category=? ORDER BY name', (cat,)).fetchall()
    else:
        rows = db.execute('SELECT * FROM products WHERE active=1 ORDER BY category, name').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/products/categories', methods=['GET'])
def get_categories():
    db   = get_db()
    rows = db.execute('SELECT DISTINCT category FROM products WHERE active=1 ORDER BY category').fetchall()
    return jsonify([r['category'] for r in rows])

@app.route('/api/admin/products', methods=['GET'])
@require_admin
def admin_get_products():
    db   = get_db()
    rows = db.execute('SELECT * FROM products ORDER BY category, name').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/products', methods=['POST'])
@require_admin
def add_product():
    d  = request.json
    db = get_db()
    db.execute(
        'INSERT INTO products (name, description, price, img_url, category, unit, active) VALUES (?,?,?,?,?,?,1)',
        (d['name'], d.get('description',''), float(d['price']),
         d.get('img_url',''), d.get('category','Geral'), d.get('unit','un'))
    )
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/admin/products/<int:pid>', methods=['PUT'])
@require_admin
def update_product(pid):
    d  = request.json
    db = get_db()
    db.execute(
        'UPDATE products SET name=?, description=?, price=?, img_url=?, category=?, unit=?, active=? WHERE id=?',
        (d['name'], d.get('description',''), float(d['price']),
         d.get('img_url',''), d.get('category','Geral'), d.get('unit','un'),
         int(d.get('active',1)), pid)
    )
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/admin/products/<int:pid>', methods=['DELETE'])
@require_admin
def delete_product(pid):
    db = get_db()
    db.execute('UPDATE products SET active=0 WHERE id=?', (pid,))
    db.commit()
    return jsonify({'ok': True})

# ── Pedidos ───────────────────────────────────────────────
@app.route('/api/orders', methods=['POST'])
def create_order():
    d         = request.json
    customer  = d.get('customer_name', '').strip()
    phone     = d.get('customer_phone', '').strip()
    items     = d.get('items', [])

    if not customer:
        return jsonify({'error': 'Nome do cliente obrigatório'}), 400
    if not items:
        return jsonify({'error': 'Carrinho vazio'}), 400

    db    = get_db()
    total = 0.0
    validated = []

    for item in items:
        row = db.execute('SELECT * FROM products WHERE id=? AND active=1', (item['product_id'],)).fetchone()
        if not row:
            return jsonify({'error': f'Produto inválido: {item["product_id"]}'}), 400
        qty      = max(1, int(item.get('quantity', 1)))
        subtotal = row['price'] * qty
        total   += subtotal
        validated.append({
            'product_id': row['id'], 'name': row['name'],
            'unit': row['unit'], 'price': row['price'],
            'quantity': qty, 'subtotal': subtotal
        })

    cur = db.execute(
        'INSERT INTO orders (customer_name, customer_phone, total, status, created_at) VALUES (?,?,?,?,?)',
        (customer, phone, total, 'pendente', datetime.now().isoformat())
    )
    order_id = cur.lastrowid

    for v in validated:
        db.execute(
            'INSERT INTO order_items (order_id, product_id, product_name, price, quantity, unit) VALUES (?,?,?,?,?,?)',
            (order_id, v['product_id'], v['name'], v['price'], v['quantity'], v['unit'])
        )
    db.commit()

    # WhatsApp message
    lines = [f"🛒 *Pedido #{order_id} — Freitas Mercadinho*", f"👤 Cliente: {customer}"]
    if phone:
        lines.append(f"📞 Telefone: {phone}")
    lines.append("")
    for v in validated:
        lines.append(f"• {v['name']} × {v['quantity']} {v['unit']} — R$ {v['subtotal']:.2f}".replace('.', ','))
    lines += ["", f"*Total: R$ {total:.2f}*".replace('.', ','),
              "", "Sua satisfação é nosso compromisso! 🏪"]
    msg = "\n".join(lines)

    return jsonify({'ok': True, 'order_id': order_id, 'total': total, 'whatsapp_msg': msg})

@app.route('/api/admin/orders', methods=['GET'])
@require_admin
def get_orders():
    db     = get_db()
    orders = db.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
    result = []
    for o in orders:
        items = db.execute('SELECT * FROM order_items WHERE order_id=?', (o['id'],)).fetchall()
        result.append({**dict(o), 'items': [dict(i) for i in items]})
    return jsonify(result)

@app.route('/api/admin/orders/<int:oid>/status', methods=['PUT'])
@require_admin
def update_order_status(oid):
    status  = request.json.get('status')
    allowed = ['pendente','confirmado','separando','entregue','cancelado']
    if status not in allowed:
        return jsonify({'error': 'Status inválido'}), 400
    db = get_db()
    db.execute('UPDATE orders SET status=? WHERE id=?', (status, oid))
    db.commit()
    return jsonify({'ok': True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
