from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from scripts.data_generation.watchhumans_synthetic import (
    ARCHETYPES, OUTPUT_CSV, generate_watch_humans_dataset, save_watch_humans_dataset,
)

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'data_generation' / 'watchhumans_synthetic.py'


class WatchHumansTests(unittest.TestCase):
    def test_repeatable_valid_data(self):
        df = generate_watch_humans_dataset(20)
        pd.testing.assert_frame_equal(df, generate_watch_humans_dataset(20))
        self.assertTrue(df.human_id.is_unique)
        self.assertTrue(df.age.between(18, 55).all())
        for archetype in ARCHETYPES:
            self.assertTrue(df[f'{archetype}_score'].between(0, 1).all())
        self.assertTrue(OUTPUT_CSV.is_absolute())

    def test_csv_roundtrip_and_failed_write_preserves_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'nested' / 'data.csv'
            df = generate_watch_humans_dataset(5)
            save_watch_humans_dataset(df, path)
            pd.testing.assert_frame_equal(df, pd.read_csv(path), check_dtype=False)
            original = path.read_bytes()
            with patch.object(pd.DataFrame, 'to_csv', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    save_watch_humans_dataset(df, path)
            self.assertEqual(original, path.read_bytes())
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_cli_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'output' / 'humans.csv'
            subprocess.run([sys.executable, str(SCRIPT), '--rows', '3', '--output', str(output)], cwd=folder, check=True, capture_output=True)
            self.assertEqual(len(pd.read_csv(output)), 3)

    def test_import_does_not_generate_or_save(self):
        with tempfile.TemporaryDirectory() as folder:
            code = f"""import runpy
from unittest.mock import patch
import pandas as pd
with patch.object(pd.DataFrame, 'to_csv', side_effect=AssertionError('unexpected write')):
    runpy.run_path({str(SCRIPT)!r})
"""
            subprocess.run([sys.executable, '-c', code], cwd=folder, check=True, capture_output=True)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_invalid_size(self):
        for n in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                generate_watch_humans_dataset(n)
