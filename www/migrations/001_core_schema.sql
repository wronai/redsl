-- =============================================================
-- REDSL Panel — Initial schema
-- File: migrations/001_core_schema.sql
-- =============================================================
-- Umieść w katalogu www/migrations/
-- Uruchom: php lib/Migration/run.php
-- =============================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- KLIENCI
CREATE TABLE clients (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_name      VARCHAR(255)   NOT NULL,
    tax_id            VARCHAR(20),
    regon             VARCHAR(20),
    address_line1     VARCHAR(255),
    address_line2     VARCHAR(255),
    city              VARCHAR(100),
    postal_code       VARCHAR(10),
    country           CHAR(2)        NOT NULL DEFAULT 'PL',
    contact_name      VARCHAR(255),
    contact_email     VARCHAR(255)   NOT NULL,
    contact_phone     VARCHAR(30),
    github_login      VARCHAR(100),
    status            ENUM('lead','active','suspended','archived') NOT NULL DEFAULT 'lead',
    notes             TEXT,
    created_at        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (contact_email),
    INDEX idx_status (status),
    INDEX idx_tax_id (tax_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- UMOWY (NDA, service, aneksy)
CREATE TABLE contracts (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id         INT UNSIGNED   NOT NULL,
    type              ENUM('nda','service','addendum') NOT NULL,
    number            VARCHAR(32)    UNIQUE NOT NULL,
    status            ENUM('draft','sent','signed','expired','cancelled') NOT NULL DEFAULT 'draft',
    sent_at           DATETIME,
    signed_at         DATETIME,
    valid_until       DATE,
    pdf_path          VARCHAR(500),
    signed_pdf_path   VARCHAR(500),
    access_token      CHAR(64),
    metadata          JSON,
    created_at        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    INDEX idx_client_status (client_id, status),
    INDEX idx_access_token (access_token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- PROJEKTY (repo klientów)
CREATE TABLE projects (
    id                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id             INT UNSIGNED   NOT NULL,
    name                  VARCHAR(255)   NOT NULL,
    repo_url              VARCHAR(500)   NOT NULL,
    repo_provider         ENUM('github','gitlab','gitea','bitbucket') NOT NULL DEFAULT 'github',
    default_branch        VARCHAR(100)   NOT NULL DEFAULT 'main',
    auth_token_encrypted  BLOB,
    auth_token_nonce      BLOB,
    clone_path            VARCHAR(500),
    last_commit_sha       CHAR(40),
    language_primary      VARCHAR(32),
    scan_schedule         ENUM('on_demand','daily','weekly','monthly') NOT NULL DEFAULT 'weekly',
    scan_timeout_sec      INT UNSIGNED   NOT NULL DEFAULT 600,
    next_scan_at          DATETIME,
    last_scan_at          DATETIME,
    status                ENUM('active','paused','error') NOT NULL DEFAULT 'active',
    last_error            TEXT,
    created_at            DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_client (client_id),
    INDEX idx_due_scan (status, next_scan_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- SKANY
CREATE TABLE scan_runs (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id        INT UNSIGNED   NOT NULL,
    commit_sha        CHAR(40),
    started_at        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at       DATETIME,
    status            ENUM('queued','cloning','running','parsing','completed','failed') NOT NULL DEFAULT 'queued',
    artifacts_path    VARCHAR(500),
    metrics_summary   JSON,
    error_message     TEXT,
    duration_sec      INT UNSIGNED,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_started (project_id, started_at DESC),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- TICKETY
CREATE TABLE tickets (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id          INT UNSIGNED   NOT NULL,
    scan_run_id         INT UNSIGNED,
    parent_ticket_id    INT UNSIGNED,
    category            ENUM('auto','user_defined') NOT NULL,
    type                VARCHAR(50),
    title               VARCHAR(500)   NOT NULL,
    description         TEXT,
    file_path           VARCHAR(500),
    function_name       VARCHAR(255),
    line_start          INT UNSIGNED,
    line_end            INT UNSIGNED,
    metrics_before      JSON,
    metrics_after       JSON,
    price_pln           DECIMAL(10,2)  NOT NULL,
    status              ENUM('proposed','approved','rejected','in_progress','pr_open','merged','expired') NOT NULL DEFAULT 'proposed',
    pr_url              VARCHAR(500),
    pr_number           INT UNSIGNED,
    pr_opened_at        DATETIME,
    merged_at           DATETIME,
    expired_at          DATETIME,
    invoice_item_id     INT UNSIGNED,
    created_at          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id)       REFERENCES projects(id)   ON DELETE CASCADE,
    FOREIGN KEY (scan_run_id)      REFERENCES scan_runs(id)  ON DELETE SET NULL,
    FOREIGN KEY (parent_ticket_id) REFERENCES tickets(id)    ON DELETE CASCADE,
    INDEX idx_project_status (project_id, status),
    INDEX idx_merged (merged_at),
    INDEX idx_pr_open (status, pr_opened_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- FAKTURY
CREATE TABLE invoices (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id       INT UNSIGNED   NOT NULL,
    number          VARCHAR(32)    UNIQUE NOT NULL,
    issue_date      DATE           NOT NULL,
    due_date        DATE           NOT NULL,
    period_start    DATE           NOT NULL,
    period_end      DATE           NOT NULL,
    subtotal_pln    DECIMAL(10,2)  NOT NULL,
    vat_rate        DECIMAL(4,2)   NOT NULL DEFAULT 23.00,
    vat_amount_pln  DECIMAL(10,2)  NOT NULL,
    total_pln       DECIMAL(10,2)  NOT NULL,
    status          ENUM('draft','sent','paid','overdue','cancelled') NOT NULL DEFAULT 'draft',
    pdf_path        VARCHAR(500),
    sent_at         DATETIME,
    paid_at         DATETIME,
    payment_method  ENUM('transfer','card','other'),
    created_at      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    INDEX idx_client_status (client_id, status),
    INDEX idx_due_date (due_date, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- POZYCJE FAKTURY
CREATE TABLE invoice_items (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    invoice_id   INT UNSIGNED   NOT NULL,
    ticket_id    INT UNSIGNED   NOT NULL,
    description  VARCHAR(500)   NOT NULL,
    amount_pln   DECIMAL(10,2)  NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_id)  REFERENCES tickets(id)  ON DELETE RESTRICT,
    UNIQUE KEY uniq_ticket (ticket_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Zamknięcie FK z tickets → invoice_items (po utworzeniu invoice_items)
ALTER TABLE tickets
    ADD CONSTRAINT fk_tickets_invoice_item
    FOREIGN KEY (invoice_item_id) REFERENCES invoice_items(id) ON DELETE SET NULL;


-- AUDIT LOG (append-only)
CREATE TABLE audit_log (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor       VARCHAR(100)   NOT NULL,
    action      VARCHAR(100)   NOT NULL,
    entity_type VARCHAR(50)    NOT NULL,
    entity_id   INT UNSIGNED,
    payload     JSON,
    ip_address  VARCHAR(45),
    created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_actor_time (actor, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- SEKWENCJA NUMERACJI FAKTUR (atomowa dla concurrent cronów)
CREATE TABLE invoice_sequence (
    year       SMALLINT UNSIGNED PRIMARY KEY,
    next_value INT UNSIGNED NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- MIGRATIONS TRACKING
CREATE TABLE _migrations (
    filename    VARCHAR(255)  PRIMARY KEY,
    applied_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Oznacz ten plik jako zastosowany (żeby runner go nie powtórzył)
INSERT INTO _migrations (filename) VALUES ('001_core_schema.sql');
