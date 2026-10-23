import tempfile
import unittest
from pathlib import Path

from scrubname import find_roms, main, scrub


class ScrubTests(unittest.TestCase):
    def test_strips_region_rev_and_dump_tags(self):
        self.assertEqual(scrub("Super Mario World (USA) (Rev 1)"), "Super Mario World")
        self.assertEqual(scrub("Pokemon - Red Version (USA, Europe) [!]"), "Pokemon - Red Version")
        self.assertEqual(scrub("Metroid (Europe) (En,Fr)"), "Metroid")
        self.assertEqual(scrub("Legend of Zelda, The (USA)"), "Legend of Zelda, The")

    def test_keeps_disc_and_track_tags(self):
        self.assertEqual(scrub("Final Fantasy VII (USA) (Disc 1)"), "Final Fantasy VII (Disc 1)")
        self.assertEqual(scrub("Crash Bandicoot (USA) (Track 02)"), "Crash Bandicoot (Track 02)")

    def test_never_returns_empty(self):
        self.assertEqual(scrub("(USA)"), "(USA)")


class RenameTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def touch(self, name, text=""):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, newline="")
        return path

    def names(self):
        return sorted(p.name for p in self.dir.iterdir())

    def test_renames_roms_and_ignores_other_files(self):
        self.touch("Tetris (World) (Rev A).gb")
        self.touch("notes (USA).txt")
        main([str(self.dir), "-y"])
        self.assertEqual(self.names(), ["Tetris.gb", "notes (USA).txt"])

    def test_skips_collisions(self):
        self.touch("Tetris (Japan).gb")
        self.touch("Tetris (World) (Rev A).gb")
        main([str(self.dir), "-y"])
        self.assertEqual(self.names(), ["Tetris (World) (Rev A).gb", "Tetris.gb"])

    def test_dry_run_changes_nothing(self):
        self.touch("Tetris (World).gb")
        main([str(self.dir), "-n"])
        self.assertEqual(self.names(), ["Tetris (World).gb"])

    def test_rewrites_cue_file_lines(self):
        self.touch("Crash (USA) (Track 01).bin")
        self.touch("Crash (USA).cue", 'FILE "Crash (USA) (Track 01).bin" BINARY\r\n  TRACK 01 MODE2/2352\r\n')
        main([str(self.dir), "-y"])
        cue = (self.dir / "Crash.cue").read_bytes().decode()
        self.assertEqual(cue, 'FILE "Crash (Track 01).bin" BINARY\r\n  TRACK 01 MODE2/2352\r\n')

    def test_recursive_flag(self):
        self.touch("sub/Metroid (Europe).nes")
        self.assertEqual(find_roms(self.dir, recursive=False), [])
        self.assertEqual(len(find_roms(self.dir, recursive=True)), 1)


if __name__ == "__main__":
    unittest.main()
