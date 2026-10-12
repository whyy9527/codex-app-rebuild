"""Read actual shared-query captures for the frontend mold; never drive or pass UI."""
import argparse
import json
import re
from PIL import Image
from capabilities.rebuild.contracts import local_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--captures', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    from pathlib import Path
    root = Path(args.workspace).resolve()
    captures = local_file(root, args.captures, must_exist=False)
    observed = {'states': {}}
    for state, relative in {'student-baseline':'number/number-baseline',
                            'student-number':'number/number-result',
                            'student-empty':'no-match/no-match-result'}.items():
        ax = (captures/(relative+'.ax.txt')).read_text()
        image_path = captures/(relative+'.png')
        texts, elements = [], {}
        for line in ax.splitlines():
            match = re.match(r'^\s*\d+ (text|button|link)(?: \([^)]*\))? (.*)$', line)
            if match:
                role, name = match.groups()
                name = re.split(r", (?:Value|Help): ", name)[0]
                texts.append(name)
                if role in ('button', 'link') and name in ('查询', '重置'):
                    elements[name] = {'role': role}
        with Image.open(image_path) as image:
            pixels = list(image.size)
        observed['states'][state] = {'accessible_text':texts, 'elements':elements,
            'capture_pixels':pixels, 'capture': {
                'path':image_path.relative_to(root).as_posix(),
                'content_rect_points':[4,80,1462,749], 'backing_scale':2,
                'window_points':[1470,833]},
            'evidence':(captures/(relative+'.ax.txt')).relative_to(root).as_posix()}
    with local_file(root,args.out,must_exist=False).open('x') as stream:
        json.dump(observed,stream,ensure_ascii=False,indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
