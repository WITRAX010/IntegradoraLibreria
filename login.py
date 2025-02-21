from flask import Blueprint, render_template_string, request, redirect, url_for
import mysql.connector
from app import get_db_connection  # Importa la conexión desde `app.py`

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
            background-color: #f4f4f9;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: #fff;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            width: 300px;
        }
        h2 {
            text-align: center;
            margin-bottom: 20px;
        }
        label {
            font-size: 14px;
            margin-bottom: 5px;
            display: block;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        button {
            width: 100%;
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .message {
            color: #d9534f;
            text-align: center;
            margin-top: 20px;
        }
        .role-message {
            color: #28a745;
            font-size: 16px;
            text-align: center;
            margin-top: 20px;
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

        {% if role %}
            <div class="role-message">Bienvenido, {{ role }} {{ nombre }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

@login_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT UsuariolD, Username, Nombre, PrimerApellido, SegundoApellido, Rol, Password 
                FROM Usuarios 
                WHERE Username = %s
            """
            cursor.execute(query, (username,))
            user = cursor.fetchone()  # Obtener un solo resultado
            cursor.close()  # Cerrar cursor antes de cerrar conexión
            conn.close()

            if user and user['Password'] == password:  # Compara la contraseña directamente
                nombre_completo = f"{user['Nombre']} {user['PrimerApellido']} {user['SegundoApellido']}"
                role = "Administrador" if user['Rol'] else "Cliente"
                # Redirigir al dashboard correspondiente
                if user['Rol']:
                    return redirect(url_for('usuarios.admin_dashboard', nombre=nombre_completo))  # Admin
                else:
                    return redirect(url_for('usuarios.cliente_dashboard', nombre=nombre_completo))  # Cliente
            else:
                return render_template_string(login_template, error="Usuario o contraseña incorrectos.")
        
        except mysql.connector.Error as err:
            return f"Error de base de datos: {err}"

    return render_template_string(login_template)
