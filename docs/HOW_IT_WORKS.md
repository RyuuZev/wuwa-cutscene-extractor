# Cara Kerja Teknis

Dokumen ini menjelaskan format file, logika pemetaan versi, dan batasan alat.

## 1. Format file video WuWa

Lokasi sumber:

```text
<Game>\Client\Saved\Resources\Video\hd\Paks\<id>\Video_<id>-HD-WindowsNoEditor.pak
```

Meskipun berekstensi `.pak`, file ini **bukan** arsip Unreal Engine. Isinya adalah file **MP4** yang dibungkus header kecil. Contoh 60 byte pertama (file `Video_275_0`):

```text
offset  isi
0x00    00 00 00 00 00 00 00 00 82 2f 78 00 00 00 00 00
0x10    82 2f 78 00 00 00 00 00 00 00 00 00 9b 13 8a d9   <- 0x00782f82 = panjang MP4 (dua kali)
0x20    0b 6b 92 71 16 b2 6a 25 cd 6f 31 ae 3d 4a 45 63   <- 16 byte hash/signature (byte 28-43)
0x30    00 00 00 00 00 00 00 00 20 66 74 79 70 69 73 6f   <- byte 53-56 = ukuran box, 57 = "ftyp"
```

Fakta penting:

- Nilai `0x00782f82` = `7.876.482` = panjang payload MP4 (sama dengan akhir box `mdat`).
- String `ftyp` ada di **offset 57**. Box MP4 selalu diawali 4 byte ukuran, jadi file MP4 asli dimulai di `57 - 4 = 53`.
- Karena itu **header pembungkus = 53 byte**. Offset ini konsisten untuk 165 paket yang diuji.

Setelah header, isinya MP4 normal:

```text
ftyp (32 byte) -> moov (metadata) -> free -> mdat (data video H.264)
```

Di belakang `mdat` ada blok kecil (pada contoh 477 byte, diakhiri 53 byte nol) yang tidak dipakai player. Alat ini menyalin apa adanya sampai EOF; ffmpeg/ffprobe mengabaikannya.

## 2. Menemukan batas MP4

Jangan hardcode 53. Alat mencari `b"ftyp"` di 64 KB pertama, lalu memakai `index - 4` sebagai awal MP4. Ini lebih tahan kalau header berubah sedikit di versi game lain.

```python
idx = head.find(b"ftyp")
offset = idx - 4
src.seek(offset)
```

Jika `ftyp` tidak ditemukan (`idx < 4`), file dilaporkan gagal dan tidak ditulis.

## 3. Video ini tidak punya audio

Semua 165 paket diuji hanya punya **satu track** (`trak`) video H.264, tanpa `soun`/`mp4a`/`aac`. Struktur MP4 hanya `ftyp`, `moov`, `free`, `mdat`; tidak ada box audio. Jadi bukan kerusakan hasil ekstraksi: audio cutscene diputar terpisah oleh engine dari bank Wwise (`Client/Content/Aki/WwiseAudio_Generated` di dalam pak utama).

## 4. Pemetaan `CgId` -> versi

Nama folder memuat ID dan varian:

```text
147_0   ->  CgId = 147, varian 0
312_2   ->  CgId = 312, varian 2
```

`CgId` sama dengan field `CgId` pada data cutscene game (`videodata.json`), yang juga memuat:

- `CgName` — nama cutscene (mis. `R0013`),
- `CgFile` — path aset asli (mis. `Roles/01_2/.../R0013_Nvzhu`),
- `GirlOrBoy` — varian protagonis.

Untuk menentukan versi, data publik [`Arikatsu/WutheringWaves_Data`](https://github.com/Arikatsu/WutheringWaves_Data) diambil per branch versi (0.7 sampai 3.7). Untuk setiap `CgId`, dicatat **branch pertama** tempat ID itu muncul. Itulah versinya.

Hasil olahan disimpan di [`data/cgid_versions.json`](../data/cgid_versions.json):

```json
{
  "videos": {
    "147": {
      "version": "1.2",
      "cg_name": "R0013",
      "cg_file": "/Game/Aki/Sequence/.../R0013_Nvzhu.R0013_Nvzhu",
      "girl_or_boy": 0
    }
  }
}
```

Alat tidak melakukan request jaringan saat dijalankan; semua pemetaan dibaca dari file JSON tersebut.

## 5. Alur alat

1. Resolve folder game: pastikan ada `Client`.
2. Baca `data/cgid_versions.json`.
3. Kumpulkan subfolder angka di `Client/Saved/Resources/Video/hd/Paks`.
4. Untuk tiap folder:
   1. ambil `CgId` dari nama folder,
   2. tentukan `version` + `cg_name`,
   3. buka `.pak` mode `rb`, cari `ftyp`, salin payload ke `Videos/v<versi>/<Nama>_<Id>.mp4` (via `.part` lalu `os.replace`),
   4. verifikasi opsional dengan `ffprobe`,
   5. catat baris untuk `index.csv`.
5. Tulis `index.csv` (UTF-8 dengan BOM agar rapi dibuka Excel).

## 6. Batasan

- **Versi bergantung pada data publik.** CgId baru yang belum ada di data akan masuk `vunknown`. Perbarui `data/cgid_versions.json` bila perlu.
- **Hanya video.** Tidak ada audio, subjudul, maupun voice pack.
- **Butuh resource video terunduh.** Kalau game belum lengkap, folder `Paks` bisa kosong.
- **Nama file mengikuti `CgName`.** Jika `CgName` kosong, dipakai `NA`; ID selalu disertakan agar unik.
- **`videodata` bersifat datamining.** Pemetaan versi adalah hasil komunitas, bukan API resmi Kuro Games.

## 7. Verifikasi manual

```bash
# lihat isi stream tanpa decode
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height -show_entries format=duration "Videos\v1.2\R0013_147_0.mp4"

# putar
ffplay "Videos\v1.2\R0013_147_0.mp4"
```

## Kredit

- Data versi/cutscene: `Arikatsu/WutheringWaves_Data`.
- Referensi alur ekstraksi: `SunsetMkt/WuWa-Cutscenes`.
- Pemeriksaan byte dan media: FFmpeg.
