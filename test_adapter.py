import io
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from adapter import ROWS, pack, read_strip


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


if __name__ == "__main__":
    unittest.main()
