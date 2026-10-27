CREATE DATABASE IF NOT EXISTS khetiyan
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE khetiyan;

CREATE TABLE state (
  id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  code        CHAR(2)       NOT NULL,
  name_hi     VARCHAR(80)   NOT NULL,
  name_en     VARCHAR(80)   NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_state_code (code)
) ENGINE = InnoDB;

CREATE TABLE district (
  id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  state_id    INT UNSIGNED  NOT NULL,
  code        VARCHAR(10)   NOT NULL,
  name_hi     VARCHAR(80)   NOT NULL,
  name_en     VARCHAR(80)   NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_district_code (state_id, code),
  CONSTRAINT fk_district_state FOREIGN KEY (state_id)
    REFERENCES state (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

CREATE TABLE tehsil (
  id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  district_id INT UNSIGNED  NOT NULL,
  code        VARCHAR(10)   NOT NULL,
  name_hi     VARCHAR(80)   NOT NULL,
  name_en     VARCHAR(80)   NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_tehsil_code (district_id, code),
  CONSTRAINT fk_tehsil_district FOREIGN KEY (district_id)
    REFERENCES district (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

CREATE TABLE village (
  id               INT UNSIGNED   NOT NULL AUTO_INCREMENT,
  tehsil_id        INT UNSIGNED   NOT NULL,
  code             VARCHAR(10)    NOT NULL,
  name_hi          VARCHAR(80)    NOT NULL,
  name_en          VARCHAR(80)    NOT NULL,
  total_area_hectare DECIMAL(12,4) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_village_code (tehsil_id, code),
  CONSTRAINT fk_village_tehsil FOREIGN KEY (tehsil_id)
    REFERENCES tehsil (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_village_area CHECK (total_area_hectare IS NULL OR total_area_hectare >= 0)
) ENGINE = InnoDB;

CREATE TABLE land_type (
  id      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code    VARCHAR(20)      NOT NULL,
  name_hi VARCHAR(50)      NOT NULL,
  name_en VARCHAR(50)      NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_land_type_code (code)
) ENGINE = InnoDB;

CREATE TABLE person (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  aadhaar_hash  CHAR(64)        NULL,
  aadhaar_last4 CHAR(4)         NULL,
  name_hi       VARCHAR(120)    NOT NULL,
  name_en       VARCHAR(120)    NULL,
  father_name_hi VARCHAR(120)   NULL,
  gender        ENUM('male', 'female', 'other') NOT NULL DEFAULT 'other',
  date_of_birth DATE            NULL,
  mobile        VARCHAR(15)     NULL,
  address_hi    VARCHAR(255)    NULL,
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_person_aadhaar (aadhaar_hash),
  KEY idx_person_name (name_hi),
  CONSTRAINT chk_person_last4 CHECK (aadhaar_last4 IS NULL OR aadhaar_last4 REGEXP '^[0-9]{4}$')
) ENGINE = InnoDB;

CREATE TABLE khasra (
  id                 BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  village_id         INT UNSIGNED     NOT NULL,
  khasra_no          VARCHAR(20)      NOT NULL,
  area_hectare       DECIMAL(10,4)    NOT NULL,
  land_type_id       TINYINT UNSIGNED NOT NULL,
  soil_type          VARCHAR(50)      NULL,
  irrigation_source  VARCHAR(50)      NULL,
  boundary           JSON             NULL,
  is_disputed        BOOLEAN          NOT NULL DEFAULT FALSE,
  created_at         TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_khasra_village_no (village_id, khasra_no),
  KEY idx_khasra_village (village_id),
  CONSTRAINT fk_khasra_village FOREIGN KEY (village_id)
    REFERENCES village (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_khasra_land_type FOREIGN KEY (land_type_id)
    REFERENCES land_type (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_khasra_area CHECK (area_hectare > 0)
) ENGINE = InnoDB;

CREATE TABLE khata (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  village_id INT UNSIGNED    NOT NULL,
  khata_no   VARCHAR(20)     NOT NULL,
  khata_type ENUM('individual', 'joint', 'institutional') NOT NULL DEFAULT 'individual',
  created_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_khata_village_no (village_id, khata_no),
  CONSTRAINT fk_khata_village FOREIGN KEY (village_id)
    REFERENCES village (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

CREATE TABLE mutation (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  mutation_no      VARCHAR(30)     NOT NULL,
  khasra_id        BIGINT UNSIGNED NOT NULL,
  from_person_id   BIGINT UNSIGNED NULL,
  to_person_id     BIGINT UNSIGNED NOT NULL,
  share_percentage DECIMAL(5,2)    NOT NULL,
  mutation_type    ENUM('sale', 'inheritance', 'gift', 'partition', 'government_allotment', 'correction') NOT NULL,
  order_date       DATE            NOT NULL,
  status           ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
  remarks_hi       VARCHAR(255)    NULL,
  created_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_mutation_no (mutation_no),
  KEY idx_mutation_khasra (khasra_id),
  CONSTRAINT fk_mutation_khasra FOREIGN KEY (khasra_id)
    REFERENCES khasra (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_mutation_from_person FOREIGN KEY (from_person_id)
    REFERENCES person (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_mutation_to_person FOREIGN KEY (to_person_id)
    REFERENCES person (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_mutation_share CHECK (share_percentage > 0 AND share_percentage <= 100)
) ENGINE = InnoDB;

CREATE TABLE ownership (
  id                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  khasra_id            BIGINT UNSIGNED NOT NULL,
  khata_id             BIGINT UNSIGNED NOT NULL,
  person_id            BIGINT UNSIGNED NOT NULL,
  share_percentage     DECIMAL(5,2)    NOT NULL,
  acquisition_mode     ENUM('sale', 'inheritance', 'gift', 'partition', 'government_allotment') NOT NULL,
  from_date            DATE            NOT NULL,
  to_date              DATE            NULL,
  source_mutation_id   BIGINT UNSIGNED NULL,
  created_at           TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_ownership_khasra_current (khasra_id, to_date),
  KEY idx_ownership_person (person_id),
  KEY idx_ownership_khata (khata_id),
  CONSTRAINT fk_ownership_khasra FOREIGN KEY (khasra_id)
    REFERENCES khasra (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_ownership_khata FOREIGN KEY (khata_id)
    REFERENCES khata (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_ownership_person FOREIGN KEY (person_id)
    REFERENCES person (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_ownership_mutation FOREIGN KEY (source_mutation_id)
    REFERENCES mutation (id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT chk_ownership_share CHECK (share_percentage > 0 AND share_percentage <= 100),
  CONSTRAINT chk_ownership_dates CHECK (to_date IS NULL OR to_date >= from_date)
) ENGINE = InnoDB;

CREATE TABLE crop (
  id      SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code    VARCHAR(20)       NOT NULL,
  name_hi VARCHAR(50)       NOT NULL,
  name_en VARCHAR(50)       NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_crop_code (code)
) ENGINE = InnoDB;

CREATE TABLE crop_cycle (
  id                BIGINT UNSIGNED   NOT NULL AUTO_INCREMENT,
  khasra_id         BIGINT UNSIGNED   NOT NULL,
  crop_id           SMALLINT UNSIGNED NOT NULL,
  season            ENUM('kharif', 'rabi', 'zaid') NOT NULL,
  crop_year         SMALLINT UNSIGNED NOT NULL,
  sown_date         DATE              NULL,
  harvested_date    DATE              NULL,
  area_hectare      DECIMAL(10,4)     NULL,
  yield_quintal     DECIMAL(12,2)     NULL,
  created_at        TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_crop_cycle (khasra_id, crop_id, season, crop_year),
  CONSTRAINT fk_crop_cycle_khasra FOREIGN KEY (khasra_id)
    REFERENCES khasra (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_crop_cycle_crop FOREIGN KEY (crop_id)
    REFERENCES crop (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_crop_cycle_year CHECK (crop_year BETWEEN 1900 AND 2100),
  CONSTRAINT chk_crop_cycle_dates CHECK (harvested_date IS NULL OR sown_date IS NULL OR harvested_date >= sown_date)
) ENGINE = InnoDB;

CREATE TABLE app_user (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  username      VARCHAR(50)  NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name_hi  VARCHAR(120) NOT NULL,
  role          ENUM('admin', 'tehsildar', 'patwari', 'viewer') NOT NULL,
  village_id    INT UNSIGNED NULL,
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_app_user_username (username),
  CONSTRAINT fk_app_user_village FOREIGN KEY (village_id)
    REFERENCES village (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;

CREATE TABLE land_document (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  khasra_id    BIGINT UNSIGNED NOT NULL,
  doc_type     ENUM('khasra_map', 'jamabandi', 'mutation_order', 'sale_deed', 'gift_deed', 'other') NOT NULL,
  file_name    VARCHAR(255)    NOT NULL,
  file_uri     VARCHAR(500)    NOT NULL,
  uploaded_by  INT UNSIGNED    NOT NULL,
  uploaded_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_land_document_khasra (khasra_id),
  CONSTRAINT fk_land_document_khasra FOREIGN KEY (khasra_id)
    REFERENCES khasra (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_land_document_user FOREIGN KEY (uploaded_by)
    REFERENCES app_user (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

CREATE TABLE audit_log (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  table_name  VARCHAR(64)     NOT NULL,
  record_id   BIGINT UNSIGNED NOT NULL,
  action      ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
  old_value   JSON            NULL,
  new_value   JSON            NULL,
  changed_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_audit_table_record (table_name, record_id)
) ENGINE = InnoDB;

DELIMITER $$

CREATE TRIGGER trg_ownership_share_ins
BEFORE INSERT ON ownership
FOR EACH ROW
BEGIN
  DECLARE current_total DECIMAL(8,2);

  IF NEW.to_date IS NULL THEN
    SELECT COALESCE(SUM(share_percentage), 0) INTO current_total
    FROM ownership
    WHERE khasra_id = NEW.khasra_id AND to_date IS NULL;

    IF current_total + NEW.share_percentage > 100 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Total current ownership share for this khasra cannot exceed 100%';
    END IF;
  END IF;
END$$

CREATE TRIGGER trg_ownership_share_upd
BEFORE UPDATE ON ownership
FOR EACH ROW
BEGIN
  DECLARE current_total DECIMAL(8,2);

  IF NEW.to_date IS NULL THEN
    SELECT COALESCE(SUM(share_percentage), 0) INTO current_total
    FROM ownership
    WHERE khasra_id = NEW.khasra_id
      AND to_date IS NULL
      AND id <> NEW.id;

    IF current_total + NEW.share_percentage > 100 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Total current ownership share for this khasra cannot exceed 100%';
    END IF;
  END IF;
END$$

CREATE TRIGGER trg_ownership_audit_ins
AFTER INSERT ON ownership
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (table_name, record_id, action, new_value)
  VALUES ('ownership', NEW.id, 'INSERT', JSON_OBJECT(
    'khasra_id', NEW.khasra_id,
    'khata_id', NEW.khata_id,
    'person_id', NEW.person_id,
    'share_percentage', NEW.share_percentage,
    'acquisition_mode', NEW.acquisition_mode,
    'from_date', NEW.from_date,
    'to_date', NEW.to_date
  ));
END$$

CREATE TRIGGER trg_ownership_audit_upd
AFTER UPDATE ON ownership
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (table_name, record_id, action, old_value, new_value)
  VALUES ('ownership', NEW.id, 'UPDATE',
    JSON_OBJECT(
      'khasra_id', OLD.khasra_id,
      'khata_id', OLD.khata_id,
      'person_id', OLD.person_id,
      'share_percentage', OLD.share_percentage,
      'from_date', OLD.from_date,
      'to_date', OLD.to_date
    ),
    JSON_OBJECT(
      'khasra_id', NEW.khasra_id,
      'khata_id', NEW.khata_id,
      'person_id', NEW.person_id,
      'share_percentage', NEW.share_percentage,
      'from_date', NEW.from_date,
      'to_date', NEW.to_date
    )
  );
END$$

CREATE TRIGGER trg_ownership_audit_del
AFTER DELETE ON ownership
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (table_name, record_id, action, old_value)
  VALUES ('ownership', OLD.id, 'DELETE', JSON_OBJECT(
    'khasra_id', OLD.khasra_id,
    'khata_id', OLD.khata_id,
    'person_id', OLD.person_id,
    'share_percentage', OLD.share_percentage,
    'from_date', OLD.from_date,
    'to_date', OLD.to_date
  ));
END$$

DELIMITER ;

CREATE OR REPLACE VIEW v_current_ownership AS
SELECT
  o.id                AS ownership_id,
  o.khasra_id,
  k.khasra_no,
  v.name_hi           AS village_hi,
  t.name_hi           AS tehsil_hi,
  d.name_hi           AS district_hi,
  o.khata_id,
  kh.khata_no,
  o.person_id,
  p.name_hi           AS owner_hi,
  p.name_en           AS owner_en,
  o.share_percentage,
  o.acquisition_mode,
  o.from_date
FROM ownership o
JOIN khasra  k  ON k.id  = o.khasra_id
JOIN village v  ON v.id  = k.village_id
JOIN tehsil  t  ON t.id  = v.tehsil_id
JOIN district d ON d.id  = t.district_id
JOIN khata   kh ON kh.id = o.khata_id
JOIN person  p  ON p.id  = o.person_id
WHERE o.to_date IS NULL;

CREATE OR REPLACE VIEW v_khasra_summary AS
SELECT
  k.id                AS khasra_id,
  k.village_id,
  k.khasra_no,
  v.name_hi           AS village_hi,
  k.area_hectare,
  lt.name_hi          AS land_type_hi,
  k.is_disputed,
  COALESCE(SUM(o.share_percentage), 0) AS allocated_share,
  COUNT(DISTINCT o.person_id)          AS owner_count
FROM khasra k
JOIN village   v  ON v.id = k.village_id
JOIN land_type lt ON lt.id = k.land_type_id
LEFT JOIN ownership o
  ON o.khasra_id = k.id AND o.to_date IS NULL
GROUP BY k.id, k.village_id, k.khasra_no, v.name_hi, k.area_hectare, lt.name_hi, k.is_disputed;
