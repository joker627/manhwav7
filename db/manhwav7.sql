-- =========================
-- USUARIOS
-- =========================
CREATE TABLE usuarios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(60) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    pass_hash VARCHAR(255) NOT NULL,
    avatar VARCHAR(255) DEFAULT NULL,
    banner VARCHAR(255) DEFAULT NULL,
    bio TEXT,
    rol ENUM('user','admin','superadmin') DEFAULT 'user',
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Superadmin único
DELIMITER //
CREATE TRIGGER unico_superadmin
BEFORE UPDATE ON usuarios
FOR EACH ROW
BEGIN
    IF NEW.rol = 'superadmin' AND (OLD.rol IS NULL OR OLD.rol <> 'superadmin') THEN
        IF (SELECT COUNT(*) FROM usuarios WHERE rol = 'superadmin' AND id <> NEW.id) >= 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Ya existe un superadmin';
        END IF;
    END IF;
END;//
CREATE TRIGGER unico_superadmin_insert
BEFORE INSERT ON usuarios
FOR EACH ROW
BEGIN
    IF NEW.rol='superadmin' THEN
        IF (SELECT COUNT(*) FROM usuarios WHERE rol='superadmin') >= 1 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Ya existe un superadmin';
        END IF;
    END IF;
END;//
DELIMITER ;

-- =========================
-- EVENT: limpiar vistas antiguas (mensual)
-- Nota: `SET GLOBAL event_scheduler = ON` requiere privilegios de administrador.
-- Si no lo puedes ejecutar desde aquí, activa el scheduler en la configuración del servidor.
-- =========================
SET GLOBAL event_scheduler = ON;

CREATE EVENT IF NOT EXISTS limpiar_vistas_antiguas
ON SCHEDULE EVERY 1 MONTH
STARTS CURRENT_TIMESTAMP
DO
    DELETE FROM vistas_capitulo WHERE fecha < DATE_SUB(NOW(), INTERVAL 6 MONTH);


-- =========================
-- SCANS
-- =========================
CREATE TABLE scans (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) UNIQUE NOT NULL,
    descripcion TEXT,
    logo VARCHAR(255),
    banner VARCHAR(255),
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seguir scan
CREATE TABLE seguir_scan (
    id_usuario BIGINT,
    id_scan BIGINT,
    PRIMARY KEY(id_usuario,id_scan),
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY(id_scan) REFERENCES scans(id) ON DELETE CASCADE
);


-- =========================
-- MANGAS
-- =========================
CREATE TABLE mangas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    portada VARCHAR(255),
    id_scan BIGINT,
    total_likes INT DEFAULT 0,
    total_vistas INT DEFAULT 0,
    total_seguidores INT DEFAULT 0,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FULLTEXT(titulo,descripcion),
    FOREIGN KEY(id_scan) REFERENCES scans(id) ON DELETE SET NULL
);

CREATE INDEX idx_rank ON mangas(total_likes,total_vistas,total_seguidores);

-- =========================
-- FAVORITOS (usuarios que marcaron un manga como favorito)
-- =========================
CREATE TABLE favoritos (
    id_usuario BIGINT NOT NULL,
    id_manga BIGINT NOT NULL,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id_usuario,id_manga),
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY(id_manga) REFERENCES mangas(id) ON DELETE CASCADE
);


-- =========================
-- GÉNEROS (categorías) + relación many-to-many
-- =========================
CREATE TABLE generos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE manga_generos (
    id_manga BIGINT NOT NULL,
    id_genero INT NOT NULL,
    PRIMARY KEY (id_manga, id_genero),
    FOREIGN KEY (id_manga) REFERENCES mangas(id) ON DELETE CASCADE,
    FOREIGN KEY (id_genero) REFERENCES generos(id) ON DELETE CASCADE
);


-- =========================
-- CAPITULOS
-- =========================
CREATE TABLE capitulos (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_manga BIGINT NOT NULL,
    numero DECIMAL(6,2) NOT NULL,
    titulo VARCHAR(200),
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_manga) REFERENCES mangas(id) ON DELETE CASCADE
);

CREATE INDEX idx_caps ON capitulos(id_manga,numero);

-- =========================
-- HISTORIAL LECTURA
-- =========================
CREATE TABLE historial_lectura (
    id_usuario BIGINT,
    id_capitulo BIGINT,
    pagina INT DEFAULT 1,
    actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(id_usuario,id_capitulo),
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY(id_capitulo) REFERENCES capitulos(id) ON DELETE CASCADE
);

