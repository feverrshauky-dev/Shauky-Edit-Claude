# Style Guide Rujukan — "Editorial Green"

Sumber: `reference/reference-claude-edit.mp4` (TikTok @justyn.ai, 58s, 9:16).
Ini rujukan **gaya** sahaja untuk video Shauky akan datang. Jangan salin skrip, nama, handle atau footage dia — ambil bahasa visual, struktur dan rentak.

Semua ukuran px di bawah dah diskala ke kanvas projek **1080×1920** (sumber 576×1024, ×1.875).
Frame rujukan: `reference/frames/` (01–09 = momen utama, `sheet-1..6` = contact sheet setiap 0.5s).

---

## 1. Rasa keseluruhan

- **Editorial / majalah**, bukan "TikTok neon". Tenang, mahal, yakin.
- Palet hijau hutan + krim + emas. Serif tinggi-kontras untuk tajuk, serif sempit untuk caption.
- Grafik **selalu bercakap tentang apa yang sedang disebut** — setiap ayat ada visual literal (sebut "prompt" → kotak prompt menaip; sebut "raw footage" → kad fail + "BAD TAKE").
- Talking head kekal jadi pusat; grafik duduk di **atas kepala (zon 5–35% tinggi)** atau **di belakang kepala**, jarang tutup muka.
- Hampir tiada dead air. Setiap 1.5–3s ada sesuatu berubah (potongan, grafik masuk, sudut kamera bertukar).

## 2. Palet warna (sampel dari frame)

| Token | Hex | Guna |
|---|---|---|
| `--forest` | `#173328` | Latar hook penuh, kad grafik, kotak "BIGGER" |
| `--forest-cap` | `#24372a` (~92% opacity) | Kotak caption |
| `--cream` | `#f1ebdf` | Teks utama atas hijau, banner, kotak prompt |
| `--gold` | `#c0a858` | Perkataan penekanan (italic), bingkai majalah |
| `--ink` | `#1a1a1a` | Teks atas krim |
| `--dim` | `rgba(241,235,223,0.38)` | Perkataan caption yang belum disebut |
| `--strike` | `#d8423a` | Garis potong ("No CapCut" ✗) |

Grade footage: hangat, kontras sederhana, hitam sedikit diangkat. Seksyen "moody" = sejuk + gelap (demo grade berubah ikut arahan).

## 3. Tipografi (anggaran Google Fonts)

| Peranan | Rupa dalam rujukan | Cadangan font |
|---|---|---|
| Tajuk besar / perkataan hero ("I DIDN'T EDIT", "HUGE", "NEVER", masthead) | Didone sempit, tinggi-kontras, huruf besar | **Bodoni Moda** / **Playfair Display** (condensed via `font-stretch` atau scaleX 0.85) |
| Penekanan italic ("Claude *did.*", "*captions.*", "*sentence.*", "*nothing.*") | Serif italic, sering emas | **Instrument Serif Italic** / **Playfair Display Italic** |
| Caption | Serif sempit, regular | **Instrument Serif** / **Libre Caslon Condensed** |
| Kontras berat ("BIGGER", "THAT'S JUST ONE MORE") | Grotesk hitam tebal | **Archivo Black** / **Inter 900** |
| Label kecil ("TO CLAUDE", "RAW TAKE", timecode, issue line) | Monospace kecil, huruf besar, tracking lebar | **JetBrains Mono** / **IBM Plex Mono**, 18–22px, `letter-spacing: .2em` |

Peraturan: **campur serif + italic emas dalam satu frasa** — perkataan kunci sahaja jadi italic emas (`Claude` krim, `did.` emas). Titik noktah dikekalkan ("did.", "nothing.", "sentence.") — rasa ayat muktamad.

## 4. Caption (sepanjang video)

- **Satu baris, 2–4 perkataan**, di tengah, `top ≈ 1300–1340px` (~70% tinggi). Kekal di posisi sama walaupun sudut kamera tukar.
- Kotak `--forest-cap`, radius kecil (4–6px), padding `6px 16px`. Tiada bayang tebal, tiada outline.
- Font serif sempit ~58–64px, `--cream`.
- **Gaya karaoke terbalik**: seluruh frasa muncul serentak; perkataan yang **belum disebut malap** (`--dim`), jadi krim penuh bila disebut. Tiada pop/scale per perkataan.
- Caption hilang bila ada grafik tipografi besar yang ulang ayat yang sama ("BIGGER captions" tiada caption bawah sebab dah ada).

