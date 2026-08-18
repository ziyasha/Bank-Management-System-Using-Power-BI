-- database/schema.sql
--
-- Consolidated schema for the Bank Management System.
-- This supersedes migration_add_branch.sql and migration_bank_customers.sql —
-- if you're setting up a FRESH database, just run this file and you're done.
-- (Those two migration files are only needed if you already have an older
-- database you don't want to drop and want to upgrade in place instead.)
--
-- Run with:
--   mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS banking_system;
USE banking_system;

-- ---------------------------------------------------------------------
-- users
-- role_id: 1 = admin, 2 = staff, 3 = customer, 4 = manager
-- ---------------------------------------------------------------------
CREATE TABLE users (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(150)    NOT NULL,
    email           VARCHAR(150)    NOT NULL,          -- intentionally NOT unique
    phone           VARCHAR(15)     NOT NULL UNIQUE,     -- enforced unique at the DB level too
    password        VARCHAR(255)    NOT NULL,            -- bcrypt hash
    address         VARCHAR(255),
    date_of_birth   DATE            NOT NULL,
    role_id         INT             NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'ACTIVE',
    transaction_pin VARCHAR(255),                         -- bcrypt hash, nullable until set
    branch          VARCHAR(100)    NOT NULL DEFAULT 'MAIN',
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_users_phone (phone),
    INDEX idx_users_branch (branch),
    INDEX idx_users_role (role_id)
);

-- ---------------------------------------------------------------------
-- bank_customers
-- The "branch counter" record: staff enter these details in person,
-- BEFORE the customer ever self-registers on the app. Self-registration
-- checks phone + date_of_birth + id_proof_number against this table.
-- ---------------------------------------------------------------------
CREATE TABLE bank_customers (
    bank_customer_id     INT AUTO_INCREMENT PRIMARY KEY,
    full_name             VARCHAR(150)    NOT NULL,
    phone                 VARCHAR(15)     NOT NULL UNIQUE,
    date_of_birth         DATE            NOT NULL,
    id_proof_number       VARCHAR(50)     NOT NULL UNIQUE,
    address               VARCHAR(255),
    branch                VARCHAR(100)    NOT NULL,
    is_registered_on_app  BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_bank_customers_branch (branch)
);

-- ---------------------------------------------------------------------
-- accounts
-- ---------------------------------------------------------------------
CREATE TABLE accounts (
    account_id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id                  INT             NOT NULL,
    account_number           VARCHAR(20)     NOT NULL UNIQUE,
    account_type             VARCHAR(20)     NOT NULL,      -- SAVINGS / CURRENT
    balance                  DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    account_status           VARCHAR(20)     NOT NULL DEFAULT 'INACTIVE',   -- INACTIVE / ACTIVE / REJECTED
    account_request_status   VARCHAR(20)     NOT NULL DEFAULT 'PENDING',    -- PENDING / APPROVED / REJECTED
    is_verified               BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at                TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_accounts_user (user_id)
);

-- ---------------------------------------------------------------------
-- transactions
-- ---------------------------------------------------------------------
CREATE TABLE transactions (
    transaction_id     INT AUTO_INCREMENT PRIMARY KEY,
    account_number      VARCHAR(20)     NOT NULL,
    transaction_type    VARCHAR(20)     NOT NULL,     -- DEPOSIT / WITHDRAW / TRANSFER_OUT / TRANSFER_IN
    amount               DECIMAL(15,2)   NOT NULL,
    balance_after        DECIMAL(15,2)   NOT NULL,
    description          VARCHAR(255),
    transaction_time     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (account_number) REFERENCES accounts(account_number),
    INDEX idx_transactions_account (account_number),
    INDEX idx_transactions_time (transaction_time)
);

-- ---------------------------------------------------------------------
-- loans
-- ---------------------------------------------------------------------
CREATE TABLE loans (
    loan_id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT             NOT NULL,
    loan_amount       DECIMAL(15,2)   NOT NULL,
    loan_type         VARCHAR(20)     NOT NULL,   -- HOME / CAR / PERSONAL
    duration          INT             NOT NULL,   -- months
    id_proof          VARCHAR(50),
    income_proof      VARCHAR(50),
    status             VARCHAR(30)     NOT NULL DEFAULT 'PENDING',
    admin_status       VARCHAR(20)     NOT NULL DEFAULT 'PENDING',
    remarks            VARCHAR(255),
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_loans_user (user_id),
    INDEX idx_loans_status (status)
);

-- ---------------------------------------------------------------------
-- complaints
-- ---------------------------------------------------------------------
CREATE TABLE complaints (
    complaint_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT             NOT NULL,
    subject            VARCHAR(150)    NOT NULL,
    description         TEXT,
    status              VARCHAR(20)     NOT NULL DEFAULT 'OPEN',
    created_at           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    resolved_on          TIMESTAMP       NULL,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_complaints_user (user_id),
    INDEX idx_complaints_status (status)
);

-- ---------------------------------------------------------------------
-- notifications
-- ---------------------------------------------------------------------
CREATE TABLE notifications (
    notification_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id               INT             NOT NULL,
    message                VARCHAR(255)    NOT NULL,
    is_read                 BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at               TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_notifications_user (user_id)
);