-- =========================
-- LIKES
-- =========================
CREATE TABLE likes_manga (
    id_usuario BIGINT,
    id_manga BIGINT,
    PRIMARY KEY(id_usuario,id_manga),
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY(id_manga) REFERENCES mangas(id) ON DELETE CASCADE
);

DELIMITER //
CREATE TRIGGER sumar_like AFTER INSERT ON likes_manga
FOR EACH ROW BEGIN
    UPDATE mangas SET total_likes=total_likes+1 WHERE id=NEW.id_manga;
END;//

CREATE TRIGGER restar_like AFTER DELETE ON likes_manga
FOR EACH ROW BEGIN
    UPDATE mangas SET total_likes=GREATEST(total_likes-1,0) WHERE id=OLD.id_manga;
END;//
DELIMITER ;

-- =========================
-- SEGUIR MANGA
-- =========================
CREATE TABLE seguir_manga (
    id_usuario BIGINT,
    id_manga BIGINT,
    PRIMARY KEY(id_usuario,id_manga),
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY(id_manga) REFERENCES mangas(id) ON DELETE CASCADE
);

DELIMITER //
CREATE TRIGGER sumar_seg AFTER INSERT ON seguir_manga
FOR EACH ROW BEGIN
    UPDATE mangas SET total_seguidores=total_seguidores+1 WHERE id=NEW.id_manga;
END;//

CREATE TRIGGER restar_seg AFTER DELETE ON seguir_manga
FOR EACH ROW BEGIN
    UPDATE mangas SET total_seguidores=GREATEST(total_seguidores-1,0) WHERE id=OLD.id_manga;
END;//
DELIMITER ;

-- =========================
-- COMENTARIOS
-- =========================
CREATE TABLE comentarios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_usuario BIGINT,
    id_capitulo BIGINT,
    contenido TEXT NOT NULL,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY(id_capitulo) REFERENCES capitulos(id) ON DELETE CASCADE
);

-- Índice para consultas rápidas de comentarios por capítulo/fecha
CREATE INDEX idx_comentarios_cap ON comentarios (id_capitulo, creado);

-- =========================
-- NOTIFICACIONES
-- =========================
CREATE TABLE notificaciones (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_usuario BIGINT NOT NULL,
    tipo ENUM('like','capitulo','comentario','sistema') NOT NULL,
    id_manga BIGINT DEFAULT NULL,
    id_capitulo BIGINT DEFAULT NULL,
    id_comentario BIGINT DEFAULT NULL,
    titulo VARCHAR(255) DEFAULT NULL,
    mensaje TEXT DEFAULT NULL,
    leido BOOLEAN NOT NULL DEFAULT FALSE,
    creado TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY(id_manga) REFERENCES mangas(id) ON DELETE SET NULL,
    FOREIGN KEY(id_capitulo) REFERENCES capitulos(id) ON DELETE SET NULL,
    FOREIGN KEY(id_comentario) REFERENCES comentarios(id) ON DELETE SET NULL,
    INDEX idx_notif_usuario (id_usuario, leido)
);

-- Índice para búsquedas por usuario/tipo/manga (optimiza eliminación e inserción masiva)
CREATE INDEX idx_notif_user_type_manga ON notificaciones (id_usuario, tipo, id_manga, leido, creado);

-- Índice para acelerar búsquedas/operaciones en notificaciones de capítulos
CREATE INDEX idx_notif_capitulo ON notificaciones (tipo, id_manga, id_capitulo);

-- =========================
-- FEED / ACTIVIDAD / ANUNCIOS
-- =========================
CREATE TABLE feed (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('nuevo_capitulo','nuevo_manga','anuncio','logro'),
    id_usuario BIGINT NULL,
    id_manga BIGINT NULL,
    id_capitulo BIGINT NULL,
    texto VARCHAR(255),
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY(id_manga) REFERENCES mangas(id) ON DELETE SET NULL,
    FOREIGN KEY(id_capitulo) REFERENCES capitulos(id) ON DELETE SET NULL
);

-- Índice para consultas rápidas del feed (por fecha y tipo)
CREATE INDEX idx_feed_global ON feed (creado DESC, tipo);

