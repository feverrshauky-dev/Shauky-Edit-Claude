# Template TikTok Live: Rebate Akhir Tahun

Overlay 1080×1920 (9:16) untuk live jual kereta. Rebate diambil dari poster promosi Nov–Dis 2026.

## Fail

| Fail | Guna untuk |
|---|---|
| `overlay.html` | Overlay bergerak: countdown masa sebenar, kad model bertukar setiap 8 saat, ticker, banner "JANGAN SCROLL DULU!" |
| `png/overlay-<model>.png` | Overlay lutsinar (PNG statik), satu fail untuk setiap model |
| `png/latar/0-umum.png` … `5-myvi.png` | 6 gambar latar Green Screen untuk live dari telefon: satu umum dan satu untuk setiap model |
| `video/latar-green-screen-bergerak.mp4` | Latar bergerak (untuk akaun yang Green Screen-nya terima video, atau untuk video promo) |

## Cara guna

### A. Live dari PC (TikTok LIVE Studio / OBS): paling cantik
1. Tambah source **Kamera** dulu.
2. Tambah source **Link / Browser Source** di atasnya, dan pilih `overlay.html` (dalam OBS: tanda "Local file"). Saiz: **1080 × 1920**.
3. Kad model bertukar sendiri. Banner "JANGAN SCROLL DULU!" keluar sendiri setiap 75 saat.
4. Kalau nak kawal sendiri (OBS: klik kanan source → *Interact*):
   - `1` Aruz · `2` Ativa · `3` Myvi · `4` Bezza · `5` Axia · `0` = auto semula
   - `H` = banner "Jangan scroll" (tekan bila ramai orang baru masuk)
   - `C` = CTA bergoyang · `T` = sorok/tunjuk T&S
5. Pilihan URL: `overlay.html?model=axia` (kunci satu model), `?preview=1` (tengok dengan latar kelabu + senarai kekunci).

> Kalau LIVE Studio tak boleh buka fail HTML, guna PNG dalam `png/` sebagai source **Gambar**.

### B. Live dari telefon sahaja
Overlay tak boleh dilekat terus atas live telefon. Ada dua cara lain:

**Cara 1: Green Screen + tukar gambar ikut model (cuma perlu satu telefon)**
1. Simpan keenam-enam gambar dalam `png/latar/` ke galeri telefon:
   `0-umum` · `1-ativa` · `2-axia` · `3-bezza` · `4-aruz` · `5-myvi`
2. Buka LIVE, tekan **Effects**, pilih **Green Screen**, kemudian pilih **0-umum**. Tekan Go LIVE.
3. Bila kau nak cerita pasal satu model, tekan **Effects → Green Screen** dan pilih gambar model tu. Latar terus bertukar.
4. Habis cerita model tu, pilih **0-umum** semula, atau terus ke model seterusnya.
5. Berdiri supaya badan kau di bahagian bawah. Kad model dan rebate ada di atas kepala kau.

Susunan nombor ikut susunan cerita yang dicadangkan (rebate paling tinggi dulu): Ativa → Axia → Bezza → Aruz → Myvi.
Kalau Green Screen dalam LIVE kau terima video, `video/latar-green-screen-bergerak.mp4` pun boleh dipakai.

**Cara 2: Skrin kedua di belakang kau (lebih "hidup")**
Guna tablet, laptop, TV atau telefon lama sebagai papan iklan bergerak di belakang kau.
1. Hantar `overlay-satu-fail.html` ke peranti itu (WhatsApp ke diri sendiri, Telegram atau Google Drive). Fail ini satu saja; gambar dan font dah ada di dalamnya.
2. Buka dengan Chrome. Tambah `?mode=skrin` di hujung alamat untuk versi skrin penuh dengan latar biru.
3. Kawal dengan **sentuh**:
   - Sentuh **kad model**: tukar ke model seterusnya
   - Sentuh dua kali **kad model**: kembali bertukar sendiri
   - Sentuh **tajuk RM7,500**: banner "JANGAN SCROLL DULU!"
   - Sentuh **CTA kuning**: CTA bergoyang
