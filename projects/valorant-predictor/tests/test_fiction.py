import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_fiction import ROOT, strict_json
from validate_fiction import validate_dataset


class FictionIntegrity(unittest.TestCase):
    def setUp(self):
        self.context = json.loads((ROOT / 'data/fiction-context.json').read_text())
        self.event = json.loads((ROOT / 'data/event.json').read_text())
        self.forecast = (ROOT / 'data/gpt-6.1-sol-forecast.json').read_bytes()
        self.value = json.loads((ROOT / 'data/codex-fiction.json').read_text())

    def check(self, value, forecast=None):validate_dataset(value, 'codex', self.context, self.event, self.forecast if forecast is None else forecast)

    def test_actual_model_output_is_bound_to_engine(self):
        manifest = json.loads((ROOT / 'data/model-fiction.json').read_text())
        forecasts = json.loads((ROOT / 'data/model-forecasts.json').read_text())
        for channel, filename in manifest.items():
            with self.subTest(channel=channel):
                value = json.loads((ROOT / 'data' / filename).read_text())
                validate_dataset(value, channel, self.context, self.event, (ROOT / 'data' / forecasts[channel]).read_bytes())

    def test_model_identity_cannot_be_borrowed_from_another_provider(self):
        value = copy.deepcopy(self.value)
        value['runtime_attestation']['model'] = 'mimo-v2.6-pro'
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):self.check(value)

    def test_stale_forecast_is_rejected_even_if_results_look_same(self):
        with self.assertRaisesRegex(ValueError, 'stale'):self.check(self.value, self.forecast + b' ')

    def test_duplicate_case_keys_are_rejected_before_parsing(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):strict_json('{"case":{},"case":{}}')

    def test_missing_case_and_unknown_player_are_rejected(self):
        value = copy.deepcopy(self.value);value['cases'].pop(next(iter(value['cases'])))
        with self.assertRaises(ValueError):self.check(value)
        value = copy.deepcopy(self.value);row = next(iter(value['cases'].values()));row['players']['fake:player'] = {'rating': 10, 'comment': '虚构的未知选手不允许混入名单'}
        with self.assertRaises(ValueError):self.check(value)

    def test_fiction_cannot_rewrite_winner_or_mvp_team(self):
        value = copy.deepcopy(self.value);row = next(iter(value['cases'].values()));row['input']['series']['winner'] = 'UNKNOWN'
        with self.assertRaises(ValueError):self.check(value)
        value = copy.deepcopy(self.value);row = next(iter(value['cases'].values()));row['maps']['0']['mvp'] = next(p for p in row['players'] if not p.startswith(row['input']['series']['maps'][0]['winner'] + ':'))
        with self.assertRaises(ValueError):self.check(value)

    def test_out_of_range_rating_and_impossible_map_text_are_rejected(self):
        value = copy.deepcopy(self.value);row = next(iter(value['cases'].values()));next(iter(row['players'].values()))['rating'] = float('nan')
        with self.assertRaises(ValueError):self.check(value)
        value = copy.deepcopy(self.value);row = next(iter(value['cases'].values()));row['maps']['0']['story'] += ' 该图回合比分13比99。'
        with self.assertRaises(ValueError):self.check(value)


if __name__ == '__main__':unittest.main()
