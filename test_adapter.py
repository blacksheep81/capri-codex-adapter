import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from adapter import ROWS, pack, read_strip
from preview import render


class AdapterTests(unittest.TestCase):
    def test_strip_preserves_order_and_pixels(self):
        image = Image.new("RGBA", (4, 2), (255, 0, 0, 255))
        image.paste((0, 255, 0, 255), (2, 0, 4, 2))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        frames = read_strip(buffer.getvalue(), 2)
        self.assertEqual(frames[1].getpixel((0, 0)), (0, 255, 0, 255))
        with self.assertRaises(ValueError):
            read_strip(buffer.getvalue(), 3)

    def test_missing_states_block_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                pack(root, root / "output", "capri", "Capri")
            self.assertFalse((root / "output").exists())

    def test_pack_geometry_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for state, count in ROWS.items():
                folder = root / "frames" / state
                folder.mkdir(parents=True)
                for i in range(count):
                    frame = Image.new("RGBA", (192, 208))
                    frame.putpixel((90 + i, 100), (255, 255, 255, 255))
                    frame.save(folder / f"{i:02}.png")
            out = root / "capri"
            pack(root / "frames", out, "capri", "Capri")
            self.assertEqual(json.loads((out / "pet.json").read_text())["spriteVersionNumber"], 2)
            with Image.open(out / "spritesheet.webp") as atlas:
                self.assertEqual(atlas.size, (1536, 2288))
                self.assertIsNone(atlas.crop((6 * 192, 0, 8 * 192, 208)).getbbox())
            with self.assertRaises(FileExistsError):
                pack(root / "frames", out, "capri", "Capri")

    def test_preview_uses_exact_atlas_pixels(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            atlas = Image.new("RGBA", (1536, 2288))
            atlas.putpixel((50, 50), (255, 0, 0, 255))
            path = root / "atlas.png"
            atlas.save(path)
            with patch("preview.subprocess.run") as encode:
                render(path, root / "preview")
                encode.assert_called_once()
            with Image.open(root / "preview/frames/idle/00.png") as frame:
                self.assertEqual(frame.getpixel((50, 50)), (255, 0, 0, 255))
            self.assertTrue((root / "preview/idle-jump-idle.gif").exists())
            with self.assertRaises(FileExistsError):
                render(path, root / "preview")


if __name__ == "__main__":
    unittest.main()
