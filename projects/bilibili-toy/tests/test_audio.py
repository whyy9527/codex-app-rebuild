"""Collector-format and timed-trigger guards; synthetic data is never product evidence."""
import importlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
from urllib.parse import urlsplit


@unittest.skipUnless(importlib.util.find_spec('numpy') and importlib.util.find_spec('scipy'),
                     'Optional local audio analysis dependencies unavailable')
class AudioEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = importlib.import_module('projects.bilibili-toy.tools.audio_report')

    def test_output_format_is_read_and_integer_pcm_is_not_reinterpreted_as_float(self):
        data = struct.pack('<4f', 0, .25, -.5, 0)
        fmt = struct.pack('<HHIIHH', 3, 2, 48000, 384000, 8, 32)
        body = b'WAVEfmt ' + struct.pack('<I', len(fmt)) + fmt + b'data' + struct.pack('<I', len(data)) + data
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'format.wav'
            path.write_bytes(b'RIFF' + struct.pack('<I', len(body)) + body)
            samples, rate, _ = self.report.read_float_wav(path)
            self.assertEqual(rate, 48000)
            self.assertEqual(samples.tolist(), [[0, .25], [-.5, 0]])
            path.write_bytes(path.read_bytes().replace(fmt, struct.pack('<HHIIHH', 1, 2, 48000, 192000, 4, 16)))
            with self.assertRaisesRegex(ValueError, 'float32'):
                self.report.read_float_wav(path)

    def test_expired_or_missing_actions_cannot_turn_sampled_silence_into_mute_evidence(self):
        ready = {'ready_unix_ms': 1000, 'duration_seconds': 10}
        actions = [{'action': 'play', 'before_unix_ms': 2000, 'after_unix_ms': 2500},
                   {'action': 'pause', 'before_unix_ms': 5000, 'after_unix_ms': 5500}]
        self.assertEqual(self.report.trigger_stamps(ready, actions), [2000, 2500, 5000, 5500])
        with self.assertRaises(ValueError):
            self.report.trigger_stamps(ready, [])
        with self.assertRaisesRegex(ValueError, 'capture interval'):
            self.report.trigger_stamps(ready, [actions[0], {**actions[1], 'after_unix_ms': 11000}])

    def test_elided_root_slash_is_equivalent_but_different_origins_and_paths_fail(self):
        expected = urlsplit('http://127.0.0.1:4617/')
        self.assertTrue(self.report.same_endpoint(urlsplit('http://127.0.0.1:4617'), expected))
        for value in ('https://127.0.0.1:4617/', 'http://127.0.0.1:4618/', 'http://127.0.0.1:4617/other'):
            self.assertFalse(self.report.same_endpoint(urlsplit(value), expected))


if __name__ == '__main__':
    unittest.main()