-- Índice opcional para consultas del feed por usuario (reciente primero)
CREATE INDEX idx_feed_user ON feed (id_usuario, creado DESC);

-- Índice adicional para búsquedas por tipo y fecha (mejora anuncios/filtrado)
CREATE INDEX idx_feed_tipo_fecha ON feed (tipo, creado DESC);

-- =========================
-- ANUNCIOS DIRECTOS
-- =========================
CREATE TABLE anuncios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200),
    contenido TEXT,
    imagen VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- VISTAS
-- =========================
CREATE TABLE vistas_capitulo (
    id_capitulo BIGINT,
    id_manga BIGINT DEFAULT NULL,
    fecha DATE,
    vistas INT DEFAULT 1,
    PRIMARY KEY(id_capitulo,fecha),
    FOREIGN KEY(id_capitulo) REFERENCES capitulos(id) ON DELETE CASCADE,
    FOREIGN KEY(id_manga) REFERENCES mangas(id) ON DELETE SET NULL,
    INDEX idx_vistas_manga_fecha (id_manga, fecha)
);

-- =========================
-- Trigger: notificar nuevo capítulo (insertar en feed y notificaciones)
-- =========================
DELIMITER //
CREATE TRIGGER notificar_nuevo_capitulo
AFTER INSERT ON capitulos
FOR EACH ROW
BEGIN
    -- Insertar en feed global
    INSERT INTO feed (tipo, id_manga, id_capitulo, texto)
    VALUES ('nuevo_capitulo', NEW.id_manga, NEW.id, CONCAT('Nuevo capítulo disponible de ', (SELECT titulo FROM mangas WHERE id = NEW.id_manga)));

    -- Limpiar notificaciones previas para este manga (seguidores o favoritos)
    DELETE n FROM notificaciones n
    JOIN (
        SELECT id_usuario FROM seguir_manga WHERE id_manga = NEW.id_manga
        UNION
        SELECT id_usuario FROM favoritos WHERE id_manga = NEW.id_manga
    ) AS u ON u.id_usuario = n.id_usuario
    WHERE n.tipo = 'capitulo' AND n.id_manga = NEW.id_manga;

    -- Insertar nueva notificación (lista deduplicada por UNION)
    INSERT INTO notificaciones (id_usuario, tipo, id_manga, id_capitulo, titulo, mensaje)
    SELECT u.id_usuario, 'capitulo', NEW.id_manga, NEW.id,
           'Nuevo capítulo disponible', CONCAT('Salió un nuevo capítulo (', NEW.numero, ') del manga que sigues o tienes en favoritos.')
    FROM (
        SELECT id_usuario FROM seguir_manga WHERE id_manga = NEW.id_manga
        UNION
        SELECT id_usuario FROM favoritos WHERE id_manga = NEW.id_manga
    ) AS u;
END;//
DELIMITER ;

-- =========================
-- BEFORE INSERT: rellenar id_manga en vistas_capitulo si no se proporciona
-- =========================
DELIMITER //
CREATE TRIGGER poblar_idmanga_vistas_before_insert
BEFORE INSERT ON vistas_capitulo
FOR EACH ROW
BEGIN
    IF NEW.id_manga IS NULL THEN
        SET NEW.id_manga = (SELECT id_manga FROM capitulos WHERE id = NEW.id_capitulo LIMIT 1);
    END IF;
END;//
DELIMITER ;


-- =========================
-- Trigger: actualizar total_vistas en mangas
-- =========================
DELIMITER //
CREATE TRIGGER actualizar_vistas_totales
AFTER INSERT ON vistas_capitulo
FOR EACH ROW
BEGIN
    IF NEW.id_manga IS NOT NULL THEN
        UPDATE mangas
        SET total_vistas = total_vistas + NEW.vistas
        WHERE id = NEW.id_manga;
    END IF;
END;//
DELIMITER ;

-- Trigger: ajustar total_vistas si se actualiza la fila de vistas_capitulo
DELIMITER //
CREATE TRIGGER actualizar_vistas_totales_update
AFTER UPDATE ON vistas_capitulo
FOR EACH ROW
BEGIN
    -- sumar la diferencia (puede ser negativa)
    IF NEW.id_manga IS NOT NULL THEN
        UPDATE mangas
        SET total_vistas = GREATEST(total_vistas + (NEW.vistas - OLD.vistas), 0)
        WHERE id = NEW.id_manga;
    END IF;
END;//
DELIMITER ;
