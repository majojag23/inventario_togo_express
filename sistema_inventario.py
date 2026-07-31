import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_URL = os.environ.get('DATABASE_URL')

def get_db():
    if DB_URL:
        url = DB_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        return conn

PRODUCTOS_FACTURA = [
    ("Cerveza Corona Extra (330 mL)", 2.25, 1.65, 24, "Cerveza Corona Extra (330 mL).jpg"),
    ("Cerveza Corona Extra six", 12.50, 9.90, 4, "Cerveza Corona Extra six.jpg"),
    ("Cerveza Pilsener (355 mL) u", 1.75, 1.36, 36, "Cerveza Pilsener (355 mL) u.jpg"),
    ("Cerveza Pilsener (355 mL) six", 9.75, 8.15, 6, "Cerveza Pilsener (355 mL).jpg"),
    ("Cerveza Pilsener (473 mL) u", 2.25, 1.75, 24, "Pilsener 473 mL.jpg"),
    ("Cerveza Pilsener (473 mL) six", 12.50, 9.90, 4, "Pilsener 473 mL six.jpg"),
    ("Cerveza Suprema (330 mL) u", 1.85, 1.42, 18, "Cerveza Suprema (330 mL).jpg"),
    ("Cerveza Suprema six", 10.25, 8.50, 3, "SUPREMA SIX.jpg"),
    ("Coca-Cola 2.5 L", 2.95, 2.13, 6, "Coca-Cola 2.5 L.jpg"),
    ("Coca-Cola Litro", 1.75, 1.30, 6, "Coca-Cola Litro.jpg"),
    ("Coca-Cola Personal", 1.65, 1.25, 2, "Coca-Cola Personal.jpg"),
    ("Coca-Cola zero 1.25", 1.85, 1.30, 2, "Coca-Cola zero 1.25.jpg"),
    ("del valle 2.5", 1.75, 1.30, 4, "del valle 2.5.jpg"),
    ("Rehidratante Elec", 3.10, 2.35, 1, "Rehidratante Elec.jpg"),
    ("Smirnoff Vodka", 18.99, 12.95, 1, "smirnoff vodka.jpg"),
    ("Ron Bacardí Blanco", 21.50, 14.60, 1, "Ron Bacardí Blanco.jpg"),
    ("Ron Bacardí Carta Blanco Oro", 14.50, 9.40, 2, "Ron Bacardí Carta Blanco Oro.jpg"),
    ("Ron Bacardí Oro 750 ml", 18.50, 12.35, 1, "Ron Bacardí Oro 750 ml.jpg"),
    ("Vino Reservado Concha y Toro", 8.99, 5.95, 1, "Vino Reservado Concha y Toro.jpg"),
    ("Doritos Extra Queso", 2.15, 1.63, 2, "Doritos Extra Queso.jpg"),
    ("Doritos NACHO", 2.15, 1.63, 2, "Doritos NACHO.jpg"),
    ("Papas Lays con Sal", 2.60, 1.96, 3, "Papas Lays con Sal.jpg"),
    ("LAYS BARBACOA 80 GR", 2.10, 1.57, 1, "LAYS BARBACOA 80 GR.jpg"),
    ("CHURRITOS PEQUE", 0.75, 0.51, 3, "CHURRITOS PEQUE.jpg"),
    ("CHETOOS", 0.75, 0.51, 3, "CHETOOS.jpg"),
    ("NOCHOS 150", 1.65, 1.20, 2, "NOCHOS 150.jpg"),
    ("JALAPEÑO 150", 1.65, 1.20, 2, "JALAPEÑO 150.jpg"),
    ("Semillas Surtidas", 3.85, 2.95, 2, "semillas.jpg"),
    ("LECHE ENTERA", 1.95, 1.50, 2, "LECHE ENTERA.jpg"),
    ("LECHE DESLAC", 1.65, 1.25, 3, "LECHE DESLAC.jpg"),
    ("PALETA D/YOGURT", 1.25, 0.74, 6, "PALETA D/YOGURT.jpg"),
    ("PALETA TASTY", 1.00, 0.60, 6, "PALETA TASTY.jpg"),
    ("MALBORO GOLD", 3.75, 2.05, 10, "MALBORO GOLD.jpg"),
    ("MALBORO VISTA / FOREST", 4.50, 3.50, 10, "MALBORO VISTA.jpg"),
    ("PALLMALL", 2.50, 1.95, 10, "PALLMALL.jpg"),
    ("HIELERA NAPOLI CO", 9.99, 7.00, 1, "HIELERA NAPOLI CO.jpg"),
    ("Hielo Selectos 2", 1.60, 1.15, 2, "Hielo Selectos 2.jpg"),
    ("ALIMENTO P/PERRO", 4.25, 3.15, 2, "ALIMENTO P/PERRO.jpg")
]

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                precio NUMERIC(10,2) NOT NULL,
                costo NUMERIC(10,2) NOT NULL,
                stock INTEGER NOT NULL,
                ventas INTEGER DEFAULT 0,
                imagen VARCHAR(255)
            )
        ''' if DB_URL else '''
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial_ventas (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER,
                monto NUMERIC(10,2) NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''' if DB_URL else '''
            CREATE TABLE IF NOT EXISTS historial_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                monto REAL NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM productos")
        res = cursor.fetchone()
        
        count = 0
        if isinstance(res, dict):
            count = list(res.values())[0]
        elif isinstance(res, (tuple, list)):
            count = res[0]

        if count == 0:
            for p in PRODUCTOS_FACTURA:
                q = '''
                    INSERT INTO productos (nombre, precio, costo, stock, ventas, imagen)
                    VALUES (%s, %s, %s, %s, 0, %s)
                ''' if DB_URL else '''
                    INSERT INTO productos (nombre, precio, costo, stock, ventas, imagen)
                    VALUES (?, ?, ?, ?, 0, ?)
                '''
                cursor.execute(q, p)
            conn.commit()

        conn.close()
    except Exception as e:
        print("Error en init_db:", e)

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/productos', methods=['GET'])
def get_productos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM productos ORDER BY nombre ASC')
    prods = cursor.fetchall()
    conn.close()
    
    lista = []
    for p in prods:
        d = dict(p)
        d['precio'] = float(d['precio']) if d['precio'] is not None else 0.0
        d['costo'] = float(d['costo']) if d['costo'] is not None else 0.0
        d['stock'] = int(d['stock']) if d['stock'] is not None else 0
        d['ventas'] = int(d['ventas']) if d['ventas'] is not None else 0
        lista.append(d)
        
    return jsonify(lista)

def extraer_marca_medida(nombre):
    nombre_low = nombre.lower()
    medida = ""
    if "473" in nombre_low:
        medida = "473"
    elif "355" in nombre_low:
        medida = "355"
    elif "330" in nombre_low:
        medida = "330"
    
    marca = ""
    for m in ['corona', 'pilsener', 'suprema']:
        if m in nombre_low:
            marca = m
            break
            
    return marca, medida

@app.route('/api/vender/<int:id>', methods=['POST'])
def vender_producto(id):
    conn = get_db()
    cursor = conn.cursor()
    
    q_sel = 'SELECT * FROM productos WHERE id = %s' if DB_URL else 'SELECT * FROM productos WHERE id = ?'
    cursor.execute(q_sel, (id,))
    prod = cursor.fetchone()
    
    if prod and prod['stock'] > 0:
        nombre_prod = prod['nombre'].lower()
        precio_prod = float(prod['precio'])
        
        # 1. Restar 1 al producto vendido
        q_upd = 'UPDATE productos SET stock = stock - 1, ventas = ventas + 1 WHERE id = %s' if DB_URL else 'UPDATE productos SET stock = stock - 1, ventas = ventas + 1 WHERE id = ?'
        cursor.execute(q_upd, (id,))
        
        # 2. Registrar la venta
        q_hist = 'INSERT INTO historial_ventas (producto_id, monto, fecha) VALUES (%s, %s, %s)' if DB_URL else 'INSERT INTO historial_ventas (producto_id, monto, fecha) VALUES (?, ?, ?)'
        cursor.execute(q_hist, (id, precio_prod, datetime.now()))
        
        cursor.execute('SELECT * FROM productos')
        todos = [dict(p) for p in cursor.fetchall()]
        
        marca, medida = extraer_marca_medida(nombre_prod)
        
        if marca:
            es_six = 'six' in nombre_prod
            for item in todos:
                item_nombre = item['nombre'].lower()
                item_marca, item_medida = extraer_marca_medida(item_nombre)
                
                # Deben coincidir MARCA y MEDIDA exactas
                if item_marca == marca and item_medida == medida:
                    if es_six and 'six' not in item_nombre:
                        nuevo_stock_u = max(0, int(item['stock']) - 6)
                        q_upd_u = 'UPDATE productos SET stock = %s WHERE id = %s' if DB_URL else 'UPDATE productos SET stock = ? WHERE id = ?'
                        cursor.execute(q_upd_u, (nuevo_stock_u, item['id']))
                        break
                    elif not es_six and 'six' in item_nombre:
                        stock_actual_u = int(prod['stock']) - 1
                        possible_six = stock_actual_u // 6
                        if int(item['stock']) > possible_six:
                            q_upd_six = 'UPDATE productos SET stock = %s WHERE id = %s' if DB_URL else 'UPDATE productos SET stock = ? WHERE id = ?'
                            cursor.execute(q_upd_six, (possible_six, item['id']))
                        break

        conn.commit()
        conn.close()
        return jsonify({"success": True})
    
    conn.close()
    return jsonify({"success": False, "message": "Agotado"}), 400

@app.route('/api/devolver/<int:id>', methods=['POST'])
def devolver_producto(id):
    conn = get_db()
    cursor = conn.cursor()
    
    q_sel = 'SELECT * FROM productos WHERE id = %s' if DB_URL else 'SELECT * FROM productos WHERE id = ?'
    cursor.execute(q_sel, (id,))
    prod = cursor.fetchone()
    
    if prod:
        nombre_prod = prod['nombre'].lower()
        precio_prod = float(prod['precio'])
        nuevas_ventas = max(0, int(prod['ventas']) - 1)
        
        q_upd = 'UPDATE productos SET stock = stock + 1, ventas = %s WHERE id = %s' if DB_URL else 'UPDATE productos SET stock = stock + 1, ventas = ? WHERE id = ?'
        cursor.execute(q_upd, (nuevas_ventas, id))
        
        q_hist = 'INSERT INTO historial_ventas (producto_id, monto, fecha) VALUES (%s, %s, %s)' if DB_URL else 'INSERT INTO historial_ventas (producto_id, monto, fecha) VALUES (?, ?, ?)'
        cursor.execute(q_hist, (id, -precio_prod, datetime.now()))

        cursor.execute('SELECT * FROM productos')
        todos = [dict(p) for p in cursor.fetchall()]
        
        marca, medida = extraer_marca_medida(nombre_prod)
        
        if marca:
            es_six = 'six' in nombre_prod
            for item in todos:
                item_nombre = item['nombre'].lower()
                item_marca, item_medida = extraer_marca_medida(item_nombre)
                
                if item_marca == marca and item_medida == medida:
                    if es_six and 'six' not in item_nombre:
                        nuevo_stock_u = int(item['stock']) + 6
                        q_upd_u = 'UPDATE productos SET stock = %s WHERE id = %s' if DB_URL else 'UPDATE productos SET stock = ? WHERE id = ?'
                        cursor.execute(q_upd_u, (nuevo_stock_u, item['id']))
                        break
                    elif not es_six and 'six' in item_nombre:
                        stock_actual_u = int(prod['stock']) + 1
                        possible_six = stock_actual_u // 6
                        if int(item['stock']) < possible_six:
                            q_upd_six = 'UPDATE productos SET stock = %s WHERE id = %s' if DB_URL else 'UPDATE productos SET stock = ? WHERE id = ?'
                            cursor.execute(q_upd_six, (possible_six, item['id']))
                        break

        conn.commit()
        conn.close()
        return jsonify({"success": True})
    
    conn.close()
    return jsonify({"success": False, "message": "Producto no encontrado"}), 400

@app.route('/api/agregar-venta-manual', methods=['POST'])
def agregar_venta_manual():
    monto = float(request.json.get('monto', 0))
    if monto > 0:
        conn = get_db()
        cursor = conn.cursor()
        q_hist = 'INSERT INTO historial_ventas (producto_id, monto, fecha) VALUES (NULL, %s, %s)' if DB_URL else 'INSERT INTO historial_ventas (producto_id, monto, fecha) VALUES (NULL, ?, ?)'
        cursor.execute(q_hist, (monto, datetime.now()))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route('/api/resumen-ventas', methods=['GET'])
def resumen_ventas():
    conn = get_db()
    cursor = conn.cursor()
    
    hoy = datetime.now().strftime('%Y-%m-%d')
    mes = datetime.now().strftime('%Y-%m')
    
    if DB_URL:
        cursor.execute("SELECT COALESCE(SUM(monto), 0) as total FROM historial_ventas WHERE TO_CHAR(fecha, 'YYYY-MM-DD') = %s", (hoy,))
    else:
        cursor.execute("SELECT COALESCE(SUM(monto), 0) as total FROM historial_ventas WHERE strftime('%Y-%m-%d', fecha) = ?", (hoy,))
    res_hoy = cursor.fetchone()
    total_hoy = float(list(res_hoy.values())[0] if isinstance(res_hoy, dict) else res_hoy[0])
    
    if DB_URL:
        cursor.execute("SELECT COALESCE(SUM(monto), 0) as total FROM historial_ventas WHERE TO_CHAR(fecha, 'YYYY-MM') = %s", (mes,))
    else:
        cursor.execute("SELECT COALESCE(SUM(monto), 0) as total FROM historial_ventas WHERE strftime('%Y-%m', fecha) = ?", (mes,))
    res_mes = cursor.fetchone()
    total_mes = float(list(res_mes.values())[0] if isinstance(res_mes, dict) else res_mes[0])

    conn.close()
    return jsonify({"hoy": total_hoy, "mes": total_mes})

@app.route('/api/reiniciar-ventas', methods=['POST'])
def reiniciar_ventas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM productos')
    cursor.execute('DELETE FROM historial_ventas')
    for p in PRODUCTOS_FACTURA:
        q = '''
            INSERT INTO productos (nombre, precio, costo, stock, ventas, imagen)
            VALUES (%s, %s, %s, %s, 0, %s)
        ''' if DB_URL else '''
            INSERT INTO productos (nombre, precio, costo, stock, ventas, imagen)
            VALUES (?, ?, ?, ?, 0, ?)
        '''
        cursor.execute(q, p)
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/producto/eliminar/<int:id>', methods=['DELETE', 'POST'])
def eliminar_producto(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM productos WHERE id = %s' if DB_URL else 'DELETE FROM productos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

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
    cursor = conn.cursor()

    if id_prod:
        if filename:
            q = 'UPDATE productos SET nombre=%s, precio=%s, costo=%s, stock=%s, imagen=%s WHERE id=%s' if DB_URL else 'UPDATE productos SET nombre=?, precio=?, costo=?, stock=?, imagen=? WHERE id=?'
            cursor.execute(q, (nombre, precio, costo, stock, filename, id_prod))
        else:
            q = 'UPDATE productos SET nombre=%s, precio=%s, costo=%s, stock=%s WHERE id=%s' if DB_URL else 'UPDATE productos SET nombre=?, precio=?, costo=?, stock=? WHERE id=?'
            cursor.execute(q, (nombre, precio, costo, stock, id_prod))
    else:
        q = 'INSERT INTO productos (nombre, precio, costo, stock, imagen) VALUES (%s, %s, %s, %s, %s)' if DB_URL else 'INSERT INTO productos (nombre, precio, costo, stock, imagen) VALUES (?, ?, ?, ?, ?)'
        cursor.execute(q, (nombre, precio, costo, stock, filename or 'default.jpg'))

    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filename):
        return send_from_directory('.', filename)
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
