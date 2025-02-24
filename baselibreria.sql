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

-- Modificar la columna Password para permitir hasta 64 caracteres
ALTER TABLE Usuarios MODIFY Password VARCHAR(64);

------------------------------------------------------------
-- Stored Procedures
------------------------------------------------------------

-- Procedimiento para agregar un nuevo usuario
DELIMITER //
CREATE PROCEDURE sp_AgregarUsuario(
  IN p_Username VARCHAR(50),
  IN p_Email VARCHAR(50),
  IN p_Password VARCHAR(64),
  IN p_Nombre VARCHAR(50),
  IN p_PrimerApellido VARCHAR(50),
  IN p_SegundoApellido VARCHAR(50),
  IN p_Telefono VARCHAR(20),
  IN p_Rol BOOLEAN
)
BEGIN
  INSERT INTO Usuarios(Username, Email, Password, Nombre, PrimerApellido, SegundoApellido, Telefono, Rol)
  VALUES(p_Username, p_Email, p_Password, p_Nombre, p_PrimerApellido, p_SegundoApellido, p_Telefono, p_Rol);
END //
DELIMITER ;

-- Procedimiento para agregar un nuevo libro
DELIMITER //
CREATE PROCEDURE sp_AgregarLibro(
  IN p_NombreLibro VARCHAR(50),
  IN p_Precio DECIMAL(10,2),
  IN p_Stock INT,
  IN p_Descripcion VARCHAR(255)
)
BEGIN
  INSERT INTO Libros(NombreLibro, Precio, Stock, Descripcion)
  VALUES(p_NombreLibro, p_Precio, p_Stock, p_Descripcion);
END //
DELIMITER ;

-- Procedimiento para agregar un nuevo pedido
DELIMITER //
CREATE PROCEDURE sp_AgregarPedido(
  IN p_UsuariolD INT,
  IN p_Total DECIMAL(10,2),
  IN p_EstadoPedido VARCHAR(20),
  IN p_LibrolD INT,
  IN p_Cantidad INT,
  IN p_PrecioVenta DECIMAL(10,2)
)
BEGIN
  INSERT INTO Pedidos(UsuariolD, Total, EstadoPedido, LibrolD, Cantidad, PrecioVenta)
  VALUES(p_UsuariolD, p_Total, p_EstadoPedido, p_LibrolD, p_Cantidad, p_PrecioVenta);
END //
DELIMITER ;

-- Procedimiento para agregar una nueva dirección
DELIMITER //
CREATE PROCEDURE sp_AgregarDireccion(
  IN p_UsuariolD INT,
  IN p_Calle VARCHAR(50),
  IN p_Colonia VARCHAR(20),
  IN p_Pais INT,
  IN p_Ciudad VARCHAR(20)
)
BEGIN
  INSERT INTO Direccion(UsuariolD, Calle, Colonia, Pais, Ciudad)
  VALUES(p_UsuariolD, p_Calle, p_Colonia, p_Pais, p_Ciudad);
END //
DELIMITER ;
