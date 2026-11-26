# Live Signal — Website Publik (Gratis, GitHub Pages)

Website statis yang menampilkan sinyal trading Andri secara **live**:
harga + chart candle 5m tiap beberapa detik, daftar sinyal + statistik backtest
yang diperbarui otomatis beberapa menit setelah ada sinyal baru / perubahan status.

## Isi folder

| File | Fungsi |
|---|---|
| `index.html` | Satu-satunya halaman website. Tanpa library luar, tanpa server. Harga live diambil langsung dari API publik OKX (cadangan: Binance) oleh browser pengunjung. |
| `signals.json` | Data sinyal + statistik + PDH/PDL + harga saat sync. Dibuat otomatis oleh `sync-signals.py`. |
| `sync-signals.py` | Baca tracker resmi (`backtest-signal-stats.md`) → tulis `signals.json`. Status sinyal disalin apa adanya; script ini TIDAK menentukan status. Harga live diambil dari OKX public API (tanpa login). |
| `publish.sh` | Jalankan sync lalu push ke GitHub (butuh `GITHUB_REPO` + `GITHUB_TOKEN`). |
| `README.md` | File ini. |

## Cara kerja live-nya

- **Harga & chart:** browser pengunjung memanggil API publik OKX tiap 5 detik (ticker) dan tiap 60 detik (candle 5m). Tidak ada server sendiri, tidak ada biaya.
- **Sinyal & status:** `signals.json` diperbarui oleh `sync-signals.py` setiap kali tracker berubah (sinyal baru / HIT TP / HIT SL / kadaluarsa). Website memuat ulang `signals.json` tiap 30 detik. Jeda dari sinyal diterbitkan di Muse sampai muncul di website: hitungan menit.
- **Chart bersih:** zona entry / SL / TP hanya digambar untuk sinyal MENUNGGU (masih valid) atau BERJALAN — sama seperti aturan di ruang Live Signal Muse. Kalau tidak ada, chart hanya candle + garis PDH/PDL.

## Deploy (sekali saja)

1. Buat repo publik baru di GitHub, mis. `live-signal`.
2. Di repo **Settings > Pages > Build and deployment > Branch: main**, simpan.
3. Buat Personal Access Token (Settings > Developer settings > Personal access tokens > Tokens (classic), scope `public_repo`).
4. Jalankan dari folder ini:
   ```bash
   GITHUB_REPO="https://github.com/<username>/live-signal.git" \
   GITHUB_TOKEN="<token>" ./publish.sh
   ```
5. Website aktif di `https://<username>.github.io/live-signal/` — link ini yang dishare ke grup Telegram.

## Update otomatis

Supaya `signals.json` selalu segar tanpa dijalankan manual, pasang cron tiap 5 menit
yang menjalankan `publish.sh` dengan `GITHUB_REPO` + `GITHUB_TOKEN` terisi.
Cron hanya push kalau ada perubahan (commit kosong dilewati).

## Catatan

- Siapa pun yang pegang link website bisa melihat sinyalnya.
- Sinyal dari analisa teknikal, bukan ajakan jual/beli.
- Harga OKX (perpetual swap) bisa berbeda beberapa dolar dari harga Binance Futures.
