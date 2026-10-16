"""Dynamic original captures must not become artificial passing pixel contracts."""
from importlib import import_module
import unittest


class MajorPageContract(unittest.TestCase):
    def test_desktop_geometry_and_fixed_build_cannot_drift(self):
        import copy
        import json
        from pathlib import Path
        module = import_module('projects.bilibili-toy.tools.major_pages_probe')
        protocol = json.loads((Path(__file__).parents[1]/'major-pages-desktop.json').read_text())
        ax = '''0 standard window Web Inspector — www.bilibili.com
1 row (selected) <div class="ticker ticker-closed">
2 text height : 38px
3 text border-top-width : 1px
4 text box-sizing : border-box
5 text 1194 × 37'''
        module.validate_ticker(ax, 'source', protocol, 'https://www.bilibili.com/')
        for changed in (ax.replace('38px', '45px'), ax.replace('www.bilibili.com', 'other.example')):
            with self.assertRaises(ValueError):
                module.validate_ticker(changed, 'source', protocol, 'https://www.bilibili.com/')
        broken = copy.deepcopy(protocol)
        broken['regions']['business']['source'][3] -= 1
        with self.assertRaises(ValueError):
            module.validate_ticker(ax, 'source', broken, 'https://www.bilibili.com/')
        frame = 'https://www.bilibilitoy.com/toy/LkvCZhw12wgT2Pqx/43482999941120-v26947/index.html'
        module.validate_source_build(frame, '43482999941120-v26947')
        with self.assertRaises(ValueError):
            module.validate_source_build(frame.replace('26947', '26934'), '43482999941120-v26947')

    def test_unstable_source_is_pending_without_requiring_candidate_instability(self):
        module = import_module('projects.bilibili-toy.tools.major_pages_probe')
        state = {'interactions': {'repeat_pixels_identical': False, 'at_scroll_origin': True},
                 'capture': {'path': 'source.png', 'content_rect_points': [0, 0, 375, 667]},
                 'accessible_text': ['Actual original text']}
        source = {'states': {'leaderboard.business': state},
                  'records': {'leaderboard': [{'ax': 'source.ax.txt'}]}}
        result = module.freeze(source, {'scope': 'test'})['requirements']
        self.assertEqual(result[0]['kind'], 'pending')
        self.assertFalse(any(x.get('field') == 'repeat_pixels_identical' for x in result))
        self.assertEqual(next(x for x in result if x['kind'] == 'accessible_text')['text'], 'Actual original text')
        state['interactions']['repeat_pixels_identical'] = True
        result = module.freeze(source, {'scope': 'test'})['requirements']
        self.assertEqual(result[0]['kind'], 'image_pixels')
        self.assertEqual(result[0]['reference_image'], 'source.png')


if __name__ == '__main__':
    unittest.main()
