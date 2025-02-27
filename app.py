from flask import Flask, redirect, url_for
from db import get_db_connection

app = Flask(__name__)

# Configuración de la aplicación
app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave segura

# Importa los blueprints después de crear la aplicación
from login import login_bp
from usuarios import usuarios_bp

# Registra los blueprints
app.register_blueprint(login_bp)
app.register_blueprint(usuarios_bp)

# Ruta para la URL raíz
@app.route('/')
def index():
    return redirect(url_for('login.login'))

if __name__ == '__main__':
    app.run(debug=True)