> Beza dengan style sekarang (`shauky-tiktok/compositions/captions.html`): sekarang Montserrat 800 putih + highlight lime, kotak gelap bulat. Gaya rujukan ni jauh lebih tenang — serif, hijau, malap→terang.

## 5. Katalog grafik (guna semula)

| # | Grafik | Bila guna | Detail |
|---|---|---|---|
| G1 | **Hook kinetik serif atas latar hijau** | 0–3s | Latar bilik diganti `--forest` penuh, subjek dipotong (cutout) di depan. Perkataan besar masuk satu-satu (blur→tajam / slide dari bawah), **di belakang kepala**. Timecode mono kecil berdetik (`00:00:01:07`). |
| G2 | **Payoff italic emas** | Selepas hook | 1 frasa, italic, perkataan terakhir emas. Kemudian latar hijau "terbuka" kembali ke bilik sebenar. |
| G3 | **Ikon app + strike merah** | Senarai "tak guna X, Y" | Ikon app squircle 120px, pop masuk atas kepala, garis merah condong melintang. Perkataan penutup italic ("*nothing.*") besar. |
| G4 | **Kotak prompt menaip** | Bila sebut arahan/ayat | Pil krim lebar 900px di atas (top ~180px), label mono `TO CLAUDE`, teks menaip dengan caret, butang bulat hijau ↑ → bertukar spinner. |
| G5 | **Wipe garis menegak** | Before/after grade | Garis putih nipis sapu kiri→kanan, sebelah kanan dah ditukar grade. |
| G6 | **Kad screenshot terapung** | "video-video terbaik masuk" | 2–4 kad potret kecil condong sikit, masuk berperingkat di zon atas. |
| G7 | **Masthead majalah** | Sebut "macam cover majalah" | Perkataan raksasa didone di belakang kepala, bingkai emas nipis keliling frame, issue line mono (`NO. 01 · OCTOBER 2026 · EDITED BY …`), barcode kecil. |
| G8 | **Kad UI timeline / dropzone** | Bercerita tentang proses | Kad hijau gelap, radius 12px, border krim nipis, kandungan UI ringkas (track, waveform, fail `.MP4`). Masuk dengan slide + scale 0.96→1. |
| G9 | **Kad footage + cop "BAD TAKE"** | Tunjuk bahan mentah | Kad potret kecil, cop merah condong muncul bertubi-tubi, label pill `1:16 of raw footage`. |
| G10 | **Kaunter flip "RAW TAKE"** | Banding durasi | Kad hijau, label mono, digit serif besar flip 1:16 → 0:55. |
| G11 | **Picture-in-picture rekursif** | "apa yang kau tengok sekarang" | Frame mengecil ke dalam kad, berulang (efek Droste). |
| G12 | **Perkataan hero di belakang kepala** | Penekanan 1 perkataan | "HUGE", "NEVER" — didone ~300px, krim, subjek di depan. NEVER: huruf muncul satu-satu, frasa kecil di atasnya. |
| G13 | **Mozek bukti sosial** | "ramai orang buat ni" | Grid 3×3 thumbnail penuh skrin, ~1s sahaja. |
| G14 | **Kad storyboard / chat** | Tunjuk cara kerja | Kad UI besar hijau dengan teks kecil (sengaja tak perlu dibaca penuh), zoom perlahan ke butiran. Chat: bubble krim, nama + avatar, balasan muncul. |
| G15 | **Tipo susun berat + italic** | Senarai arahan pendek | "BIGGER" (grotesk hitam, atas kotak hijau) + "*captions.*" (italic emas); "THAT'S JUST ONE MORE" huruf kecil tebal muncul per perkataan + banner krim condong dengan "*sentence.*" raksasa. |
| G16 | **Kad video walkthrough** | Promosi lead magnet | Kad thumbnail gaya player + tajuk serif + label bab mono yang bertukar. |
| G17 | **CTA kotak komen** | Akhir | Tajuk pil putih `Comment "EDIT" and I'll send you the walkthrough`, kotak komen menaip `EDIT`, balasan "Sending it over.", hati jadi merah. Kekal di skrin sehingga habis. |
| G18 | **Pill follow** | Penutup | Pill profil (avatar, handle, tagline) butang `Follow` → `✓ Following`. |

