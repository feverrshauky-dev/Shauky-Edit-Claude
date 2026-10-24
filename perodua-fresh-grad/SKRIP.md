# Skrip Voiceover — Cara Fresh Grad Beli Perodua (89.5 saat, 9:16)

Video animasi penuh (tanpa gambar) dengan suara ElevenLabs "Ashraf"
(`assets/vo/voiceover.mp3`, dinormalkan ke -16 LUFS) dan sari kata perkataan demi perkataan.
Teks yang dihantar ke ElevenLabs ada dalam `SKRIP-ELEVENLABS.txt`.

| Masa | Babak | Skrin |
|---|---|---|
| 0:00–0:06.5 | Hook | "NAK BELI PERODUA?" · kereta brek pada "Tunggu dulu" · "JANGAN SIGN DULU!" |
| 0:06.5–0:20.6 | Langkah 1 · Bajet | Peraturan 15–20% · gaji RM3,000 · RM450–600 |
| 0:20.6–0:33.5 | Langkah 2 · Model | Axia / Bezza / Myvi muncul bila disebut · tanda "ngam-ngam" pada Myvi |
| 0:33.5–0:47.45 | Langkah 3 · Dokumen | Setiap dokumen ditanda bila disebut · tip baru kerja |
| 0:47.45–0:57 | Langkah 4 · Kredit | Jarum jatuh merah pada "PTPTN", naik semula pada "settle" |
| 0:57–0:70.9 | Langkah 5 · Kos | Resit diisi ikut sebutan · ~RM870 · "BUKAN RM425 JE!" |
| 0:70.9–0:81 | Langkah 6 · Proses | 4 langkah showroom ke kunci |
| 0:81–0:89.5 | CTA | "SAVE & SHARE" · "NOMBOR AKU DI BIO" |

## Tukar suara

Rakam / jana suara baru dari `SKRIP-ELEVENLABS.txt`, letak di `assets/vo/voiceover.mp3`, kemudian:

```bash
python3 scripts/align.py assets/vo/voiceover.mp3 SKRIP-ELEVENLABS.txt transcript/words.json
python3 scripts/build_captions.py
```

`align.py` padankan skrip dengan jeda dalam suara (tanpa ASR). Jika masa ayat berubah,
laraskan masa babak dalam `index.html` dan masa animasi dalam `compositions/*.html`
(semuanya ditulis dalam saat filem, bertanda perkataan yang disebut).

## Andaian angka

- Ansuran: deposit 10%, tempoh 9 tahun, kadar rata 3% setahun.
  Contoh Bezza ~RM40k: pinjaman RM36,000 + faedah RM9,720 = RM45,720 ÷ 108 bulan ≈ RM425.
- Harga (~RM38k Axia, ~RM40k Bezza, ~RM47k Myvi) ialah anggaran varian pertengahan.
  Semak harga terkini dengan showroom sebelum posting, dan ubah angka dalam `compositions/model.html` jika perlu.
- Kos bulanan dalam `compositions/kos.html` ialah anggaran kasar untuk contoh sahaja.

## Render semula

```bash
cd perodua-fresh-grad
npm run check
npm run render   # keluar di renders/
```
