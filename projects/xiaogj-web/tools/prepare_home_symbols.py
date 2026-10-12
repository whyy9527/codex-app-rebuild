"""Prepare an observed DOM SVG sprite for external SVG use; keep the source intact."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

SVG_NS = 'http://www.w3.org/2000/svg'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = ET.fromstring(args.source.read_bytes())
    if root.tag == 'svg':
        root.set('xmlns', SVG_NS)
    elif root.tag != '{' + SVG_NS + '}svg':
        raise ValueError('Expected an observed SVG root')
    data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    reparsed = ET.fromstring(data)
    if reparsed.tag != '{' + SVG_NS + '}svg':
        raise ValueError('External sprite lacks the SVG namespace')
    if not reparsed.findall('{' + SVG_NS + '}symbol'):
        raise ValueError('External sprite contains no SVG symbols')
    if args.out.exists() and args.out.read_bytes() == data:
        return
    with args.out.open('xb') as output:
        output.write(data)


if __name__ == '__main__':
    main()
