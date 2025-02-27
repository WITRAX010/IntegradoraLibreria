from flask import Blueprint, render_template, render_template_string, request, redirect, url_for, session, flash
from db import get_db_connection
import hashlib
from datetime import datetime, timedelta

# Blueprint para manejar rutas de usuario
usuarios_bp = Blueprint('usuarios', __name__)

def navbar(role, nombre):
    admin_links = '''
    <li><a href="{{ url_for('usuarios.admin_libros') }}">Gestionar Libros</a></li>
    <li><a href="{{ url_for('usuarios.admin_pedidos') }}">Pedidos</a></li>
    <li><a href="{{ url_for('usuarios.admin_reportes') }}">Reportes</a></li>
    '''
    cliente_links = '''
    <li><a href="{{ url_for('usuarios.cliente_dashboard') }}">Inicio</a></li>
    <li><a href="{{ url_for('usuarios.carrito') }}">Carrito</a></li>
    <li><a href="{{ url_for('usuarios.mis_pedidos') }}">Mis Pedidos</a></li>
    <li><a href="{{ url_for('usuarios.configuracion') }}">Mi Cuenta</a></li>
    '''
    return f'''
    <header>
        <nav class="navbar">
            <div class="logo"><a href="{{ url_for('usuarios.cliente_dashboard') }}" style="color: white; text-decoration: none;">LibreriaKOA</a></div>
            <ul class="nav-links">
                {admin_links if role == 'admin' else cliente_links}
                <li><a href="/login">Cerrar sesión</a></li>
            </ul>
        </nav>
    </header>
    '''

