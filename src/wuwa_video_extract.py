#!/usr/bin/env python3
"""Extract and organize Wuthering Waves cutscene videos.

The video resource files (``Video_<id>-HD-WindowsNoEditor.pak``) are plain
MP4 files with a small 53-byte wrapper at the front. This tool strips that
wrapper, verifies the result with ffprobe, groups the videos by the game
version they first appeared in, and writes an ``index.csv``.

Only the Python standard library is required. ffprobe is optional and is
only used to verify codec/resolution/duration.

The tool never writes to the game directory: the source .pak files are opened
in read-only mode and all output goes to the ``--out`` directory.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_SRC = Path("Client/Saved/Resources/Video/hd/Paks")
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "cgid_versions.json"
FTYP = b"ftyp"
PROBE_SIZE = 64 * 1024


def log(msg: str = "") -> None:
    print(msg, flush=True)


def resolve_game_dir(raw: str | None) -> Path:
    """Return the directory that contains ``Client``."""
    if raw is None:
        candidates = [Path.cwd(), Path.cwd() / "Wuthering Waves Game"]
    else:
        base = Path(raw).expanduser().resolve()
        candidates = [base, base / "Wuthering Waves Game"]

    for cand in candidates:
        if (cand / "Client").is_dir():
            return cand
        if (cand / "Wuthering Waves Game" / "Client").is_dir():
            return cand / "Wuthering Waves Game"

    raise SystemExit(
        "Tidak bisa menemukan folder game. Berikan path yang berisi 'Client', "
        "contoh: --game \"D:\\Game\\Wuthering Waves\\Wuthering Waves Game\""
    )


def load_versions(path: Path) -> dict[str, dict]:
    if not path.is_file():
        raise SystemExit(f"File data versi tidak ditemukan: {path}")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh).get("videos", {})


def find_pak(folder: Path) -> Path | None:
    paks = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".pak")
    return paks[0] if paks else None


def extract(pak_path: Path, out_path: Path) -> bool:
    """Copy the MP4 payload (from 'ftyp') to ``out_path``. Read-only on source."""
    with pak_path.open("rb") as src:
        head = src.read(PROBE_SIZE)
        idx = head.find(FTYP)
        if idx < 4:
            return False
        offset = idx - 4
        src.seek(offset)
        tmp = out_path.with_suffix(out_path.suffix + ".part")
        try:
            with tmp.open("wb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            os.replace(tmp, out_path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
    return True


def probe(path: Path) -> dict | None:
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    proc = subprocess.run(
        [exe, "-v", "error", "-show_entries", "stream=codec_name,width,height",
         "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    video = next((s for s in data.get("streams", []) if s.get("width")), {})
    return {
        "codec": video.get("codec_name", ""),
        "width": video.get("width", ""),
        "height": video.get("height", ""),
        "duration_s": round(float(data.get("format", {}).get("duration", 0) or 0), 2),
    }


def safe_name(value: str) -> str:
    cleaned = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in str(value))
    return cleaned.strip("_") or "NA"


def collect_folders(src: Path) -> list[Path]:
    folders = []
    for entry in src.iterdir():
        if not entry.is_dir():
            continue
        try:
            int(entry.name.split("_")[0])
        except ValueError:
            continue
        folders.append(entry)
    return sorted(folders, key=lambda p: int(p.name.split("_")[0]))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract Wuthering Waves cutscene videos (.pak -> .mp4) and group them by version.",
    )
    parser.add_argument("--game", help="Folder game (yang berisi 'Client'). Contoh: ...\\Wuthering Waves Game")
    parser.add_argument("--out", default="Videos", help="Folder output (default: ./Videos)")
    parser.add_argument("--data", default=str(DATA_FILE), help="File JSON pemetaan versi")
    parser.add_argument("--samples", type=int, metavar="N", help="Hanya proses N video pertama (untuk uji coba)")
    parser.add_argument("--force", action="store_true", help="Ekstrak ulang walaupun file output sudah ada")
    parser.add_argument("--no-index", action="store_true", help="Jangan tulis index.csv")
    parser.add_argument("--dry-run", action="store_true", help="Tampilkan rencana tanpa menulis file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    game_dir = resolve_game_dir(args.game)
    src = game_dir / DEFAULT_SRC
    if not src.is_dir():
        raise SystemExit(
            f"Folder video tidak ditemukan: {src}\n"
            "Pastikan game sudah diunduh lengkap dan path --game benar."
        )

    versions = load_versions(Path(args.data))
    folders = collect_folders(src)
    if args.samples is not None:
        folders = folders[: max(args.samples, 0)]
    if not folders:
        log("Tidak ada paket video yang ditemukan.")
        return 1

    out_root = Path(args.out).expanduser().resolve()
    have_ffprobe = shutil.which("ffprobe") is not None
    if not have_ffprobe:
        log("[info] ffprobe tidak ditemukan; metadata codec/resolusi/durasi dilewati.")

    if args.dry_run:
        counts: dict[str, int] = {}
        for folder in folders:
            cid = folder.name.split("_")[0]
            ver = versions.get(cid, {}).get("version", "unknown")
            counts[ver] = counts.get(ver, 0) + 1
        log(f"Game : {game_dir}")
        log(f"Sumber: {src}")
        log(f"Output: {out_root}")
        log(f"Total : {len(folders)} video")
        for ver in sorted(counts):
            log(f"  v{ver}: {counts[ver]}")
        return 0

    out_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    ok = failed = skipped = 0

    for n, folder in enumerate(folders, 1):
        folder_id = folder.name
        cid = folder_id.split("_")[0]
        meta = versions.get(cid, {})
        version = meta.get("version", "unknown")
        name = safe_name(meta.get("cg_name") or "NA")
        out_dir = out_root / f"v{version}"
        out_path = out_dir / f"{name}_{folder_id}.mp4"

        if out_path.exists() and out_path.stat().st_size > 1024 and not args.force:
            skipped += 1
        else:
            pak = find_pak(folder)
            if pak is None:
                log(f"[{n}/{len(folders)}] SKIP {folder_id}: .pak tidak ada")
                failed += 1
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            if not extract(pak, out_path):
                log(f"[{n}/{len(folders)}] FAIL {folder_id}: MP4 payload tidak ditemukan")
                failed += 1
                continue

        info = probe(out_path) or {}
        rows.append({
            "id": folder_id,
            "version": version,
            "cg_name": name,
            "cg_file": meta.get("cg_file", ""),
            "girl_or_boy": meta.get("girl_or_boy", ""),
            "codec": info.get("codec", ""),
            "width": info.get("width", ""),
            "height": info.get("height", ""),
            "duration_s": info.get("duration_s", ""),
            "size_mb": round(out_path.stat().st_size / 1048576, 2),
            "file": os.path.relpath(out_path, out_root),
        })
        ok += 1

        if n % 10 == 0 or n == len(folders):
            log(f"[{n}/{len(folders)}] ok={ok} skip={skipped} fail={failed} last={out_path.name}")

    if not args.no_index and rows:
        index_path = out_root / "index.csv"
        with index_path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        log(f"index: {index_path}")

    log(f"\nSelesai: {ok} ok, {skipped} dilewati, {failed} gagal -> {out_root}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
