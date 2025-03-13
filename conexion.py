import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="basedatosintegradora.cjnmbvgjimyl.us-east-1.rds.amazonaws.com",
        user="admin",  # Cambia si tienes otro usuario
        password="cisco123",  # Agrega tu contraseña si tienes
        database="integradora1"
    )
