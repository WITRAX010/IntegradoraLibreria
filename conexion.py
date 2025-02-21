import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Cambia si tienes otro usuario
        password="root",  # Agrega tu contraseña si tienes
        database="integradora"
    )