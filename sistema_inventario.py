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

# CATÁLOGO COMPLETO AUDITADO (37 ARTÍCULOS DE LA FACTURA E INVENTARIO)
PRODUCTOS_FACTURA = [
    # CERVEZAS Y BEBIDAS
    ("Cerveza Corona Extra (330 mL)", 2.25, 1.65, 24, "Cerveza Corona Extra (330 mL).jpg"),
    ("Cerveza Corona Extra six", 12.50, 9.90, 4, "Cerveza Corona Extra six.jpg"),
    ("Cerveza Pilsener (355 mL) u", 1.75, 1.36, 36, "Cerveza Pilsener (355 mL) u.jpg"),
    ("Cerveza Pilsener (355 mL)", 9.75, 8.15, 6, "Cerveza Pilsener (355 mL).jpg"),
    ("Cerveza Suprema (330 mL)", 1.85, 1.42, 18, "Cerveza Suprema (330 mL).jpg"),
    ("Cerveza Suprema six", 10.25, 8.50, 3, "SUPREMA SIX.jpg"),

    # GASEOSAS Y REFRESCOS
    ("Coca-Cola 2.5 L", 2.95, 2.13, 6, "Coca-Cola 2.5 L.jpg"),
    ("Coca-Cola Litro", 1.75, 1.30, 6, "Coca-Cola Litro.jpg"),
    ("Coca-Cola Personal", 1.65, 1.25, 2, "Coca-Cola Personal.jpg"),
    ("Coca-Cola zero 1.25", 1.85, 1.30, 2, "Coca-Cola zero 1.25.jpg"),
    ("del valle 2.5", 1.75, 1.30, 4, "del valle 2.5.jpg"),
    ("Rehidratante Elec", 3.10, 2.35, 1, "Rehidratante Elec.jpg"),

    # LICORES Y VINOS
    ("Smirnoff Vodka", 18.99, 12.95, 1, "smirnoff vodka.jpg"),
    ("Ron Bacardí Blanco", 21.50, 14.60, 1, "Ron Bacardí Blanco.jpg"),
    ("Ron Bacardí Carta Blanco Oro", 14.50, 9.40, 2, "Ron Bacardí Carta Blanco Oro.jpg"),
    ("Ron Bacardí Oro 750 ml", 18.50, 12.35, 1, "Ron Bacardí Oro 750 ml.jpg"),
    ("Vino Reservado Concha y Toro", 8.99, 5.95, 1, "Vino Reservado Concha y Toro.jpg"),

    # SNACKS Y BOQUITAS
    ("Doritos Extra Queso", 2.15, 1.63, 2, "Doritos Extra Queso.jpg"),
    ("Doritos NACHO", 2.15, 1.63, 2, "Doritos NACHO.jpg"),
    ("Papas Lays con Sal", 2.60, 1.96, 3, "Papas Lays con Sal.jpg"),
    ("LAYS BARBACOA 80 GR", 2.10, 1.57, 1, "LAYS BARBACOA 80 GR.jpg"),
    ("CHURRITOS PEQUE", 0.75, 0.51, 3, "CHURRITOS PEQUE.jpg"),
    ("CHETOOS", 0.75, 0.51, 3, "CHETOOS.jpg"),
    ("NOCHOS 150", 1.65, 1.20, 2, "NOCHOS 150.jpg"),
    ("JALAPEÑO 150", 1.65, 1.20, 2, "JALAPEÑO 150.jpg"),
    ("Semillas Surtidas", 3.85, 2.95, 2, "semillas.jpg"),

    # LÁCTEOS Y HELADOS
    ("LECHE ENTERA", 1.95, 1.50, 2, "LECHE ENTERA.jpg"),
    ("LECHE DESLAC", 1.65, 1.25, 3, "LECHE DESLAC.jpg"),
    ("PALETA D/YOGURT", 1.25, 0.74, 6, "PALETA D/YOGURT.jpg"),
    ("PALETA TASTY", 1.00, 0.60, 6, "PALETA TASTY.jpg"),

    # CIGARROS Y OTROS
    ("MALBORO GOLD", 3.75, 2.05, 10, "MALBORO GOLD.jpg"),
    ("MALBORO FOREST", 4.99, 4.10, 10, "MALBORO FOREST.jpg"),
    ("MALBORO VISTA", 4.50, 3.50, 10, "MALBORO VISTA.jpg"),
    ("PALLMALL", 2.50, 1.95, 10, "PALLMALL.jpg"),
    ("HIELERA NAPOLI CO", 9.99, 7.00, 1, "HIELERA NAPOLI CO.jpg"),
    ("Hielo Selectos 2", 1.60, 1.15, 2, "Hielo Selectos 2.jpg"),
    ("ALIMENTO P/PERRO", 4.25, 3.15, 2, "ALIMENTO P/PERRO.jpg")
]

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
        # Si la base de datos no tiene todos los productos, los refresca
        cursor.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        if count < len(PRODUCTOS_FACTURA):
            conn.execute("DELETE FROM productos")
            cursor.executemany('''
                INSERT INTO productos (nombre, precio, costo, stock, ventas, imagen)
                VALUES (?, ?, ?, ?, 0, ?)
            ''', PRODUCTOS_FACTURA)
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
    prods = conn.execute('SELECT * FROM productos ORDER BY nombre ASC').fetchall()
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

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Busca la imagen en la carpeta uploads o en el directorio raíz donde están guardadas
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    # Busca ignorando extensión
    base = os.path.splitext(filename)[0]
    for ext in ['.jpg', '.png', '.jpeg', '.JPG', '.PNG', '.webp']:
        if os.path.exists(base + ext):
            return send_from_directory('.', base + ext)
    return send_from_directory('.', 'logo_togo_express.png')

@app.route('/logo_togo_express.png')
@app.route('/logo_togo_express.jpg')
def serve_logo():
    if os.path.exists('logo_togo_express.png'):
        return send_from_directory('.', 'logo_togo_express.png')
    elif os.path.exists('logo_togo_express.jpg'):
        return send_from_directory('.', 'logo_togo_express.jpg')
    return "", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
