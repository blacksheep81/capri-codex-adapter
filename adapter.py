"""Inspect upstream Capri strips and pack separately approved Codex frames."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import urllib.request

from PIL import Image

REVISION = "d2876694bce524e37d89ea1bb043f34e431486e5"
BASE = f"https://raw.githubusercontent.com/lachydotmcg/capri-desktop/{REVISION}"
CLIPS = {
    "idle": (16, 8, "d4c4f0db71440fdf7be18f7ebecaa2241d25265f"),
    "blink": (4, 8, "9a8cda9b288ab4daacb0eddcadf59b3f61072e6b"),
    "grin": (16, 8, "f33768684af3ede1d3f30c141b810dd6045c3e8b"),
    "glitch": (10, 15, "b3383f98095c135025208a99313f87140328b598"),
    "dangle": (24, 10, "bb63c1ea5b9973693ed51df075cf945b6c7390d1"),
    "sleep": (16, 6, "ba8ef455a65b3faa4c2dc3292406c5244b9682ad"),
    "wake": (13, 15, "a53305d820cc85078b25b94d4d8a40167627f489"),
}
ROWS = {
    "idle": 6, "running-right": 8, "running-left": 8, "waving": 4,
    "jumping": 5, "failed": 8, "waiting": 6, "running": 6, "review": 6,
    "look-first": 8, "look-second": 8,
}


def read_strip(data, count):
    with Image.open(io.BytesIO(data)) as source:
        source.load()
        if source.width % count:
            raise ValueError("Strip width is not divisible by its documented frame count")
        image = source.convert("RGBA")
    width = image.width // count
    frames = [image.crop((i * width, 0, (i + 1) * width, image.height))
              for i in range(count)]
    if any(frame.getchannel("A").getbbox() is None for frame in frames):
        raise ValueError("Source contains an empty frame")
    return frames


def prepare(destination):
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        stage = Path(temporary) / "prepared"
        stage.mkdir()
        report = {"upstream": BASE, "revision": REVISION, "clips": {},
                  "ready_pet": False,
                  "reason": "Original clips are not Codex state animations. No automatic state substitution."}
        for name, (count, fps, expected) in CLIPS.items():
            request = urllib.request.Request(f"{BASE}/assets/sprites/{name}.png",
                                             headers={"User-Agent": "capri-codex-adapter"})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read(30 * 1024 * 1024 + 1)
            if len(data) > 30 * 1024 * 1024:
                raise ValueError("Source exceeds the download size limit")
            blob = b"blob " + str(len(data)).encode() + b"\0" + data
            if hashlib.sha1(blob).hexdigest() != expected:
                raise ValueError(f"Upstream content mismatch: {name}")
            frames = read_strip(data, count)
            folder = stage / name
            folder.mkdir()
            for index, frame in enumerate(frames):
                frame.save(folder / f"{index:02}.png")
            frames[0].save(stage / f"{name}.gif", save_all=True,
                           append_images=frames[1:], duration=round(1000 / fps),
                           loop=0, disposal=2)
            report["clips"][name] = {"frames": count, "fps": fps,
                                     "size": list(frames[0].size), "git_blob": expected}
        (stage / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        shutil.move(str(stage), destination)
    print(f"Prepared source clips only: {destination}")


def pack(frames_root, destination, pet_id, name):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", pet_id):
        raise ValueError("Pet ID must contain lowercase letters, numbers and hyphens")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    atlas = Image.new("RGBA", (1536, 2288))
    for row, (state, count) in enumerate(ROWS.items()):
        files = sorted((frames_root / state).glob("*.png"))
        if len(files) != count:
            raise ValueError(f"{state}: expected {count} approved PNG frames, got {len(files)}")
        for column, file in enumerate(files):
            with Image.open(file) as source:
                frame = source.convert("RGBA")
            if frame.size != (192, 208) or frame.getchannel("A").getbbox() is None:
                raise ValueError(f"Expected nonempty 192x208 frame: {file}")
            alpha = frame.getchannel("A")
            if alpha.getextrema()[0] != 0:
                raise ValueError(f"Frame needs a transparent background: {file}")
            if any(alpha.getpixel(p) for p in ((0, 0), (191, 0), (0, 207), (191, 207))):
                raise ValueError(f"Opaque frame corners: {file}")
            atlas.paste(frame, (column * 192, row * 208))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        stage = Path(temporary) / "package"
        stage.mkdir()
        atlas.save(stage / "spritesheet.webp", lossless=True)
        manifest = {"id": pet_id, "displayName": name,
                    "description": "Unofficial Capri fan adaptation.",
                    "spriteVersionNumber": 2, "spritesheetPath": "spritesheet.webp"}
        (stage / "pet.json").write_text(json.dumps(manifest, indent=2) + "\n")
        shutil.move(str(stage), destination)
    print("Packed candidate only. Geometry checked; motion/direction QA still required.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("prepare", help="Download pinned art and extract original clips")
    inspect.add_argument("--output", type=Path, default=Path("work/source"))
    build = commands.add_parser("pack", help="Pack already approved v2 frames; never invent missing states")
    build.add_argument("--frames", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--id", default="capri")
    build.add_argument("--name", default="Capri")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.output)
        else:
            pack(args.frames, args.output, args.id, args.name)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
