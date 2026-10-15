"""Record only the explicitly selected task-owned Safari output; no UI actions.

Current Codex drives the shared UI actions through CUA after ready.json appears.
The existing ScreenCaptureKit collector receives no AX action list.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
COLLECTOR = WORKSPACE / 'projects/duolingo-web/capture-owned-audio.swift'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', required=True, type=int)
    parser.add_argument('--out', required=True)
    parser.add_argument('--seconds', type=float, default=12)
    args = parser.parse_args()
    if args.pid <= 0 or not 5 <= args.seconds <= 30:
        parser.error('Explicit owned Safari PID and bounded 5–30 second capture required')
    command = subprocess.check_output(['ps', '-p', str(args.pid), '-o', 'comm='], text=True).strip()
    if Path(command).name != 'Safari':
        parser.error('This case captures only its task-owned Safari instance')
    output = (WORKSPACE / args.out).resolve()
    if not output.is_relative_to(ROOT / 'private'):
        parser.error('Raw application audio belongs in project private evidence')
    output.mkdir(parents=True, exist_ok=True)
    if any((output / name).exists() for name in ('output.wav', 'ready.json', 'failure.json', 'collector.log')):
        parser.error('Recorded evidence already exists; choose a new output directory')
    with (output / 'capture-request.json').open('x') as stream:
        json.dump({'owned_pid': args.pid, 'seconds': args.seconds,
                   'requested_unix_ms': time.time_ns() // 1_000_000}, stream)
    binary = ROOT / 'private/capture-owned-audio'
    subprocess.run(['swiftc', '-parse-as-library', str(COLLECTOR), '-o', str(binary)], check=True)
    wav = output / 'output.wav'
    process = subprocess.Popen([str(binary), str(args.pid), str(wav), str(args.seconds)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    first = process.stdout.readline().strip()
    if first != 'READY owned application audio capture':
        stdout, stderr = process.communicate()
        (output / 'failure.json').write_text(json.dumps({'stdout': first + stdout,
            'stderr': stderr, 'exit_code': process.returncode, 'result': 'unavailable'}, indent=2))
        raise RuntimeError('Owned application output capture did not become ready; preserve failure.json')
    ready = {'kind': 'owned_safari_audio_ready', 'owned_pid': args.pid,
             'ready_unix_ms': time.time_ns() // 1_000_000,
             'ready_utc': datetime.now(timezone.utc).isoformat(), 'duration_seconds': args.seconds,
             'collector': str(COLLECTOR.relative_to(WORKSPACE)),
             'collector_sha256': hashlib.sha256(COLLECTOR.read_bytes()).hexdigest(),
             'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
             'microphone': False, 'screen_frames': False,
             'capture_started_before_ready': True, 'ui_driver': 'Current Codex via CUA; no Swift AX actions'}
    (output / 'ready.json').write_text(json.dumps(ready, indent=2) + '\n')
    print(json.dumps({'ready': str((output / 'ready.json').relative_to(WORKSPACE))}), flush=True)
    stdout, stderr = process.communicate()
    (output / 'collector.log').write_text(first + '\n' + stdout + '\n' + stderr)
    if process.returncode:
        raise RuntimeError('Owned audio collector failed; preserve collector.log')
    result = json.loads(wav.with_suffix('.wav.json').read_text())
    if result.get('ui_actions'):
        raise RuntimeError('Collector must not drive native UI outside CUA')
    print(json.dumps({'frames': result['frames'], 'peak': result['peak'], 'rms': result['rms'],
                      'owned_pid': result['owned_pid'], 'microphone': result['microphone']}))


if __name__ == '__main__':
    main()
