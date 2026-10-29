# wuwa-cutscene-extractor

**Bahasa Indonesia** | [English](README.en.md)

Ekstrak cutscene **Wuthering Waves** dari paket `.pak` milik game menjadi file `.mp4` biasa, lalu rapikan otomatis ke folder **per versi** lengkap dengan `index.csv`.

> **Disclaimer:** alat ini hanya membaca file game milikmu sendiri. Alat tidak memodifikasi file game, tidak menyertakan aset atau media berhak cipta, dan tidak menyertakan AES key apa pun. Semua aset Wuthering Waves adalah milik Kuro Games. Gunakan untuk keperluan pribadi (mis. arsip cutscene pribadi) dan patuhi ToS yang berlaku.

## Kenapa bisa tanpa AES / FModel?

File video di `Client/Saved/Resources/Video/hd/Paks/<id>/Video_<id>-HD-WindowsNoEditor.pak` **bukan arsip Unreal Engine**. Isinya adalah **file MP4 utuh** yang diberi **header pembungkus 53 byte** di depan:

```text
[ 53 byte header game ][ file MP4 asli (mulai dari box 'ftyp') ]
```

Jadi cukup membuang 53 byte pertama. Tidak perlu dekripsi, tidak perlu AES key. Detail teknis ada di [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md).

## Fitur

- Deteksi otomatis folder video game (tidak perlu konfigurasi rumit).
- Ekstrak MP4 dengan membuang header pembungkus 53 byte.
- Kategorikan video ke folder `v<versi>` berdasarkan `CgId` (versi pertama cutscene muncul).
- Penamaan file `NamaCutscene_Id.mp4`.
- `index.csv` berisi versi, nama, path asli, codec, resolusi, durasi, ukuran.
- Verifikasi otomatis dengan `ffprobe` kalau tersedia.
- Mode `--dry-run`, `--samples`, `--force`, dan resume (file yang sudah ada dilewati).
- **Hanya standard library Python** — tanpa dependensi pip.
- **Tidak pernah menulis ke folder game.** File `.pak` dibuka read-only; semua output ke folder `--out`.

## Kebutuhan

- Windows (diuji di Windows 10/11 dengan Python 3.13).
- Python 3.9 atau lebih baru.
- `ffmpeg`/`ffprobe` **opsional** — hanya untuk mengisi metadata codec/resolusi/durasi di `index.csv`.
- Game Wuthering Waves sudah terunduh lengkap (minimal resource video sudah ada).

## Instalasi

```bash
git clone https://github.com/RyuuZev/wuwa-cutscene-extractor.git
cd wuwa-cutscene-extractor
```

Tidak ada `pip install`. Langsung pakai.

## Cara pakai

Uji dulu tanpa menulis file:

```bash
python src/wuwa_video_extract.py --game "D:\Game\Wuthering Waves\Wuthering Waves Game" --dry-run
```

Ekstrak beberapa video untuk uji coba:

```bash
python src/wuwa_video_extract.py --game "D:\Game\Wuthering Waves\Wuthering Waves Game" --out "D:\Game\Wuthering Waves\Videos" --samples 5
```

Ekstrak semuanya:

```bash
python src/wuwa_video_extract.py --game "D:\Game\Wuthering Waves\Wuthering Waves Game" --out "D:\Game\Wuthering Waves\Videos"
```

### Opsi

| Opsi | Keterangan |
|---|---|
| `--game PATH` | Folder game yang berisi `Client`. Jika kosong, dicoba otomatis dari folder kerja dan subfolder `Wuthering Waves Game`. |
| `--out PATH` | Folder output. Default `./Videos`. |
| `--data PATH` | File pemetaan versi. Default `data/cgid_versions.json`. |
| `--samples N` | Proses hanya `N` video pertama (berguna untuk uji coba). |
| `--force` | Ekstrak ulang walau file output sudah ada. |
| `--no-index` | Jangan tulis `index.csv`. |
| `--dry-run` | Tampilkan ringkasan rencana tanpa menulis file. |

### Struktur output

```text
Videos/
├── index.csv
├── v1.2/
│   ├── R0010_173_1.mp4
│   └── R0013_147_0.mp4
├── v1.3/
├── v2.0/
├── v2.7/
├── v3.5/
└── v3.7/
```

