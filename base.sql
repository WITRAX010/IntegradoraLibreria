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

alter table Usuarios
modify column Password varchar(64)
not null;

-- Insertar datos en la tabla Usuarios
INSERT INTO Usuarios (Username, Email, Password, Nombre, PrimerApellido, SegundoApellido, Telefono, Rol)
VALUES 
  ('juan123', 'juan@mail.com', '12345', 'Juan', 'Perez', 'Lopez', '55512345', FALSE),
  ('admin123', 'admin@mail.com', 'adminpass', 'Admin', 'Master', 'CEO', '55500000', TRUE);

-- Ver los datos insertados
SELECT * FROM usuarios;

ALTER TABLE Usuarios MODIFY Telefono INT;

SET SQL_SAFE_UPDATES = 0;

UPDATE Usuarios 
SET password = '713bfda78870bf9d1b261f565286f85e97ee614efe5f0faf7c34e7ca4f65baca'
WHERE username = 'admin123';

SET SQL_SAFE_UPDATES = 1;

ALTER TABLE Direccion MODIFY Pais VARCHAR(50) NOT NULL;

ALTER TABLE Libros 
ADD COLUMN FechaPublicacion DATETIME DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN EsNuevo BOOLEAN DEFAULT TRUE;


-- Crear tabla para almacenar las valoraciones de los libros
CREATE TABLE ValoracionesLibros (
    ValoracionlD INT AUTO_INCREMENT PRIMARY KEY,
    UsuariolD INT NOT NULL,
    LibrolD INT NOT NULL,
    Rating FLOAT NOT NULL,
    FechaValoracion DATETIME NOT NULL,
    FOREIGN KEY (UsuariolD) REFERENCES Usuarios(UsuariolD),
    FOREIGN KEY (LibrolD) REFERENCES Libros(LibrolD),
    CONSTRAINT check_rating CHECK (Rating >= 1 AND Rating <= 5),
    CONSTRAINT unique_valoracion UNIQUE (UsuariolD, LibrolD)
);
ALTER TABLE Libros ADD COLUMN Rating FLOAT DEFAULT 0;

ALTER TABLE Usuarios MODIFY COLUMN Telefono BIGINT NOT NULL;
