create database integradora;

use integradora;

CREATE TABLE Usuarios (
UsuariolD INT PRIMARY KEY,
Username VARCHAR(50) NOT NULL,
Email VARCHAR(50) NOT NULL,
Password VARCHAR(20) NOT NULL,
Nombre VARCHAR(50) NOT NULL,
PrimerApellido VARCHAR(50) NOT NULL,
SegundoApellido VARCHAR(50) NOT NULL,
Telefono VARCHAR(20) NOT NULL,
Rol BOOLEAN
);

CREATE TABLE Libros (
LibrolD INT PRIMARY KEY,
NombreLibro VARCHAR(50) NOT NULL,
Precio DECIMAL(10,2) NOT NULL,
Stock INT NOT NULL,
Descripcion VARCHAR(255)
);

CREATE TABLE Pedidos (
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

CREATE TABLE Direccion (
DireccionlD INT PRIMARY KEY,
UsuariolD INT NOT NULL,
Calle VARCHAR(50) NOT NULL,
Colonia VARCHAR(20) NOT NULL,
pais INT NOT NULL,
Ciudad VARCHAR(20) NOT NULL,
FOREIGN KEY (UsuariolD) REFERENCES Usuarios(UsuariolD)
);

INSERT INTO Usuarios (UsuariolD, Username, Email, Password, Nombre, PrimerApellido, SegundoApellido, Telefono, Rol)
VALUES (1, 'juan123', 'juan@mail.com', '12345', 'Juan', 'Perez', 'Lopez', '5551234567', FALSE);

INSERT INTO Usuarios (UsuariolD, Username, Email, Password, Nombre, PrimerApellido, SegundoApellido, Telefono, Rol)
VALUES 
(2, 'admin123', 'admin@mail.com', 'adminpass', 'Admin', 'Master', 'CEO', '5550000000', TRUE),
(3, 'juan123', 'juan@mail.com', '12345', 'Juan', 'Perez', 'Lopez', '5551234567', FALSE);


DELETE FROM Usuarios
WHERE UsuariolD = 3; 
SELECT * FROM Usuarios;