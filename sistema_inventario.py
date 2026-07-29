import os
import sqlite3
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'inventario.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                costo REAL NOT NULL,
                stock INTEGER NOT NULL,
                ventas INTEGER DEFAULT 0,
                imagen TEXT
            )
        ''')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM productos")
        if cursor.fetchone()[0] == 0:
            productos_iniciales = [
                ("Cerveza Corona Extra (330 mL)", 2.25, 1.65, 24, 0, "Cerveza Corona Extra (330 mL).jpg"),
                ("Cerveza Corona Extra six", 12.50, 9.90, 4, 0, "Cerveza Corona Extra six.jpg"),
                ("Cerveza Pilsener (355 mL) u", 1.75, 1.36, 36, 0, "Cerveza Pilsener (355 mL) u.jpg"),
                ("Cerveza Pilsener (355 mL)", 9.75, 8.15, 6, 0, "Cerveza Pilsener (355 mL).jpg"),
                ("Cerveza Suprema (330 mL)", 1.85, 1.42, 18, 0, "Cerveza Suprema (330 mL).jpg"),
                ("Coca-Cola 2.5 L", 2.95, 2.13, 6, 0, "Coca-Cola 2.5 L.jpg"),
                ("Vodka Smirnoff No. 21", 18.99, 12.95, 1, 0, "smirnoff vodka.jpg"),
                ("Ron Bacardí Carta Blanco", 14.50, 9.40, 2, 0, "Ron Bacardí Carta Blanco Oro.jpg"),
                ("Doritos Extra Queso", 2.15, 1.63, 2, 0, "Doritos Extra Queso.jpg"),
                ("Papas Lays con Sal", 2.60, 1.96, 3, 0, "Papas Lays con Sal.jpg")
            ]
            cursor.executemany('''
                INSERT INTO productos (nombre, precio, costo, stock, ventas, imagen)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', productos_iniciales)
            conn.commit()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/productos', methods=['GET'])
def get_productos():
    conn = get_db()
    prods = conn.execute('SELECT * FROM productos').fetchall()
    return jsonify([dict(p) for p in prods])

@app.route('/api/vender/<int:id>', methods=['POST'])
def vender_producto(id):
    conn = get_db()
    prod = conn.execute('SELECT * FROM productos WHERE id = ?', (id,)).fetchone()
    if prod and prod['stock'] > 0:
        conn.execute('UPDATE productos SET stock = stock - 1, ventas = ventas + 1 WHERE id = ?', (id,))
        conn.commit()
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Agotado"}), 400

@app.route('/api/producto/guardar', methods=['POST'])
def guardar_producto():
    id_prod = request.form.get('id')
    nombre = request.form.get('nombre')
    precio = float(request.form.get('precio', 0))
    costo = float(request.form.get('costo', 0))
    stock = int(request.form.get('stock', 0))

    imagen_file = request.files.get('imagen')
    filename = None

    if imagen_file and allowed_file(imagen_file.filename):
        filename = secure_filename(imagen_file.filename)
        imagen_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = get_db()
    if id_prod:
        if filename:
            conn.execute('''
                UPDATE productos SET nombre=?, precio=?, costo=?, stock=?, imagen=? WHERE id=?
            ''', (nombre, precio, costo, stock, filename, id_prod))
        else:
            conn.execute('''
                UPDATE productos SET nombre=?, precio=?, costo=?, stock=? WHERE id=?
            ''', (nombre, precio, costo, stock, id_prod))
    else:
        conn.execute('''
            INSERT INTO productos (nombre, precio, costo, stock, imagen) VALUES (?, ?, ?, ?, ?)
        ''', (nombre, precio, costo, stock, filename or 'default.jpg'))

    conn.commit()
    return jsonify({"success": True})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    return send_from_directory('.', filename)

# Servir el logo corporativo guardado en la raíz
@app.route('/logo_togo_express.jpg')
def serve_logo():
    return send_from_directory('.', 'logo_togo_express.jpg')

if __name__ == '__main__':
    # Configurado para servidor de Virtual Machine
    app.run(host='0.0.0.0', port=5000, debug=True)