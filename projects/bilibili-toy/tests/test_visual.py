import importlib.util
from pathlib import Path
import unittest
import tempfile

MODULE = Path(__file__).resolve().parents[1] / 'tools/visual_probe.py'
SPEC = importlib.util.spec_from_file_location('visual_probe', MODULE)
visual = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(visual)


class VisualPreparation(unittest.TestCase):
    def setUp(self):
        self.url = 'https://www.bilibili.com/toy/test/index.html?plat_id=620'
        self.protocol = {'height_css': 600, 'actual_samples_per_css_pixel': 2,
                         'zoom_label': '( 100% )', 'pixel_ratio_label': '2x',
                         'scene_heading': 'heading S16 · AI 赛制介绍, Value: 1'}
        self.spec = {'width_css': 1200, 'viewport_pixels': [124, 298, 2400, 1200]}
        self.ax = f'''0 standard window Task, UUID=ABC-123
1 text field Description: smart search field, Value: {self.url}, ID: Address
2 text field Description: Width, Value: 1200
3 text field Description: Height, Value: 600
4 text Description: Zoom Level, Value: ( 100% )
5 pop up button Description: Pixel Ratio, Value: 2x
6 heading S16 · AI 赛制介绍, Value: 1
7 text Original method body
8 button 展开 AI 模拟速报（含后续剧情）
9 scroll bar (settable, float) 0'''

    def test_rounded_zoom_does_not_override_actual_sampling(self):
        self.assertEqual(visual.measure_sampling(self.spec, self.protocol), 2)
        wrong = {**self.spec, 'viewport_pixels': [124, 298, 2388, 1194]}
        with self.assertRaisesRegex(ValueError, 'sampling differs'):
            visual.measure_sampling(wrong, self.protocol)

    def test_window_query_toolbar_and_complete_scope_are_required(self):
        self.assertTrue(visual.ax_facts(self.ax, self.url, self.spec, self.protocol, 'ABC-123')['at_scroll_origin'])
        for changed, message in [
                (self.ax.replace('ABC-123', 'DEF-456'), 'window differs'),
                (self.ax.replace('plat_id=620', 'plat_id=1'), 'share query differs'),
                (self.ax.replace('Width, Value: 1200', 'Width, Value: 1199'), 'toolbar differs'),
                (self.ax.replace('8 button 展开 AI 模拟速报（含后续剧情）', ''), 'scene unavailable'),
                (self.ax.replace('7 text', '7 container (showing 10-20 of 30 items)\n10 text'), 'truncated')]:
            with self.assertRaisesRegex(ValueError, message):
                visual.ax_facts(changed, self.url, self.spec, self.protocol, 'ABC-123')
        scrolled = self.ax.replace('float) 0', 'float) 0.5')
        self.assertFalse(visual.ax_facts(scrolled, self.url, self.spec, self.protocol)['at_scroll_origin'])

    def test_unstable_reference_cannot_be_frozen_as_static(self):
        source = {'states': {'method-main': {'interactions': {'repeat_pixels_identical': False, 'at_scroll_origin': True}}}}
        with self.assertRaisesRegex(ValueError, 'Stable source pixels'):
            visual.freeze(source, self.protocol)

    def test_inspector_must_select_owned_body_and_save_owned_filename(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            inspector = folder / 'source.inspector.ax.txt'
            saved = folder / 'source.save.ax.txt'
            good_inspector = '0 standard window Web Inspector — www.bilibili.com — index.html\n1 row (selected, expanded) Description: <body>'
            good_save = '0 sheet ID: save-panel\n1 text field Value: source.png\n2 pop up button Value: ' + folder.name
            inspector.write_text(good_inspector)
            saved.write_text(good_save)
            self.assertEqual(visual.inspector_provenance(folder, 'source', self.url), [inspector, saved])
            for changed in [good_inspector.replace('www.bilibili.com', 'other.test'), good_inspector.replace('<body>', '<head>')]:
                inspector.write_text(changed)
                with self.assertRaisesRegex(ValueError, 'body selection'):
                    visual.inspector_provenance(folder, 'source', self.url)
            inspector.write_text(good_inspector)
            for changed in [good_save.replace('source.png', 'unrelated.png'), good_save.replace(folder.name, 'Documents')]:
                saved.write_text(changed)
                with self.assertRaisesRegex(ValueError, 'save destination'):
                    visual.inspector_provenance(folder, 'source', self.url)
