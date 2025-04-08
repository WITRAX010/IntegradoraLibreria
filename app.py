from flask import Flask, redirect, url_for
from db import get_db_connection
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from extensions import mail
from login import login_bp
from usuarios import usuarios_bp
from login import login_bp

app = Flask(__name__)

# Configuración de la aplicación
app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave segura

# Registra los blueprints
app.register_blueprint(login_bp)
app.register_blueprint(usuarios_bp)

# Configuración de Flask-Mail 
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Servidor SMTP de Gmail
app.config['MAIL_PORT'] = 587  
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '20223tn010@utez.edu.mx'  # Tu correo Gmail
app.config['MAIL_PASSWORD'] = 'bpck hwjs asnc aqbz'  # Tu contraseña de Gmail

mail = Mail(app)

@app.route('/send_email', methods=['POST'])
def send_email():
    email = request.form['email']
    subject = request.form['subject']
    message = request.form['message']
    
    msg = Message(subject, sender='20223tn010@utez.edu.mx', recipients=[email])
    msg.body = message
    mail.send(msg)
    
    return 'Correo enviado!'

@app.route('/')
def index():
    return redirect(url_for('login.login'))


if __name__ == '__main__':
    app.run(debug=True)

def create_app():
    app = Flask(__name__)
    app.secret_key = 'tu_clave_secreta_segura'
    
    # Registrar Blueprints
    app.register_blueprint(login_bp)
    app.register_blueprint(usuarios_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True)
