# wuwa-cutscene-extractor

[Bahasa Indonesia](README.md) | **English**

Extract **Wuthering Waves** cutscenes from the game's `.pak` bundles into regular `.mp4` files, then organize them automatically into **per-version folders** with an `index.csv`.

> **Disclaimer:** this tool only reads your own local game files. It does not modify game files, ships no copyrighted media, and contains no AES keys. All Wuthering Waves assets belong to Kuro Games. Use it for personal purposes (e.g. your own cutscene archive) and respect the applicable Terms of Service.

## Why this works without AES / FModel

The video files under `Client/Saved/Resources/Video/hd/Paks/<id>/Video_<id>-HD-WindowsNoEditor.pak` are **not Unreal Engine archives**. Each one is a complete **MP4 file** wrapped in a **53-byte header**:

```text
[ 53-byte game wrapper ][ real MP4 (starts at the 'ftyp' box) ]
```

Stripping the first 53 bytes is all it takes. No decryption, no AES key. Technical details: [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md).

## Features

- Auto-detects the game's video folder.
- Extracts MP4 by removing the 53-byte wrapper.
- Groups videos into `v<version>` folders using `CgId` (first version the cutscene appeared in).
- Names files `CutsceneName_Id.mp4`.
- Writes `index.csv` with version, name, original asset path, codec, resolution, duration, size.
- Optional verification with `ffprobe`.
- `--dry-run`, `--samples`, `--force`, and resume support (existing outputs are skipped).
- **Python standard library only** — no pip dependencies.
- **Never writes to the game folder.** `.pak` files are opened read-only; all output goes to `--out`.

## Requirements

- Windows (tested on Windows 10/11 with Python 3.13).
- Python 3.9+.
- `ffmpeg`/`ffprobe` **optional** — only used to fill codec/resolution/duration in `index.csv`.
- A fully downloaded Wuthering Waves install (video resources present).

## Install

```bash
git clone https://github.com/RyuuZev/wuwa-cutscene-extractor.git
cd wuwa-cutscene-extractor
```

No `pip install` needed.

## Usage

Dry run first (writes nothing):

```bash
python src/wuwa_video_extract.py --game "D:\Game\Wuthering Waves\Wuthering Waves Game" --dry-run
```

Try a few videos:

```bash
python src/wuwa_video_extract.py --game "D:\Game\Wuthering Waves\Wuthering Waves Game" --out "D:\Game\Wuthering Waves\Videos" --samples 5
```

Extract everything:

```bash
python src/wuwa_video_extract.py --game "D:\Game\Wuthering Waves\Wuthering Waves Game" --out "D:\Game\Wuthering Waves\Videos"
```

### Options

| Option | Description |
|---|---|
| `--game PATH` | Game folder containing `Client`. If omitted, the current directory and its `Wuthering Waves Game` subfolder are tried. |
| `--out PATH` | Output folder. Default `./Videos`. |
| `--data PATH` | Version mapping file. Default `data/cgid_versions.json`. |
| `--samples N` | Process only the first `N` videos (useful for testing). |
| `--force` | Re-extract even if the output already exists. |
| `--no-index` | Do not write `index.csv`. |
| `--dry-run` | Print the plan without writing files. |

### Output layout

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

### `index.csv` columns

| Column | Content |
|---|---|
| `id` | Original folder name, e.g. `147_0` (the number is the `CgId`). |
| `version` | First version the cutscene appeared in, e.g. `1.2`. |
| `cg_name` | Cutscene name from game data, e.g. `R0013`. |
| `cg_file` | Original asset path inside the game. |
| `girl_or_boy` | Protagonist variant flag (0/1). |
| `codec`, `width`, `height`, `duration_s` | `ffprobe` metadata (empty if ffprobe is missing). |
| `size_mb` | MP4 file size. |
| `file` | Relative output path, e.g. `v1.2\R0013_147_0.mp4`. |

## Example result

On a full 3.7 install (165 video bundles, ~12.45 GB):

| Version | Videos | Version | Videos | Version | Videos |
|---|---:|---|---:|---|---:|
| 1.2 | 5 | 2.7 | 28 | 3.3 | 12 |
| 1.3 | 1 | 2.8 | 5 | 3.4 | 4 |
| 1.4 | 3 | 3.0 | 18 | 3.5 | 14 |
| 2.0 | 6 | 3.1 | 17 | 3.6 | 7 |
| 2.1 | 5 | 3.2 | 4 | 3.7 | 12 |
| 2.3 | 6 |   |   |   |   |
| 2.6 | 18 |   |   |   |   |

Numbers may vary depending on your game version and the voice/resolution packs you downloaded.

## No audio in the videos?

That is expected. WuWa video files are **video-only** (a single H.264 track, no audio). Cutscene audio is played separately by the game engine from Wwise banks. This repo focuses on video extraction; muxing audio is a separate job (see [`SunsetMkt/WuWa-Cutscenes`](https://github.com/SunsetMkt/WuWa-Cutscenes)).

## Troubleshooting

- **"Cannot find the game folder"** — point `--game` at the folder that contains `Client`, usually `...\Wuthering Waves Game`.
- **"Video folder not found"** — run the game once so resources are fully downloaded.
- **`ffprobe` not found** — metadata in `index.csv` stays empty, but extraction still works. Install ffmpeg for full metadata.
- **A video lands in `vunknown`** — its `CgId` is missing from `data/cgid_versions.json` (usually a newer game version than the data). Refresh the data or ignore it.
- **0 videos found** — check the path and make sure `Client/Saved/Resources/Video/hd/Paks` contains numbered subfolders.

## How it works (short)

1. Enumerate subfolders of `Saved/Resources/Video/hd/Paks`.
2. Read the leading number of each folder name (e.g. `147_0` → `147` = `CgId`).
3. Open the `.pak` read-only, find the `ftyp` marker, and copy from 4 bytes before `ftyp` to end of file (dropping the 53-byte header).
4. Look up the `CgId` in `data/cgid_versions.json` to get its version and cutscene name.
5. Write to `Videos/v<version>/<Name>_<Id>.mp4` and summarize in `index.csv`.

Full write-up: [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md).

## Credits

- `CgId` → version/name data: [`Arikatsu/WutheringWaves_Data`](https://github.com/Arikatsu/WutheringWaves_Data) (branches 0.7–3.7).
- Cutscene/audio extraction reference: [`SunsetMkt/WuWa-Cutscenes`](https://github.com/SunsetMkt/WuWa-Cutscenes).
- Media verification: [FFmpeg](https://ffmpeg.org/).

## License

Code: [MIT](LICENSE). Game assets (video, audio, cutscene names) remain the property of Kuro Games and are **not** covered by this license.
