# Google Cloud Run Deployment Guide

## Prasyarat
1.  Punya akun **Google Cloud Platform (GCP)**.
2.  Install **Google Cloud SDK** di komputer Anda.

## Langkah-Langkah Deployment

### 1. Login ke Google Cloud
Buka terminal dan jalankan:
```bash
gcloud auth login
```

### 2. Set Project ID
Buat project baru di GCP Console atau gunakan yang sudah ada. Set di terminal:
```bash
gcloud config set project [PROJECT_ID_ANDA]
```

### 3. Aktifkan Service yang Dibutuhkan
Aktifkan Cloud Run dan Container Registry:
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 4. Deploy ke Cloud Run
Jalankan perintah ini dari dalam folder `edg-monitoring`. Ini akan otomatis membuild container dan mendeploynya.
```bash
gcloud run deploy edg-monitor --source . --region asia-southeast2 --allow-unauthenticated
```
*Catatan:* `asia-southeast2` adalah region Jakarta.

### 6. Cara Update / Edit Code (Re-Deploy)
Jika Anda mengubah kode program (misal: edit `app.py`), Anda cukup **menjalankan ulang perintah deploy yang sama**:

```bash
gcloud run deploy edg-monitor --source . --region asia-southeast2 --allow-unauthenticated
```

Google Cloud Run akan otomatis:
1.  Membuild ulang aplikasi Anda dengan kode terbaru.
2.  Membuat "Revisi" baru.
3.  Memindahkan traffic user ke versi terbaru secara otomatis (tanpa downtime).

---

## Troubleshooting
- Jika error permission, pastikan akun Anda di GCP memiliki role **Cloud Run Admin** dan **Storage Admin**.
- Pastikan file `Dockerfile` dan `requirements.txt` ada di folder yang sama saat menjalankan command deploy.
