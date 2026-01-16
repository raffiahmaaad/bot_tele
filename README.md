# 🤖 Digital Store Telegram Bot

Bot Telegram untuk toko produk digital dengan pembayaran QRIS melalui Pakasir.

## ✨ Fitur

- 📦 **Katalog Produk** - Browse kategori dan produk dengan inline keyboard
- 💳 **Pembayaran QRIS** - Generate QRIS via Pakasir, tampilkan QR code ke pembeli
- 🚀 **Auto-Delivery** - Kirim produk digital otomatis setelah pembayaran
- ⚙️ **Admin Panel** - Kelola produk, kategori, dan lihat pesanan

## 📋 Prasyarat

- Python 3.10+
- Bot Token dari [@BotFather](https://t.me/botfather)
- Akun [Pakasir](https://pakasir.com) dengan Project & API Key
- (Opsional) Server dengan IP publik atau ngrok untuk webhook

## 🚀 Instalasi

### 1. Clone dan Setup

```bash
# Buat virtual environment
python -m venv venv

# Aktifkan (Windows)
.\venv\Scripts\activate

# Aktifkan (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Konfigurasi

```bash
# Copy file konfigurasi
copy .env.example .env

# Edit file .env dengan kredensial Anda
notepad .env
```

Isi konfigurasi berikut:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
PAKASIR_PROJECT_SLUG=your_project_slug
PAKASIR_API_KEY=your_api_key
WEBHOOK_URL=https://your-domain.com/webhook/pakasir
ADMIN_TELEGRAM_IDS=123456789
```

### 3. Jalankan Bot

```bash
python main.py
```

## 🔄 Menjalankan Bot 24/7 (Auto-Run)

### Opsi 1: VPS dengan systemd (Linux)

1. Buat service file:

```bash
sudo nano /etc/systemd/system/digital-store-bot.service
```

2. Isi dengan:

```ini
[Unit]
Description=Digital Store Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/bot_tele
ExecStart=/path/to/bot_tele/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable dan start:

```bash
sudo systemctl enable digital-store-bot
sudo systemctl start digital-store-bot
sudo systemctl status digital-store-bot
```

### Opsi 2: Docker (Recommended)

```bash
# Build dan jalankan
docker-compose up -d

# Lihat logs
docker-compose logs -f

# Stop
docker-compose down
```

### Opsi 3: Cloud Platform (Railway/Render/Fly.io)

#### Railway

1. Push ke GitHub
2. Connect repo ke [Railway](https://railway.app)
3. Add environment variables
4. Deploy otomatis

#### Render

1. Connect ke [Render](https://render.com)
2. Pilih "Web Service"
3. Set start command: `python main.py`
4. Add environment variables

### Opsi 4: Windows Task Scheduler

1. Buka Task Scheduler
2. Create Basic Task
3. Trigger: "When the computer starts"
4. Action: Start a program
5. Program: `pythonw.exe`
6. Arguments: `D:\Project\bot_tele\main.py`
7. Start in: `D:\Project\bot_tele`

## 📱 Cara Pakai

### Untuk Pembeli

1. Start bot dengan `/start`
2. Pilih "📦 Katalog Produk"
3. Pilih kategori → Pilih produk
4. Klik "🛒 Beli Sekarang"
5. Scan QRIS dengan e-wallet
6. Produk dikirim otomatis!

### Untuk Admin

1. Tambahkan Telegram ID Anda ke `ADMIN_TELEGRAM_IDS`
2. Start bot → Pilih "⚙️ Admin Panel"
3. Kelola kategori dan produk
4. Lihat statistik penjualan

## 🔗 Webhook Pakasir

Untuk menerima notifikasi pembayaran otomatis:

1. Set `WEBHOOK_URL` di `.env`
2. Pastikan URL bisa diakses publik
3. Untuk testing lokal, gunakan [ngrok](https://ngrok.com):

```bash
ngrok http 5000
```

4. Copy URL ngrok ke Pakasir dashboard

## 📁 Struktur Folder

```
bot_tele/
├── main.py              # Entry point
├── config.py            # Configuration
├── database.py          # Database operations
├── requirements.txt     # Dependencies
├── .env                 # Your credentials (gitignore)
├── handlers/            # Bot command handlers
├── services/            # Business logic
├── webhook/             # Payment webhook server
└── utils/               # Utilities
```

## 🛠️ Troubleshooting

### Bot tidak merespon

- Cek bot token di `.env`
- Pastikan tidak ada instance bot lain yang berjalan

### Pembayaran tidak terdeteksi

- Cek webhook URL di Pakasir dashboard
- Pastikan port webhook terbuka
- Test dengan ngrok untuk debugging

### Produk tidak terkirim

- Cek logs untuk error
- Pastikan content produk valid
- Untuk file, pastikan path benar

## 📝 License

MIT License - bebas digunakan dan dimodifikasi.
