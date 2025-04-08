from flask import Blueprint, render_template, render_template_string, request, redirect, url_for, session, flash
from db import get_db_connection
import hashlib
import mysql.connector  
from datetime import datetime, timedelta
import requests
from extensions import mail
from flask_mail import Message
from flask import Blueprint, request, jsonify
from db import get_db_connection
from functools import wraps


# Blueprint para manejar rutas de usuario
usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:  # Verifica si el usuario está autenticado
            flash("Debes iniciar sesión para acceder a esta página.", "warning")
            return redirect(url_for('login.login'))  # Redirige al login si no hay sesión activa
        return f(*args, **kwargs)
    return decorated_function

def require_api_key(f):
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return jsonify({"error": "API Key requerida"}), 403

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuarios WHERE api_key = %s", (api_key,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({"error": "API Key inválida"}), 403

        return f(*args, **kwargs)
    return decorated_function

@usuarios_bp.route('/perfil', methods=['GET'])
@login_required
@require_api_key
def perfil():
    api_key = request.headers.get('X-API-KEY')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Nombre, PrimerApellido, SegundoApellido, Username, Rol FROM Usuarios WHERE api_key = %s", (api_key,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        return jsonify(user)
    return jsonify({"error": "Usuario no encontrado"}), 404

# Función para obtener información de un libro desde una API externa
def obtener_informacion_libro(isbn):
    url = f"https://api.ejemplo.com/libros/{isbn}"  # URL de la API (cambia esto por la URL real)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza una excepción si la solicitud no fue exitosa
        return response.json()  # Devuelve los datos en formato JSON
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener información del libro: {e}")
        return None

from flask import url_for

def navbar(role, nombre):
    # Enlaces para administradores
    admin_links = f'''
    <li><a href="{url_for('usuarios.admin_libros')}">Gestionar Libros</a></li>
    <li><a href="{url_for('usuarios.admin_pedidos')}">Pedidos</a></li>
    <li><a href="{url_for('usuarios.admin_reportes')}">Reportes</a></li>
    <li><a href="{url_for('usuarios.admin_usuarios')}">Usuarios</a></li>
    '''
    
    # Enlaces para clientes
    cliente_links = f'''
    <li><a href="{url_for('usuarios.cliente_dashboard')}">Inicio</a></li>
    <li><a href="{url_for('usuarios.carrito')}">Carrito</a></li>
    <li><a href="{url_for('usuarios.mis_pedidos')}">Mis Pedidos</a></li>
    <li><a href="{url_for('usuarios.direcciones')}">Mis Direcciones</a></li>
    <li><a href="{url_for('usuarios.configuracion')}">Mi Cuenta</a></li>
    '''
    
    # Enlace del dashboard (dependiendo del rol)
    dashboard_link = url_for('usuarios.admin_dashboard') if role == 'admin' else url_for('usuarios.cliente_dashboard')
    
    # Construir el navbar
    return f'''
    <header>
        <nav class="navbar">
            <div class="logo"><a href="{dashboard_link}" style="color: white; text-decoration: none;">LibreriaKOA</a></div>
            <ul class="nav-links">
                {admin_links if role == 'admin' else cliente_links}
                <li><a href="/login">Cerrar sesión</a></li>
            </ul>
        </nav>
    </header>
    '''

# Función para verificar si un libro es nuevo (menos de 14 días desde su publicación)
def es_libro_nuevo(fecha_publicacion):
    if not fecha_publicacion:
        return False
    limite_dias = 14  # Libros con menos de 14 días se consideran nuevos
    fecha_limite = datetime.now() - timedelta(days=limite_dias)
    return fecha_publicacion > fecha_limite



@usuarios_bp.route('/direcciones', methods=['GET', 'POST'])
@login_required
def direcciones():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para ver sus direcciones', 'error')
        return redirect(url_for('login.login'))
        
    user_id = session['user_id']
    conn = get_db_connection()

    if conn is None:
        flash('Error al conectar a la base de datos', 'error')
        return redirect(url_for('usuarios.direcciones'))

    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        calle = request.form['calle']
        colonia = request.form['colonia']
        pais = request.form['pais']
        ciudad = request.form['ciudad']

        try:
            cursor.execute(
                "INSERT INTO Direccion (UsuariolD, Calle, Colonia, Pais, Ciudad) VALUES (%s, %s, %s, %s, %s)",
                (user_id, calle, colonia, pais, ciudad)
            )
            conn.commit()
            flash('Dirección agregada correctamente', 'success')
        except mysql.connector.Error as err:
            print(f"Error al agregar dirección: {err}")
            flash(f'Error al agregar la dirección: {err}', 'error')
        finally:
            cursor.close()

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Direccion WHERE UsuariolD = %s", (user_id,))
        direcciones = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error al obtener direcciones: {err}")
        flash(f'Error al obtener las direcciones: {err}', 'error')
        direcciones = []
    finally:
        cursor.close()
        conn.close()

    return render_template('direcciones.html', direcciones=direcciones)




