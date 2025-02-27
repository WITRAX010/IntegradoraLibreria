from flask import Blueprint, render_template_string, request, redirect, url_for
import mysql.connector
import hashlib
from db import get_db_connection  # Cambia esta línea

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
        input[type="email"], input[type="tel"] {
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
    </style>
</head>
<body>
    <div class="container">
        <h2>Iniciar Sesión</h2>
        {% if error %}
        <div class="message">{{ error }}</div>
        {% endif %}
        <form method="post">
            <label for="username">Username:</label>
            <input type="text" name="username" id="username" required><br><br>
            <label for="password">Password:</label>
            <input type="password" name="password" id="password" required><br><br>
            <button type="submit">Ingresar</button>
        </form>
        <a href="/login/register">¿No tienes cuenta? Regístrate aquí.</a>
        {% if role %}
        <div class="role-message">Bienvenido, {{ role }} {{ nombre }}</div>
        {% endif %}
    </div>
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
        input[type="email"], input[type="tel"] {
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
        a {
            text-decoration: none;
            color: #4CAF50;
            display: block;
            text-align: center;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Registrarse</h2>
        <form method="post">
            <label for="username">Username:</label>
            <input type="text" name="username" required><br>
            <label for="email">Email:</label>
            <input type="email" name="email" required><br>
            <label for="password">Password:</label>
            <input type="password" name="password" required><br>
            <label for="nombre">Nombre:</label>
            <input type="text" name="nombre" required><br>
            <label for="primer_apellido">Primer Apellido:</label>
            <input type="text" name="primer_apellido" required><br>
            <label for="segundo_apellido">Segundo Apellido:</label>
            <input type="text" name="segundo_apellido" required><br>
            <label for="telefono">Teléfono:</label>
            <input type="tel" name="telefono" required><br>
            <button type="submit">Registrar</button>
        </form>
        <a href="/login">¿Ya tienes cuenta? Inicia sesión aquí.</a>
    </div>
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
                nombre_completo = f"{user['Nombre']} {user['PrimerApellido']} {user['SegundoApellido']}"
                role = "Administrador" if user['Rol'] else "Cliente"
                return redirect(url_for('usuarios.admin_dashboard' if user['Rol'] else 'usuarios.cliente_dashboard', nombre=nombre_completo))
            else:
                return render_template_string(login_template, error="Usuario o contraseña incorrectos.")
        except mysql.connector.Error as err:
            return f"Error de base de datos: {err}"
    return render_template_string(login_template)

# Ruta para registrar un nuevo usuario
@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        nombre = request.form['nombre']
        primer_apellido = request.form['primer_apellido']
        segundo_apellido = request.form['segundo_apellido']
        telefono = request.form['telefono']
        # Hashear la contraseña antes de insertarla
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
            INSERT INTO Usuarios (Username, Email, Password, Nombre, PrimerApellido, SegundoApellido, Telefono, Rol)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
            """
            cursor.execute(query, (username, email, hashed_password, nombre, primer_apellido, segundo_apellido, telefono))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/login')
        except mysql.connector.Error as err:
            return f"Error de base de datos: {err}"
    return render_template_string(register_template)
