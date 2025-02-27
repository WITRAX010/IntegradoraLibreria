import mysql.connector
from mysql.connector import Error

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