## 6. Struktur & rentak (template 55s)

| Masa | Beat | Grafik | Kamera |
|---|---|---|---|
| 0–2s | **Hook kontroversi** ("Aku tak edit satu saat pun video ni") | G1 | Close-up, latar hijau |
| 2–3s | **Twist / siapa sebenarnya** | G2 | Close-up |
| 3–5.5s | **Buang alternatif** ("No X, no Y, nothing.") | G3 | Close-up, latar sebenar |
| 5.5–7.5s | **Janji 1 ayat** | G4 | Close-up |
| 7.5–15s | **Demo #1** — arahan → hasil (grade, kad, masthead) | G4→G5→G6→G7 | Whip-blur → **wide duduk** |
| 15–22s | **Kredibiliti / "aku tak tahu apa-apa"** + bukti bahan mentah | G8→G9→G10→G11 | Blur → **wide berdiri/mencangkung** |
| 22–27s | **Demo #2** — arahan lain, hasil lain | G4→G12 | Sudut lain (meja + lampu) |
| 27–28.5s | **Bukti sosial** | G13 | — |
| 28.5–38.5s | **Pembeza** ("cara aku lain sikit…") | G14 | **Close-up dekat** (mic nampak) |
| 38.5–43.5s | **Klimaks penekanan** | G12 (NEVER) → G15 | Close-up |
| 43.5–50.5s | **Lead magnet + CTA komen** | G16→G17 | **Wide berdiri** |
| 50.5–54s | **Follow CTA** | G17 kekal + G18 | Close-up santai |

Rentak:
- **3–4 sudut kamera** (close-up, medium duduk, wide duduk, wide berdiri) — tukar sudut setiap pergantian beat, bukan setiap ayat.
- Jump cut ketat; jeda >0.25s dibuang.
- Peralihan: **whip/motion blur** antara sudut, **blur-in** bila masuk seksyen baru. Tiada zoom-punch agresif, tiada shake.
- Grafik masuk ~0.1s sebelum perkataan disebut, keluar bila ayat seterusnya mula.

## 7. Audio

- Suara dominan, tiada ruang senyap (lantai bunyi ~-35 dB → kemungkinan ada music bed perlahan; muzik tak menonjol).
- Bunyi jenis "UI": klik menaip pada kotak prompt/komen, whoosh lembut pada blur transition, pop kecil untuk ikon. Elak riser/impact berat — tak kena dengan rasa editorial.
- Aset SFX sedia ada yang sesuai: `click-soft.mp3`, `whoosh-short.mp3`, `pop.mp3`, `sparkle.mp3` (jarang). Elak `impact-bass-1`, `glitch-1`.

## 8. Checklist sebelum render

- [ ] Hook 0–3s ada latar hijau + perkataan serif di belakang kepala + payoff italic emas
- [ ] Caption serif sempit, satu baris, kotak hijau, perkataan belum-sebut malap
- [ ] Setiap ayat penting ada grafik literal dari katalog §5
- [ ] Sekurang-kurangnya 3 sudut kamera, tukar ikut beat
- [ ] Hanya `--forest / --cream / --gold` (+ merah untuk strike sahaja)
- [ ] Grafik di zon atas atau belakang kepala — muka tak tertutup
- [ ] CTA komen 1 perkataan + kotak komen menaip, kekal hingga akhir
- [ ] Follow pill di 3–4s terakhir
- [ ] SFX ringan sahaja (klik, whoosh, pop)

## 9. Nota teknikal HyperFrames

- **Teks di belakang kepala** (G1, G7, G12) perlukan matte/cutout subjek: lapisan footage → teks → cutout subjek di atas. Guna `/media-use` (cutouts) dan `references/media-treatments.md` sebelum buat.
- Letak token warna & font di `index.html` (`:root`) supaya semua sub-composition kongsi.
- Grafik dari katalog boleh jadi komponen guna semula dalam `compositions/components/` (cth. `prompt-box.html`, `hero-word.html`, `comment-cta.html`).
