# 📚 Panduan Deploy Bot ke Cloud Platform

Panduan lengkap untuk deploy bot ke berbagai platform cloud gratis.

---

## 📋 Persiapan Sebelum Deploy

1. **Push ke GitHub** (wajib untuk semua platform)

```bash
cd d:\Project\bot_tele
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/bot_tele.git
git push -u origin main
```

2. **Siapkan environment variables:**
   - `TELEGRAM_BOT_TOKEN`
   - `PAKASIR_PROJECT_SLUG`
   - `PAKASIR_API_KEY`
   - `ADMIN_TELEGRAM_IDS`

---

## 🥈 Koyeb (Recommended - No Sleep, Free)

### Langkah-langkah:

1. **Daftar di [koyeb.com](https://www.koyeb.com)**

   - Sign up dengan GitHub (lebih mudah)

2. **Create New App**

   - Klik "Create App"
   - Pilih "GitHub"
   - Connect repository `bot_tele`

3. **Configure Build**

   - Builder: `Dockerfile`
   - Port: `5000`

4. **Set Environment Variables**

   ```
   TELEGRAM_BOT_TOKEN = xxx
   PAKASIR_PROJECT_SLUG = xxx
   PAKASIR_API_KEY = xxx
   ADMIN_TELEGRAM_IDS = 123456789
   WEBHOOK_PORT = 5000
   ```

5. **Deploy**

   - Klik "Deploy"
   - Tunggu build selesai (~2-3 menit)

6. **Set Webhook URL di Pakasir**
   - Copy URL dari Koyeb: `https://your-app-xxx.koyeb.app`
   - Tambahkan `/webhook/pakasir`
   - Set di Pakasir dashboard: `https://your-app-xxx.koyeb.app/webhook/pakasir`

### ✅ Selesai! Bot berjalan 24/7

---

## 🥉 Fly.io (No Sleep, Free)

### Langkah-langkah:

1. **Install Fly CLI**

   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Login**

   ```bash
   flyctl auth login
   ```

3. **Buat file `fly.toml`** di folder project:

   ```toml
   app = "digital-store-bot"
   primary_region = "sin"  # Singapore

   [build]
     dockerfile = "Dockerfile"

   [http_service]
     internal_port = 5000
     force_https = true
     auto_stop_machines = false   # Penting! Jangan auto stop
     auto_start_machines = true

   [env]
     WEBHOOK_PORT = "5000"
   ```

4. **Launch App**

   ```bash
   cd d:\Project\bot_tele
   flyctl launch --no-deploy
   ```

5. **Set Secrets (Environment Variables)**

   ```bash
   flyctl secrets set TELEGRAM_BOT_TOKEN=xxx
   flyctl secrets set PAKASIR_PROJECT_SLUG=xxx
   flyctl secrets set PAKASIR_API_KEY=xxx
   flyctl secrets set ADMIN_TELEGRAM_IDS=123456789
   ```

6. **Deploy**

   ```bash
   flyctl deploy
   ```

7. **Get URL**

   ```bash
   flyctl info
   ```

   URL: `https://digital-store-bot.fly.dev`

8. **Set Webhook di Pakasir**
   - `https://digital-store-bot.fly.dev/webhook/pakasir`

---

## 4️⃣ Northflank (No Sleep, Free)

### Langkah-langkah:

1. **Daftar di [northflank.com](https://northflank.com)**

   - Sign up dengan GitHub

2. **Create New Service**

   - Pilih "Add Service" → "Combined Service"
   - Connect GitHub repo

3. **Configure**

   - Build: Dockerfile
   - Port: 5000

4. **Environment Variables**

   - Add semua credentials

5. **Deploy**

   - Klik Deploy

6. **Get Public URL**
   - Copy URL: `https://xxx.northflank.app`
   - Webhook: `https://xxx.northflank.app/webhook/pakasir`

---

## 5️⃣ Zeabur (No Sleep, $5 Credit/bulan)

### Langkah-langkah:

1. **Daftar di [zeabur.com](https://zeabur.com)**

   - Sign up dengan GitHub

2. **Create Project**

   - Klik "New Project"
   - Pilih region: Singapore

3. **Add Service**

   - Pilih "Git" → Connect repo
   - Zeabur auto-detect Dockerfile

4. **Set Variables**

   - Tab "Variables"
   - Add semua credentials

5. **Generate Domain**

   - Tab "Networking"
   - Klik "Generate Domain"
   - URL: `https://xxx.zeabur.app`

6. **Set Webhook**
   - `https://xxx.zeabur.app/webhook/pakasir`

---

## 🚂 Railway (Sleep setelah credit habis)

### Langkah-langkah:

1. **Daftar di [railway.app](https://railway.app)**

   - Sign up dengan GitHub

2. **New Project**

   - Klik "New Project"
   - Pilih "Deploy from GitHub repo"
   - Select `bot_tele`

3. **Configure**

   - Railway auto-detect Dockerfile
   - Klik project → "Variables"

4. **Add Variables**

   ```
   TELEGRAM_BOT_TOKEN = xxx
   PAKASIR_PROJECT_SLUG = xxx
   PAKASIR_API_KEY = xxx
   ADMIN_TELEGRAM_IDS = 123456789
   WEBHOOK_PORT = 5000
   ```

5. **Generate Domain**

   - Tab "Settings"
   - Klik "Generate Domain"
   - URL: `https://xxx.up.railway.app`

6. **Set Webhook Pakasir**
   - `https://xxx.up.railway.app/webhook/pakasir`

### ⚠️ Catatan Railway:

- Free credit $5/bulan
- ~500 jam runtime
- Bot akan mati jika credit habis

---

## 🎨 Render (Sleep after 15min idle)

### Langkah-langkah:

1. **Daftar di [render.com](https://render.com)**

   - Sign up dengan GitHub

2. **New Web Service**

   - Klik "New" → "Web Service"
   - Connect GitHub repo

3. **Configure**

   - Name: `digital-store-bot`
   - Region: Singapore
   - Runtime: Docker
   - Instance Type: **Free**

4. **Environment Variables**

   - Add semua credentials
   - Tambahkan `WEBHOOK_PORT=5000`

5. **Create Web Service**

   - Klik "Create Web Service"
   - Tunggu deploy

6. **Get URL**
   - URL: `https://digital-store-bot.onrender.com`
   - Webhook: `https://digital-store-bot.onrender.com/webhook/pakasir`

### ⚠️ Catatan Render Free:

- Sleep setelah 15 menit tidak ada request
- Cold start ~30 detik
- **Workaround:** Gunakan [UptimeRobot](https://uptimerobot.com) untuk ping setiap 5 menit

---

## 🔧 Troubleshooting

### Bot tidak merespon setelah deploy

1. Cek logs di dashboard platform
2. Pastikan semua environment variables terisi
3. Cek bot token valid

### Webhook tidak bekerja

1. Pastikan URL benar: `https://xxx/webhook/pakasir`
2. Cek port 5000 exposed
3. Test dengan curl:
   ```bash
   curl https://your-app.com/health
   ```

### Database reset saat redeploy

- Untuk persistent storage, gunakan database eksternal (PostgreSQL)
- Atau mount volume (Fly.io, Koyeb support ini)

---

## 📊 Ringkasan

| Platform   | Free 24/7? | Webhook? | Kemudahan | Link                                     |
| ---------- | ---------- | -------- | --------- | ---------------------------------------- |
| Koyeb      | ✅         | ✅       | ⭐⭐⭐    | [koyeb.com](https://koyeb.com)           |
| Fly.io     | ✅         | ✅       | ⭐⭐      | [fly.io](https://fly.io)                 |
| Northflank | ✅         | ✅       | ⭐⭐⭐    | [northflank.com](https://northflank.com) |
| Zeabur     | ✅         | ✅       | ⭐⭐⭐    | [zeabur.com](https://zeabur.com)         |
| Railway    | ⚠️         | ✅       | ⭐⭐⭐    | [railway.app](https://railway.app)       |
| Render     | ⚠️         | ✅       | ⭐⭐⭐    | [render.com](https://render.com)         |

**Rekomendasi:** Mulai dengan **Koyeb** (paling mudah) atau **Fly.io** (paling stabil)
