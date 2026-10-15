"""Freeze/observe actual mobile PNG facts; compare with the common frontend CLI."""
import argparse
import hashlib
import json
import re
from urllib.parse import urlsplit
from PIL import Image, ImageChops
from .visual_probe import ROOT, WORKSPACE, private_path, relative, ax_facts, inspector_provenance, validate_lossless_image
from capabilities.rebuild.images import srgb_image


def observe(directory, side, protocol, url):
    spec = protocol[side]
    header = directory / spec['header_evidence']
    header_ax = header.read_text()
    if 'standard window Web Inspector — ' + urlsplit(url).hostname not in header_ax:
        raise ValueError('Actual header inspector belongs to another origin')
    match = re.search(r'--header-height:[^0-9]*([0-9.]+)px', header_ax)
    if not match or float(match[1]) != spec['header_css']:
        raise ValueError('Actual header measurement differs')
    transformation_files = []
    if side == 'source':
        for proof in protocol.get('source_node_deletions', []):
            before, after = [directory / proof[name] for name in ('before', 'after')]
            for path in (before, after):
                if 'standard window Web Inspector — www.bilibili.com' not in path.read_text():
                    raise ValueError('Original DOM deletion inspector unavailable')
            if not re.search(proof['node_pattern'], before.read_text()) or re.search(proof['node_pattern'], after.read_text()):
                raise ValueError('Requested original DOM deletion not observed')
            transformation_files.extend([before, after, directory / proof['menu']])
    records, crops, identity = [], {}, None
    facts = None
    for stem in spec['frames']:
        before, after, image = [directory / (stem + suffix) for suffix in ('.ax.txt', '.after.ax.txt', '.png')]
        if protocol.get('author_removed') and any(re.search(r'container .*AI 区新人 UP', p.read_text()) for p in (before, after)):
            raise ValueError('Requested author deletion not preserved')
        first = ax_facts(before.read_text(), url, spec, protocol, identity)
        last = ax_facts(after.read_text(), url, spec, protocol, first['uuid'])
        if first != last or not first['at_scroll_origin']:
            raise ValueError('Actual mobile page state or scroll origin changed')
        identity = first['uuid']
        if facts is not None and facts != first:
            raise ValueError('Actual mobile repeated facts differ')
        facts = first
        provenance = inspector_provenance(directory, stem, url)
        inspector_ax = provenance[0].read_text()
        expected_box = r'\d+ text ' + str(spec['width_css']) + r'\s+×\s+' + str(protocol['height_css']) + r'$'
        if not re.search(expected_box, inspector_ax, re.M):
            raise ValueError('Actual inspected body CSS box differs from toolbar')
        with Image.open(image) as im:
            validate_lossless_image(im, spec['viewport_pixels'][2:])
            rgb = srgb_image(im)
            for name, regions in protocol['regions'].items():
                x, y, w, h = regions[side]
                if x < 0 or y < 0 or x+w > im.width or y+h > im.height:
                    raise ValueError('Declared complete region exceeds actual PNG')
                crops.setdefault(name, []).append(rgb.crop((x, y, x+w, y+h)))
        files = [before, after, image, header, *provenance, *transformation_files]
        records.append({'image': relative(image), 'ax': relative(before), 'after_ax': relative(after),
                        'sha256': {relative(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}})
    states = {}
    for name, regions in protocol['regions'].items():
        stable = all(ImageChops.difference(crops[name][0], crop).getbbox() is None for crop in crops[name][1:])
        states[name] = {'capture': {'path': records[0]['image'], 'content_rect_points': regions[side],
                                  'backing_scale': 1, 'window_points': spec['viewport_pixels'][2:], 'state_consistent': True},
                        'interactions': {'repeat_pixels_identical': stable, 'at_scroll_origin': True},
                        'accessible_text': facts['texts'] if name == 'business' else []}
    return {'states': states, 'records': records, 'window_uuid': identity, 'actual_header_css': spec['header_css']}


def freeze(source, protocol):
    requirements = []
    for name, state in source['states'].items():
        if not state['interactions']['repeat_pixels_identical']:
            raise ValueError('Source region repeat is unstable: ' + name)
        requirements.append({'id': name+'.pixels', 'state': name, 'kind': 'image_pixels',
                             'reference_image': state['capture']['path'], 'pixels': protocol['regions'][name]['source'][2:],
                             'reference_capture': state['capture'], 'evidence': [state['capture']['path']]})
        for field, value in state['interactions'].items():
            requirements.append({'id': name+'.'+field, 'state': name, 'kind': 'interaction_boolean',
                                 'field': field, 'expected': value, 'evidence': [source['records'][0]['ax']]})
        for i, text in enumerate(state['accessible_text']):
            requirements.append({'id': name+'.text.'+str(i), 'state': name, 'kind': 'accessible_text',
                                 'text': text, 'evidence': [source['records'][0]['ax']]})
    return {'schema_version': 1, 'scope': protocol['scope'], 'requirements': requirements}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['freeze', 'observe'])
    parser.add_argument('--captures', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--candidate-url', help='Optional local loopback root for prepublication acceptance')
    parser.add_argument('--protocol', choices=['mobile-png.json', 'user-removal-png.json', 'user-removal-desktop.json'], default='mobile-png.json')
    args = parser.parse_args()
    protocol = json.loads((ROOT/args.protocol).read_text())
    original = (ROOT/'private/original-share-entry-url.txt').read_text().strip()
    url = original if args.mode == 'freeze' else 'https://s16.xinxiayiyan.com/?' + urlsplit(original).query
    if args.candidate_url:
        endpoint = urlsplit(args.candidate_url)
        if args.mode != 'observe' or endpoint.scheme != 'http' or endpoint.hostname != '127.0.0.1' or endpoint.path != '/' or endpoint.query or endpoint.fragment:
            raise ValueError('Only an explicit local loopback root is allowed')
        url = args.candidate_url + '?' + urlsplit(original).query
    facts = observe(private_path(args.captures), 'source' if args.mode == 'freeze' else 'candidate', protocol, url)
    output = private_path(args.out)
    if args.mode == 'freeze':
        output.mkdir()
        (output/'source.json').write_text(json.dumps(facts, ensure_ascii=False, indent=2))
        contract = freeze(facts, protocol)
        (output/'contract.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2))
        print(json.dumps({'requirements': len(contract['requirements'])}))
    else:
        with output.open('x') as stream:
            json.dump(facts, stream, ensure_ascii=False, indent=2)
        print(json.dumps({'states': len(facts['states'])}))


if __name__ == '__main__':
    main()
