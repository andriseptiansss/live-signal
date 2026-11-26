#!/usr/bin/env python3
"""Sync Live Signal tracker -> signals.json untuk website publik (GitHub Pages).

Sumber kebenaran SATU-SATUNYA adalah tracker:
  workspace/goals/btcusdt-daily-analysis/files/backtest-signal-stats.md
Script ini TIDAK mengubah status sinyal — status (MENUNGGU / BERJALAN /
HIT TP / HIT SL / TIDAK VALID) disalin apa adanya dari tracker. Perubahan
status hanya dilakukan oleh cron cek-market / backtest harian; sync berikutnya
yang mempublikasikannya ke website (jeda hitungan menit).

Yang dilakukan script ini:
  1. Parse tabel sinyal + blok statistik + PDH/PDL terbaru dari tracker.
  2. Ambil harga live dari OKX public API (tanpa login) untuk price_now.
  3. Tulis signals.json (sinyal urutan terbaru dulu) di folder yang sama.

Jalankan:  python3 sync-signals.py
Keluar:   exit 0 jika signals.json ditulis, exit 1 jika parsing gagal
           (file lama dibiarkan, tidak ditimpa setengah jalan).
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACKER = Path.home() / "workspace/goals/btcusdt-daily-analysis/files/backtest-signal-stats.md"
OUT = HERE / "signals.json"

PAIRS = {
    "BTC": {"symbol": "BTCUSDT.P", "okx": "BTC-USDT-SWAP", "decimals": 1},
    "ETH": {"symbol": "ETHUSDT.P", "okx": "ETH-USDT-SWAP", "decimals": 2},
    "BNB": {"symbol": "BNBUSDT.P", "okx": "BNB-USDT-SWAP", "decimals": 2},
    "SOL": {"symbol": "SOLUSDT.P", "okx": "SOL-USDT-SWAP", "decimals": 2},
}

WIB = timezone(timedelta(hours=7))


def parse_id_number(text):
    """Format Indonesia: titik = pemisah ribuan, koma = desimal.
    '60.480,0' -> 60480.0 ; '1.720' -> 1720.0 ; '1.674,89' -> 1674.89 ;
    '0,93' -> 0.93 ; '61.121,7 (test 11:40)' -> 61121.7"""
    m = re.search(r"(\d[\d\.]*(?:,\d+)?)", text)
    if not m:
        return None
    tok = m.group(1).rstrip(".")
    return float(tok.replace(".", "").replace(",", "."))


def parse_range(text):
    """'60.700–60.750' -> (60700.0, 60750.0) ; '59.427–59.750' -> (59427.0, 59750.0).
    Mengembalikan (low, high) atau None."""
    parts = re.split(r"[–\-]", text)
    nums = [parse_id_number(p) for p in parts]
    nums = [n for n in nums if n is not None]
    if len(nums) >= 2:
        return (min(nums), max(nums))
    return None


def parse_sl(text, direction):
    """SL cell -> harga garis SL.
    'di atas 61.603,3' -> 61603.3 ; '60.700–60.750' (SHORT) -> 60750.0 (tepi atas);
    'di bawah 1.667' -> 1667.0 ; range LONG -> tepi bawah."""
    rng = parse_range(text)
    if rng:
        return rng[1] if direction == "SHORT" else rng[0]
    return parse_id_number(text)


def parse_tp(text):
    """TP cell -> (low, high) zona TP, atau (nilai, nilai) kalau satu harga."""
    rng = parse_range(text)
    if rng:
        return rng
    v = parse_id_number(text)
    return (v, v) if v is not None else None


def parse_entry(text, note):
    """Entry cell + kolom Hasil -> (entry_price, zone_low, zone_high).
    - '61.121,7 (test 11:40)' + note '(61.106,9–61.603,3)' -> (61121.7, 61106.9, 61603.3)
    - '61.500–61.650' -> (61500.0, 61500.0, 61650.0)  [entry = tepi terdekat, sesuai tracker]
    - '60.480,0' -> (60480.0, 60480.0, 60480.0)"""
    rng = parse_range(text)
    if rng:
        return (rng[0], rng[0], rng[1])
    price = parse_id_number(text)
    if price is None:
        return (None, None, None)
    # zona dari catatan, mis. "retest supply baru 07:15 (61.106,9–61.603,3)"
    m = re.search(r"\((\d[\d\.,–\-]*)\)", note or "")
    if m:
        z = parse_range(m.group(1))
        if z:
            return (price, z[0], z[1])
    return (price, price, price)


def parse_tracker(text):
    signals = []
    # Tabel sinyal: baris diawali "| <angka> |"
    for line in text.splitlines():
        line = line.strip()
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 9:
            continue
        _num, name, entry_c, sl_c, tp_c, risk_c, reward_c, ratio_c, status, note = cells[:10]
        m = re.match(r"(BTC|ETH|BNB|SOL)\s+(Short|Long)", name, re.IGNORECASE)
        if not m:
            continue
        base, side = m.group(1).upper(), m.group(2).upper()
        direction = "SHORT" if side == "SHORT" else "LONG"
        entry, zone_lo, zone_hi = parse_entry(entry_c, note)
        sl = parse_sl(sl_c, direction)
        tp = parse_tp(tp_c)
        if entry is None or sl is None or tp is None:
            print(f"WARN: sinyal {name} tidak lengkap, dilewati", file=sys.stderr)
            continue
        risk = parse_id_number(risk_c.replace("%", ""))
        reward = parse_id_number(reward_c.replace("%", ""))
        ratio_m = re.search(r"1\s*:\s*([\d,]+)", ratio_c)
        ratio = f"1:{ratio_m.group(1)}" if ratio_m else None
        date_m = re.search(r"(\d{2}:\d{2})", note or "")
        signals.append({
            "id": len(signals) + 1,
            "pair": PAIRS[base]["symbol"],
            "okx": PAIRS[base]["okx"],
            "decimals": PAIRS[base]["decimals"],
            "name": name,
            "direction": direction,
            "entry": entry,
            "entry_zone": [zone_lo, zone_hi],
            "sl": sl,
            "tp_zone": [tp[0], tp[1]],
            "risk_pct": risk,
            "reward_pct": reward,
            "ratio": ratio,
            "status": status.strip(),
            "note": note.strip(),
        })
    if not signals:
        raise ValueError("tidak ada sinyal ter-parse dari tracker")

    stats = {}
    for key, pat in [
        ("total", r"Total sinyal diberikan:\s*(\d+)"),
        ("hit_tp", r"HIT TP:\s*(\d+)"),
        ("hit_sl", r"HIT SL:\s*(\d+)"),
        ("invalid", r"Tidak valid \(kadaluarsa\):\s*(\d+)"),
        ("running", r"Masih BERJALAN:\s*(\d+)"),
        ("waiting", r"Masih MENUNGGU:\s*(\d+)"),
    ]:
        m = re.search(pat, text)
        stats[key] = int(m.group(1)) if m else 0
    m = re.search(r"Winrate \(dari sinyal selesai\):\s*([\d,]+)%", text)
    stats["winrate"] = float(m.group(1).replace(",", ".")) if m else 0.0

    # PDH/PDL terbaru: ambil kemunculan TERAKHIR pola "BTC PDH ... / PDL ..."
    pdh_pdl = {}
    for base in PAIRS:
        pat = rf"{base} PDH ([\d\.,]+) / PDL ([\d\.,]+)"
        found = re.findall(pat, text)
        if found:
            pdh, pdl = found[-1]
            pdh_pdl[PAIRS[base]["symbol"]] = {
                "pdh": parse_id_number(pdh),
                "pdl": parse_id_number(pdl),
            }
    return signals, stats, pdh_pdl


def fetch_okx_prices():
    prices = {}
    for base, info in PAIRS.items():
        url = f"https://www.okx.com/api/v5/market/ticker?instId={info['okx']}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "live-signal-site/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.load(r)
            d = data["data"][0]
            last = float(d["last"])
            open24 = float(d["open24h"])
            prices[info["symbol"]] = {
                "last": last,
                "change_24h_pct": round((last - open24) / open24 * 100, 2),
                "high_24h": float(d["high24h"]),
                "low_24h": float(d["low24h"]),
            }
        except Exception as e:  # noqa: BLE001 - harga live opsional, situs tetap jalan
            print(f"WARN: harga OKX {base} gagal: {e}", file=sys.stderr)
    return prices


def main():
    text = TRACKER.read_text(encoding="utf-8")
    signals, stats, pdh_pdl = parse_tracker(text)
    # Terbaru dulu (sesuai aturan dashboard Live Signal).
    signals = list(reversed(signals))
    for i, s in enumerate(signals, start=1):
        s["id"] = i
    prices = fetch_okx_prices()
    now_wib = datetime.now(WIB).strftime("%Y-%m-%d %H:%M WIB")
    out = {
        "generated_at_wib": now_wib,
        "source": "tracker backtest-signal-stats.md (sumber kebenaran status sinyal)",
        "pairs": [PAIRS[b]["symbol"] for b in ("BTC", "ETH", "BNB", "SOL")],
        "stats": stats,
        "pdh_pdl": pdh_pdl,
        "prices": prices,
        "signals": signals,
    }
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(OUT)
    print(f"OK: {OUT} ditulis — {len(signals)} sinyal, "
          f"stats total={stats['total']} TP={stats['hit_tp']} SL={stats['hit_sl']} "
          f"invalid={stats['invalid']} running={stats['running']} "
          f"winrate={stats['winrate']}% @ {now_wib}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
