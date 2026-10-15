"""Dynamic original captures must not become artificial passing pixel contracts."""
from importlib import import_module
import unittest


class MajorPageContract(unittest.TestCase):
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
