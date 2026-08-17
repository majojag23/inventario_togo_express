import os
import sqlite3
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_URL = os.environ.get('DATABASE_URL')
TZ_SV = timezone(timedelta(hours=-6))

def get_now_sv():
    return datetime.now(TZ_SV)

def get_db():
    if DB_URL:
        url = DB_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        return conn

MAPA_IMAGENES_EXACTO = [
    ("golden grande", "golden grande.jpg"),
    ("golden six pack grande", "golden six pack grande.png"),
    ("golden 355", "golden 355 ml.jpg"),
    ("golden six pack pequeño", "golden six pack pequeño.png"),
    ("regia extra grande", "regia extra grande.png"),
    ("regia grande six", "regia six paq grande.png"),
    ("regia pequeña", "regia pequeña.png"),
    ("regia six paq pequeña", "regia six paq pequeña.png"),
    ("mirinda", "Gaseosairinda Naranja.png"),
    ("tropical fresa", "gaseosa tropical fresa.png"),
    ("tropical uva", "gaseosa tropical uva.png"),
    ("crema y especias", "Lays crema y especias.jpg"),
    ("zero lata", "coca coloa zero.jpg"),
    ("cookies", "pinguinos cookies 80gr.jpg"),
    ("clásicos", "pinguinos 80gr.jpg"),
    ("clasicos", "pinguinos 80gr.jpg"),
    ("gansito", "gansito 50 gr.jpg"),
    ("choco wow", "galletas chocowow.jpg"),
    ("triple chocolate", "pinguinos triple chocolate  80gr.jpg"),
    ("fresa crush", "pinguinos fresa  80gr.jpg")
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
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_sv VARCHAR(50)
            )
        ''' if DB_URL else '''
            CREATE TABLE IF NOT EXISTS historial_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                monto REAL NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_sv TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras_facturas (
                id SERIAL PRIMARY KEY,
                concepto VARCHAR(255) NOT NULL,
                monto NUMERIC(10,2) NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''' if DB_URL else '''
            CREATE TABLE IF NOT EXISTS compras_facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concepto TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bases_manuales (
                clave VARCHAR(50) PRIMARY KEY,
                valor NUMERIC(10,2) NOT NULL
            )
        ''' if DB_URL else '''
            CREATE TABLE IF NOT EXISTS bases_manuales (
                clave TEXT PRIMARY KEY,
                valor REAL NOT NULL
            )
        ''')
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

@app.route('/api/forzar-vinculacion', methods=['POST'])
def forzar_vinculacion():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM productos")
        prods = cursor.fetchall()
        
        actualizados = 0
        for p in prods:
            pid = p['id'] if isinstance(p, dict) else p[0]
            pnombre = (p['nombre'] if isinstance(p, dict) else p[1]).lower().strip()
            
            for clave, archivo in MAPA_IMAGENES_EXACTO:
                if clave in pnombre:
                    q_upd = "UPDATE productos SET imagen = %s WHERE id = %s" if DB_URL else "UPDATE productos SET imagen = ? WHERE id = ?"
                    cursor.execute(q_upd, (archivo, pid))
                    actualizados += 1
                    break
                    
        conn.commit()
        conn.close()
        return jsonify({"success": True, "actualizados": actualizados})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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

@app.route('/api/producto/guardar', methods=['POST'])
def guardar_producto():
    try:
        id_prod = request.form.get('id')
        nombre = request.form.get('nombre')
        precio = float(request.form.get('precio', 0))
        costo = float(request.form.get('costo', 0))
        stock = int(request.form.get('stock', 0))
        imagen_actual = request.form.get('imagen_actual')

        imagen_file = request.files.get('imagen')
        filename = None

        if imagen_file and allowed_file(imagen_file.filename):
            filename = secure_filename(imagen_file.filename)
            imagen_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db()
        cursor = conn.cursor()

        if id_prod and id_prod.strip() != "":
            id_int = int(id_prod)
            foto_final = filename if filename else (imagen_actual if imagen_actual else 'default.jpg')
            q = 'UPDATE productos SET nombre=%s, precio=%s, costo=%s, stock=%s, imagen=%s WHERE id=%s' if DB_URL else 'UPDATE productos SET nombre=?, precio=?, costo=?, stock=?, imagen=? WHERE id=?'
            cursor.execute(q, (nombre, precio, costo, stock, foto_final, id_int))
        else:
            q = 'INSERT INTO productos (nombre, precio, costo, stock, imagen) VALUES (%s, %s, %s, %s, %s)' if DB_URL else 'INSERT INTO productos (nombre, precio, costo, stock, imagen) VALUES (?, ?, ?, ?, ?)'
            cursor.execute(q, (nombre, precio, costo, stock, filename or 'default.jpg'))

        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print("Error al guardar producto:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/producto/eliminar/<int:id>', methods=['DELETE', 'POST'])
def eliminar_producto(id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        q_hist = 'UPDATE historial_ventas SET producto_id = NULL WHERE producto_id = %s' if DB_URL else 'UPDATE historial_ventas SET producto_id = NULL WHERE producto_id = ?'
        cursor.execute(q_hist, (id,))
        
        q_del = 'DELETE FROM productos WHERE id = %s' if DB_URL else 'DELETE FROM productos WHERE id = ?'
        cursor.execute(q_del, (id,))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print("Error en eliminar_producto:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/actualizar-bases-manuales', methods=['POST'])
def actualizar_bases_manuales():
    try:
        data = request.json or {}
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM historial_ventas")
        cursor.execute("DELETE FROM compras_facturas")
        cursor.execute("UPDATE productos SET ventas = 0")
        
        for clave in ['hoy', 'mes', 'facturas', 'ganancia']:
            if clave in data:
                v = float(data[clave])
                if DB_URL:
                    q = 'INSERT INTO bases_manuales (clave, valor) VALUES (%s, %s) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor'
                    cursor.execute(q, (clave, v))
                else:
                    q = 'INSERT OR REPLACE INTO bases_manuales (clave, valor) VALUES (?, ?)'
                    cursor.execute(q, (clave, v))
                
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print("Error en actualizar_bases_manuales:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/resumen-ventas', methods=['GET'])
def resumen_ventas():
    try:
        now_sv = get_now_sv()
        hoy_str = now_sv.strftime('%Y-%m-%d')

        conn = get_db()
        cursor = conn.cursor()

        bm = {}
        try:
            cursor.execute("SELECT clave, valor FROM bases_manuales")
            filas_b = cursor.fetchall()
            for f in filas_b:
                d = dict(f)
                bm[str(d['clave'])] = float(d['valor'])
        except Exception:
            conn.rollback()

        base_hoy = bm.get('hoy', 0.00)
        base_mes = bm.get('mes', 386.00)
        base_facturas = bm.get('facturas', 205.24)
        base_ganancia = bm.get('ganancia', 110.85)

        ventas_hoy_reales = 0.0
        try:
            q_hoy = "SELECT COALESCE(SUM(monto), 0) FROM historial_ventas WHERE fecha_sv = %s" if DB_URL else "SELECT COALESCE(SUM(monto), 0) FROM historial_ventas WHERE fecha_sv = ?"
            cursor.execute(q_hoy, (hoy_str,))
            res_vh = cursor.fetchone()
            if res_vh:
                ventas_hoy_reales = float(list(dict(res_vh).values())[0] if isinstance(res_vh, dict) else res_vh[0] or 0)
        except Exception:
            conn.rollback()

        ventas_mes_reales = 0.0
        try:
            cursor.execute("SELECT COALESCE(SUM(monto), 0) FROM historial_ventas")
            res_vm = cursor.fetchone()
            if res_vm:
                ventas_mes_reales = float(list(dict(res_vm).values())[0] if isinstance(res_vm, dict) else res_vm[0] or 0)
        except Exception:
            conn.rollback()

        compras_nuevas = 0.0
        try:
            cursor.execute("SELECT COALESCE(SUM(monto), 0) FROM compras_facturas")
            res_c = cursor.fetchone()
            if res_c:
                compras_nuevas = float(list(dict(res_c).values())[0] if isinstance(res_c, dict) else res_c[0] or 0)
        except Exception:
            conn.rollback()

        ganancia_nuevas = 0.0
        try:
            cursor.execute('SELECT ventas, precio, costo FROM productos')
            prods = cursor.fetchall()
            for p in prods:
                d = dict(p)
                v = int(d.get('ventas', 0) or 0)
                precio = float(d.get('precio', 0) or 0)
                costo = float(d.get('costo', 0) or 0)
                ganancia_nuevas += v * (precio - costo)
        except Exception:
            conn.rollback()

        conn.close()

        total_hoy = base_hoy + ventas_hoy_reales
        total_mes = base_mes + ventas_mes_reales
        total_facturas = base_facturas + compras_nuevas
        ganancia_real = base_ganancia + ganancia_nuevas
        capital_libre_reinversion = total_mes - total_facturas - ganancia_real

        return jsonify({
            "hoy": float(total_hoy),
            "mes": float(total_mes),
            "compras_mes": float(total_facturas),
            "ganancia_real": float(ganancia_real),
            "capital_reinversion": float(capital_libre_reinversion),
            "base_hoy": float(base_hoy),
            "base_mes": float(base_mes),
            "base_facturas": float(base_facturas),
            "base_ganancia": float(base_ganancia)
        })
    except Exception as e:
        print("Error general en resumen_ventas:", e)
        return jsonify({
            "hoy": 0.00,
            "mes": 386.00,
            "compras_mes": 205.24,
            "ganancia_real": 110.85,
            "capital_reinversion": 69.91,
            "base_hoy": 0.00,
            "base_mes": 386.00,
            "base_facturas": 205.24,
            "base_ganancia": 110.85
        })

@app.route('/api/vender/<int:id>', methods=['POST'])
def vender_producto(id):
    conn = get_db()
    cursor = conn.cursor()
    
    q_sel = 'SELECT * FROM productos WHERE id = %s' if DB_URL else 'SELECT * FROM productos WHERE id = ?'
    cursor.execute(q_sel, (id,))
    prod = cursor.fetchone()
    
    if prod and prod['stock'] > 0:
        precio_prod = float(prod['precio'])
        now_sv = get_now_sv()
        hoy_str = now_sv.strftime('%Y-%m-%d')

        q_upd = 'UPDATE productos SET stock = stock - 1, ventas = ventas + 1 WHERE id = %s' if DB_URL else 'UPDATE productos SET stock = stock - 1, ventas = ventas + 1 WHERE id = ?'
        cursor.execute(q_upd, (id,))
        
        q_hist = 'INSERT INTO historial_ventas (producto_id, monto, fecha_sv) VALUES (%s, %s, %s)' if DB_URL else 'INSERT INTO historial_ventas (producto_id, monto, fecha_sv) VALUES (?, ?, ?)'
        cursor.execute(q_hist, (id, precio_prod, hoy_str))
        
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
        precio_prod = float(prod['precio'])
        nuevas_ventas = max(0, int(prod['ventas']) - 1)
        now_sv = get_now_sv()
        hoy_str = now_sv.strftime('%Y-%m-%d')

        q_upd = 'UPDATE productos SET stock = stock + 1, ventas = %s WHERE id = %s' if DB_URL else 'UPDATE productos SET stock = stock + 1, ventas = ? WHERE id = ?'
        cursor.execute(q_upd, (nuevas_ventas, id))
        
        q_hist = 'INSERT INTO historial_ventas (producto_id, monto, fecha_sv) VALUES (%s, %s, %s)' if DB_URL else 'INSERT INTO historial_ventas (producto_id, monto, fecha_sv) VALUES (?, ?, ?)'
        cursor.execute(q_hist, (id, -precio_prod, hoy_str))

        conn.commit()
        conn.close()
        return jsonify({"success": True})
    conn.close()
    return jsonify({"success": False}), 400

@app.route('/api/agregar-compra', methods=['POST'])
def agregar_compra():
    try:
        data = request.json or {}
        concepto = data.get('concepto', 'Compra de Factura')
        monto = float(data.get('monto', 0))
        if monto > 0:
            conn = get_db()
            cursor = conn.cursor()
            q = 'INSERT INTO compras_facturas (concepto, monto) VALUES (%s, %s)' if DB_URL else 'INSERT INTO compras_facturas (concepto, monto) VALUES (?, ?)'
            cursor.execute(q, (concepto, monto))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Monto inválido"}), 400
    except Exception as e:
        print("Error en agregar_compra:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/historial-compras', methods=['GET'])
def historial_compras():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM compras_facturas ORDER BY fecha DESC')
    filas = cursor.fetchall()
    conn.close()
    res = []
    for f in filas:
        d = dict(f)
        d['monto'] = float(d['monto'])
        d['fecha'] = str(d['fecha'])
        res.append(d)
    return jsonify(res)

@app.route('/api/historial-ventas/<string:tipo>', methods=['GET'])
def detalle_historial(tipo):
    conn = get_db()
    cursor = conn.cursor()
    now_sv = get_now_sv()
    hoy_str = now_sv.strftime('%Y-%m-%d')

    if tipo == 'hoy':
        try:
            q = '''
                SELECT h.id, COALESCE(p.nombre, 'Venta / Registro') as producto,
                       h.monto as precio, COALESCE(p.costo, 0) as costo, h.fecha 
                FROM historial_ventas h 
                LEFT JOIN productos p ON h.producto_id = p.id 
                WHERE h.fecha_sv = %s
                ORDER BY h.fecha DESC
            ''' if DB_URL else '''
                SELECT h.id, COALESCE(p.nombre, 'Venta / Registro') as producto,
                       h.monto as precio, COALESCE(p.costo, 0) as costo, h.fecha 
                FROM historial_ventas h 
                LEFT JOIN productos p ON h.producto_id = p.id 
                WHERE h.fecha_sv = ?
                ORDER BY h.fecha DESC
            '''
            cursor.execute(q, (hoy_str,))
        except Exception:
            conn.rollback()
            cursor.execute("SELECT h.id, COALESCE(p.nombre, 'Venta') as producto, h.monto as precio, COALESCE(p.costo, 0) as costo, h.fecha FROM historial_ventas h LEFT JOIN productos p ON h.producto_id = p.id ORDER BY h.fecha DESC")
    else:
        q = '''
            SELECT h.id, COALESCE(p.nombre, 'Venta / Registro') as producto,
                   h.monto as precio, COALESCE(p.costo, 0) as costo, h.fecha 
            FROM historial_ventas h 
            LEFT JOIN productos p ON h.producto_id = p.id 
            ORDER BY h.fecha DESC
        '''
        cursor.execute(q)

    filas = cursor.fetchall()
    conn.close()
    res = []
    for f in filas:
        d = dict(f)
        precio = float(d.get('precio', 0) or 0)
        costo = float(d.get('costo', 0) or 0)
        
        if precio < 0:
            ganancia = precio + costo
        else:
            ganancia = (precio - costo) if precio > 0 else 0.0

        d['monto'] = precio
        d['ganancia'] = ganancia
        if isinstance(d['fecha'], datetime):
            d['fecha'] = d['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            d['fecha'] = str(d['fecha'])
        res.append(d)
    return jsonify(res)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return send_from_directory('.', 'logo_togo_express.png')

@app.route('/logo_togo_express.png')
def serve_logo():
    return send_from_directory('.', 'logo_togo_express.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
