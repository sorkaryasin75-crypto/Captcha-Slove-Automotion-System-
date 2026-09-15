# Telegram Manual CAPTCHA Worker Management Platform

A production-grade, highly secure, Telegram-based manual CAPTCHA worker management platform built with Node.js, TypeScript, PostgreSQL, and Telegraf. This system strictly complies with human-in-the-loop workflows, ensuring official API integration without violating security mechanisms or bypassing third-party anti-bot protections.

---

## 🚀 Features

- **Telegram Inline Keyboard Interface**: Complete navigation, task management, and workflow controls entirely via responsive inline keyboards.
- **Worker Management**: Secure registration, session tracking, and performance statistics for every individual worker.
- **Task State Machine**: Robust lifecycle management (`PENDING` ➔ `ASSIGNED` ➔ `DISPLAYED` ➔ `ANSWER_SUBMITTED` ➔ `SUCCESS`/`INCORRECT`).
- **Idempotency & Rate Limiting**: Built-in mechanisms to prevent duplicate submissions, race conditions, and API throttling.
- **Official API Integration**: Standardized integration adhering strictly to official documentation and terms of service.
- **Observability & Health Checks**: Integrated `/health` and `/ready` endpoints with structured JSON logging for deployment pipelines.

---

## 📁 Project Structure

```text
my-captcha-platform/
├── migrations/
│   └── 001_initial_schema.sql
├── src/
│   ├── config/          # Database and service configurations
│   ├── bot/             # Telegram bot setup, keypads, and handlers
│   ├── services/        # 2Captcha and task queue management
│   ├── database/        # PostgreSQL connection and pool queries
│   ├── middleware/      # Authentication, validation, and logging
│   ├── utils/           # Error handling and helper functions
│   └── index.ts         # Main entry point & Express server setup
├── tests/               # Unit and integration test suites
├── Dockerfile
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
