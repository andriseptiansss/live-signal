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
| `publish-api.py` | Cara publish utama: sync + buat repo (kalau belum ada) + upload file yang berubah via GitHub API + aktifkan Pages. Token dipakai lewat koneksi `custom.github` di Secure Vault, tidak dibaca dari file/env. Jalankan: `python3 publish-api.py`. |
| `publish.sh` | Cara manual cadangan (git push, butuh `GITHUB_REPO` + `GITHUB_TOKEN` di env). |
| `README.md` | File ini. |

## Cara kerja live-nya

- **Harga & chart:** browser pengunjung memanggil API publik OKX tiap 5 detik (ticker) dan tiap 60 detik (candle 5m). Tidak ada server sendiri, tidak ada biaya.
- **Sinyal & status:** `signals.json` diperbarui oleh `sync-signals.py` setiap kali tracker berubah (sinyal baru / HIT TP / HIT SL / kadaluarsa). Website memuat ulang `signals.json` tiap 30 detik. Jeda dari sinyal diterbitkan di Muse sampai muncul di website: hitungan menit.
- **Chart bersih:** zona entry / SL / TP hanya digambar untuk sinyal MENUNGGU (masih valid) atau BERJALAN — sama seperti aturan di ruang Live Signal Muse. Kalau tidak ada, chart hanya candle + garis PDH/PDL.

## Deploy (sekali saja, sudah dilakukan)

Repo `andriseptiansss/live-signal` sudah dibuat dan Pages sudah aktif di
`https://andriseptiansss.github.io/live-signal/` (26 Nov 2026).
Untuk deploy ulang / publish perubahan, jalankan dari folder ini:

```bash
python3 publish-api.py
```

Token GitHub tersimpan di koneksi `custom.github` (Secure Vault), scope
`public_repo`, akun `andriseptiansss` (login via Google). Jangan taruh token
di file atau env.

## Update otomatis

Cron `sync-live-signal-website` berjalan tiap 10 menit dan menjalankan
`publish-api.py`, jadi `signals.json` selalu segar tanpa dijalankan manual.
File yang isinya tidak berubah dilewati (tidak ada commit kosong).

## Catatan

- Siapa pun yang pegang link website bisa melihat sinyalnya.
- Sinyal dari analisa teknikal, bukan ajakan jual/beli.
- Harga OKX (perpetual swap) bisa berbeda beberapa dolar dari harga Binance Futures.
