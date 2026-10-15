"""Compare captured application output, never synthesized test signals."""
import argparse
from array import array
import json
import math
from pathlib import Path
import subprocess
import wave


def samples(path, out):
    converted = out / (path.parent.name + '-' + path.name)
    subprocess.run(['afconvert', '-f', 'WAVE', '-d', 'LEI16', str(path), str(converted)], check=True, capture_output=True)
    with wave.open(str(converted)) as wav:
        rate, channels = wav.getframerate(), wav.getnchannels()
        values = array('h', wav.readframes(wav.getnframes()))[::channels]
    nonzero = [i for i, value in enumerate(values) if value]
    spans = []
    if nonzero:
        start = previous = nonzero[0]
        for index in nonzero[1:]:
            if index - previous > rate // 2:
                spans.append(values[start:previous+1]);start = index
            previous = index
        spans.append(values[start:previous+1])
    return rate, spans


def compare(reference, candidate, out):
    rows, measurements = [], {}
    def check(name, actual, expected):
        rows.append({'id': name, 'actual': actual, 'expected': expected, 'status': 'pass' if actual == expected else 'fail'})
    receipts = {}
    for label, path in [('reference', reference), ('candidate', candidate)]:
        observed = json.loads((path / 'observed.json').read_text())
        check(label + '-driver-error', observed.get('error'), None)
        receipts[label] = {}
        for capture in observed.get('captures', []):
            phase = capture['phase'];receipt = json.loads((path / (phase + '.wav.json')).read_text())
            receipts[label][phase] = receipt
            check(label + '-' + phase + '-capture-error', receipt.get('failure'), None)
            check(label + '-' + phase + '-sampled', receipt['frames'] > 0, True)
            check(label + '-' + phase + '-microphone-disabled', receipt['microphone'], False)
            check(label + '-' + phase + '-explicit-owned-process-filter', receipt['filter_mode'], 'explicit_owned_process_objects')
            check(label + '-' + phase + '-capture-attributed', bool(receipt['captured_pids']) and set(receipt['captured_pids']) <= set(receipt['owned_pid_tree']), True)
            actions = receipt['real_browser_actions']
            check(label + '-' + phase + '-real-triggers', len(actions), 3 if observed.get('cue', 'pick') == 'pick' else 1)
            check(label + '-' + phase + '-triggers-in-recording', all(0 < a['elapsed_seconds_after_capture_ready'] < receipt['duration_seconds'] for a in actions), True)
            check(label + '-' + phase + '-output', receipt['peak'] == 0 and receipt['rms'] == 0 if phase == 'muted' else receipt['peak'] > 0 and receipt['rms'] > 0, True)
        check(label + '-phases', list(receipts[label]), list(receipts['reference']))
    for phase in receipts['reference']:
        a_rate, a = samples(reference / (phase + '.wav'), out)
        b_rate, b = samples(candidate / (phase + '.wav'), out)
        check(phase + '-sample-rate', b_rate, a_rate)
        check(phase + '-signal-events', len(b), len(a))
        measurements[phase] = {'reference_lengths': [len(s) for s in a], 'candidate_lengths': [len(s) for s in b], 'correlation': []}
        for first, second in zip(a, b):
            # Report continuous similarity; no post-hoc threshold declares parity.
            correlations = []
            for lag in [-1, 0, 1]:
                left, right = (first[-lag:], second) if lag < 0 else (first, second[lag:])
                length = min(len(left), len(right));left, right = left[:length], right[:length]
                energy = math.sqrt(sum(x*x for x in left) * sum(x*x for x in right))
                correlations.append({'lag_samples': lag, 'coefficient': sum(x*y for x,y in zip(left,right))/energy if energy else None})
            measurements[phase]['correlation'].append(correlations)
    return {'status': 'pass' if all(r['status'] == 'pass' for r in rows) else 'fail', 'rows': rows, 'measurements': measurements, 'scope': 'Actual owned-browser output, real cue triggers, sampled mute/restoration where present. Continuous waveform measurements do not certify all audio cues or physical speaker volume.'}


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--reference',required=True);p.add_argument('--observed',required=True);p.add_argument('--out',required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3];out=root/a.out;out.mkdir(parents=True,exist_ok=False)
    result=compare(root/a.reference,root/a.observed,out);(out/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':result['status'],'passed':sum(r['status']=='pass'for r in result['rows']),'total':len(result['rows']),'measurements':result['measurements']}));raise SystemExit(0 if result['status']=='pass'else 1)
