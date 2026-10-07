"""Portable evidence projection; raw records stay local and are not rewritten."""
from copy import deepcopy
import hashlib
import re
from capabilities.exploration.ledger import digest, verify_records

LOCAL_PATH = re.compile(r"/(?:Users|opt|Library|private|var|tmp|usr|Applications)/[^\s'\"\\,)\]]+")


def redact(value):
    if isinstance(value, str):
        return LOCAL_PATH.sub('<local-path>', value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def portable_records(records):
    verify_records(records)
    projected = []
    for original in records:
        record = redact(deepcopy(original))
        record.pop('_integrity', None)
        evaluation = record.get('evaluation')
        provenance = {'raw_record_digest': digest(original), 'projection': 'local-path-redacted-v1'}
        if evaluation:
            provenance['raw_output_sha256'] = original['evaluation']['output_sha256']
            provenance['raw_evaluator_digest'] = original['evaluation']['evaluator_digest']
            evaluation['output_sha256'] = hashlib.sha256(evaluation['output'].encode()).hexdigest()
            evaluation['output_scope'] = 'path-redacted projection; output_bytes refers to raw execution'
            evaluation['evaluator_digest'] = digest({'command': evaluation['command'], 'tests': {
                key: value for key, value in evaluation['source_files'].items() if key.startswith('tests/')}})
        record['export_provenance'] = provenance
        record['_integrity'] = {'prefix': digest(projected), 'content': digest(record)}
        projected.append(record)
    verify_records(projected)
    return projected
