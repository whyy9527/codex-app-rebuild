"""Freeze observed responsive-web facts and retain strict, unmasked image results."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]


def private_path(value):
    path = (WORKSPACE / value).resolve()
    if not path.is_relative_to(ROOT / 'private'):
        raise ValueError('Mobile evidence must stay in project private')
    return path


def relative(path):
    return str(path.relative_to(WORKSPACE))


def observed_endpoint(ax, expected_scheme):
    field = next((line for line in ax.splitlines() if 'smart search field' in line), '')
    value = re.search(r'Value: (.*?)(?:, (?:ID|Placeholder):|$)', field)
    if not value:
        raise ValueError('Actual browser endpoint unavailable')
    url = value[1] if '://' in value[1] else expected_scheme + '://' + value[1]
    actual = urlsplit(url)
    return actual.scheme, actual.netloc, actual.path or '/', actual.query


def load_capture(value, protocol, source=False, source_query=None):
    path = private_path(value)
    raw = path.read_bytes()
    observed = json.loads(raw)
    prep = observed['preparation']
    endpoint = urlsplit(prep['url'])
    if source:
        if (endpoint.scheme, endpoint.netloc, endpoint.path) != ('https', 'www.bilibili.com', '/toy/LkvCZhw12wgT2Pqx/index.html'):
            raise ValueError('Actual original endpoint required')
    elif (endpoint.scheme, endpoint.hostname, endpoint.path) not in (
            ('http', '127.0.0.1', '/'), ('https', 's16.xinxiayiyan.com', '/')):
        raise ValueError('Owned candidate endpoint required')
    if source_query is not None and endpoint.query != source_query:
        raise ValueError('Original share query was not preserved')
    if set(observed['states']) != set(protocol['cases']):
        raise ValueError('Every observed mobile scene is required')
    viewport = protocol['viewport']
    if (prep['width'], prep['height']) != (viewport['width'], viewport['height']):
        raise ValueError('Prepared responsive viewport differs')
    states = {}
    for name, state in observed['states'].items():
        state = dict(state)
        ax = private_path(state['ax'])
        image = private_path(state['image'])
        actual_ax = ax.read_text()
        after = ax.with_name(ax.name.replace('.ax.txt', '.after.ax.txt'))
        if prep['windowUuid'] not in actual_ax or observed_endpoint(actual_ax, endpoint.scheme) != (
                endpoint.scheme, endpoint.netloc, endpoint.path or '/', endpoint.query):
            raise ValueError('Raw AX endpoint or owned window differs')
        if not after.exists():
            raise ValueError('Post-screenshot state observation missing')
        expected = {'Width': str(viewport['width']), 'Height': str(viewport['height']),
                    'Zoom Level': viewport['zoom'], 'Pixel Ratio': viewport['pixel_ratio']}
        if any(state['elements'][key]['value'] != val for key, val in expected.items()):
            raise ValueError('Actual responsive toolbar measurement differs')
        if state['interactions']['at_scroll_origin'] is not True:
            raise ValueError('Actual application scroll was not reset')
        with Image.open(image) as im:
            if list(im.size) != protocol['capture']['window_points']:
                raise ValueError('Raw screenshot does not match measured window geometry')
        state['ax'], state['image'] = relative(ax), relative(image)
        state['capture'] = {key: protocol['capture'][key] for key in
                            ('content_rect_points', 'backing_scale', 'window_points')}
        state['capture'].update(path=relative(image), state_consistent=True)
        state['raw_sha256'] = {relative(file): hashlib.sha256(file.read_bytes()).hexdigest()
                               for file in (ax, after, image)}
        states[name] = state
    return {'states': states, 'preparation': prep,
            'raw_observation_sha256': hashlib.sha256(raw).hexdigest()}, endpoint.query


def freeze(source, protocol):
    requirements = []
    for name, state in source['states'].items():
        evidence = [state['ax']]
        for i, text in enumerate(state['accessible_text']):
            requirements.append({'id': f'{name}.text.{i}', 'state': name,
                                 'kind': 'accessible_text', 'text': text, 'evidence': evidence})
        for element, value in state['elements'].items():
            requirements.append({'id': name + '.value.' + element, 'state': name,
                                 'kind': 'element_value', 'element': element,
                                 'value': value['value'], 'evidence': evidence})
        for field, value in state['interactions'].items():
            requirements.append({'id': name + '.' + field, 'state': name,
                                 'kind': 'interaction_boolean', 'field': field,
                                 'expected': value, 'evidence': evidence})
        requirements.append({'id': name + '.pixels', 'state': name, 'kind': 'image_pixels',
                             'reference_image': state['image'],
                             'pixels': protocol['capture']['content_rect_points'][2:],
                             'reference_capture': state['capture'], 'evidence': [state['image']]})
    return {'schema_version': 1, 'scope': protocol['scope'],
            'source_observation_sha256': source['raw_observation_sha256'],
            'requirements': requirements}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    protocol = json.loads((ROOT / 'mobile.json').read_text())
    source, query = load_capture(args.reference, protocol, source=True)
    candidate, _ = load_capture(args.candidate, protocol, source_query=query)
    contract = freeze(source, protocol)
    out = private_path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    for filename, data in [('contract.json', contract), ('source.json', source), ('candidate.json', candidate)]:
        (out / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'states': len(source['states']), 'requirements': len(contract['requirements']),
                      'scope': protocol['scope']}))


if __name__ == '__main__':
    main()
