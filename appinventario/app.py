from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import pandas as pd
import os
from datetime import datetime
import barcode
from barcode.writer import ImageWriter
import io
import uuid
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)

# Configuración de la aplicación
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['BARCODE_FOLDER'] = 'static/barcodes'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB máximo
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Crear directorios si no existen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['BARCODE_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Tabla de grupos
    c.execute('''CREATE TABLE IF NOT EXISTS grupos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT UNIQUE,
                  descripcion TEXT)''')
    
    # Tabla de códigos de barras utilizados
    c.execute('''CREATE TABLE IF NOT EXISTS codigos_barras
                 (codigo TEXT PRIMARY KEY)''')
    
    # Tabla de dispositivos
    c.execute('''CREATE TABLE IF NOT EXISTS dispositivos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  grupo_id INTEGER,
                  responsable TEXT,
                  marca TEXT,
                  vpn TEXT,
                  canal_vpn TEXT,
                  room TEXT,
                  cuentas_tiktok TEXT,
                  pais TEXT,
                  apple_id TEXT,
                  foto TEXT,
                  costo REAL,
                  fecha_agregacion DATE,
                  comentarios TEXT,
                  codigo_barras TEXT UNIQUE,
                  FOREIGN KEY (grupo_id) REFERENCES grupos (id))''')
    
    # Tabla de productos de venta
    c.execute('''CREATE TABLE IF NOT EXISTS productos_venta
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  grupo_id INTEGER,
                  marca TEXT,
                  descripcion TEXT,
                  caducidad DATE,
                  fecha_agregacion DATE,
                  costo REAL,
                  lote TEXT,
                  codigo_barras TEXT UNIQUE,
                  FOREIGN KEY (grupo_id) REFERENCES grupos (id))''')
    
    # Tabla de material general
    c.execute('''CREATE TABLE IF NOT EXISTS material_general
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT,
                  tipo TEXT,
                  grupo_id INTEGER,
                  room TEXT,
                  fecha_agregacion DATE,
                  precio REAL,
                  codigo_barras TEXT UNIQUE,
                  FOREIGN KEY (grupo_id) REFERENCES grupos (id))''')
    
    # Insertar grupos por defecto si no existen
    grupos = [('EC', 'Grupo EC'), ('GL', 'Grupo GL'), ('RH', 'Grupo RH'), 
              ('PCG', 'Grupo PCG'), ('ALMACEN', 'Grupo ALMACEN')]
    
    for grupo in grupos:
        try:
            c.execute("INSERT INTO grupos (nombre, descripcion) VALUES (?, ?)", grupo)
        except sqlite3.IntegrityError:
            pass  # El grupo ya existe
    
    conn.commit()
    conn.close()

# Generar código de barras único
def generar_codigo_barras():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    while True:
        # Generar un código numérico aleatorio de 12 dígitos
        codigo = str(datetime.now().timestamp()).replace('.', '')[-12:]
        
        # Verificar si el código ya existe
        c.execute("SELECT * FROM codigos_barras WHERE codigo = ?", (codigo,))
        if not c.fetchone():
            c.execute("INSERT INTO codigos_barras (codigo) VALUES (?)", (codigo,))
            conn.commit()
            break
    
    conn.close()
    return codigo

# Generar imagen de código de barras
def generar_imagen_codigo_barras(codigo):
    try:
        # Crear código de barras CODE128
        code128 = barcode.get_barcode_class('code128')
        barcode_instance = code128(codigo, writer=ImageWriter())
        
        # Guardar la imagen
        filename = f"{codigo}"
        filepath = os.path.join(app.config['BARCODE_FOLDER'], filename)
        barcode_instance.save(filepath)
        
        return f"/{filepath}.png"
    except Exception as e:
        print(f"Error generando código de barras: {e}")
        return ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inventario_general')
def inventario_general():
    # Esta vista ahora solo mostrará los botones de grupos
    conn = sqlite3.connect('inventory.db')
    grupos = pd.read_sql_query("SELECT * FROM grupos", conn)
    conn.close()
    
    return render_template('inventario_general.html', 
                           grupos=grupos.to_dict('records'))

@app.route('/inventario_grupo/<grupo_nombre>')
def inventario_grupo(grupo_nombre):
    # Vista para mostrar el inventario de un grupo específico
    conn = sqlite3.connect('inventory.db')
    
    # Obtener información del grupo
    grupo_info = pd.read_sql_query("SELECT * FROM grupos WHERE nombre = ?", conn, params=(grupo_nombre,))
    
    if grupo_info.empty:
        conn.close()
        return "Grupo no encontrado", 404
    
    # Obtener dispositivos del grupo
    dispositivos = pd.read_sql_query("SELECT d.* FROM dispositivos d JOIN grupos g ON d.grupo_id = g.id WHERE g.nombre = ?", conn, params=(grupo_nombre,))
    
    # Obtener productos de venta del grupo
    productos_venta = pd.read_sql_query("SELECT p.* FROM productos_venta p JOIN grupos g ON p.grupo_id = g.id WHERE g.nombre = ?", conn, params=(grupo_nombre,))
    
    # Obtener material general del grupo
    material_general = pd.read_sql_query("SELECT m.* FROM material_general m JOIN grupos g ON m.grupo_id = g.id WHERE g.nombre = ?", conn, params=(grupo_nombre,))
    
    conn.close()
    
    return render_template('inventario_grupo.html', 
                           grupo=grupo_info.iloc[0],
                           dispositivos=dispositivos.to_dict('records'),
                           productos_venta=productos_venta.to_dict('records'),
                           material_general=material_general.to_dict('records'))

@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    conn = sqlite3.connect('inventory.db')
    grupos = pd.read_sql_query("SELECT * FROM grupos", conn)
    conn.close()
    
    if request.method == 'POST':
        print("=== INICIANDO PROCESO DE AGREGAR PRODUCTO ===")
        print("Datos del formulario:", dict(request.form))
        
        tipo = request.form['tipo']
        grupo_id = request.form['grupo_id']
        print(f"Tipo: {tipo}, Grupo ID: {grupo_id}")
        
        # Validar campos requeridos
        if tipo == 'dispositivo':
            print("Validando campos de dispositivo...")
            campos_requeridos = ['responsable', 'marca', 'vpn', 'room', 'pais', 'costo']
            
            # Solo validar canal_vpn si no es "No tiene" y el campo existe
            vpn = request.form['vpn']
            if vpn != 'No tiene' and 'canal_vpn' in request.form:
                campos_requeridos.append('canal_vpn')
            
            for campo in campos_requeridos:
                valor = request.form.get(campo)
                print(f"Campo {campo}: '{valor}'")
                if not valor:
                    print(f"ERROR: Campo requerido faltante: {campo}")
                    return jsonify({
                        'success': False, 
                        'message': f'Error: El campo "{campo}" es requerido para dispositivos'
                    })
            
            # Validar VPN y canal único (solo si no es "No tiene" y el campo existe)
            vpn = request.form['vpn']
            canal_vpn = request.form.get('canal_vpn', '')  # Usar get() para evitar KeyError
            
            print(f"VPN: {vpn}, Canal VPN: {canal_vpn}")
            
            if vpn != 'No tiene' and canal_vpn:  # Solo validar si tiene VPN y canal
                try:
                    conn = sqlite3.connect('inventory.db')
                    c = conn.cursor()
                    c.execute('''SELECT COUNT(*) FROM dispositivos 
                                WHERE vpn = ? AND canal_vpn = ?''', 
                             (vpn, canal_vpn))
                    existe_combinacion = c.fetchone()[0] > 0
                    conn.close()
                    
                    if existe_combinacion:
                        print(f"ERROR: Combinación VPN ya existe: {vpn} - {canal_vpn}")
                        return jsonify({
                            'success': False, 
                            'message': f'Error: La VPN "{vpn}" con el canal "{canal_vpn}" ya está en uso. Por favor use una combinación diferente.'
                        })
                except Exception as e:
                    print(f"Error validando VPN: {e}")
                    return jsonify({
                        'success': False, 
                        'message': f'Error validando VPN: {str(e)}'
                    })
        
        # Si pasa todas las validaciones, proceder con el registro
        codigo_barras = generar_codigo_barras()
        foto_url = ''
        print(f"Código de barras generado: {codigo_barras}")
        
        # Procesar imagen solo para dispositivos
        if tipo == 'dispositivo' and 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    foto_url = f"/static/uploads/{unique_filename}"
                    print(f"Imagen guardada exitosamente: {foto_url}")
                except Exception as e:
                    print(f"Error guardando imagen: {e}")
                    foto_url = ''
        else:
            print("No hay imagen o no es dispositivo")
                    
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        
        try:
            if tipo == 'dispositivo':
                # Si no tiene VPN, guardar cadena vacía en canal_vpn
                canal_vpn_value = request.form.get('canal_vpn', '') if request.form['vpn'] != 'No tiene' else ''
                
                print(f"Insertando dispositivo en base de datos...")
                print(f"Valores: responsable={request.form['responsable']}, marca={request.form['marca']}, vpn={request.form['vpn']}, canal_vpn={canal_vpn_value}")
                
                c.execute('''INSERT INTO dispositivos 
                             (grupo_id, responsable, marca, vpn, canal_vpn, room, 
                              cuentas_tiktok, pais, apple_id, foto, costo, fecha_agregacion, 
                              comentarios, codigo_barras)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (grupo_id, request.form['responsable'], request.form['marca'],
                              request.form['vpn'], canal_vpn_value, request.form['room'],
                              request.form.get('cuentas_tiktok', ''), request.form['pais'], 
                              request.form.get('apple_id', ''), foto_url, 
                              float(request.form['costo']), datetime.now().date(),
                              request.form.get('comentarios', ''), codigo_barras))
                print("Dispositivo insertado exitosamente")
            
            elif tipo == 'producto_venta':
                caducidad = request.form.get('caducidad_venta') if request.form.get('caducidad_venta') else None
                print(f"Insertando producto de venta...")
                
                c.execute('''INSERT INTO productos_venta 
                             (grupo_id, marca, descripcion, caducidad, fecha_agregacion, 
                              costo, lote, codigo_barras)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                             (grupo_id, request.form['marca_venta'], request.form['descripcion_venta'],
                              caducidad, datetime.now().date(), float(request.form['costo_venta']),
                              request.form.get('lote_venta', ''), codigo_barras))
                print("Producto de venta insertado exitosamente")
            
            elif tipo == 'material_general':
              print(f"Insertando material general...")
    
              c.execute('''INSERT INTO material_general 
                 (nombre, tipo, grupo_id, room, fecha_agregacion, precio, codigo_barras)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (request.form['nombre_material'], request.form['tipo_material'], grupo_id,
                  request.form['room_material'], datetime.now().date(), 
                  float(request.form['precio_material']), codigo_barras))
              print("Material general insertado exitosamente")
            
            conn.commit()
            print("Commit realizado exitosamente")
            
        except sqlite3.OperationalError as e:
            conn.close()
            print(f"Error operacional de base de datos: {e}")
            if 'locked' in str(e):
                return jsonify({
                    'success': False, 
                    'message': 'Error: La base de datos está en uso. Intente nuevamente.'
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': f'Error de base de datos: {str(e)}'
                })
        except Exception as e:
            conn.close()
            print(f"Error inesperado: {e}")
            return jsonify({
                'success': False, 
                'message': f'Error inesperado: {str(e)}'
            })
        
        conn.close()
        
        # Generar imagen del código de barras
        barcode_path = generar_imagen_codigo_barras(codigo_barras)
        print(f"Imagen de código de barras generada: {barcode_path}")
        
        # Obtener el nombre del grupo para mostrar
        conn = sqlite3.connect('inventory.db')
        grupo_nombre = pd.read_sql_query("SELECT nombre FROM grupos WHERE id = ?", conn, params=(grupo_id,)).iloc[0]['nombre']
        conn.close()
        
        print("Proceso completado exitosamente")
        return jsonify({
            'success': True, 
            'message': 'Producto agregado correctamente', 
            'codigo_barras': codigo_barras,
            'barcode_image': barcode_path,
            'tipo': tipo,
            'grupo': grupo_nombre,
            'foto_url': foto_url
        })
    
    return render_template('agregar_producto.html', grupos=grupos.to_dict('records'))

@app.route('/buscar_producto', methods=['GET', 'POST'])
def buscar_producto():
    if request.method == 'POST':
        codigo_barras = request.form['codigo_barras']
        
        conn = sqlite3.connect('inventory.db')
        
        # Buscar en dispositivos
        dispositivo = pd.read_sql_query('''SELECT d.*, g.nombre as grupo_nombre, g.id as grupo_id 
                                         FROM dispositivos d 
                                         JOIN grupos g ON d.grupo_id = g.id 
                                         WHERE d.codigo_barras = ?''', 
                                       conn, params=(codigo_barras,))
        
        # Buscar en productos de venta
        producto_venta = pd.read_sql_query('''SELECT p.*, g.nombre as grupo_nombre, g.id as grupo_id 
                                            FROM productos_venta p 
                                            JOIN grupos g ON p.grupo_id = g.id 
                                            WHERE p.codigo_barras = ?''', 
                                          conn, params=(codigo_barras,))
        
        # Buscar en material general
        material = pd.read_sql_query('''SELECT m.*, g.nombre as grupo_nombre, g.id as grupo_id 
                                      FROM material_general m 
                                      JOIN grupos g ON m.grupo_id = g.id 
                                      WHERE m.codigo_barras = ?''', 
                                    conn, params=(codigo_barras,))
        
        # Obtener lista de grupos para el dropdown
        grupos = pd.read_sql_query("SELECT * FROM grupos", conn)
        
        conn.close()
        
        producto = None
        tipo = None
        
        if not dispositivo.empty:
            producto = dispositivo.to_dict('records')[0]
            tipo = 'dispositivo'
        elif not producto_venta.empty:
            producto = producto_venta.to_dict('records')[0]
            tipo = 'producto_venta'
        elif not material.empty:
            producto = material.to_dict('records')[0]
            tipo = 'material_general'
        
        if producto:
            return render_template('resultado_busqueda.html', 
                                 producto=producto, 
                                 tipo=tipo, 
                                 codigo_barras=codigo_barras,
                                 grupos=grupos.to_dict('records'))
        else:
            return render_template('resultado_busqueda.html', error="Producto no encontrado")
    
    return render_template('buscar_producto.html')

@app.route('/editar_producto/<tipo>/<int:id>', methods=['POST'])
def editar_producto(tipo, id):
    try:
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        
        # Obtener el nuevo grupo_id del formulario
        nuevo_grupo_id = request.form.get('grupo_id')
        
        if tipo == 'dispositivo':
            # Validar VPN y canal único (excluyendo el registro actual)
            vpn = request.form['vpn']
            canal_vpn = request.form['canal_vpn']
            
            c.execute('''SELECT COUNT(*) FROM dispositivos 
                        WHERE vpn = ? AND canal_vpn = ? AND id != ?''', 
                     (vpn, canal_vpn, id))
            existe_combinacion = c.fetchone()[0] > 0
            
            if existe_combinacion:
                conn.close()
                return jsonify({
                    'success': False, 
                    'message': f'Error: La VPN "{vpn}" con el canal "{canal_vpn}" ya está en uso. Por favor use una combinación diferente.'
                })
            
            # Continuar con la actualización incluyendo el grupo_id
            c.execute('''UPDATE dispositivos SET 
                         grupo_id=?, responsable=?, marca=?, vpn=?, canal_vpn=?, room=?,
                         cuentas_tiktok=?, pais=?, apple_id=?, foto=?, costo=?,
                         comentarios=?
                         WHERE id=?''',
                         (nuevo_grupo_id, request.form['responsable'], request.form['marca'],
                          request.form['vpn'], request.form['canal_vpn'], request.form['room'],
                          request.form['cuentas_tiktok'], request.form['pais'], 
                          request.form['apple_id'], request.form['foto'], 
                          request.form['costo'], request.form['comentarios'], id))
        
        elif tipo == 'producto_venta':
            caducidad = request.form['caducidad'] if request.form['caducidad'] else None
            c.execute('''UPDATE productos_venta SET 
                         grupo_id=?, marca=?, descripcion=?, caducidad=?, costo=?, lote=?
                         WHERE id=?''',
                         (nuevo_grupo_id, request.form['marca'], request.form['descripcion'],
                          caducidad, request.form['costo'], request.form['lote'], id))
        
        elif tipo == 'material_general':
            c.execute('''UPDATE material_general SET 
                         grupo_id=?, nombre=?, tipo=?, room=?, precio=?
                         WHERE id=?''',
                         (nuevo_grupo_id, request.form['nombre'], request.form['tipo'],
                          request.form['room'], request.form['precio'], id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Producto actualizado correctamente'})
    
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/eliminar_producto/<tipo>/<int:id>', methods=['POST'])
def eliminar_producto(tipo, id):
    try:
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        
        # Primero obtener el código de barras para eliminarlo de la tabla de códigos
        if tipo == 'dispositivo':
            c.execute("SELECT codigo_barras, foto FROM dispositivos WHERE id=?", (id,))
        elif tipo == 'producto_venta':
            c.execute("SELECT codigo_barras FROM productos_venta WHERE id=?", (id,))
        elif tipo == 'material_general':
            c.execute("SELECT codigo_barras FROM material_general WHERE id=?", (id,))
        
        resultado = c.fetchone()
        codigo_barras = None
        foto_path = None
        
        if resultado:
            codigo_barras = resultado[0]
            if tipo == 'dispositivo' and len(resultado) > 1:
                foto_path = resultado[1]
            
            # Eliminar la imagen del código de barras si existe
            if codigo_barras:
                ruta_imagen = os.path.join(app.config['BARCODE_FOLDER'], f"{codigo_barras}.png")
                if os.path.exists(ruta_imagen):
                    os.remove(ruta_imagen)
            
            # Eliminar de la tabla de códigos de barras
            if codigo_barras:
                try:
                    c.execute("DELETE FROM codigos_barras WHERE codigo=?", (codigo_barras,))
                except sqlite3.OperationalError as e:
                    print(f"Error eliminando código de barras: {e}")
        
        # Eliminar la foto del dispositivo si existe
        if foto_path and os.path.exists(foto_path.lstrip('/')):
            try:
                os.remove(foto_path.lstrip('/'))
            except Exception as e:
                print(f"Error eliminando foto: {e}")
        
        # Eliminar el producto
        if tipo == 'dispositivo':
            c.execute("DELETE FROM dispositivos WHERE id=?", (id,))
        elif tipo == 'producto_venta':
            c.execute("DELETE FROM productos_venta WHERE id=?", (id,))
        elif tipo == 'material_general':
            c.execute("DELETE FROM material_general WHERE id=?", (id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Producto eliminado correctamente'})
    
    except sqlite3.OperationalError as e:
        if 'locked' in str(e):
            return jsonify({'success': False, 'message': 'Error: La base de datos está en uso. Intente nuevamente.'})
        else:
            return jsonify({'success': False, 'message': f'Error de base de datos: {str(e)}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error inesperado: {str(e)}'})

@app.route('/exportar_excel')
def exportar_excel():
    grupo = request.args.get('grupo', 'todos')
    tipo = request.args.get('tipo', 'todos')
    
    conn = sqlite3.connect('inventory.db')
    
    # Obtener datos según los filtros
    datos = {}
    
    if tipo in ['todos', 'dispositivos']:
        if grupo == 'todos':
            dispositivos = pd.read_sql_query("SELECT d.*, g.nombre as grupo_nombre FROM dispositivos d JOIN grupos g ON d.grupo_id = g.id", conn)
        else:
            dispositivos = pd.read_sql_query("SELECT d.*, g.nombre as grupo_nombre FROM dispositivos d JOIN grupos g ON d.grupo_id = g.id WHERE g.nombre = ?", conn, params=(grupo,))
        datos['Dispositivos'] = dispositivos
    
    if tipo in ['todos', 'productos_venta']:
        if grupo == 'todos':
            productos_venta = pd.read_sql_query("SELECT p.*, g.nombre as grupo_nombre FROM productos_venta p JOIN grupos g ON p.grupo_id = g.id", conn)
        else:
            productos_venta = pd.read_sql_query("SELECT p.*, g.nombre as grupo_nombre FROM productos_venta p JOIN grupos g ON p.grupo_id = g.id WHERE g.nombre = ?", conn, params=(grupo,))
        datos['Productos de Venta'] = productos_venta
    
    if tipo in ['todos', 'material_general']:
        if grupo == 'todos':
            material_general = pd.read_sql_query("SELECT m.*, g.nombre as grupo_nombre FROM material_general m JOIN grupos g ON m.grupo_id = g.id", conn)
        else:
            material_general = pd.read_sql_query("SELECT m.*, g.nombre as grupo_nombre FROM material_general m JOIN grupos g ON m.grupo_id = g.id WHERE g.nombre = ?", conn, params=(grupo,))
        datos['Material General'] = material_general
    
    conn.close()
    
    # Crear archivo Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for nombre, df in datos.items():
            df.to_excel(writer, sheet_name=nombre, index=False)
    
    output.seek(0)
    
    filename = f"inventario_{grupo}.xlsx" if grupo != 'todos' else "inventario_completo.xlsx"
    
    return send_file(output, download_name=filename, as_attachment=True)

@app.route('/generar_codigos_barras', methods=['POST'])
def generar_codigos_barras():
    cantidad = int(request.form.get('cantidad', 1))
    codigos = []
    
    for _ in range(cantidad):
        codigo = generar_codigo_barras()
        generar_imagen_codigo_barras(codigo)
        codigos.append(codigo)
    
    return jsonify({'success': True, 'codigos': codigos})

if __name__ == '__main__':
    init_db()
    # Para desarrollo con IP específica
    context = ('cert.pem', 'key.pem')
    app.run(host='172.16.42.203', port=5000, debug=True, ssl_context=context)