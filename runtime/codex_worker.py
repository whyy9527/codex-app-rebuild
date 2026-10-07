"""Bounded Codex CLI source synthesis using existing authentication; no global configuration edits."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

SCHEMA = {'type': 'object', 'properties': {'source': {'type': 'string'}, 'rationale': {'type': 'string'}},
          'required': ['source', 'rationale'], 'additionalProperties': False}


def validate_reply(value):
    if not isinstance(value, dict) or set(value) != {'source', 'rationale'}:
        raise ValueError('expected source and rationale')
    if any(not isinstance(value[key], str) or not value[key].strip() for key in value):
        raise ValueError('nonempty source and rationale required')
    if len(value['source']) > 40000:
        raise ValueError('source exceeds contract limit')
    return value


def parse_attestation(stderr, model, effort):
    header = stderr.split('user\n', 1)[0][:10000]
    values = {}
    for field in ('model', 'provider', 'reasoning effort'):
        match = re.search(r'^' + re.escape(field) + r':\s*(.+)$', header, re.M)
        if not match:
            raise ValueError('missing runtime attestation: ' + field)
        values[field] = match[1].strip()
    if values['model'] != model or values['reasoning effort'] != effort:
        raise ValueError('runtime model or effort mismatch')
    return values


class CodexWorker:
    def __init__(self, *, model, effort='medium', timeout=180, receipt_path=None):
        self.model, self.effort, self.timeout = model, effort, timeout
        self.receipts = []
        self.receipt_path=Path(receipt_path) if receipt_path is not None else None

    def generate(self, prompt, *, role):
        began=time.monotonic()
        count=len(self.receipts)
        try:
            return self._generate(prompt,role=role)
        except BaseException as error:
            if len(self.receipts)==count:
                status='unavailable' if isinstance(error,OSError) else 'timeout' if isinstance(error,subprocess.TimeoutExpired) else 'invalid'
                self.receipts.append({'role':role,'status':status,'error_type':type(error).__name__,
                                      'requested_model':self.model,'requested_effort':self.effort,
                                      'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                                      'wall_seconds':round(time.monotonic()-began,6),
                                      'model_tokens':None,'model_cost':None})
            raise
        finally:
            if self.receipt_path is not None and len(self.receipts)>count:
                self.receipt_path.parent.mkdir(parents=True,exist_ok=True)
                with self.receipt_path.open('a') as stream:
                    for receipt in self.receipts[count:]: stream.write(json.dumps(receipt)+'\n')

    def _generate(self, prompt, *, role):
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='exploration-worker-') as folder:
            root = Path(folder)
            (root / 'schema.json').write_text(json.dumps(SCHEMA))
            command = ['codex', 'exec', '--ignore-user-config', '--skip-git-repo-check', '--ephemeral',
                       '--sandbox', 'read-only', '--color', 'never', '--model', self.model,
                       '-c', f'model_reasoning_effort="{self.effort}"', '-c', 'features.hooks=false',
                       '--output-schema', str(root / 'schema.json'), '--output-last-message', str(root / 'reply.json'), '-']
            process = subprocess.Popen(command, cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True, start_new_session=True)
            try:
                stdout, stderr = process.communicate(prompt, timeout=self.timeout)
            except BaseException:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
                raise
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if process.returncode:
                # Raw CLI output remains local to caller; never treat a failed call as a proposal.
                self.receipts.append({'role': role, 'status': 'fail', 'exit_code': process.returncode,
                                      'requested_model': self.model, 'requested_effort': self.effort,
                                      'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                                      'stderr_sha256': hashlib.sha256(stderr.encode()).hexdigest(),
                                      'wall_seconds': round(time.monotonic() - started, 6),
                                      'model_tokens': None, 'model_cost': None})
                raise RuntimeError('Codex worker failed; diagnostic digest retained')
            attestation = parse_attestation(stderr, self.model, self.effort)
            reply = validate_reply(json.loads((root / 'reply.json').read_text()))
            tokens = re.search(r'tokens used\s*\n\s*([\d,]+)', stdout + '\n' + stderr)
            receipt = {'role': role, 'status': 'pass', 'attestation': attestation,
                       'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                       'source_sha256': hashlib.sha256(reply['source'].encode()).hexdigest(),
                       'wall_seconds': round(time.monotonic() - started, 6),
                       'cli_reported_tokens': int(tokens[1].replace(',', '')) if tokens else None,
                       'model_cost': None, 'transport': 'existing ChatGPT-authenticated Codex CLI'}
            self.receipts.append(receipt)
            return {**reply, 'receipt': receipt}
