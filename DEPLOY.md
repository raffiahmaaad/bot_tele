# BotStore VPS Deployment Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- Neon PostgreSQL database
ssss

## Quick Start

### 1. Upload ke VPS

Upload semua file ke `/home/container/`

### 2. Configure Environment

Copy `.env.example` ke `.env` dan edit:

```bash
cp .env.example .env
nano .env
```

Isi dengan:

```env
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
JWT_SECRET_KEY=random-string-32-karakter
FLASK_ENV=production
PORT=5001
```

### 3. Deploy

```bash
chmod +x deploy.sh start.sh
./deploy.sh
```

### 4. Start Application

```bash
./start.sh
```

## Manual Start

### Backend Only

```bash
cd api
python app.py
```

### Frontend Only

```bash
cd web
npm install
npm run build
npm start
```

## Ports

- Backend API: 5001
- Frontend: 3000

## Logs

- Backend: `logs/backend.log`
- Frontend: `logs/frontend.log`
