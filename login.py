from flask import Blueprint, render_template_string, request, redirect, url_for, session, flash
import mysql.connector
import hashlib
import re
from db import get_db_connection

# Blueprint para manejar rutas de login
login_bp = Blueprint('login', __name__, url_prefix='/login')

# HTML y CSS del formulario de login
login_template = '''
<!doctype html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Inicio de Sesión</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 350px;
            box-sizing: border-box;
        }
        h2 {
            text-align: center;
            color: #333;
        }
        label {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
            display: block;
        }
        input[type="text"], input[type="password"],
        input[type="email"], input[type="tel"], input[type="number"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .message {
            color: red;
            font-size: 14px;
            text-align: center;
        }
        .success-message {
            color: green;
            font-size: 14px;
            text-align: center;
        }
        .role-message {
            color: green;
            font-size: 14px;
            text-align: center;
        }
        a {
            text-decoration: none;
            color: #4CAF50;
            display: block;
            text-align: center;
            margin-top: 10px;
        }
        .password-container {
            position: relative;
            width: 100%;
        }
        .toggle-password {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Iniciar Sesión</h2>
        {% if error %}
        <div class="message">{{ error }}</div>
        {% endif %}
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="{{ category }}-message">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="post">
            <label for="username">Username:</label>
            <input type="text" name="username" id="username" required><br><br>
            
            <label for="password">Password:</label>
            <div class="password-container">
                <input type="password" name="password" id="password" required>
                <span class="toggle-password" onclick="togglePasswordVisibility('password')">👁️</span>
            </div><br><br>
            
            <button type="submit">Ingresar</button>
        </form>
        <a href="/login/register">¿No tienes cuenta? Regístrate aquí.</a>
        {% if role %}
        <div class="role-message">Bienvenido, {{ role }} {{ nombre }}</div>
        {% endif %}
    </div>
    
    <script>
        function togglePasswordVisibility(fieldId) {
            const passwordField = document.getElementById(fieldId);
            if (passwordField.type === "password") {
                passwordField.type = "text";
            } else {
                passwordField.type = "password";
            }
        }
    </script>
</body>
</html>
'''

# HTML y CSS del formulario de registro
register_template = '''
<!doctype html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Registro de Usuario</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 350px;
            box-sizing: border-box;
        }
        h2 {
            text-align: center;
            color: #333;
        }
        label {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
            display: block;
        }
        input[type="text"], input[type="password"],
        input[type="email"], input[type="number"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .message {
            color: red;
            font-size: 14px;
            text-align: center;
            margin-bottom: 10px;
        }
        a {
            text-decoration: none;
            color: #4CAF50;
            display: block;
            text-align: center;
            margin-top: 10px;
        }
        .password-container {
            position: relative;
            width: 100%;
        }
        .toggle-password {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Registrarse</h2>
        {% if error %}
        <div class="message">{{ error }}</div>
        {% endif %}
        <form method="post" onsubmit="return validateForm()">
            <label for="username">Username:</label>
            <input type="text" name="username" id="username" required><br>
            
            <label for="email">Email:</label>
            <input type="email" name="email" id="email" required><br>
            
            <label for="password">Password:</label>
            <div class="password-container">
                <input type="password" name="password" id="password" required>
                <span class="toggle-password" onclick="togglePasswordVisibility('password')">👁️</span>
            </div><br>
            
            <label for="confirm_password">Confirmar Password:</label>
            <div class="password-container">
                <input type="password" name="confirm_password" id="confirm_password" required>
                <span class="toggle-password" onclick="togglePasswordVisibility('confirm_password')">👁️</span>
            </div><br>
            
            <label for="nombre">Nombre:</label>
            <input type="text" name="nombre" id="nombre" required><br>
            
            <label for="primer_apellido">Primer Apellido:</label>
            <input type="text" name="primer_apellido" id="primer_apellido" required><br>
            
            <label for="segundo_apellido">Segundo Apellido:</label>
            <input type="text" name="segundo_apellido" id="segundo_apellido" required><br>
            
            <label for="telefono">Teléfono (8 dígitos):</label>
            <input type="number" name="telefono" id="telefono" required min="10000000" max="99999999"><br>
            
            <button type="submit">Registrar</button>
        </form>
        <a href="/login">¿Ya tienes cuenta? Inicia sesión aquí.</a>
    </div>
    
    <script>
        function togglePasswordVisibility(fieldId) {
            const passwordField = document.getElementById(fieldId);
            if (passwordField.type === "password") {
                passwordField.type = "text";
            } else {
                passwordField.type = "password";
            }
        }
        
        function validateForm() {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            const telefono = document.getElementById('telefono').value;
            
            // Validar que las contraseñas coincidan
            if (password !== confirmPassword) {
                alert('Las contraseñas no coinciden');
                return false;
            }
            
            // Validar que el teléfono tenga 8 dígitos
            if (telefono.length !== 8) {
                alert('El teléfono debe tener exactamente 8 dígitos');
                return false;
            }
            
            return true;
        }
    </script>
</body>
</html>
'''

