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

MAPA_IMAGENES = {
    "lays crema y especias": "Lays crema y especias.jpg",
    "Coca-Cola zero Lata": "coca coloa zero.jpg",
    "Pingüinos Cookies & Cream (80g)": "pinguinos cookies 80gr.jpg",
    "Pingüinos Clásicos (80g)": "pinguinos 80gr.jpg",
    "Gansito Marinela (50g)": "gansito 50 gr.jpg",
    "Galletas Choco Wow Chispas": "galletas chocowow.jpg",
    "Pingüinos Triple Chocolate (80g)": "pinguinos triple chocolate  80gr.jpg",
    "Pingüinos Fresa Crush (80g)": "pinguinos fresa  80gr.jpg",
    "Cerveza Corona Extra (330 mL)": "Cerveza Corona Extra (330 mL).jpg",
    "Cerveza Corona Extra six": "Cerveza Corona Extra six.jpg",
    "Cerveza Pilsener (355 mL) u": "Cerveza Pilsener (355 mL) u.jpg",
    "Cerveza Pilsener (355 mL) six": "Cerveza Pilsener (355 mL).jpg",
    "Cerveza Pilsener (473ml)": "pilsener (473ml)u.webp",
    "Cerveza Pilsener (473 mL) u": "pilsener (473ml)u.webp",
    "Cerveza Pilsener (473 mL) six": "cerveza pilsener (473ml) six.jpg",
    "Cerveza Pilsener (473 mL) six paq": "cerveza pilsener (473ml) six.jpg",
    "Cerveza Suprema (330 mL) u": "Cerveza Suprema (330 mL).jpg",
    "Cerveza Suprema six": "SUPREMA SIX.jpg",
    "Coca-Cola 2.5 L": "Coca-Cola 2.5 L.jpg",
    "Coca-Cola Litro": "Coca-Cola Litro.jpg",
    "Coca-Cola Personal": "Coca-Cola Personal.jpg",
    "Coca-Cola zero 1.25": "Coca-Cola zero 1.25.jpg",
    "Coca-Cola 1.25": "coca cola 1.25.jpg",
    "del valle 2.5": "del valle 2.5.jpg",
    "Doritos Extra Queso": "Doritos Extra Queso.jpg",
    "Doritos NACHO": "Doritos NACHO.jpg",
    "Papas Lays con Sal": "Papas Lays con Sal.jpg",
    "LAYS BARBACOA 80 GR": "LAYS BARBACOA 80 GR.jpg",
    "Lays Flamin Hot": "lays flaming hot.jpg",
    "CHURRITOS PEQUE": "CHURRITOS PEQUE.jpg",
    "CHETOOS": "CHETOOS.jpg",
    "NOCHOS 150": "NOCHOS 150.jpg",
    "JALAPEÑO 150": "JALAPEÑO 150.jpg",
    "Semillas Surtidas": "semillas.jpg",
    "LECHE ENTERA": "LECHE ENTERA.jpg",
    "LECHE DESLAC": "LECHE DESLAC.jpg",
    "paleta Nevería capuchino": "paleta_capuchino.jpeg",
    "paleta Nevería napolitano": "paleta_napolitano.jpeg",
    "paleta Nevería naranja": "paleta_naranjo.jpeg",
    "paleta Nevería neve choc": "paleta_neve_choc.jpeg",
    "paleta Nevería nevehola": "paleta_nevehola.jpeg",
    "paleta Nevería sandía": "paleta_sandia.jpeg",
    "paleta yogur choco maní": "paleta_mani.jpeg",
    "paleta yogurtt banano": "paleta_banano.jpeg",
    "paleta yogurtt fresa": "paleta_fresa.jpeg",
    "paleta palikakao": "paleta palikakao.jpg",
    "Maruchan carne": "Maruchan carne.jpg",
    "Maruchan pollo": "Maruchan pollo.jpg",
    "MALBORO GOLD": "MALBORO GOLD.jpg",
    "MALBORO VISTA / FOREST": "MALBORO VISTA.jpg",
    "PALLMALL": "PALLMALL.jpg",
    "HIELERA NAPOLI CO": "HIELERA NAPOLI CO.jpg",
    "Hielo Selectos 2": "Hielo Selectos 2.jpg",
    "ALIMENTO P/PERRO": "ALIMENTO P/PERRO.jpg",
    "huevos cubeta": "huevos cubeta.jpg",
    "Rehidratante Elec": "Rehidratante Elec.jpg",
    "Smirnoff Vodka": "smirnoff vodka.jpg",
    "Ron Bacardí Blanco": "Ron Bacardí Blanco.jpg",
    "Ron Bacardí Carta Blanco Oro": "Ron Bacardí Carta Blanco Oro.jpg",
    "Ron Bacardí Oro 750 ml": "Ron Bacardí Oro 750 ml.jpg",
    "Ron Bacardí Oro 980 ml": "Ron Bacardí Oro 750 ml.jpg",
    "Vino Reservado Concha y Toro": "Vino Reservado Concha y Toro.jpg",
    "Agua Alpina": "agua alpina.jpg",
    "agua": "agua alpina.jpg"
}

