"""Freeze source-derived audio behavior facts from real completed captures."""
import argparse
import hashlib
import json
from pathlib import Path

from .audio_report import inspect_capture, waveform_measurement

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]


def private_path(value):
    path = (WORKSPACE / value).resolve()
    if not path.is_relative_to(ROOT / 'private'):
        raise ValueError('Audio evidence must stay in project private')
    return path


def facts(observation, include_restore=False):
    interactions = {'sampled_frames_present': observation['frames'] > 0,
                    'actions_inside_capture': observation['actions_inside_capture'],
                    'sound_enabled': observation['sound_enabled_observed'],
                    'audio_detected': observation['peak'] > 0,
                    'microphone_used': observation['microphone']}
    if include_restore:
        interactions['restored_from_observed_mute'] = observation['restored_from_observed_mute']
    return {'accessible_text': [observation['prepared_player_headline']],
            'elements': {'sample_rate': {'value': str(observation['sample_rate'])},
                         'channels': {'value': str(observation['channels'])}},
            'interactions': interactions, 'audio_observation': observation}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--captures', required=True, help='Private map of actual source/candidate capture directories')
    parser.add_argument('--out', required=True, help='New private frozen-evidence directory')
    args = parser.parse_args()
    raw = private_path(args.captures).read_bytes()
    captures = json.loads(raw)
    protocol = json.loads((ROOT / 'audio.json').read_text())
    cases = {case['id']: case for case in protocol['cases']}
    if set(captures) != set(cases):
        raise ValueError('Every observed audio case is required; missing/extra cases rejected')
    source, candidate, measurements, requirements = {}, {}, {}, []
    for name, case in cases.items():
        row = captures[name]
        a, pcm_a, rate_a = inspect_capture(private_path(row['source']))
        b, pcm_b, rate_b = inspect_capture(private_path(row['candidate']))
        if not a['endpoint_url'].startswith('https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html') or b['endpoint_url'] != 'http://127.0.0.1:4617/':
            raise ValueError('Actual original and candidate endpoint provenance required')
        for observation in (a, b):
            if observation['sound_enabled_observed'] != case['sound_enabled']:
                raise ValueError('Requested source-owned audio prestate not observed')
            if 'sound_before_toggle' in case and observation.get('sound_enabled_before_toggle') != case['sound_before_toggle']:
                raise ValueError('Actual persisted mute prestate not observed')
        source[name], candidate[name] = facts(a, 'sound_before_toggle' in case), facts(b, 'sound_before_toggle' in case)
        evidence = [row['source'] + '/' + leaf for leaf in
                    ('prepared.ax.txt', 'playing.ax.txt', 'paused.ax.txt', 'actions.json', 'ready.json', 'output.wav', 'output.wav.json')]
        for field, expected in source[name]['interactions'].items():
            requirements.append({'id': name + '.' + field, 'state': name, 'kind': 'interaction_boolean',
                                 'field': field, 'expected': expected, 'evidence': evidence})
        for element, value in source[name]['elements'].items():
            requirements.append({'id': name + '.' + element, 'state': name, 'kind': 'element_value',
                                 'element': element, 'value': value['value'], 'evidence': evidence})
        for index, text in enumerate(source[name]['accessible_text']):
            requirements.append({'id': name + '.scene.' + str(index), 'state': name,
                                 'kind': 'accessible_text', 'text': text, 'evidence': evidence})
        if case['sound_enabled']:
            if rate_a != rate_b:
                raise ValueError('Sample rates differ; no resampling to force equality')
            measurements[name] = waveform_measurement(pcm_a, pcm_b, rate_a)
    output = private_path(args.out)
    output.mkdir(parents=True, exist_ok=False)
    contract = {'schema_version': 1, 'source_capture_map_sha256': hashlib.sha256(raw).hexdigest(),
                'scope': protocol['scope'], 'requirements': requirements}
    for filename, data in [('contract.json', contract), ('source.json', {'states': source}),
                           ('candidate.json', {'states': candidate}), ('waveform-measurements.json', measurements)]:
        (output / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'requirements': len(requirements), 'states': list(cases),
                      'scope': 'Observed BP output/mute/restoration only; waveform identity remains a separate measurement'}))


if __name__ == '__main__':
    main()