# Ruta para el login
@login_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT UsuariolD, Username, Nombre, PrimerApellido,
            SegundoApellido, Rol, Password
            FROM Usuarios
            WHERE Username = %s
            """
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            # Verificar si el hash de la contraseña coincide
            if user and hashlib.sha256(password.encode()).hexdigest() == user['Password']:
                # Guardar información del usuario en la sesión
                session['user_id'] = user['UsuariolD']
                session['username'] = user['Username']
                session['role'] = user['Rol']
                session['nombre'] = f"{user['Nombre']} {user['PrimerApellido']} {user['SegundoApellido']}"
                
                # Redireccionar según el rol
                if user['Rol']:  # Administrador
                    return redirect(url_for('usuarios.admin_dashboard', nombre=session['nombre']))
                else:  # Cliente
                    return redirect(url_for('usuarios.cliente_dashboard', nombre=session['nombre']))
            else:
                return render_template_string(login_template, error="Usuario o contraseña incorrectos.")
        except mysql.connector.Error as err:
            flash(f"Error de base de datos: {err}", "error")
            return render_template_string(login_template, error=f"Error de base de datos: {err}")
    return render_template_string(login_template)

# Ruta para registrar un nuevo usuario
@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        nombre = request.form['nombre']
        primer_apellido = request.form['primer_apellido']
        segundo_apellido = request.form['segundo_apellido']
        telefono = request.form['telefono']
        
        # Validaciones en el servidor
        error = None
        
        # Verificar que las contraseñas coinciden
        if password != confirm_password:
            error = "Las contraseñas no coinciden"
        
        # Verificar que el teléfono tiene 8 dígitos
        if not telefono.isdigit() or len(telefono) != 8:
            error = "El teléfono debe tener exactamente 8 dígitos"
            
        if error:
            return render_template_string(register_template, error=error)
            
        # Hashear la contraseña antes de insertarla
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
            INSERT INTO Usuarios (Username, Email, Password, Nombre, PrimerApellido, SegundoApellido, Telefono, Rol)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
            """
            cursor.execute(query, (username, email, hashed_password, nombre, primer_apellido, segundo_apellido, int(telefono), ))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Usuario registrado exitosamente. Ahora puede iniciar sesión.", "success")
            return redirect('/login')
        except mysql.connector.Error as err:
            flash(f"Error de base de datos: {err}", "error")
            return render_template_string(register_template, error=f"Error de base de datos: {err}")
    return render_template_string(register_template)

# Ruta para cerrar sesión
@login_bp.route('/logout')
def logout():
    # Eliminar los datos de la sesión
    session.clear()
    flash("Sesión cerrada correctamente", "success")
    return redirect('/login')