PRODUCTOS_FACTURA = [
    ("lays crema y especias", 2.00, 1.50, 6, "Lays crema y especias.jpg"),
    ("Coca-Cola zero Lata", 1.20, 0.85, 10, "coca coloa zero.jpg"),
    ("Pingüinos Cookies & Cream (80g)", 1.25, 0.85, 6, "pinguinos cookies 80gr.jpg"),
    ("Pingüinos Clásicos (80g)", 1.25, 0.85, 6, "pinguinos 80gr.jpg"),
    ("Gansito Marinela (50g)", 1.00, 0.65, 6, "gansito 50 gr.jpg"),
    ("Galletas Choco Wow Chispas", 0.60, 0.40, 10, "galletas chocowow.jpg"),
    ("Pingüinos Triple Chocolate (80g)", 1.25, 0.85, 6, "pinguinos triple chocolate  80gr.jpg"),
    ("Pingüinos Fresa Crush (80g)", 1.25, 0.85, 6, "pinguinos fresa  80gr.jpg"),
    ("Cerveza Corona Extra (330 mL)", 2.25, 1.65, 24, "Cerveza Corona Extra (330 mL).jpg"),
    ("Cerveza Corona Extra six", 12.50, 9.90, 4, "Cerveza Corona Extra six.jpg"),
    ("Cerveza Pilsener (355 mL) u", 1.75, 1.36, 36, "Cerveza Pilsener (355 mL) u.jpg"),
    ("Cerveza Pilsener (355 mL) six", 9.75, 8.15, 6, "Cerveza Pilsener (355 mL).jpg"),
    ("Cerveza Pilsener (473ml)", 2.50, 1.75, 13, "pilsener (473ml)u.webp"),
    ("Cerveza Pilsener (473 mL) six paq", 14.00, 9.90, 2, "cerveza pilsener (473ml) six.jpg"),
    ("Cerveza Suprema (330 mL) u", 1.85, 1.42, 18, "Cerveza Suprema (330 mL).jpg"),
    ("Cerveza Suprema six", 10.25, 8.50, 3, "SUPREMA SIX.jpg"),
    ("Coca-Cola 2.5 L", 2.95, 2.13, 6, "Coca-Cola 2.5 L.jpg"),
    ("Coca-Cola Litro", 1.75, 1.30, 6, "Coca-Cola Litro.jpg"),
    ("Coca-Cola Personal", 1.65, 1.25, 2, "Coca-Cola Personal.jpg"),
    ("Coca-Cola zero 1.25", 1.85, 1.30, 2, "Coca-Cola zero 1.25.jpg"),
    ("Coca-Cola 1.25", 2.10, 1.50, 6, "coca cola 1.25.jpg"),
    ("del valle 2.5", 1.75, 1.30, 4, "del valle 2.5.jpg"),
    ("Doritos Extra Queso", 2.15, 1.63, 2, "Doritos Extra Queso.jpg"),
    ("Doritos NACHO", 2.15, 1.63, 2, "Doritos NACHO.jpg"),
    ("Papas Lays con Sal", 2.60, 1.96, 3, "Papas Lays con Sal.jpg"),
    ("LAYS BARBACOA 80 GR", 2.10, 1.57, 1, "LAYS BARBACOA 80 GR.jpg"),
    ("Lays Flamin Hot", 2.10, 1.57, 6, "lays flaming hot.jpg"),
    ("CHURRITOS PEQUE", 0.75, 0.51, 3, "CHURRITOS PEQUE.jpg"),
    ("CHETOOS", 0.75, 0.51, 3, "CHETOOS.jpg"),
    ("NOCHOS 150", 1.65, 1.20, 2, "NOCHOS 150.jpg"),
    ("JALAPEÑO 150", 1.65, 1.20, 2, "JALAPEÑO 150.jpg"),
    ("Semillas Surtidas", 3.85, 2.95, 2, "semillas.jpg"),
    ("LECHE ENTERA", 1.95, 1.50, 2, "LECHE ENTERA.jpg"),
    ("LECHE DESLAC", 1.65, 1.25, 3, "LECHE DESLAC.jpg"),
    ("paleta Nevería capuchino", 1.00, 0.60, 6, "paleta_capuchino.jpeg"),
    ("paleta Nevería napolitano", 1.00, 0.60, 6, "paleta_napolitano.jpeg"),
    ("paleta Nevería naranja", 1.00, 0.60, 6, "paleta_naranjo.jpeg"),
    ("paleta Nevería neve choc", 1.00, 0.60, 6, "paleta_neve_choc.jpeg"),
    ("paleta Nevería nevehola", 1.00, 0.60, 6, "paleta_nevehola.jpeg"),
    ("paleta Nevería sandía", 1.00, 0.60, 6, "paleta_sandia.jpeg"),
    ("paleta yogur choco maní", 1.00, 0.60, 6, "paleta_mani.jpeg"),
    ("paleta yogurtt banano", 1.00, 0.60, 6, "paleta_banano.jpeg"),
    ("paleta yogurtt fresa", 1.00, 0.60, 6, "paleta_fresa.jpeg"),
    ("paleta palikakao", 1.00, 0.60, 6, "paleta palikakao.jpg"),
    ("Maruchan carne", 1.25, 0.90, 12, "Maruchan carne.jpg"),
    ("Maruchan pollo", 1.25, 0.90, 12, "Maruchan pollo.jpg"),
    ("MALBORO GOLD", 3.75, 2.05, 10, "MALBORO GOLD.jpg"),
    ("MALBORO VISTA / FOREST", 4.50, 3.50, 10, "MALBORO VISTA.jpg"),
    ("PALLMALL", 2.50, 1.95, 10, "PALLMALL.jpg"),
    ("HIELERA NAPOLI CO", 9.99, 7.00, 1, "HIELERA NAPOLI CO.jpg"),
    ("Hielo Selectos 2", 1.60, 1.15, 2, "Hielo Selectos 2.jpg"),
    ("ALIMENTO P/PERRO", 4.25, 3.15, 2, "ALIMENTO P/PERRO.jpg"),
    ("huevos cubeta", 6.00, 4.50, 1, "huevos cubeta.jpg"),
    ("Rehidratante Elec", 3.10, 2.35, 1, "Rehidratante Elec.jpg"),
    ("Smirnoff Vodka", 18.99, 12.95, 1, "smirnoff vodka.jpg"),
    ("Ron Bacardí Blanco", 21.50, 14.60, 1, "Ron Bacardí Blanco.jpg"),
    ("Ron Bacardí Carta Blanco Oro", 14.50, 9.40, 2, "Ron Bacardí Carta Blanco Oro.jpg"),
    ("Ron Bacardí Oro 750 ml", 21.00, 14.00, 1, "Ron Bacardí Oro 750 ml.jpg"),
    ("Ron Bacardí Oro 980 ml", 21.00, 14.00, 1, "Ron Bacardí Oro 750 ml.jpg"),
    ("Vino Reservado Concha y Toro", 8.99, 5.95, 1, "Vino Reservado Concha y Toro.jpg"),
    ("agua", 2.00, 1.50, 2, "agua alpina.jpg")
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

        try:
            if DB_URL:
                cursor.execute("ALTER TABLE historial_ventas ADD COLUMN fecha_sv VARCHAR(50);")
            else:
                cursor.execute("ALTER TABLE historial_ventas ADD COLUMN fecha_sv TEXT;")
            conn.commit()
        except Exception:
            conn.rollback()

        # DEDUPLICAR PRODUCTOS
        try:
            if DB_URL:
                cursor.execute('''
                    DELETE FROM productos p1
                    USING productos p2
                    WHERE LOWER(TRIM(p1.nombre)) = LOWER(TRIM(p2.nombre))
                      AND p1.id > p2.id;
                ''')
            else:
                cursor.execute('''
                    DELETE FROM productos
                    WHERE id NOT IN (
                        SELECT MIN(id)
                        FROM productos
                        GROUP BY LOWER(TRIM(nombre))
                    );
                ''')
            conn.commit()
        except Exception as e:
            conn.rollback()

        # INSERCIÓN ÚNICA INICIAL
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

        # VINCULAR IMÁGENES
        for nombre_prod, img_file in MAPA_IMAGENES.items():
            try:
                q_auto = 'UPDATE productos SET imagen = %s WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))' if DB_URL else 'UPDATE productos SET imagen = ? WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))'
                cursor.execute(q_auto, (img_file, nombre_prod))
                conn.commit()
            except Exception:
                conn.rollback()

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
            ganancia = precio - costo if precio > 0 else 0.0

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
