"""Render review artifacts from the exact encoded v2 candidate, without redrawing it."""

import argparse
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw
from adapter import ROWS


def render(atlas_path, output):
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    with Image.open(atlas_path) as source:
        atlas = source.convert("RGBA")
    if atlas.size != (1536, 2288):
        raise ValueError("Expected a 1536x2288 v2 candidate")
    output.mkdir(parents=True)
    clips = {}
    all_frames = []
    for row, (state, count) in enumerate(ROWS.items()):
        folder = output / "frames" / state
        folder.mkdir(parents=True)
        frames = []
        for column in range(count):
            cell = atlas.crop((column * 192, row * 208, (column + 1) * 192, (row + 1) * 208))
            cell.save(folder / f"{column:02}.png")
            canvas = Image.new("RGB", (192, 240), (238, 238, 238))
            canvas.paste(cell, (0, 24), cell)
            ImageDraw.Draw(canvas).text((6, 6), f"{state} {column}", fill="black")
            frames.append(canvas)
        clips[state] = frames
        if row < 9:
            all_frames.extend(frames)
        frames[0].save(output / f"{state}.gif", save_all=True,
                       append_images=frames[1:], duration=160, loop=0)
    sequences = {
        "all-states": all_frames,
        "idle-jump-idle": clips["idle"] + clips["jumping"] + clips["idle"],
        "look-loop": clips["look-first"] + clips["look-second"],
    }
    for name, frames in sequences.items():
        frames[0].save(output / f"{name}.gif", save_all=True,
                       append_images=frames[1:], duration=160, loop=0)
    for index in (0, 6, 22, 26):
        all_frames[index].save(output / f"still-{index:02}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(output / "all-states.gif"),
                    "-movflags", "+faststart", "-pix_fmt", "yuv420p",
                    str(output / "all-states.mp4")], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("atlas", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.atlas, args.output)
