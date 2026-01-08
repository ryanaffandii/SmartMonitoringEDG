# Panduan Install & Deploy ke Google Cloud (Khusus Mac Apple Silicon / M1 / M2)

Ikuti langkah-langkah di bawah ini satu per satu di terminal Anda.

### 1. Download & Install Google Cloud SDK

Copy dan paste perintah di bawah ini ke terminal (per baris):

```bash
# 1. Download file instalasi (versi Apple Silicon)
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-arm.tar.gz

# 2. Ekstrak file
tar -xf google-cloud-cli-darwin-arm.tar.gz

# 3. Jalankan script instalasi
./google-cloud-sdk/install.sh
```

**Penting:**
*   Saat proses instalasi (`install.sh`), jika ditanya `Do you want to help improve the Google Cloud CLI...`, ketik `Y` atau `N` lalu Enter.
*   Jika ditanya `Do you want to update your $PATH...`, ketik `Y` lalu Enter.
*   Jika diminta path config file, tekan **Enter** saja (default).

### 2. Restart Terminal
Setelah instalasi selesai, **tutup terminal Anda sepenuhnya** dan buka terminal baru agar perintah `gcloud` bisa dikenali.

### 3. Login & Setup Project
Di terminal baru, jalankan:

```bash
gcloud auth login
```
*(Akan membuka browser, silakan login dengan akun Google Anda)*

Setelah login, set project ID Anda (ganti `PROJECT_ID` dengan ID project SmartMonitoringEDG Anda dari dashboard Google Cloud):
```bash
gcloud config set project [PROJECT_ID_ANDA]
```

### 4. Deploy Aplikasi
Pastikan Anda berada di folder `edg-monitoring`, lalu jalankan:

```bash
gcloud run deploy edg-monitor --source . --region asia-southeast2 --allow-unauthenticated
```
Tunggu proses hingga selesai (sekitar 2-5 menit). Nanti akan muncul link URL aplikasi Anda.
