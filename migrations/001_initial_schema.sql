CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    display_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_tasks INT DEFAULT 0,
    failed_tasks INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS captcha_tasks (
    id SERIAL PRIMARY KEY,
    provider_task_id VARCHAR(255) UNIQUE NOT NULL,
    worker_id INT REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_at TIMESTAMP,
    submitted_at TIMESTAMP,
    completed_at TIMESTAMP,
    attempt_count INT DEFAULT 0,
    reward NUMERIC(10, 4) DEFAULT 0.0000,
    error_code VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255),
    telegram_user_id BIGINT,
    operation VARCHAR(100),
    result VARCHAR(50),
    error_code VARCHAR(100),
    duration_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
