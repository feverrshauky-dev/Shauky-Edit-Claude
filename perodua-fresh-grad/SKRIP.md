# Skrip Voiceover — Cara Fresh Grad Beli Perodua (56 saat, 9:16)

Video ni animasi penuh, tak guna gambar langsung. Rakam suara ikut masa di bawah,
atau letak lagu trending saja; teks atas skrin dah cukup untuk sampaikan mesej.

| Masa | Babak | Skrin | Voiceover |
|---|---|---|---|
| 0:00–0:05 | Hook | "NAK BELI PERODUA?" · kereta masuk · "JANGAN SIGN DULU!" | "Baru grad, nak beli Perodua? Jangan sign apa-apa dulu. Ada 6 benda kau wajib tahu." |
| 0:05–0:13 | Langkah 1 · Bajet | Gaji RM3,000 · bar 15–20% · RM450–600 | "Satu, kira bajet. Ansuran kereta jangan lebih 15 sampai 20 peratus gaji. Gaji 3 ribu, maksimum dalam 450 ke 600 sebulan." |
| 0:13–0:22 | Langkah 2 · Model | Axia ~RM410 · Bezza ~RM425 · Myvi ~RM500 | "Dua, pilih model ikut poket. Axia dalam 410 sebulan, Bezza 425, Myvi dalam 500. Gaji 3 ribu, Myvi dah ngam-ngam." |
| 0:22–0:30 | Langkah 3 · Dokumen | Senarai semak 5 dokumen · tip baru kerja | "Tiga, sediakan dokumen: IC, lesen, slip gaji 3 bulan, penyata KWSP, penyata bank, dan surat tawaran kerja. Baru kerja? Ada bank terima slip pertama, atau guna penjamin." |
| 0:30–0:36 | Langkah 4 · Kredit | CCRIS / CTOS · meter · amaran PTPTN | "Empat, semak CCRIS dan CTOS. PTPTN tertunggak boleh buat loan ditolak, jadi settle dulu." |
| 0:36–0:44 | Langkah 5 · Kos tersembunyi | Resit: jumlah ~RM870 · "BUKAN RM425 JE!" | "Lima, kira kos tersembunyi. Minyak, insurans, tol, servis. Ansuran 425, tapi sebenarnya hampir 900 sebulan." |
| 0:44–0:51 | Langkah 6 · Proses | Test drive → mohon 2–3 bank → sign → semak PDI | "Enam, test drive dan tempah, mohon 2 ke 3 bank, baca perjanjian, dan semak kereta betul-betul sebelum ambil kunci." |
| 0:51–0:56 | CTA | "SAVE & SHARE" · "NOMBOR AKU DI BIO" | "Save dan share dekat kawan kau. Nak kira ansuran ikut gaji kau? Nombor aku dekat bio." |

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