### Kolom `index.csv`

| Kolom | Isi |
|---|---|
| `id` | Nama folder asli, mis. `147_0` (angka = `CgId`). |
| `version` | Versi pertama cutscene muncul, mis. `1.2`. |
| `cg_name` | Nama cutscene dari data game, mis. `R0013`. |
| `cg_file` | Path aset asli di dalam game. |
| `girl_or_boy` | Penanda varian protagonis (0/1). |
| `codec`, `width`, `height`, `duration_s` | Metadata hasil `ffprobe` (kosong bila ffprobe tidak ada). |
| `size_mb` | Ukuran file MP4. |
| `file` | Path relatif hasil, mis. `v1.2\R0013_147_0.mp4`. |

## Hasil contoh

Pada instalasi penuh versi 3.7 (165 paket video, ~12,45 GB) pembagiannya:

| Versi | Video | Versi | Video | Versi | Video |
|---|---:|---|---:|---|---:|
| 1.2 | 5 | 2.7 | 28 | 3.3 | 12 |
| 1.3 | 1 | 2.8 | 5 | 3.4 | 4 |
| 1.4 | 3 | 3.0 | 18 | 3.5 | 14 |
| 2.0 | 6 | 3.1 | 17 | 3.6 | 7 |
| 2.1 | 5 | 3.2 | 4 | 3.7 | 12 |
| 2.3 | 6 |   |   |   |   |
| 2.6 | 18 |   |   |   |   |

Angka bisa berbeda tergantung versi game dan paket suara/resolusi yang kamu unduh.

## Video tidak ada suara?

Itu normal. File video WuWa memang **video-only** (satu track H.264, tanpa audio). Audio cutscene diputar terpisah oleh mesin game dari bank Wwise. Repo ini fokus pada ekstraksi video; penggabungan audio adalah pekerjaan terpisah (lihat [`SunsetMkt/WuWa-Cutscenes`](https://github.com/SunsetMkt/WuWa-Cutscenes)).

## Troubleshooting

- **"Tidak bisa menemukan folder game"** — pastikan `--game` menunjuk ke folder yang berisi `Client`, biasanya `...\Wuthering Waves Game`.
- **"Folder video tidak ditemukan"** — jalankan game sekali agar resource terunduh lengkap.
- **`ffprobe` tidak ditemukan** — metadata di `index.csv` akan kosong, tetapi ekstraksi tetap jalan. Install ffmpeg bila ingin metadata lengkap.
- **`vid N` masuk `vunknown`** — `CgId` tidak ada di `data/cgid_versions.json` (biasanya versi game lebih baru dari data). Perbarui data atau abaikan.
- **0 video ditemukan** — cek path dan pastikan folder `Client/Saved/Resources/Video/hd/Paks` berisi subfolder berangka.

## Cara kerja (ringkas)

1. Cari semua subfolder di `Saved/Resources/Video/hd/Paks`.
2. Ambil angka di depan nama folder (mis. `147_0` → `147` = `CgId`).
3. Buka `.pak` read-only, cari penanda `ftyp`, lalu salin dari 4 byte sebelum `ftyp` sampai akhir file (membuang header 53 byte).
4. Cocokkan `CgId` dengan `data/cgid_versions.json` untuk mendapatkan versi + nama cutscene.
5. Tulis hasil ke `Videos/v<versi>/<Nama>_<Id>.mp4` dan rangkum di `index.csv`.

Penjelasan lengkap: [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md).

## Kredit

- Data pemetaan `CgId` → versi/nama: [`Arikatsu/WutheringWaves_Data`](https://github.com/Arikatsu/WutheringWaves_Data) (branch 0.7–3.7).
- Referensi alur ekstraksi cutscene dan audio: [`SunsetMkt/WuWa-Cutscenes`](https://github.com/SunsetMkt/WuWa-Cutscenes).
- Verifikasi media: [FFmpeg](https://ffmpeg.org/).

## Lisensi

Kode: [MIT](LICENSE). Aset game (video, audio, nama cutscene) tetap milik Kuro Games dan **tidak** termasuk dalam lisensi ini.
