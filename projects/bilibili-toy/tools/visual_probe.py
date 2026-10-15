"""Re-derive a scoped visual probe from immutable native AX and screenshots."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from PIL import Image, ImageChops
from capabilities.rebuild.frontend import compare
from capabilities.rebuild.images import srgb_image

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]


def private_path(value):
    path = (WORKSPACE / value).resolve()
    if not path.is_relative_to(ROOT / 'private'):
        raise ValueError('Visual evidence must remain private')
    return path


def relative(path):
    return str(path.relative_to(WORKSPACE))


def measure_sampling(spec, protocol):
    width, height = spec['viewport_pixels'][2:]
    scale = protocol['actual_samples_per_css_pixel']
    if width != spec['width_css'] * scale or height != protocol['height_css'] * scale:
        raise ValueError('Actual screenshot sampling differs from the declared CSS viewport')
    return scale


def ax_facts(ax, expected_url, spec, protocol, window_uuid=None):
    identity = re.search(r'UUID=([A-Fa-f0-9-]+)', ax)
    if not identity or (window_uuid and identity[1] != window_uuid):
        raise ValueError('Owned visual window differs')
    field = next((line for line in ax.splitlines() if 'smart search field' in line), '')
    value = re.search(r'Value: (.*?)(?:, (?:ID|Placeholder):|$)', field)
    if not value:
        raise ValueError('Actual browser address unavailable')
    address = value[1] if '://' in value[1] else 'https://' + value[1]
    if urlsplit(address) != urlsplit(expected_url):
        raise ValueError('Actual visual endpoint or share query differs')
    for label, expected in [('Width', str(spec['width_css'])), ('Height', str(protocol['height_css'])),
                            ('Zoom Level', protocol['zoom_label']), ('Pixel Ratio', protocol['pixel_ratio_label'])]:
        if not re.search(r'Description: ' + re.escape(label) + r', Value: ' + re.escape(expected) + r'$', ax, re.M):
            raise ValueError('Actual visual toolbar differs: ' + label)
    lines = ax.splitlines()
    start = next((i for i, line in enumerate(lines) if protocol['scene_heading'] in line), -1)
    end = next((i for i, line in enumerate(lines) if i > start and 'button 展开 AI 模拟速报' in line), -1)
    if start < 0 or end < 0:
        raise ValueError('Complete static visual scene unavailable')
    scope = '\n'.join(lines[start:end + 1])
    if re.search(r'\(showing \d+-\d+ of \d+ items\)', scope):
        raise ValueError('Visual AX scope is truncated')
    texts = [re.sub(r'\s+', ' ', re.sub(r'^\s*\d+ text ', '', line)).strip()
             for line in lines[start:end] if re.match(r'^\s*\d+ text ', line)]
    scroll = re.findall(r'scroll bar \(settable, float\) ([0-9.]+)', ax)
    return {'uuid': identity[1], 'texts': texts, 'at_scroll_origin': bool(scroll) and all(float(x) == 0 for x in scroll)}


def inspector_provenance(directory, stem, expected_url):
    inspector = directory / (stem + '.inspector.ax.txt')
    saved = directory / (stem + '.save.ax.txt')
    ax = inspector.read_text()
    hostname = urlsplit(expected_url).hostname
    if ('standard window Web Inspector — ' + hostname not in ax or
            not re.search(r'row \(selected(?:,[^)]*)?\) Description: <body', ax)):
        raise ValueError('Owned inspector body selection unavailable')
    save_ax = saved.read_text()
    if ('Value: ' + stem + '.png' not in save_ax or
            'Value: ' + directory.name not in save_ax or 'ID: save-panel' not in save_ax):
        raise ValueError('Owned PNG save destination unavailable')
    return [inspector, saved]


def observe(directory, side, protocol, url, window_uuid=None):
    spec = protocol[side]
    measure_sampling(spec, protocol)
    records = []
    for stem in spec['frames']:
        extension = protocol.get('image_extension', '.jpg')
        before, after, image = [directory / (stem + suffix) for suffix in ('.ax.txt', '.after.ax.txt', extension)]
        lossless = protocol.get('image_space') == 'inspector_body'
        provenance = inspector_provenance(directory, stem, url) if lossless else []
        first = ax_facts(before.read_text(), url, spec, protocol, window_uuid)
        last = ax_facts(after.read_text(), url, spec, protocol, first['uuid'])
        if first != last:
            raise ValueError('Static source/candidate facts changed around capture')
        with Image.open(image) as im:
            window = spec['viewport_pixels'][2:] if lossless else protocol['window_pixels']
            if list(im.size) != window:
                raise ValueError('Native window image dimensions differ')
            if lossless and im.format != 'PNG':
                raise ValueError('Lossless evidence must be actual PNG')
            rect = spec['body_business_pixels'] if lossless else spec['business_pixels']
            x, y, w, h = rect
            crop = srgb_image(im).crop((x, y, x + w, y + h))
        capture = {'path': relative(image), 'content_rect_points': rect, 'backing_scale': 1,
                   'window_points': window, 'state_consistent': True}
        records.append({'facts': first, 'crop': crop, 'capture': capture, 'ax': relative(before), 'after_ax': relative(after),
                        'sha256': {relative(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in (before, after, image, *provenance)}})
    stable = all(all(hi == 0 for lo, hi in ImageChops.difference(records[0]['crop'], record['crop']).getextrema()) for record in records[1:])
    state = {'capture': records[0]['capture'], 'accessible_text': records[0]['facts']['texts'],
             'interactions': {'at_scroll_origin': records[0]['facts']['at_scroll_origin'], 'repeat_pixels_identical': stable},
             'elements': {'iframe_size': {'rect': [0, 0, *spec['iframe_pixels'][2:]]}}}
    return {'states': {'method-main': state}, 'window_uuid': records[0]['facts']['uuid'],
            'records': [{k: v for k, v in record.items() if k != 'crop'} for record in records]}


def freeze(source, protocol):
    state = source['states']['method-main']
    if not all(state['interactions'].values()):
        raise ValueError('Stable source pixels at scroll origin required for this static probe')
    evidence = [source['records'][0]['ax'], source['records'][0]['after_ax']]
    requirements = [{'id': 'method-main.pixels', 'state': 'method-main', 'kind': 'image_pixels',
                     'reference_image': state['capture']['path'], 'pixels': protocol['source']['business_pixels'][2:],
                     'reference_capture': state['capture'], 'evidence': [state['capture']['path']]},
                    {'id': 'method-main.iframe-size', 'state': 'method-main', 'kind': 'element_geometry',
                     'element': 'iframe_size', 'rect': state['elements']['iframe_size']['rect'], 'tolerance_points': 0,
                     'evidence': [state['capture']['path']]}]
    for field, expected in state['interactions'].items():
        requirements.append({'id': 'method-main.' + field, 'state': 'method-main', 'kind': 'interaction_boolean',
                             'field': field, 'expected': expected, 'evidence': evidence})
    for i, text in enumerate(state['accessible_text']):
        requirements.append({'id': 'method-main.text.' + str(i), 'state': 'method-main', 'kind': 'accessible_text',
                             'text': text, 'evidence': evidence})
    return {'schema_version': 1, 'scope': protocol['scope'], 'requirements': requirements}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--lossless', action='store_true', help='Use actual Safari inspector body PNG evidence')
    args = parser.parse_args()
    protocol = json.loads((ROOT / ('visual-png.json' if args.lossless else 'visual.json')).read_text())
    original = (ROOT / 'private/original-share-entry-url.txt').read_text().strip()
    endpoint = urlsplit(original)
    if (endpoint.scheme, endpoint.netloc, endpoint.path) != ('https', 'www.bilibili.com', '/toy/LkvCZhw12wgT2Pqx/index.html'):
        raise ValueError('Actual original entry required')
    candidate = 'https://s16.xinxiayiyan.com/?' + urlsplit(original).query
    directory, out = private_path(args.captures), private_path(args.out)
    source = observe(directory, 'source', protocol, original)
    contract = freeze(source, protocol)
    public = observe(directory, 'candidate', protocol, candidate, source['window_uuid'])
    out.mkdir()
    results = {'source': compare(WORKSPACE, contract, source), 'public': compare(WORKSPACE, contract, public)}
    for name, data in [('protocol', protocol), ('contract', contract), ('source', source), ('public', public),
                       ('source-result', results['source']), ('public-result', results['public'])]:
        (out / (name + '.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({name: {status: sum(row['status'] == status for row in result['rows'])
                            for status in ('pass', 'fail', 'not_run', 'unavailable')} for name, result in results.items()}))


if __name__ == '__main__':
    main()
