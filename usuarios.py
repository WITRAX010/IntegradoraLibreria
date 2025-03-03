from flask import Blueprint, render_template, render_template_string, request, redirect, url_for, session, flash
from db import get_db_connection
import hashlib
import mysql.connector  
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
    <li><a href="{{ url_for('usuarios.direcciones') }}">Mis Direcciones</a></li>
    <li><a href="{{ url_for('usuarios.configuracion') }}">Mi Cuenta</a></li>
    '''
    
    dashboard_link = url_for('usuarios.admin_dashboard') if role == 'admin' else url_for('usuarios.cliente_dashboard')
    
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
def direcciones():
    # Verificar si el usuario ha iniciado sesión
    if 'user_id' not in session:
        flash('Debe iniciar sesión para ver sus direcciones', 'error')
        return redirect(url_for('login.login'))
        
    user_id = session['user_id']  # Obtener el ID del usuario de la sesión
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
            # No necesitamos convertir pais a entero ya que ahora es VARCHAR en la base de datos
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

    # Obtener las direcciones del usuario (usa un nuevo cursor después de cerrar el anterior)
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
def editar_direccion(direccion_id):
    # Verificar si el usuario ha iniciado sesión
    if 'user_id' not in session:
        flash('Debe iniciar sesión para editar direcciones', 'error')
        return redirect(url_for('login.login'))
        
    user_id = session['user_id']  # Obtener el ID del usuario de la sesión
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

    # Obtener la dirección a editar
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
def eliminar_direccion(direccion_id):
    # Verificar si el usuario ha iniciado sesión
    if 'user_id' not in session:
        flash('Debe iniciar sesión para eliminar direcciones', 'error')
        return redirect(url_for('login.login'))
        
    user_id = session['user_id']  # Obtener el ID del usuario de la sesión
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
    
# Dashboard de administrador
@usuarios_bp.route('/admin_dashboard')
def admin_dashboard():
    # Verificar si el usuario ha iniciado sesión y es administrador
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder al panel de administración', 'error')
        return redirect(url_for('login.login'))
    
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

# Primero, vamos a corregir la función JS para valorar libros en el dashboard del cliente
@usuarios_bp.route('/cliente_dashboard')
def cliente_dashboard():
    # Verificar si el usuario ha iniciado sesión
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder al panel de cliente', 'error')
        return redirect(url_for('login.login'))
        
    nombre = request.args.get('nombre', 'Cliente')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Modificar la consulta para obtener también la fecha de publicación y estado "nuevo"
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
        <style>
            .libro-card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                position: relative;
                transition: transform 0.3s;
            }
            .libro-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .etiqueta-nuevo {
                position: absolute;
                top: 10px;
                right: 10px;
                background-color: #FF5722;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            .star-rating {
                color: #FFD700;
                font-size: 24px;
                margin: 10px 0;
            }
            .libros-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
            }
            .precio {
                font-size: 1.2em;
                font-weight: bold;
                color: #333;
                margin: 10px 0;
            }
            .acciones {
                margin-top: 15px;
            }
            .rating-container {
                display: flex;
                align-items: center;
                margin: 10px 0;
            }
            .rating-stars {
                display: inline-block;
                margin-right: 10px;
            }
            .rating-value {
                font-weight: bold;
                margin-left: 5px;
            }
            .star-rating-select .star {
                cursor: pointer;
                font-size: 24px;
                color: #ccc;
            }
            .star-rating-select .star:hover {
                color: #FFD700;
            }
        </style>
    </head>
    <body>
    ''' + navbar('cliente', nombre) + '''
    <div class="container">
        <h1>Bienvenido, ''' + nombre + '''</h1>
        <p>Este es el panel de cliente. Aquí puedes ver los libros disponibles.</p>
        
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
                    <a href="#" class="btn" onclick="agregarAlCarrito({{ libro.LibrolD }})">Agregar al Carrito</a>
                    <a href="#" class="btn" onclick="mostrarValorarLibro({{ libro.LibrolD }})">Valorar</a>
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
                    <button class="btn" onclick="guardarValoracion()">Guardar</button>
                    <button class="btn" onclick="cerrarModal()">Cancelar</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Funciones JS para manejo del carrito y valoraciones
        function agregarAlCarrito(librold) {
            // Aquí implementarías la lógica para agregar al carrito
            alert('Libro agregado al carrito');
        }
        
        function mostrarValorarLibro(librold) {
            // Obtener el elemento del libro por su ID
            const libroCard = document.querySelector(`[data-libro-id="${librold}"]`);
            const libroNombre = libroCard.getAttribute('data-libro-nombre');
            
            // Configurar el modal
            document.getElementById('libro-nombre').textContent = libroNombre;
            document.getElementById('libro-id').value = librold;
            document.getElementById('modal-valorar').style.display = 'block';
            
            // Resetear las estrellas
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
    const librold = document.getElementById('libro-id').value;
    const valoracion = document.getElementById('rating-value').value;
    
    if (valoracion == 0) {
        alert('Por favor selecciona una valoración');
        return;
    }
    
    // Enviar los datos al servidor con fetch
    const formData = new FormData();
    formData.append('libro_id', librold);
    formData.append('rating', valoracion);
    
    fetch('/valorar-libro', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar la visualización de las estrellas
            const ratingContainer = document.querySelector(`#rating-container-${librold} .rating-stars`);
            const ratingValue = document.getElementById(`rating-value-${librold}`);
            
            // Actualizar el texto de rating
            ratingValue.textContent = parseFloat(data.new_rating).toFixed(1);
            
            // Actualizar las estrellas visualmente
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
            
            alert('Valoración guardada correctamente');
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

    
@usuarios_bp.route('/mis_pedidos')
def mis_pedidos():
    # Verificar si el usuario ha iniciado sesión
    if 'user_id' not in session:
        flash('Debe iniciar sesión para ver sus pedidos', 'error')
        return redirect(url_for('login.login'))
        
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

@usuarios_bp.route('/configuracion', methods=['GET', 'POST'])
def configuracion():
    # Verificar si el usuario ha iniciado sesión
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder a la configuración', 'error')
        return redirect(url_for('login.login'))
        
    user_id = session['user_id']
    nombre = request.args.get('nombre', 'Cliente')
    
    # Obtener los datos actuales del usuario
    conn = get_db_connection()
    if conn is None:
        flash('Error al conectar a la base de datos', 'error')
        return redirect(url_for('usuarios.cliente_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    # Si el formulario ha sido enviado, actualizar los datos
    if request.method == 'POST':
        # Obtener los datos del formulario
        email = request.form['email']
        nombre_usuario = request.form['nombre']
        primer_apellido = request.form['primer_apellido']
        segundo_apellido = request.form['segundo_apellido']
        telefono = request.form['telefono']
        
        # Verificar si se ha proporcionado una nueva contraseña
        nueva_password = request.form.get('nueva_password')
        confirmar_password = request.form.get('confirmar_password')
        password_actual = request.form.get('password_actual')
        
        try:
            # Primero, verificar la contraseña actual si se desea cambiar
            if nueva_password:
                # Verificar que la nueva contraseña y la confirmación coincidan
                if nueva_password != confirmar_password:
                    flash('La nueva contraseña y la confirmación no coinciden', 'error')
                    raise ValueError("Las contraseñas no coinciden")
                
                # Verificar la contraseña actual
                cursor.execute("SELECT Password FROM Usuarios WHERE UsuariolD = %s", (user_id,))
                usuario_db = cursor.fetchone()
                # Hashear la contraseña actual proporcionada para compararla con la almacenada
                hashed_password_actual = hashlib.sha256(password_actual.encode()).hexdigest()
                
                if usuario_db and usuario_db['Password'] != hashed_password_actual:
                    flash('La contraseña actual es incorrecta', 'error')
                    raise ValueError("Contraseña actual incorrecta")
                
                # Si la verificación es exitosa, incluir la nueva contraseña hasheada en la actualización
                hashed_nueva_password = hashlib.sha256(nueva_password.encode()).hexdigest()
                cursor.execute(
                    "UPDATE Usuarios SET Email = %s, Nombre = %s, PrimerApellido = %s, SegundoApellido = %s, Telefono = %s, Password = %s WHERE UsuariolD = %s",
                    (email, nombre_usuario, primer_apellido, segundo_apellido, telefono, hashed_nueva_password, user_id)
                )
            else:
                # Actualizar los datos sin cambiar la contraseña
                cursor.execute(
                    "UPDATE Usuarios SET Email = %s, Nombre = %s, PrimerApellido = %s, SegundoApellido = %s, Telefono = %s WHERE UsuariolD = %s",
                    (email, nombre_usuario, primer_apellido, segundo_apellido, telefono, user_id)
                )
            
            conn.commit()
            flash('Datos actualizados correctamente', 'success')
            
        except ValueError:
            # Los errores de validación ya han sido manejados con flash
            pass
        except mysql.connector.Error as err:
            print(f"Error al actualizar datos: {err}")
            flash(f'Error al actualizar los datos: {err}', 'error')
    
    # Obtener datos actuales del usuario para mostrar en el formulario
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
        <style>
            .form-container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            .form-control {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
            }
            .password-section {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }
            .btn-save {
                background-color: #4CAF50;
                padding: 12px 20px;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            .btn-save:hover {
                background-color: #45a049;
            }
            .alert {
                padding: 10px;
                margin-bottom: 15px;
                border-radius: 4px;
            }
            .alert-success {
                background-color: #d4edda;
                color: #155724;
            }
            .alert-error {
                background-color: #f8d7da;
                color: #721c24;
            }
        </style>
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

    
# Ruta para listar todos los libros (modificada para mostrar fecha de publicación y rating)
@usuarios_bp.route('/admin/libros')
def admin_libros():
    # Verificar si el usuario ha iniciado sesión y es administrador
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder a la gestión de libros', 'error')
        return redirect(url_for('login.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
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
        <style>
            .etiqueta-nuevo {
                background-color: #FF5722;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            .rating-stars {
                color: #FFD700;
            }
        </style>
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
def logout():
    # Eliminar los mensajes flash de la sesión
    session.pop('_flashes', None)
    
    # Cerrar la sesión del usuario
    session.clear()
    
    # Redirigir al usuario a la página de inicio de sesión
    return redirect(url_for('login.login'))
    
@usuarios_bp.route('/valorar-libro', methods=['POST'])
def valorar_libro():
    if 'user_id' not in session:
        return {'success': False, 'message': 'Debe iniciar sesión para valorar libros'}, 401
    
    usuario_id = session['user_id']
    libro_id = request.form.get('libro_id')
    rating = float(request.form.get('rating'))
    
    # Validar el rating
    if rating < 1 or rating > 5:
        return {'success': False, 'message': 'La valoración debe estar entre 1 y 5'}, 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el usuario ya ha valorado este libro
        cursor.execute("SELECT * FROM ValoracionesLibros WHERE UsuariolD = %s AND librold = %s", 
                      (usuario_id, libro_id))
        valoracion_existente = cursor.fetchone()
        
        if valoracion_existente:
            # Usuario ya valoró este libro, devolver error
            cursor.close()
            conn.close()
            return {'success': False, 'message': 'Ya has valorado este libro anteriormente.'}, 400
        else:
            # Insertar nueva valoración
            cursor.execute("INSERT INTO ValoracionesLibros (UsuariolD, librold, Rating, FechaValoracion) VALUES (%s, %s, %s, NOW())",
                          (usuario_id, libro_id, rating))
        
        # Actualizar el rating promedio en la tabla Libros
        cursor.execute("SELECT AVG(Rating) as rating_promedio FROM ValoracionesLibros WHERE librold = %s", (libro_id,))
        rating_promedio = cursor.fetchone()['rating_promedio']
        
        # Actualizar la tabla Libros con el nuevo rating promedio
        cursor.execute("UPDATE Libros SET Rating = %s WHERE LibrolD = %s", (rating_promedio, libro_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'success': True, 'message': 'Valoración guardada correctamente', 'new_rating': rating_promedio}
    
    except Exception as e:
        print(f"Error al guardar valoración: {e}")
        return {'success': False, 'message': f'Error al guardar valoración: {str(e)}'}, 500



# Ruta para agregar un libro (modificada para incluir fecha de publicación)
@usuarios_bp.route('/admin/libros/agregar', methods=['GET', 'POST'])
def agregar_libro():
    # Verificar si el usuario ha iniciado sesión y es administrador
    if 'user_id' not in session:
        flash('Debe iniciar sesión para agregar libros', 'error')
        return redirect(url_for('login.login'))
    
    if request.method == 'POST':
        nombre_libro = request.form['nombre_libro']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        descripcion = request.form['descripcion']
        es_nuevo = 'es_nuevo' in request.form  # Checkbox para marcar como nuevo
        
        # Calcular fecha de publicación (ahora para nuevo, o hace un mes para no nuevo)
        if es_nuevo:
            fecha_publicacion = datetime.now()
        else:
            fecha_publicacion = datetime.now() - timedelta(days=30)  # Un libro no nuevo tendrá más de 14 días

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Libros (NombreLibro, Precio, Stock, Descripcion, FechaPublicacion, EsNuevo, Rating) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (nombre_libro, precio, stock, descripcion, fecha_publicacion, es_nuevo, 0)  # Rating inicia en 0
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

# Ruta para editar un libro (modificada para incluir fecha de publicación)
@usuarios_bp.route('/admin/libros/editar/<int:libro_id>', methods=['GET', 'POST'])
def editar_libro(libro_id):
    # Verificar si el usuario ha iniciado sesión y es administrador
    if 'user_id' not in session:
        flash('Debe iniciar sesión para editar libros', 'error')
        return redirect(url_for('login.login'))
    
    if request.method == 'POST':
        nombre_libro = request.form['nombre_libro']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        descripcion = request.form['descripcion']
        es_nuevo = 'es_nuevo' in request.form
        
        # Si se marca como nuevo, actualizar la fecha de publicación a hoy
        if es_nuevo:
            fecha_publicacion = datetime.now()
        else:
            # Si ya no es nuevo, mantener la fecha anterior o poner una fecha vieja
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
        
        # Calcular si el libro es nuevo basado en la fecha de publicación
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



# Ruta para eliminar un libro
@usuarios_bp.route('/admin/libros/eliminar/<int:libro_id>')
def eliminar_libro(libro_id):
    # Verificar si el usuario ha iniciado sesión y es administrador
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

# Ruta para gestionar pedidos (placeholder)
@usuarios_bp.route('/admin/pedidos')
def admin_pedidos():
    # Verificar si el usuario ha iniciado sesión y es administrador
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

# Ruta para generar reportes (placeholder)
@usuarios_bp.route('/admin/reportes')
def admin_reportes():
    # Verificar si el usuario ha iniciado sesión y es administrador
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

@usuarios_bp.route('/carrito')
def carrito():
    # Verificar si el usuario ha iniciado sesión
    if 'user_id' not in session:
        flash('Debe iniciar sesión para acceder al carrito', 'error')
        return redirect(url_for('login.login'))
    
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
