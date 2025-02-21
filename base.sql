CREATE DATABASE IF NOT EXISTS integradora1;

USE integradora1;

-- Creación de la tabla Usuarios
CREATE TABLE IF NOT EXISTS Usuarios (
  UsuariolD INT AUTO_INCREMENT PRIMARY KEY,
  Username VARCHAR(50) NOT NULL,
  Email VARCHAR(50) NOT NULL,
  Password VARCHAR(20) NOT NULL,
  Nombre VARCHAR(50) NOT NULL,
  PrimerApellido VARCHAR(50) NOT NULL,
  SegundoApellido VARCHAR(50) NOT NULL,
  Telefono VARCHAR(20) NOT NULL,
  Rol BOOLEAN
);

-- Creación de la tabla Libros
CREATE TABLE IF NOT EXISTS Libros (
  LibrolD INT AUTO_INCREMENT PRIMARY KEY,
  NombreLibro VARCHAR(50) NOT NULL,
  Precio DECIMAL(10,2) NOT NULL,
  Stock INT NOT NULL,
  Descripcion VARCHAR(255)
);

-- Creación de la tabla Pedidos
CREATE TABLE IF NOT EXISTS Pedidos (
  PedidolD INT PRIMARY KEY AUTO_INCREMENT,
  UsuariolD INT NOT NULL,
  Total DECIMAL(10,2) NOT NULL,
  EstadoPedido VARCHAR(20) NOT NULL,
  LibrolD INT NOT NULL,
  Cantidad INT NOT NULL,
  PrecioVenta DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (UsuariolD) REFERENCES Usuarios(UsuariolD),
  FOREIGN KEY (LibrolD) REFERENCES Libros(LibrolD)
);

-- Creación de la tabla Direccion
CREATE TABLE IF NOT EXISTS Direccion (
  DireccionlD INT PRIMARY KEY AUTO_INCREMENT,
  UsuariolD INT NOT NULL,
  Calle VARCHAR(50) NOT NULL,
  Colonia VARCHAR(20) NOT NULL,
  Pais INT NOT NULL,
  Ciudad VARCHAR(20) NOT NULL,
  FOREIGN KEY (UsuariolD) REFERENCES Usuarios(UsuariolD)
);

-- Insertar datos en la tabla Usuarios
INSERT INTO Usuarios (Username, Email, Password, Nombre, PrimerApellido, SegundoApellido, Telefono, Rol)
VALUES 
  ('juan123', 'juan@mail.com', '12345', 'Juan', 'Perez', 'Lopez', '5551234567', FALSE),
  ('admin123', 'admin@mail.com', 'adminpass', 'Admin', 'Master', 'CEO', '5550000000', TRUE);

-- Ver los datos insertados
SELECT * FROM Usuarios;

ALTER TABLE Usuarios MODIFY Password VARCHAR(64);
