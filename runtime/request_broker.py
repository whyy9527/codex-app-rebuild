"""Host model request/response transport; does not claim to invoke a model API."""
import hashlib
import json
from pathlib import Path
from capabilities.exploration.ledger import digest
from runtime.codex_worker import validate_reply


class NeedsResponse(BaseException):
    def __init__(self, path):
        self.path = Path(path)
        super().__init__('model response required: ' + self.path.name)


class FileWorker:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.receipts = []

    def generate(self, prompt, *, role):
        binding = {'prompt': prompt, 'role': role}
        identifier = digest(binding)
        request = {**binding, 'request_digest': identifier,
                   'transport': 'interactive-codex-main-session'}
        path = self.directory / (identifier + '.json')
        response = path.with_suffix('.response.json')
        if path.exists() and json.loads(path.read_text()) != request:
            raise ValueError('request contents changed')
        if not path.exists():
            path.write_text(json.dumps(request, indent=2, ensure_ascii=False) + '\n')
        if not response.exists():
            raise NeedsResponse(path)
        value = json.loads(response.read_text())
        if value.pop('request_digest', None) != identifier:
            raise ValueError('response does not bind to requested feedback')
        reply = validate_reply(value)
        receipt = {'role': role, 'request_digest': identifier,
                   'source_sha256': hashlib.sha256(reply['source'].encode()).hexdigest(),
                   'transport': 'interactive-codex-main-session', 'runtime_model': None,
                   'model_tokens': None, 'model_cost': None,
                   'attestation': 'response artifact only; model identity and token usage not independently measured'}
        self.receipts.append(receipt)
        return {**reply, 'receipt': receipt}