4. Telefon live di depan, skrin kedua di belakang bahu kau. Matikan auto-lock dan naikkan cerah skrin.

## Susun atur (kenapa begini)
- **Atas (y 170–700):** tajuk, countdown dan ticker. Ia di bawah bar profil TikTok, jadi tak tertutup.
- **Kiri tengah dibiarkan kosong** untuk muka kau. Komen penonton keluar di kiri bawah.
- **Kanan:** kad model + CTA "KOMEN STOK". Bahagian ini tak tertutup oleh komen.

---

# Skrip Live (60 minit, ulang)

**Tajuk live (pilih satu):**
- `REBATE SEHINGGA RM7,500 🔥 Semak stok live`
- `Axia rebate RM4,900?! Tanya aku stok sekarang`
- `Perodua year end: rebate sampai 31 Dis je`

**Komen pin:**
> 📌 Taip **STOK + MODEL** (contoh: STOK AXIA). Aku semak stok & quotation terus. Rebate sehingga RM7,500, stok 2026, daftar sebelum 31 Dis. Tertakluk T&S.

### 0:00–0:05: Hook (ulang setiap kali viewer naik)
Cakap laju, tunjuk ke kad atau banner:
- "Jangan scroll dulu! Nak Axia, rebate dia sampai **RM4,900**."
- "Ativa AV sekarang rebate **RM7,500**. Ini rebate paling tinggi tahun ni."
- "Tinggal **[baca countdown] hari** je. Lepas 31 Dis, rebate ni hilang."

### Pusingan 10 minit (ulang 6 kali)
1. **Min 0–1: Hook + countdown.** Tekan `H`. Baca berapa hari lagi yang tinggal.
2. **Min 1–6: Spotlight satu model.** Tekan nombor model tu dan terangkan:
   - Rebate setiap varian. Kad akan tanda varian **TERTINGGI**.
   - Siapa yang sesuai: Axia untuk first car, Bezza untuk sedan jimat, Myvi pilihan keluarga kecil, Ativa SUV, Aruz 7 seater.
   - "Nak tahu ansuran bulanan? Komen STOK + model, aku kira untuk kau."
3. **Min 6–8: Jawab komen.** Sebut nama penonton. Ulang soalan dia kuat-kuat. Ajak dia DM atau WhatsApp.
4. **Min 8–10: CTA.** Tekan `C`. "Komen STOK sekarang. Aku semak stok warna yang kau nak."

Susunan model yang dicadangkan: **Ativa → Axia → Bezza → Aruz → Myvi** (mula dengan rebate paling tinggi supaya orang berhenti scroll).

### Ayat untuk naikkan engagement
- "Taip **1** kalau nak Axia, **2** kalau Bezza. Aku nak tengok mana lebih ramai."
- "Siapa first car? Komen 🚗."
- "Share live ni kat kawan yang tengah cari kereta. Rebate ni sampai 31 Dis je."

### Jawapan untuk bantahan biasa
- **"Nanti dulu lah."** → "Rebate ni untuk stok 2026 dan pendaftaran sebelum 31 Dis. Kalau lepas tu, aku tak boleh janji."
- **"Loan susah lulus."** → "Komen STOK, aku semak dulu kelayakan kau. Tak ada caj."
- **"Warna ni ada?"** → "Stok bergantung pada cawangan. Bagi aku model + warna, aku semak terus."

### Wajib sebut (sekali setiap 10 minit)
> "Rebate untuk stok tahun 2026 dan pendaftaran 1 Nov hingga 31 Dis 2026. Tertakluk kepada terma, syarat dan stok."

Jangan janji harga atau rebate yang tiada dalam poster rasmi.

---

## Untuk bina semula video latar
```
node tools/render_video_frames.js overlay.html <folder-frame> 30 30
ffmpeg -framerate 30 -i <folder-frame>/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 video/latar-green-screen-bergerak.mp4
```
