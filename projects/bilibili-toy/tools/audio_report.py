"""Inspect actual PID-filtered PCM and CUA triggers; keep waveform equality separate.

NumPy/SciPy are optional local analysis dependencies. No synthetic tone is used
as evidence, and a nonzero recording never becomes a full sound-fidelity pass.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from urllib.parse import urlsplit
import re

import numpy as np
from scipy.signal import correlate, correlation_lags

WORKSPACE = Path(__file__).resolve().parents[3]


def same_endpoint(actual, expected):
    return (actual.scheme, actual.netloc, actual.path or '/') == (expected.scheme, expected.netloc, expected.path or '/')


def read_float_wav(path):
    raw = path.read_bytes()
    if raw[:4] != b'RIFF' or raw[8:12] != b'WAVE':
        raise ValueError('Expected actual RIFF WAVE output')
    fmt = data = None
    offset = 12
    while offset + 8 <= len(raw):
        name, size = struct.unpack_from('<4sI', raw, offset)
        body = raw[offset + 8:offset + 8 + size]
        if len(body) != size:
            raise ValueError('Incomplete recording chunk')
        if name == b'fmt ':
            fmt = struct.unpack_from('<HHIIHH', body)
        elif name == b'data':
            data = body
        offset += 8 + size + size % 2
    if fmt is None or data is None:
        raise ValueError('Actual recording has no format or samples')
    code, channels, rate, _, alignment, bits = fmt
    if code != 3 or bits != 32 or alignment != channels * 4:
        raise ValueError('Expected collector IEEE float32 PCM')
    samples = np.frombuffer(data, dtype='<f4').reshape(-1, channels)
    if not np.isfinite(samples).all():
        raise ValueError('Non-finite PCM samples')
    return samples, rate, hashlib.sha256(raw).hexdigest()


def trigger_stamps(ready, actions):
    if [a['action'] for a in actions] != ['play', 'pause']:
        raise ValueError('Actual play and pause actions required')
    stamps = [actions[0]['before_unix_ms'], actions[0]['after_unix_ms'],
              actions[1]['before_unix_ms'], actions[1]['after_unix_ms']]
    if stamps != sorted(stamps) or not ready['ready_unix_ms'] < stamps[0] < stamps[-1] < ready['ready_unix_ms'] + ready['duration_seconds'] * 1000:
        raise ValueError('UI actions were not wholly inside the actual capture interval')
    return stamps


def inspect_capture(directory):
    ready = json.loads((directory / 'ready.json').read_text())
    system = json.loads((directory / 'output.wav.json').read_text())
    actions = json.loads((directory / 'actions.json').read_text())
    prepared = (directory / 'prepared.ax.txt').read_text()
    playing = (directory / 'playing.ax.txt').read_text()
    paused = (directory / 'paused.ax.txt').read_text()
    stamps = trigger_stamps(ready, actions)
    preparation = json.loads((directory / 'preparation.json').read_text())
    address = next((s for s in prepared.splitlines() if 'smart search field' in s or 'Address and search bar' in s), '')
    value = re.search(r'Value: ([^,\n]*)', address)
    expected_url = urlsplit(preparation['url'])
    actual_url = urlsplit(value[1] if value and '://' in value[1] else expected_url.scheme + '://' + (value[1] if value else ''))
    if not same_endpoint(actual_url, expected_url):
        raise ValueError('Prepared AX does not belong to the requested endpoint')
    if system.get('microphone') is not False or system.get('filter_mode') != 'application' or system.get('owned_pid') != ready['owned_pid'] or system.get('ui_actions'):
        raise ValueError('Wrong capture ownership, microphone mode, or non-CUA actions')
    if 'button 暂停, Help:' not in playing or 'button 播放, Help:' not in paused:
        raise ValueError('Actual player did not enter and leave playback')
    enabled = 'button 静音, Help:' in prepared
    if not enabled and 'button 开启音效, Help:' not in prepared:
        raise ValueError('Source-owned sound state unavailable')
    samples, rate, digest = read_float_wav(directory / 'output.wav')
    if len(samples) == 0 or len(samples) != system['frames'] or samples.size != system['samples']:
        raise ValueError('Actual sampled frames are missing or disagree with collector')
    peak = float(np.abs(samples).max())
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    headline = next((line.strip().split(' text ', 1)[-1] for line in prepared.splitlines()
                     if 'text AI 模拟 Claude Opus 5.5' in line), None)
    result = {'kind': 'owned_audio_observation', 'wav_sha256': digest, 'sample_rate': rate,
              'endpoint_url': preparation['url'],
              'channels': samples.shape[1], 'frames': len(samples), 'peak': peak, 'rms': rms,
              'sound_enabled_observed': enabled, 'prepared_player_headline': headline,
              'actions_inside_capture': True, 'microphone': False, 'owned_pid': system['owned_pid'],
              'playback_bounds_ms': [stamps[2] - stamps[1], stamps[3] - stamps[0]],
              'trigger_output_status': 'pass' if (peak > 0 if enabled else peak == 0) else 'fail',
              'scope': 'Actual output presence/mute during observed BP playback, not all sound types or sound identity.'}
    if 'observed_sound_before_toggle' in preparation:
        before = (directory / 'sound-before-toggle.ax.txt').read_text()
        observed_before = 'button 静音, Help:' in before
        if observed_before != preparation['observed_sound_before_toggle']:
            raise ValueError('Pre-toggle sound observation disagrees with its raw AX')
        result['sound_enabled_before_toggle'] = observed_before
        result['restored_from_observed_mute'] = not observed_before and enabled
    return result, samples, rate


def first_burst(samples, rate):
    # Pure BP oscillator cues have actual zero gaps. Twenty milliseconds joins
    # waveform zero crossings and output-quantum gaps, not separate cue events.
    active = np.flatnonzero(np.any(samples != 0, axis=1))
    if not len(active):
        raise ValueError('No actual sound burst')
    breaks = np.flatnonzero(np.diff(active) > int(rate * .02))
    last = active[breaks[0]] if len(breaks) else active[-1]
    return samples[active[0]:last + 1].astype(np.float64), int(active[0])


def waveform_measurement(source, candidate, rate):
    a, a_start = first_burst(source, rate)
    b, b_start = first_burst(candidate, rate)
    if a.shape[1] != b.shape[1]:
        raise ValueError('Recording channel counts differ')
    channels = []
    for channel in range(a.shape[1]):
        x, y = a[:, channel], b[:, channel]
        correlation = correlate(x, y, mode='full', method='fft')
        lags = correlation_lags(len(x), len(y), mode='full')
        index = int(np.argmax(correlation))
        lag = int(lags[index])
        x_offset, y_offset = max(0, lag), max(0, -lag)
        length = min(len(x) - x_offset, len(y) - y_offset)
        xx, yy = x[x_offset:x_offset + length], y[y_offset:y_offset + length]
        denom = np.linalg.norm(xx) * np.linalg.norm(yy)
        channels.append({'channel': channel, 'alignment_samples': lag,
                         'overlap_samples': length,
                         'cosine_similarity': float(np.dot(xx, yy) / denom) if denom else None,
                         'rms_difference': float(np.sqrt(np.mean((xx - yy) ** 2))),
                         'max_absolute_difference': float(np.abs(xx - yy).max())})
    return {'kind': 'first_bp_burst_waveform_measurement',
            'source_start_seconds': a_start / rate, 'candidate_start_seconds': b_start / rate,
            'source_frames': len(a), 'candidate_frames': len(b),
            'exact_same_samples': bool(a.shape == b.shape and np.array_equal(a, b)),
            'channels': channels, 'acceptance': 'measurement_only',
            'limit': 'Actual isolated first cue only. No tolerance chosen to claim full sequence, all sound types, or physical speaker equivalence.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--candidate')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    def path(value):
        resolved = (WORKSPACE / value).resolve()
        if not resolved.is_relative_to(WORKSPACE / 'projects/bilibili-toy/private'):
            parser.error('Raw audio analysis must stay in private evidence')
        return resolved
    source, a, rate = inspect_capture(path(args.source))
    report = {'source': source}
    if args.candidate:
        candidate, b, other_rate = inspect_capture(path(args.candidate))
        if other_rate != rate:
            raise ValueError('Sample rates differ; no resampling to force comparison')
        report['candidate'] = candidate
        report['same_prepared_player_headline'] = source['prepared_player_headline'] == candidate['prepared_player_headline']
        report['same_observed_sound_state'] = source['sound_enabled_observed'] == candidate['sound_enabled_observed']
        if source['sound_enabled_observed'] and candidate['sound_enabled_observed']:
            report['waveform'] = waveform_measurement(a, b, rate)
    with path(args.out).open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