# Dashboard de administrador
@usuarios_bp.route('/admin_dashboard')
def admin_dashboard():
    nombre = request.args.get('nombre', 'Administrador')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Obtener estadísticas para el dashboard
        cursor.execute("SELECT COUNT(*) as total_libros FROM Libros")
        total_libros = cursor.fetchone()['total_libros']
        cursor.execute("SELECT COUNT(*) as total_usuarios FROM Usuarios WHERE Rol = 0")
        total_usuarios = cursor.fetchone()['total_usuarios']
        cursor.execute("SELECT COUNT(*) as total_pedidos FROM Pedidos")
        total_pedidos = cursor.fetchone()['total_pedidos']
        cursor.execute("SELECT SUM(Total) as ingresos_totales FROM Pedidos")
        result = cursor.fetchone()
        ingresos_totales = result['ingresos_totales'] if result['ingresos_totales'] else 0
        cursor.close()
        conn.close()
    except Exception as e:
        total_libros = 0
        total_usuarios = 0
        total_pedidos = 0
        ingresos_totales = 0
        print(f"Error al obtener estadísticas: {e}")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel de Administración</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', nombre) + '''
    <div class="container">
        <h1>Panel de Administración</h1>
        <p>Bienvenido, ''' + nombre + '''. Aquí tienes una visión general del sistema.</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">''' + str(total_libros) + '''</div>
                <div class="stat-label">Libros en catálogo</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(total_usuarios) + '''</div>
                <div class="stat-label">Usuarios registrados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(total_pedidos) + '''</div>
                <div class="stat-label">Pedidos realizados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$''' + f"{ingresos_totales:.2f}" + '''</div>
                <div class="stat-label">Ingresos totales</div>
            </div>
        </div>
        
        <div class="card">
            <h2>Acciones rápidas</h2>
            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                <a href="{{ url_for('usuarios.admin_libros') }}" class="btn">Gestionar Libros</a>
                <a href="{{ url_for('usuarios.admin_pedidos') }}" class="btn">Ver Pedidos</a>
                <a href="{{ url_for('usuarios.admin_reportes') }}" class="btn">Generar Reportes</a>
            </div>
        </div>
    </div>
    
    <footer>
        <p>&copy; 2025 LibreriaKOA. Todos los derechos reservados.</p>
    </footer>
    </body>
    </html>
    ''')

@usuarios_bp.route('/cliente_dashboard')
def cliente_dashboard():
    nombre = request.args.get('nombre', 'Cliente')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Libros")
        libros = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        libros = []
        print(f"Error al obtener libros: {e}")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel de Cliente</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('cliente', nombre) + '''
    <div class="container">
        <h1>Bienvenido, ''' + nombre + '''</h1>
        <p>Este es el panel de cliente. Aquí puedes ver los libros disponibles.</p>
        
        <h2>Libros Disponibles</h2>
        <table class="table">
            <thead>
                <tr>
                    <th>Nombre</th>
                    <th>Precio</th>
                    <th>Stock</th>
                    <th>Descripción</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for libro in libros %}
                <tr>
                    <td>{{ libro.NombreLibro }}</td>
                    <td>${{ libro.Precio }}</td>
                    <td>{{ libro.Stock }}</td>
                    <td>{{ libro.Descripcion }}</td>
                    <td>
                        <a href="#" class="btn">Agregar al Carrito</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    </body>
    </html>
    ''', libros=libros)

@usuarios_bp.route('/mis_pedidos')
def mis_pedidos():
    nombre = request.args.get('nombre', 'Cliente')
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mis Pedidos</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('cliente', nombre) + '''
    <div class="container">
        <h1>Mis Pedidos</h1>
        <p>Aquí puedes ver el historial de tus pedidos.</p>
    </div>
    </body>
    </html>
    ''')

@usuarios_bp.route('/configuracion')
def configuracion():
    nombre = request.args.get('nombre', 'Cliente')
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Configuración</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('cliente', nombre) + '''
    <div class="container">
        <h1>Configuración</h1>
        <p>Aquí puedes configurar tu cuenta.</p>
    </div>
    </body>
    </html>
    ''')

    
# Ruta para listar todos los libros
@usuarios_bp.route('/admin/libros')
def admin_libros():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Libros")
        libros = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        libros = []
        print(f"Error al obtener libros: {e}")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gestionar Libros</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', 'Administrador') + '''
    <div class="container">
        <h1>Gestionar Libros</h1>
        <a href="{{ url_for('usuarios.agregar_libro') }}" class="btn">Agregar Libro</a>
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nombre</th>
                    <th>Precio</th>
                    <th>Stock</th>
                    <th>Descripción</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for libro in libros %}
                <tr>
                    <td>{{ libro.LibrolD }}</td>
                    <td>{{ libro.NombreLibro }}</td>
                    <td>${{ libro.Precio }}</td>
                    <td>{{ libro.Stock }}</td>
                    <td>{{ libro.Descripcion }}</td>
                    <td>
                        <a href="{{ url_for('usuarios.editar_libro', libro_id=libro.LibrolD) }}" class="btn">Editar</a>
                        <a href="{{ url_for('usuarios.eliminar_libro', libro_id=libro.LibrolD) }}" class="btn">Eliminar</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    </body>
    </html>
    ''', libros=libros)

# Ruta para agregar un libro
@usuarios_bp.route('/admin/libros/agregar', methods=['GET', 'POST'])
def agregar_libro():
    if request.method == 'POST':
        nombre_libro = request.form['nombre_libro']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        descripcion = request.form['descripcion']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Libros (NombreLibro, Precio, Stock, Descripcion) VALUES (%s, %s, %s, %s)",
                (nombre_libro, precio, stock, descripcion)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Libro agregado correctamente', 'success')
            return redirect(url_for('usuarios.admin_libros'))
        except Exception as e:
            print(f"Error al agregar libro: {e}")
            flash('Error al agregar el libro', 'error')

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agregar Libro</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', 'Administrador') + '''
    <div class="container">
        <h1>Agregar Libro</h1>
        <form method="POST">
            <div class="form-group">
                <label for="nombre_libro">Nombre del Libro</label>
                <input type="text" class="form-control" id="nombre_libro" name="nombre_libro" required>
            </div>
            <div class="form-group">
                <label for="precio">Precio</label>
                <input type="number" step="0.01" class="form-control" id="precio" name="precio" required>
            </div>
            <div class="form-group">
                <label for="stock">Stock</label>
                <input type="number" class="form-control" id="stock" name="stock" required>
            </div>
            <div class="form-group">
                <label for="descripcion">Descripción</label>
                <textarea class="form-control" id="descripcion" name="descripcion" rows="3"></textarea>
            </div>
            <button type="submit" class="btn">Agregar Libro</button>
        </form>
    </div>
    </body>
    </html>
    ''')

# Ruta para editar un libro
@usuarios_bp.route('/admin/libros/editar/<int:libro_id>', methods=['GET', 'POST'])
def editar_libro(libro_id):
    if request.method == 'POST':
        nombre_libro = request.form['nombre_libro']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        descripcion = request.form['descripcion']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Libros SET NombreLibro = %s, Precio = %s, Stock = %s, Descripcion = %s WHERE LibrolD = %s",
                (nombre_libro, precio, stock, descripcion, libro_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Libro actualizado correctamente', 'success')
            return redirect(url_for('usuarios.admin_libros'))
        except Exception as e:
            print(f"Error al actualizar libro: {e}")
            flash('Error al actualizar el libro', 'error')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Libros WHERE LibrolD = %s", (libro_id,))
        libro = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al obtener libro: {e}")
        return "Libro no encontrado", 404

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Libro</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', 'Administrador') + '''
    <div class="container">
        <h1>Editar Libro</h1>
        <form method="POST">
            <div class="form-group">
                <label for="nombre_libro">Nombre del Libro</label>
                <input type="text" class="form-control" id="nombre_libro" name="nombre_libro" value="{{ libro.NombreLibro }}" required>
            </div>
            <div class="form-group">
                <label for="precio">Precio</label>
                <input type="number" step="0.01" class="form-control" id="precio" name="precio" value="{{ libro.Precio }}" required>
            </div>
            <div class="form-group">
                <label for="stock">Stock</label>
                <input type="number" class="form-control" id="stock" name="stock" value="{{ libro.Stock }}" required>
            </div>
            <div class="form-group">
                <label for="descripcion">Descripción</label>
                <textarea class="form-control" id="descripcion" name="descripcion" rows="3">{{ libro.Descripcion }}</textarea>
            </div>
            <button type="submit" class="btn">Actualizar Libro</button>
        </form>
    </div>
    </body>
    </html>
    ''', libro=libro)

# Ruta para eliminar un libro
@usuarios_bp.route('/admin/libros/eliminar/<int:libro_id>')
def eliminar_libro(libro_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Libros WHERE LibrolD = %s", (libro_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Libro eliminado correctamente', 'success')
    except Exception as e:
        print(f"Error al eliminar libro: {e}")
        flash('Error al eliminar el libro', 'error')

    return redirect(url_for('usuarios.admin_libros'))

# Ruta para gestionar pedidos (placeholder)
@usuarios_bp.route('/admin/pedidos')
def admin_pedidos():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gestionar Pedidos</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', 'Administrador') + '''
    <div class="container">
        <h1>Gestionar Pedidos</h1>
        <p>Aquí puedes gestionar los pedidos.</p>
    </div>
    </body>
    </html>
    ''')

# Ruta para generar reportes (placeholder)
@usuarios_bp.route('/admin/reportes')
def admin_reportes():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generar Reportes</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', 'Administrador') + '''
    <div class="container">
        <h1>Generar Reportes</h1>
        <p>Aquí puedes generar reportes.</p>
    </div>
    </body>
    </html>
    ''')

@usuarios_bp.route('/carrito')
def carrito():
    nombre = request.args.get('nombre', 'Cliente')
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Carrito de Compras</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('cliente', nombre) + '''
    <div class="container">
        <h1>Carrito de Compras</h1>
        <p>Aquí puedes ver los libros que has agregado al carrito.</p>
    </div>
    </body>
    </html>
    ''')
