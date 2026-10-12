import importlib
from pathlib import Path
import tempfile
import unittest


class EnrollmentChoiceCapture(unittest.TestCase):
    def test_final_cell_continuation_survives_row_boundary_and_eof(self):
        extract = importlib.import_module(
            'projects.xiaogj-web.tools.prepare_enrollment_choices').extract
        capture = '''1 heading 选择课程
2 table
3 row (selectable)
4 checkbox
课程名称
价格
5 row (selectable)
6 cell (selectable)
7 checkbox 0
8 cell (selectable) 示例课程
9 cell (selectable) 100
元
10 row (selectable)
11 cell (selectable)
12 checkbox 0
13 cell (selectable) 示例二
14 cell (selectable) 200
元
15 row (selectable)
16 text 共 2 条 每页
17 text 条 第 1 / 1 页
'''
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'capture.txt'
            path.write_text(capture)
            result = extract(path)
        self.assertEqual(result['rows'], [['示例课程', '100元'], ['示例二', '200元']])
        self.assertEqual(result['headers'], ['课程名称', '价格'])
