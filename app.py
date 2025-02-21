from flask import Flask, redirect, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'  # Para sesiones

# Configuración de conexión a la base de datos
db_config = {
    'user': 'root',        
    'password': 'root',    
    'host': 'localhost',
    'database': 'integradora1'
}

# Función para obtener conexión a la BD con manejo de excepciones
def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Importar y registrar el blueprint de login
try:
    from login import login_bp  
    app.register_blueprint(login_bp)
except ImportError as e:
    print(f"Error al importar el blueprint de login: {e}")

# Importar y registrar el blueprint de usuarios (para los dashboards)
try:
    from usuarios import usuarios_bp  
    app.register_blueprint(usuarios_bp)
except ImportError as e:
    print(f"Error al importar el blueprint de usuarios: {e}")

# Ruta raíz que redirige a la página de login
@app.route('/')
def index():
    return redirect('/login')

# Iniciar la aplicación con manejo de errores
if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
