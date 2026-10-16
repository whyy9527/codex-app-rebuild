"""Reject stale, incomplete or misattributed fiction before a build is served."""
import hashlib
import json
from run_fiction import ROOT, cases_for, digest, strict_json, validate
from run_api_models import PROVIDERS


def validate_dataset(value, channel, context, event, forecast_bytes):
    expected_model = 'gpt-6.1-sol' if channel == 'codex' else PROVIDERS[channel]['model']
    if value['kind'] != 'fiction' or value['channel'] != channel or value['runtime_attestation']['model'] != expected_model:raise ValueError('Fiction runtime identity mismatch')
    if value['event_source_sha256'] != event['source_sha256'] or value['context_sha256'] != digest(context) or value['forecast_sha256'] != hashlib.sha256(forecast_bytes).hexdigest():raise ValueError('Fiction inputs are stale')
    cases = cases_for(channel)
    if set(value['cases']) != set(cases) or any(row['input'] != cases[key] for key, row in value['cases'].items()):raise ValueError('Fiction cannot override deterministic simulated results')
    validate({key: {field: row[field] for field in ['headline', 'summary', 'bp', 'maps', 'players']} for key, row in value['cases'].items()}, cases, context)


def main():
    context = strict_json((ROOT / 'data/fiction-context.json').read_text());event = strict_json((ROOT / 'data/event.json').read_text())
    forecasts = strict_json((ROOT / 'data/model-forecasts.json').read_text());manifest = strict_json((ROOT / 'data/model-fiction.json').read_text())
    for channel, filename in manifest.items():
        if channel not in forecasts or '/' in filename:raise ValueError('Unknown fiction channel/path')
        value = strict_json((ROOT / 'data' / filename).read_text())
        validate_dataset(value, channel, context, event, (ROOT / 'data' / forecasts[channel]).read_bytes())
    print('Verified fiction datasets:', len(manifest))


if __name__ == '__main__':main()
