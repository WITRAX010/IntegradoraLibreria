from flask import Blueprint, render_template_string, request

# Blueprint para manejar rutas de usuario
usuarios_bp = Blueprint('usuarios', __name__)

# CSS para los dashboards
usuarios_dashboard_css = '''
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
        text-align: center;
    }
    h1 {
        margin-bottom: 20px;
        font-size: 24px;
    }
    .role-message {
        font-size: 18px;
        margin-top: 10px;
    }
    a {
        display: block;
        margin-top: 20px;
        color: #007bff;
        text-decoration: none;
        font-size: 16px;
    }
    a:hover {
        text-decoration: underline;
    }
</style>
'''

# Dashboard de administrador
@usuarios_bp.route('/admin_dashboard')
def admin_dashboard():
    nombre = request.args.get('nombre', 'Administrador')  # Obtiene el nombre del usuario
    mensaje = f"Bienvenido, Administrador {nombre}!"
    return render_template_string(f'''
        {usuarios_dashboard_css}
        <div class="container">
            <h1>{mensaje}</h1>
            <div class="role-message">Este es tu panel de administración.</div>
            <a href='/login'>Cerrar sesión</a>
        </div>
    ''')

# Dashboard de cliente
@usuarios_bp.route('/cliente_dashboard')
def cliente_dashboard():
    nombre = request.args.get('nombre', 'Cliente')  # Obtiene el nombre del usuario
    mensaje = f"Bienvenido, {nombre}!"
    return render_template_string(f'''
        {usuarios_dashboard_css}
        <div class="container">
            <h1>{mensaje}</h1>
            <div class="role-message">Este es tu panel de cliente.</div>
            <a href='/login'>Cerrar sesión</a>
        </div>
    ''')