@usuarios_bp.route('/direcciones/editar/<int:direccion_id>', methods=['GET', 'POST'])
@login_required
def editar_direccion(direccion_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para editar direcciones', 'error')
        return redirect(url_for('login.login'))
        
    user_id = session['user_id']
    conn = get_db_connection()

    if conn is None:
        flash('Error al conectar a la base de datos', 'error')
        return redirect(url_for('usuarios.direcciones'))

    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        calle = request.form['calle']
        colonia = request.form['colonia']
        pais = request.form['pais']
        ciudad = request.form['ciudad']

        try:
            cursor.execute(
                "UPDATE Direccion SET Calle = %s, Colonia = %s, Pais = %s, Ciudad = %s WHERE DireccionlD = %s AND UsuariolD = %s",
                (calle, colonia, pais, ciudad, direccion_id, user_id)
            )
            conn.commit()
            flash('Dirección actualizada correctamente', 'success')
            return redirect(url_for('usuarios.direcciones'))
        except mysql.connector.Error as err:
            print(f"Error al actualizar dirección: {err}")
            flash(f'Error al actualizar la dirección: {err}', 'error')
        finally:
            cursor.close()
            conn.close()

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Direccion WHERE DireccionlD = %s AND UsuariolD = %s", (direccion_id, user_id))
        direccion = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Error al obtener la dirección: {err}")
        flash(f'Error al obtener la dirección: {err}', 'error')
        direccion = None
    finally:
        cursor.close()
        conn.close()

    if not direccion:
        flash('Dirección no encontrada', 'error')
        return redirect(url_for('usuarios.direcciones'))

    return render_template('editar_direccion.html', direccion=direccion)

@usuarios_bp.route('/direcciones/eliminar/<int:direccion_id>')
@login_required
def eliminar_direccion(direccion_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para eliminar direcciones', 'error')
        return redirect(url_for('login.login'))
        
    user_id = session['user_id']
    conn = get_db_connection()

    if conn is None:
        flash('Error al conectar a la base de datos', 'error')
        return redirect(url_for('usuarios.direcciones'))

    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM Direccion WHERE DireccionlD = %s AND UsuariolD = %s", (direccion_id, user_id))
        conn.commit()
        flash('Dirección eliminada correctamente', 'success')
    except mysql.connector.Error as err:
        print(f"Error al eliminar dirección: {err}")
        flash('Error al eliminar la dirección', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('usuarios.direcciones'))

@usuarios_bp.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder al panel de administración', 'error')
        return redirect(url_for('login.login'))
    
    nombre = request.args.get('nombre', 'Administrador')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
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

@usuarios_bp.route('/admin/ver-comentarios/<int:libro_id>')
@login_required
def ver_comentarios(libro_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('login.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.Rating, v.Comentario, v.FechaValoracion, u.Nombre AS NombreUsuario
            FROM ValoracionesLibros v
            JOIN Usuarios u ON v.UsuarioID = u.UsuarioID
            WHERE v.LibroID = %s
            ORDER BY v.FechaValoracion DESC
        """, (libro_id,))
        valoraciones = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        valoraciones = []
        print(f"Error al obtener comentarios: {e}")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Comentarios del Libro</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', 'Administrador') + '''
    <div class="container">
        <h1>Comentarios del Libro</h1>
        <a href="{{ url_for('usuarios.admin_libros') }}" class="btn">Volver a la lista de libros</a>
        <div class="comentarios-list">
            {% for valoracion in valoraciones %}
            <div class="comentario">
                <strong>{{ valoracion.NombreUsuario }}</strong> - <em>{{ valoracion.FechaValoracion.strftime('%d/%m/%Y %H:%M') }}</em>
                <div class="rating-stars">
                    {% for i in range(5) %}
                        {% if i < valoracion.Rating %}
                            <span style="color: #FFD700;">★</span>
                        {% else %}
                            <span style="color: #ccc;">★</span>
                        {% endif %}
                    {% endfor %}
                </div>
                <p>{{ valoracion.Comentario }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
    </body>
    </html>
    ''', valoraciones=valoraciones)

@usuarios_bp.route('/cliente_dashboard')
@login_required
def cliente_dashboard():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder al panel de cliente', 'error')
        return redirect(url_for('login.login'))

    nombre = request.args.get('nombre', 'Cliente')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener el término de búsqueda (si existe)
        search_query = request.args.get('q', '')

        # Construir la consulta SQL según el término de búsqueda
        if search_query:
            cursor.execute("""
                SELECT *, (DATEDIFF(NOW(), FechaPublicacion) <= 14) AS MostrarNuevo
                FROM Libros
                WHERE NombreLibro LIKE %s
            """, (f"%{search_query}%",))
        else:
            cursor.execute("SELECT *, (DATEDIFF(NOW(), FechaPublicacion) <= 14) AS MostrarNuevo FROM Libros")

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

        <!-- Formulario de búsqueda -->
        <form method="GET" action="{{ url_for('usuarios.cliente_dashboard') }}" class="search-form">
            <input type="text" name="q" placeholder="Buscar libro por nombre..." value="{{ request.args.get('q', '') }}">
            <button type="submit" class="btn-search">Buscar</button>
        </form>

        <h2>Libros Disponibles</h2>

        <div class="libros-grid">
            {% for libro in libros %}
            <div class="libro-card" data-libro-id="{{ libro.LibrolD }}" data-libro-nombre="{{ libro.NombreLibro }}">
                {% if libro.MostrarNuevo == 1 %}
                <span class="etiqueta-nuevo">NUEVO</span>
                {% endif %}
                <h3>{{ libro.NombreLibro }}</h3>
                <div class="precio">${{ libro.Precio }}</div>
                <p>{{ libro.Descripcion }}</p>
                <div class="rating-container" id="rating-container-{{ libro.LibrolD }}">
                    <div class="rating-stars">
                        {% set rating = libro.Rating|default(0)|float %}
                        {% for i in range(5) %}
                            {% if i < rating|int %}
                                <span style="color: #FFD700;">★</span>
                            {% elif i == rating|int and rating != rating|int %}
                                <span style="color: #FFD700;">★</span>
                            {% else %}
                                <span style="color: #ccc;">★</span>
                            {% endif %}
                        {% endfor %}
                    </div>
                    <span class="rating-value" id="rating-value-{{ libro.LibrolD }}">{{ libro.Rating|default(0)|float }}</span>
                </div>
                <p>Stock: {{ libro.Stock }}</p>
                <div class="acciones">
                    <!-- Botón para agregar al carrito -->
                    <form action="{{ url_for('usuarios.agregar_al_carrito', libro_id=libro.LibrolD) }}" method="POST" style="display: inline;">
                        <button type="submit" class="btn">Agregar al Carrito</button>
                    </form>
                    <!-- Botón de valorar (no lo modificamos) -->
                    <a href="#" class="btn" onclick="mostrarValorarLibro({{ libro.LibrolD }})">Valorar</a>
                    <a href="{{ url_for('usuarios.ver_comentarios_cliente', libro_id=libro.LibrolD) }}" class="btn">Ver Comentarios</a>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Modal para valorar libros -->
        <div id="modal-valorar" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="max-width: 500px; margin: 100px auto; background: white; padding: 20px; border-radius: 8px;">
                <h3>Valorar Libro</h3>
                <p>Libro: <span id="libro-nombre"></span></p>
                <div class="star-rating-select">
                    <span class="star" data-value="1" onclick="seleccionarEstrella(1)">★</span>
                    <span class="star" data-value="2" onclick="seleccionarEstrella(2)">★</span>
                    <span class="star" data-value="3" onclick="seleccionarEstrella(3)">★</span>
                    <span class="star" data-value="4" onclick="seleccionarEstrella(4)">★</span>
                    <span class="star" data-value="5" onclick="seleccionarEstrella(5)">★</span>
                </div>
                <input type="hidden" id="rating-value" value="0">
                <input type="hidden" id="libro-id" value="">
                <div style="margin-top: 20px;">
                    <label for="comentario">Comentario (opcional):</label>
                    <textarea id="comentario" rows="4" style="width: 100%;"></textarea>
                </div>
                <div style="margin-top: 20px;">
                    <button class="btn" onclick="guardarValoracion()">Guardar</button>
                    <button class="btn" onclick="cerrarModal()">Cancelar</button>
                </div>
            </div>
        </div>
    </div>
    <script>
        function agregarAlCarrito(librold) {
            alert('Libro agregado al carrito');
        }

        function mostrarValorarLibro(librold) {
            const libroCard = document.querySelector(`[data-libro-id="${librold}"]`);
            const libroNombre = libroCard.getAttribute('data-libro-nombre');

            document.getElementById('libro-nombre').textContent = libroNombre;
            document.getElementById('libro-id').value = librold;
            document.getElementById('modal-valorar').style.display = 'block';

            document.getElementById('rating-value').value = 0;
            const estrellas = document.querySelectorAll('.star-rating-select .star');
            estrellas.forEach(estrella => {
                estrella.style.color = '#ccc';
            });
        }

        function seleccionarEstrella(valor) {
            document.getElementById('rating-value').value = valor;
            const estrellas = document.querySelectorAll('.star-rating-select .star');

            estrellas.forEach((estrella, indice) => {
                if (indice < valor) {
                    estrella.style.color = '#FFD700';
                } else {
                    estrella.style.color = '#ccc';
                }
            });
        }

        function guardarValoracion() {
            const libroId = document.getElementById('libro-id').value;
            const valoracion = document.getElementById('rating-value').value;
            const comentario = document.getElementById('comentario').value;

            if (valoracion == 0) {
                alert('Por favor selecciona una valoración');
                return;
            }

            const formData = new FormData();
            formData.append('libro_id', libroId);
            formData.append('rating', valoracion);
            formData.append('comentario', comentario);

            fetch('/valorar-libro', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const ratingContainer = document.querySelector(`#rating-container-${libroId} .rating-stars`);
                    const ratingValue = document.getElementById(`rating-value-${libroId}`);

                    ratingValue.textContent = parseFloat(data.new_rating).toFixed(1);

                    let starHTML = '';
                    const rating = parseFloat(data.new_rating);
                    for (let i = 0; i < 5; i++) {
                        if (i < Math.floor(rating)) {
                            starHTML += '<span style="color: #FFD700;">★</span>';
                        } else if (i === Math.floor(rating) && rating % 1 !== 0) {
                            starHTML += '<span style="color: #FFD700;">★</span>';
                        } else {
                            starHTML += '<span style="color: #ccc;">★</span>';
                        }
                    }
                    ratingContainer.innerHTML = starHTML;

                    alert('Valoración y comentario guardados correctamente');
                } else {
                    alert('Error: ' + data.message);
                }
                cerrarModal();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al procesar la valoración');
                cerrarModal();
            });
        }

        function cerrarModal() {
            document.getElementById('modal-valorar').style.display = 'none';
        }
    </script>
    </body>
    </html>
    ''', libros=libros)


# Ruta para listar usuarios
@usuarios_bp.route('/admin/usuarios')
@login_required
def admin_usuarios():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder a la gestión de usuarios', 'error')
        return redirect(url_for('login.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuarios WHERE Rol = 0")  # Solo usuarios de tipo cliente (Rol = 0)
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        usuarios = []
        print(f"Error al obtener usuarios: {e}")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gestionar Usuarios</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', 'Administrador') + '''
    <div class="container">
        <h1>Gestionar Usuarios</h1>
        <a href="{{ url_for('usuarios.agregar_usuario') }}" class="btn">Agregar Usuario</a>
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nombre</th>
                    <th>Email</th>
                    <th>Teléfono</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for usuario in usuarios %}
                <tr>
                    <td>{{ usuario.UsuariolD }}</td>
                    <td>{{ usuario.Nombre }} {{ usuario.PrimerApellido }} {{ usuario.SegundoApellido }}</td>
                    <td>{{ usuario.Email }}</td>
                    <td>{{ usuario.Telefono }}</td>
                    <td>
                        <a href="{{ url_for('usuarios.editar_usuario', usuario_id=usuario.UsuariolD) }}" class="btn">Editar</a>
                        <a href="{{ url_for('usuarios.eliminar_usuario', usuario_id=usuario.UsuariolD) }}" class="btn">Eliminar</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    </body>
    </html>
    ''', usuarios=usuarios)

# Ruta para agregar un usuario
@usuarios_bp.route('/admin/usuarios/agregar', methods=['GET', 'POST'])
@login_required
def agregar_usuario():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para agregar usuarios', 'error')
        return redirect(url_for('login.login'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        nombre = request.form['nombre']
        primer_apellido = request.form['primer_apellido']
        segundo_apellido = request.form['segundo_apellido']
        telefono = request.form['telefono']
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Usuarios (Username, Email, Password, Nombre, PrimerApellido, SegundoApellido, Telefono, Rol) VALUES (%s, %s, %s, %s, %s, %s, %s, 0)",
                (username, email, hashed_password, nombre, primer_apellido, segundo_apellido, telefono)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Usuario agregado correctamente', 'success')
            return redirect(url_for('usuarios.admin_usuarios'))
        except Exception as e:
            print(f"Error al agregar usuario: {e}")
            flash('Error al agregar el usuario', 'error')

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agregar Usuario</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', 'Administrador') + '''
    <div class="container">
        <h1>Agregar Usuario</h1>
        <form method="POST">
            <div class="form-group">
                <label for="username">Nombre de usuario</label>
                <input type="text" class="form-control" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="email">Correo electrónico</label>
                <input type="email" class="form-control" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="password">Contraseña</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <div class="form-group">
                <label for="nombre">Nombre</label>
                <input type="text" class="form-control" id="nombre" name="nombre" required>
            </div>
            <div class="form-group">
                <label for="primer_apellido">Primer Apellido</label>
                <input type="text" class="form-control" id="primer_apellido" name="primer_apellido" required>
            </div>
            <div class="form-group">
                <label for="segundo_apellido">Segundo Apellido</label>
                <input type="text" class="form-control" id="segundo_apellido" name="segundo_apellido" required>
            </div>
            <div class="form-group">
                <label for="telefono">Teléfono</label>
                <input type="tel" class="form-control" id="telefono" name="telefono" required>
            </div>
            <button type="submit" class="btn">Agregar Usuario</button>
        </form>
    </div>
    </body>
    </html>
    ''')

# Ruta para editar un usuario
# Ruta para editar un usuario (incluyendo cambio de contraseña)
@usuarios_bp.route('/admin/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para editar usuarios', 'error')
        return redirect(url_for('login.login'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        nombre = request.form['nombre']
        primer_apellido = request.form['primer_apellido']
        segundo_apellido = request.form['segundo_apellido']
        telefono = request.form['telefono']
        nueva_password = request.form.get('nueva_password')  # Campo opcional para cambiar la contraseña
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Si se proporcionó una nueva contraseña, la actualizamos
            if nueva_password:
                hashed_password = hashlib.sha256(nueva_password.encode()).hexdigest()
                cursor.execute(
                    "UPDATE Usuarios SET Username = %s, Email = %s, Nombre = %s, PrimerApellido = %s, SegundoApellido = %s, Telefono = %s, Password = %s WHERE UsuariolD = %s",
                    (username, email, nombre, primer_apellido, segundo_apellido, telefono, hashed_password, usuario_id)
                )
            else:
                # Si no se proporcionó una nueva contraseña, actualizamos solo los demás campos
                cursor.execute(
                    "UPDATE Usuarios SET Username = %s, Email = %s, Nombre = %s, PrimerApellido = %s, SegundoApellido = %s, Telefono = %s WHERE UsuariolD = %s",
                    (username, email, nombre, primer_apellido, segundo_apellido, telefono, usuario_id)
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            flash('Usuario actualizado correctamente', 'success')
            return redirect(url_for('usuarios.admin_usuarios'))
        except Exception as e:
            print(f"Error al actualizar usuario: {e}")
            flash('Error al actualizar el usuario', 'error')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Usuarios WHERE UsuariolD = %s", (usuario_id,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al obtener usuario: {e}")
        return "Usuario no encontrado", 404

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Usuario</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('admin', 'Administrador') + '''
    <div class="container">
        <h1>Editar Usuario</h1>
        <form method="POST">
            <div class="form-group">
                <label for="username">Nombre de usuario</label>
                <input type="text" class="form-control" id="username" name="username" value="{{ usuario.Username }}" required>
            </div>
            <div class="form-group">
                <label for="email">Correo electrónico</label>
                <input type="email" class="form-control" id="email" name="email" value="{{ usuario.Email }}" required>
            </div>
            <div class="form-group">
                <label for="nombre">Nombre</label>
                <input type="text" class="form-control" id="nombre" name="nombre" value="{{ usuario.Nombre }}" required>
            </div>
            <div class="form-group">
                <label for="primer_apellido">Primer Apellido</label>
                <input type="text" class="form-control" id="primer_apellido" name="primer_apellido" value="{{ usuario.PrimerApellido }}" required>
            </div>
            <div class="form-group">
                <label for="segundo_apellido">Segundo Apellido</label>
                <input type="text" class="form-control" id="segundo_apellido" name="segundo_apellido" value="{{ usuario.SegundoApellido }}" required>
            </div>
            <div class="form-group">
                <label for="telefono">Teléfono</label>
                <input type="tel" class="form-control" id="telefono" name="telefono" value="{{ usuario.Telefono }}" required>
            </div>
            <div class="form-group">
                <label for="nueva_password">Nueva Contraseña</label>
                <input type="password" class="form-control" id="nueva_password" name="nueva_password">
                <small>Deja este campo en blanco si no deseas cambiar la contraseña.</small>
            </div>
            <button type="submit" class="btn">Actualizar Usuario</button>
        </form>
    </div>
    </body>
    </html>
    ''', usuario=usuario)

# Ruta para eliminar un usuario
@usuarios_bp.route('/admin/usuarios/eliminar/<int:usuario_id>')
@login_required
def eliminar_usuario(usuario_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para eliminar usuarios', 'error')
        return redirect(url_for('login.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Usuarios WHERE UsuariolD = %s", (usuario_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Usuario eliminado correctamente', 'success')
    except Exception as e:
        print(f"Error al eliminar usuario: {e}")
        flash('Error al eliminar el usuario', 'error')

    return redirect(url_for('usuarios.admin_usuarios'))    


@usuarios_bp.route('/mis_pedidos')
@login_required
def mis_pedidos():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para ver sus pedidos', 'error')
        return redirect(url_for('login.login'))
        
    user_id = session['user_id']
    nombre = session.get('nombre', 'Cliente')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener los pedidos del usuario
        cursor.execute("""
            SELECT p.PedidoID, p.FechaPedido, p.Total, p.Estado
            FROM Pedidos p
            WHERE p.UsuarioID = %s
            ORDER BY p.FechaPedido DESC
        """, (user_id,))
        pedidos = cursor.fetchall()
        
        # Para cada pedido, obtener sus detalles (CON LA MODIFICACIÓN PARA AGRUPAR)
        for pedido in pedidos:
            cursor.execute("""
                SELECT 
                    LibroID,
                    NombreLibro,
                    Descripcion,
                    SUM(dp.Cantidad) as Cantidad,
                    dp.PrecioUnitario,
                    SUM(dp.Cantidad * dp.PrecioUnitario) as Subtotal
                FROM DetallePedidos dp
                JOIN Libros l ON dp.LibroID = LibroID
                WHERE dp.PedidoID = %s
                GROUP BY LibroID, NombreLibro, Descripcion, dp.PrecioUnitario
            """, (pedido['PedidoID'],))
            pedido['detalles'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al obtener pedidos: {e}")
        pedidos = []
        flash('Error al cargar tus pedidos', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mis Pedidos</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
        <style>
            .pedido-card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #f9f9f9;
            }
            .pedido-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            .pedido-id {
                font-weight: bold;
                color: #0b887e;
            }
            .pedido-fecha {
                color: #666;
            }
            .pedido-total {
                font-weight: bold;
                text-align: right;
            }
            .pedido-estado {
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 0.9em;
                background-color: #4CAF50;
                color: white;
            }
            .detalle-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px dashed #eee;
            }
            .detalle-nombre {
                flex: 2;
            }
            .detalle-cantidad, .detalle-precio, .detalle-subtotal {
                flex: 1;
                text-align: center;
            }
            .detalle-header {
                font-weight: bold;
                border-bottom: 1px solid #ddd;
                margin-bottom: 5px;
                padding-bottom: 5px;
            }
            .no-pedidos {
                text-align: center;
                padding: 20px;
                color: #666;
            }
        </style>
    </head>
    <body>
    ''' + navbar('cliente', nombre) + '''
    <div class="container">
        <h1>Mis Pedidos</h1>
        
        {% if pedidos %}
            {% for pedido in pedidos %}
            <div class="pedido-card">
                <div class="pedido-header">
                    <div>
                        <span class="pedido-id">Pedido #{{ pedido.PedidoID }}</span>
                        <span class="pedido-fecha"> - {{ pedido.FechaPedido.strftime('%d/%m/%Y %H:%M') }}</span>
                    </div>
                    <div>
                        <span class="pedido-estado">{{ pedido.Estado }}</span>
                    </div>
                </div>
                
                <div class="detalle-header detalle-item">
                    <div class="detalle-nombre">Libro</div>
                    <div class="detalle-cantidad">Cantidad</div>
                    <div class="detalle-precio">Precio Unitario</div>
                    <div class="detalle-subtotal">Subtotal</div>
                </div>
                
                {% for detalle in pedido.detalles %}
                <div class="detalle-item">
                    <div class="detalle-nombre">{{ detalle.NombreLibro }}</div>
                    <div class="detalle-cantidad">{{ detalle.Cantidad }}</div>
                    <div class="detalle-precio">${{ detalle.PrecioUnitario }}</div>
                    <div class="detalle-subtotal">${{ (detalle.Cantidad * detalle.PrecioUnitario)|round(2) }}</div>
                </div>
                {% endfor %}
                
                <div class="pedido-total">
                    Total del pedido: ${{ pedido.Total }}
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="no-pedidos">
                <p>No tienes pedidos registrados.</p>
                <a href="{{ url_for('usuarios.cliente_dashboard') }}" class="btn">Ir a comprar</a>
            </div>
        {% endif %}
    </div>
    </body>
    </html>
    ''', pedidos=pedidos)

@usuarios_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder a la configuración', 'error')
        return redirect(url_for('login.login'))
        
    user_id = session['user_id']
    nombre = request.args.get('nombre', 'Cliente')
    
    conn = get_db_connection()
    if conn is None:
        flash('Error al conectar a la base de datos', 'error')
        return redirect(url_for('usuarios.cliente_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        email = request.form['email']
        nombre_usuario = request.form['nombre']
        primer_apellido = request.form['primer_apellido']
        segundo_apellido = request.form['segundo_apellido']
        telefono = request.form['telefono']
        
        nueva_password = request.form.get('nueva_password')
        confirmar_password = request.form.get('confirmar_password')
        password_actual = request.form.get('password_actual')
        
        try:
            if nueva_password:
                if nueva_password != confirmar_password:
                    flash('La nueva contraseña y la confirmación no coinciden', 'error')
                    raise ValueError("Las contraseñas no coinciden")
                
                cursor.execute("SELECT Password FROM Usuarios WHERE UsuariolD = %s", (user_id,))
                usuario_db = cursor.fetchone()
                hashed_password_actual = hashlib.sha256(password_actual.encode()).hexdigest()
                
                if usuario_db and usuario_db['Password'] != hashed_password_actual:
                    flash('La contraseña actual es incorrecta', 'error')
                    raise ValueError("Contraseña actual incorrecta")
                
                hashed_nueva_password = hashlib.sha256(nueva_password.encode()).hexdigest()
                cursor.execute(
                    "UPDATE Usuarios SET Email = %s, Nombre = %s, PrimerApellido = %s, SegundoApellido = %s, Telefono = %s, Password = %s WHERE UsuariolD = %s",
                    (email, nombre_usuario, primer_apellido, segundo_apellido, telefono, hashed_nueva_password, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE Usuarios SET Email = %s, Nombre = %s, PrimerApellido = %s, SegundoApellido = %s, Telefono = %s WHERE UsuariolD = %s",
                    (email, nombre_usuario, primer_apellido, segundo_apellido, telefono, user_id)
                )
            
            conn.commit()
            flash('Datos actualizados correctamente', 'success')
            
        except ValueError:
            pass
        except mysql.connector.Error as err:
            print(f"Error al actualizar datos: {err}")
            flash(f'Error al actualizar los datos: {err}', 'error')
    
    try:
        cursor.execute("SELECT * FROM Usuarios WHERE UsuariolD = %s", (user_id,))
        usuario = cursor.fetchone()
        if not usuario:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('login.login'))
    except mysql.connector.Error as err:
        print(f"Error al obtener datos de usuario: {err}")
        flash(f'Error al obtener los datos: {err}', 'error')
        usuario = None
    finally:
        cursor.close()
        conn.close()

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mi Cuenta</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
    ''' + navbar('cliente', usuario['Nombre'] if usuario else nombre) + '''
    <div class="container">
        <h1>Mi Cuenta</h1>
        <p>Aquí puedes editar tus datos personales.</p>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="form-container">
            <form method="POST">
                <div class="form-group">
                    <label for="username">Nombre de usuario</label>
                    <input type="text" class="form-control" id="username" value="{{ usuario.Username }}" disabled>
                    <small>El nombre de usuario no se puede cambiar</small>
                </div>
                
                <div class="form-group">
                    <label for="email">Correo electrónico</label>
                    <input type="email" class="form-control" id="email" name="email" value="{{ usuario.Email }}" required>
                </div>
                
                <div class="form-group">
                    <label for="nombre">Nombre</label>
                    <input type="text" class="form-control" id="nombre" name="nombre" value="{{ usuario.Nombre }}" required>
                </div>
                
                <div class="form-group">
                    <label for="primer_apellido">Primer Apellido</label>
                    <input type="text" class="form-control" id="primer_apellido" name="primer_apellido" value="{{ usuario.PrimerApellido }}" required>
                </div>
                
                <div class="form-group">
                    <label for="segundo_apellido">Segundo Apellido</label>
                    <input type="text" class="form-control" id="segundo_apellido" name="segundo_apellido" value="{{ usuario.SegundoApellido }}" required>
                </div>
                
                <div class="form-group">
                    <label for="telefono">Teléfono</label>
                    <input type="tel" class="form-control" id="telefono" name="telefono" value="{{ usuario.Telefono }}" required>
                </div>
                
                <div class="password-section">
                    <h3>Cambiar Contraseña</h3>
                    <p>Deja estos campos en blanco si no deseas cambiar tu contraseña</p>
                    
                    <div class="form-group">
                        <label for="password_actual">Contraseña Actual</label>
                        <input type="password" class="form-control" id="password_actual" name="password_actual">
                    </div>
                    
                    <div class="form-group">
                        <label for="nueva_password">Nueva Contraseña</label>
                        <input type="password" class="form-control" id="nueva_password" name="nueva_password">
                    </div>
                    
                    <div class="form-group">
                        <label for="confirmar_password">Confirmar Nueva Contraseña</label>
                        <input type="password" class="form-control" id="confirmar_password" name="confirmar_password">
                    </div>
                </div>
                
                <button type="submit" class="btn-save">Guardar Cambios</button>
            </form>
        </div>
    </div>
    
    <footer>
        <p>&copy; 2025 LibreriaKOA. Todos los derechos reservados.</p>
    </footer>
    </body>
    </html>
    ''', usuario=usuario)

@usuarios_bp.route('/admin/libros')
@login_required
def admin_libros():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder a la gestión de libros', 'error')
        return redirect(url_for('login.login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener el término de búsqueda (si existe)
        search_query = request.args.get('q', '')

        # Construir la consulta SQL según el término de búsqueda
        if search_query:
            cursor.execute("""
                SELECT *, (DATEDIFF(NOW(), FechaPublicacion) <= 14) AS EsNuevo
                FROM Libros
                WHERE NombreLibro LIKE %s
            """, (f"%{search_query}%",))
        else:
            cursor.execute("SELECT *, (DATEDIFF(NOW(), FechaPublicacion) <= 14) AS EsNuevo FROM Libros")

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
        <!-- Formulario de búsqueda -->
        <form method="GET" action="{{ url_for('usuarios.admin_libros') }}" style="margin-bottom: 20px;">
            <input type="text" name="q" placeholder="Buscar libro por nombre..." value="{{ request.args.get('q', '') }}">
            <button type="submit" class="btn">Buscar</button>
        </form>
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nombre</th>
                    <th>Estado</th>
                    <th>Precio</th>
                    <th>Stock</th>
                    <th>Rating</th>
                    <th>Fecha Publicación</th>
                    <th>Descripción</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for libro in libros %}
                <tr>
                    <td>{{ libro.LibrolD }}</td>
                    <td>{{ libro.NombreLibro }}</td>
                    <td>
                        {% if libro.EsNuevo %}
                            <span class="etiqueta-nuevo">NUEVO</span>
                        {% else %}
                            -
                        {% endif %}
                    </td>
                    <td>${{ libro.Precio }}</td>
                    <td>{{ libro.Stock }}</td>
                    <td>
                        <div class="rating-stars">
                            {% set rating = libro.Rating|default(0)|float %}
                            {% for i in range(5) %}
                                {% if i < rating|int %}
                                    <span style="color: #FFD700;">★</span>
                                {% elif i == rating|int and rating != rating|int %}
                                    <span style="color: #FFD700;">★</span>
                                {% else %}
                                    <span style="color: #ccc;">★</span>
                                {% endif %}
                            {% endfor %}
                            {{ rating }}
                        </div>
                    </td>
                    <td>{{ libro.FechaPublicacion.strftime('%d/%m/%Y') if libro.FechaPublicacion else 'No disponible' }}</td>
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

@usuarios_bp.route('/logout')
@login_required
def logout():
    session.pop('_flashes', None)
    session.clear()
    return redirect(url_for('login.login'))
    
@usuarios_bp.route('/valorar-libro', methods=['POST'])
@login_required
def valorar_libro():
    if 'user_id' not in session:
        return {'success': False, 'message': 'Debe iniciar sesión para valorar libros'}, 401
    
    usuario_id = session['user_id']
    libro_id = request.form.get('libro_id')
    rating = float(request.form.get('rating'))
    comentario = request.form.get('comentario', '')  # Asegúrate de obtener el comentario
    
    if rating < 1 or rating > 5:
        return {'success': False, 'message': 'La valoración debe estar entre 1 y 5'}, 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM ValoracionesLibros WHERE UsuariolD = %s AND librold = %s", 
                      (usuario_id, libro_id))
        valoracion_existente = cursor.fetchone()
        
        if valoracion_existente:
            cursor.close()
            conn.close()
            return {'success': False, 'message': 'Ya has valorado este libro anteriormente.'}, 400
        else:
            cursor.execute("INSERT INTO ValoracionesLibros (UsuariolD, librold, Rating, Comentario, FechaValoracion) VALUES (%s, %s, %s, %s, NOW())",
                          (usuario_id, libro_id, rating, comentario))  # Asegúrate de insertar el comentario
        
        cursor.execute("SELECT AVG(Rating) as rating_promedio FROM ValoracionesLibros WHERE librold = %s", (libro_id,))
        rating_promedio = cursor.fetchone()['rating_promedio']
        
        cursor.execute("UPDATE Libros SET Rating = %s WHERE LibrolD = %s", (rating_promedio, libro_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'success': True, 'message': 'Valoración guardada correctamente', 'new_rating': rating_promedio}
    
    except Exception as e:
        print(f"Error al guardar valoración: {e}")
        return {'success': False, 'message': f'Error al guardar valoración: {str(e)}'}, 500


@usuarios_bp.route('/admin/libros/agregar', methods=['GET', 'POST'])
@login_required
def agregar_libro():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para agregar libros', 'error')
        return redirect(url_for('login.login'))
    
    if request.method == 'POST':
        nombre_libro = request.form['nombre_libro']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        descripcion = request.form['descripcion']
        es_nuevo = 'es_nuevo' in request.form
        
        if es_nuevo:
            fecha_publicacion = datetime.now()
        else:
            fecha_publicacion = datetime.now() - timedelta(days=30)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Libros (NombreLibro, Precio, Stock, Descripcion, FechaPublicacion, EsNuevo, Rating) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (nombre_libro, precio, stock, descripcion, fecha_publicacion, es_nuevo, 0)
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
            <div class="form-group">
                <label>
                    <input type="checkbox" name="es_nuevo" checked> Marcar como Nuevo
                </label>
                <small>Los libros se consideran nuevos durante 14 días desde su fecha de publicación</small>
            </div>
            <button type="submit" class="btn">Agregar Libro</button>
        </form>
    </div>
    </body>
    </html>
    ''')


@usuarios_bp.route('/ver_comentarios_cliente/<int:libro_id>')
@login_required
def ver_comentarios_cliente(libro_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para ver los comentarios', 'error')
        return redirect(url_for('login.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener los comentarios y valoraciones del libro
        cursor.execute("""
            SELECT v.Rating, v.Comentario, v.FechaValoracion, u.Nombre AS NombreUsuario
            FROM ValoracionesLibros v
            JOIN Usuarios u ON v.UsuariolD = u.UsuariolD
            WHERE v.LibrolD = %s
            ORDER BY v.FechaValoracion DESC
        """, (libro_id,))
        comentarios = cursor.fetchall()
        
        # Obtener el nombre del libro
        cursor.execute("SELECT NombreLibro FROM Libros WHERE LibrolD = %s", (libro_id,))
        libro = cursor.fetchone()
        
        cursor.close()
        conn.close()
    except Exception as e:
        comentarios = []
        libro = {'NombreLibro': 'Libro no encontrado'}
        print(f"Error al obtener comentarios: {e}")

    # Renderizar la plantilla correctamente
    return render_template(
        'ver_comentarios.html',
        comentarios=comentarios,
        libro=libro,
        navbar=navbar  # Pasar la función navbar a la plantilla
    )


@usuarios_bp.route('/admin/libros/editar/<int:libro_id>', methods=['GET', 'POST'])
@login_required
def editar_libro(libro_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para editar libros', 'error')
        return redirect(url_for('login.login'))
    
    if request.method == 'POST':
        nombre_libro = request.form['nombre_libro']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        descripcion = request.form['descripcion']
        es_nuevo = 'es_nuevo' in request.form
        
        if es_nuevo:
            fecha_publicacion = datetime.now()
        else:
            fecha_publicacion = datetime.now() - timedelta(days=30)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Libros SET NombreLibro = %s, Precio = %s, Stock = %s, Descripcion = %s, FechaPublicacion = %s, EsNuevo = %s WHERE LibrolD = %s",
                (nombre_libro, precio, stock, descripcion, fecha_publicacion, es_nuevo, libro_id)
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
        
        if 'FechaPublicacion' in libro and libro['FechaPublicacion']:
            libro['es_nuevo'] = es_libro_nuevo(libro['FechaPublicacion'])
        else:
            libro['es_nuevo'] = False
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
            <div class="form-group">
                <label>
                    <input type="checkbox" name="es_nuevo" {% if libro.es_nuevo %}checked{% endif %}> Marcar como Nuevo
                </label>
                <small>Los libros se consideran nuevos durante 14 días desde su fecha de publicación</small>
            </div>
            <div class="form-group">
                <label>Rating actual: {{ libro.Rating|default(0) }}</label>
                <p><small>El rating es actualizado por los usuarios y no se puede modificar directamente</small></p>
            </div>
            <button type="submit" class="btn">Actualizar Libro</button>
        </form>
    </div>
    </body>
    </html>
    ''', libro=libro)

@usuarios_bp.route('/admin/libros/eliminar/<int:libro_id>')
@login_required
def eliminar_libro(libro_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para eliminar libros', 'error')
        return redirect(url_for('login.login'))
    
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

@usuarios_bp.route('/admin/pedidos')
@login_required
def admin_pedidos():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder a la gestión de pedidos', 'error')
        return redirect(url_for('login.login'))
    
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

@usuarios_bp.route('/admin/reportes')
@login_required
def admin_reportes():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder a los reportes', 'error')
        return redirect(url_for('login.login'))
    
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

@usuarios_bp.route('/comprar', methods=['POST'])
@login_required
def comprar():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para realizar una compra', 'error')
        return redirect(url_for('login.login'))
    
    if 'carrito' not in session or not session['carrito']:
        flash('No hay libros en el carrito', 'error')
        return redirect(url_for('usuarios.carrito'))
    
    try:
        user_id = session['user_id']
        carrito = session['carrito']
        total = sum(item['precio'] * item['cantidad'] for item in carrito)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar que el usuario existe
        cursor.execute("SELECT UsuariolD, Email, Nombre FROM Usuarios WHERE UsuariolD = %s", (user_id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('usuarios.carrito'))
        
        # Verificar stock disponible antes de procesar el pedido
        for item in carrito:
            cursor.execute("SELECT Stock FROM Libros WHERE LibrolD = %s", (item['libro_id'],))
            libro = cursor.fetchone()
            
            if not libro:
                flash(f'El libro "{item["nombre"]}" no existe', 'error')
                return redirect(url_for('usuarios.carrito'))
            
            if libro['Stock'] < item['cantidad']:
                flash(f'No hay suficiente stock para "{item["nombre"]}"', 'error')
                return redirect(url_for('usuarios.carrito'))
        
        # Insertar el pedido principal
        cursor.execute(
            "INSERT INTO Pedidos (UsuarioID, Total) VALUES (%s, %s)",
            (user_id, total)
        )
        pedido_id = cursor.lastrowid
        
        # Insertar los detalles del pedido y actualizar stock
        for item in carrito:
            # Insertar detalle
            cursor.execute(
                "INSERT INTO DetallePedidos (PedidoID, LibroID, Cantidad, PrecioUnitario) VALUES (%s, %s, %s, %s)",
                (pedido_id, item['libro_id'], item['cantidad'], item['precio'])
            )
            
            # Actualizar stock
            cursor.execute(
                "UPDATE Libros SET Stock = Stock - %s WHERE LibrolD = %s",
                (item['cantidad'], item['libro_id'])
            )
        
        conn.commit()
        
        # Crear ticket de compra
        ticket = f"Resumen de tu compra (Pedido #{pedido_id}):\n\n"
        for item in carrito:
            ticket += f"- {item['nombre']} (Cantidad: {item['cantidad']}, Precio unitario: ${item['precio']:.2f})\n"
        ticket += f"\nTotal: ${total:.2f}\n"
        
        # Enviar correos
        msg_usuario = Message(
            subject=f"Ticket de compra #{pedido_id} - LibreriaKOA",
            sender='20223tn010@utez.edu.mx',
            recipients=[usuario['Email']]
        )
        msg_usuario.body = ticket
        mail.send(msg_usuario)
        
        msg_admin = Message(
            subject=f"Nueva compra #{pedido_id} - {usuario['Nombre']}",
            sender='20223tn010@utez.edu.mx',
            recipients=['20223tn125@utez.edu.mx']
        )
        msg_admin.body = f"Se ha realizado una nueva compra:\n\n{ticket}"
        mail.send(msg_admin)
        
        # Limpiar carrito
        session['carrito'] = []
        
        flash(f'Compra realizada correctamente. Número de pedido: #{pedido_id}', 'success')
        return redirect(url_for('usuarios.mis_pedidos'))
    
    except Exception as e:
        print(f"Error al procesar la compra: {e}")
        flash('Error al procesar la compra', 'error')
        return redirect(url_for('usuarios.carrito'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
@usuarios_bp.route('/carrito')
@login_required
def carrito():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder al carrito', 'error')
        return redirect(url_for('login.login'))
    
    carrito = session.get('carrito', [])
    total = sum(item['precio'] * item['cantidad'] for item in carrito)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Carrito de Compras</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
        <style>
            table th {
                background-color: #0b887e;
                color: white;
            }
            .btn-accion {
                padding: 5px 10px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                margin: 0 2px;
            }
            .btn-eliminar {
                background-color: #ff4d4d;
                color: white;
            }
            .btn-eliminar:hover {
                background-color: #cc0000;
            }
            .btn-aumentar {
                background-color: #4CAF50;
                color: white;
            }
            .btn-aumentar:hover {
                background-color: #45a049;
            }
            .btn-reducir {
                background-color: #ffcc00;
                color: black;
            }
            .btn-reducir:hover {
                background-color: #e6b800;
            }
            .cantidad {
                display: inline-block;
                width: 30px;
                text-align: center;
            }
            .total {
                margin-top: 20px;
                font-size: 1.2em;
                font-weight: bold;
            }
            .btn-comprar {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 20px;
            }
            .btn-comprar:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
    ''' + navbar('cliente', session.get('nombre', 'Cliente')) + '''
    <div class="container">
        <h1>Carrito de Compras</h1>
        {% if carrito %}
        <table class="table">
            <thead>
                <tr>
                    <th>Libro</th>
                    <th>Precio Unitario</th>
                    <th>Cantidad</th>
                    <th>Subtotal</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for item in carrito %}
                <tr>
                    <td>{{ item.nombre }}</td>
                    <td>${{ item.precio }}</td>
                    <td>
                        <form action="{{ url_for('usuarios.reducir_cantidad', libro_id=item.libro_id) }}" method="POST" style="display: inline;">
                            <button type="submit" class="btn-accion btn-reducir">−</button>
                        </form>
                        <span class="cantidad">{{ item.cantidad }}</span>
                        <form action="{{ url_for('usuarios.aumentar_cantidad', libro_id=item.libro_id) }}" method="POST" style="display: inline;">
                            <button type="submit" class="btn-accion btn-aumentar">+</button>
                        </form>
                    </td>
                    <td>${{ item.precio * item.cantidad }}</td>
                    <td>
                        <form action="{{ url_for('usuarios.eliminar_del_carrito', libro_id=item.libro_id) }}" method="POST" style="display: inline;">
                            <button type="submit" class="btn-accion btn-eliminar">Eliminar</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <h3>Total: ${{ total }}</h3>
        <form action="{{ url_for('usuarios.comprar') }}" method="POST">
            <button type="submit" class="btn-comprar">COMPRAR</button>
        </form>
        {% else %}
        <p>No hay libros en el carrito.</p>
        {% endif %}
    </div>
    </body>
    </html>
    ''', carrito=carrito, total=total)


@usuarios_bp.route('/agregar_al_carrito/<int:libro_id>', methods=['POST'])
@login_required
def agregar_al_carrito(libro_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para agregar libros al carrito', 'error')
        return redirect(url_for('login.login'))
    
    # Obtener el carrito de la sesión (si no existe, se crea uno vacío)
    if 'carrito' not in session:
        session['carrito'] = []
    
    # Verificar si el libro ya está en el carrito
    carrito = session['carrito']
    libro_en_carrito = next((item for item in carrito if item['libro_id'] == libro_id), None)
    
    if libro_en_carrito:
        # Si el libro ya está en el carrito, aumentar la cantidad
        libro_en_carrito['cantidad'] += 1
    else:
        # Si el libro no está en el carrito, agregarlo
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Libros WHERE LibrolD = %s", (libro_id,))
            libro = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if libro:
                carrito.append({
                    'libro_id': libro['LibrolD'],
                    'nombre': libro['NombreLibro'],
                    'precio': float(libro['Precio']),  # Asegurarse de que el precio sea un float
                    'cantidad': 1  # Cantidad inicial
                })
        except Exception as e:
            print(f"Error al obtener el libro: {e}")
            flash('Error al agregar el libro al carrito', 'error')
            return redirect(url_for('usuarios.cliente_dashboard'))
    
    # Guardar el carrito actualizado en la sesión
    session['carrito'] = carrito
    flash('Libro agregado al carrito', 'success')
    return redirect(url_for('usuarios.cliente_dashboard'))

@usuarios_bp.route('/eliminar_del_carrito/<int:libro_id>', methods=['POST'])
@login_required
def eliminar_del_carrito(libro_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para eliminar libros del carrito', 'error')
        return redirect(url_for('login.login'))
    
    # Obtener el carrito de la sesión
    if 'carrito' not in session:
        flash('No hay libros en el carrito', 'error')
        return redirect(url_for('usuarios.carrito'))
    
    carrito = session['carrito']
    
    # Buscar el libro en el carrito y eliminarlo
    carrito = [item for item in carrito if item['libro_id'] != libro_id]
    
    # Guardar el carrito actualizado en la sesión
    session['carrito'] = carrito
    flash('Libro eliminado del carrito', 'success')
    return redirect(url_for('usuarios.carrito'))

@usuarios_bp.route('/aumentar_cantidad/<int:libro_id>', methods=['POST'])
@login_required
def aumentar_cantidad(libro_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para modificar el carrito', 'error')
        return redirect(url_for('login.login'))
    
    if 'carrito' not in session:
        flash('No hay libros en el carrito', 'error')
        return redirect(url_for('usuarios.carrito'))
    
    carrito = session['carrito']
    
    # Buscar el libro en el carrito
    for item in carrito:
        if item['libro_id'] == libro_id:
            # Verificar stock disponible (opcional)
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT Stock FROM Libros WHERE LibrolD = %s", (libro_id,))
                libro = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if libro and item['cantidad'] < libro['Stock']:
                    item['cantidad'] += 1
                    flash('Cantidad aumentada correctamente', 'success')
                else:
                    flash('No hay suficiente stock disponible', 'error')
            except Exception as e:
                print(f"Error al verificar stock: {e}")
                item['cantidad'] += 1  # Si falla la verificación, igual aumentamos
    
    session['carrito'] = carrito
    return redirect(url_for('usuarios.carrito'))

@usuarios_bp.route('/reducir_cantidad/<int:libro_id>', methods=['POST'])
@login_required
def reducir_cantidad(libro_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para modificar el carrito', 'error')
        return redirect(url_for('login.login'))
    
    if 'carrito' not in session:
        flash('No hay libros en el carrito', 'error')
        return redirect(url_for('usuarios.carrito'))
    
    carrito = session['carrito']
    
    # Buscar el libro en el carrito
    for item in carrito:
        if item['libro_id'] == libro_id:
            if item['cantidad'] > 1:
                item['cantidad'] -= 1
                flash('Cantidad reducida correctamente', 'success')
            else:
                flash('No puedes reducir más. Usa el botón "Eliminar" si deseas quitarlo.', 'warning')
    
    session['carrito'] = carrito
    return redirect(url_for('usuarios.carrito'))
