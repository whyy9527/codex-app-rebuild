"""Negative controls for real live-cycle evidence, separate from the product API tests."""
from importlib import import_module
import unittest
from unittest.mock import patch

probe = import_module('projects.bilibili-toy.tools.live_cycle_probe')


class LiveCycleEvidence(unittest.TestCase):
    def test_expanded_match_cannot_drop_a_game_or_a_model_row(self):
        row='10 row (selectable)\n11 cell (selectable) A\n12 cell (selectable) 1.0\n13 row (selectable)\n14 cell (selectable) B\n15 cell (selectable) 2.0\n'
        ax='1 summary KC 3 : 2 C9 入围赛 · 已完赛, Value: on\n2 table\n'+row
        for game in range(1,6):
            ax+=f'20 heading 第 {game} 局 官方 MVP：KC Example, Value: 3\n21 table\n'+row
        ax+='30 heading 接下来的比赛，AI 怎么猜, Value: 2\n'
        with patch.object(probe,'page',return_value={}):
            result=probe.match_details(ax,'https://public.example/','owned',['A','B'])
            self.assertEqual(len(result['elements']),7)
            for broken in (ax.replace('14 cell (selectable) B','14 text B',1),
                           ax.replace('20 heading 第 5 局 官方 MVP：KC Example, Value: 3','20 text Missing')):
                with self.assertRaises(ValueError):
                    probe.match_details(broken,'https://public.example/','owned',['A','B'])

    def test_response_date_is_not_the_upstream_content_modification_date(self):
        ax = '''0 standard window UUID=owned
1 text https:​/​/​public.example/​results.json?​t=100
2 text Status:
3 text 200 OK
4 text Date:
5 text Thu, 15 Oct 2026 23:30:23 GMT
6 text Last-Modified:
7 text Thu, 15 Oct 2026 23:28:02 GMT'''
        result = probe.request(ax, 'https://public.example/results.json', 'owned')
        self.assertEqual(result['response_date'], 'Thu, 15 Oct 2026 23:30:23 GMT')
        self.assertEqual(result['minute'], 100)
        for endpoint, owner in [('https://public.example/other.json', 'owned'),
                                ('https://other.example/results.json', 'owned'),
                                ('https://public.example/results.json', 'other')]:
            with self.assertRaises(ValueError):
                probe.request(ax, endpoint, owner)

    def test_complete_model_scores_are_required_and_query_changes_are_rejected(self):
        ax = '''0 standard window UUID=owned
1 text field smart search field, Value: https://public.example/?p=original
2 heading 谁最准, Value: 1
3 text 自动更新中
4 text 赛果更新于 10/16 07:28:02 （北京时间）
5 heading AI 实时积分榜, Value: 2
6 text AI 实时积分榜
7 text Example model 73.8 分 胜负 60.0 比分 10.0 阵容 2.1 KDA 1.7 MVP 0.0
8 heading 每场对答案, Value: 2
9 text 每场对答案
10 button 立即刷新
11 button 展开 AI 模拟速报'''
        result=probe.page(ax, 'https://public.example/?p=original', 'owned', ['Example model'])
        self.assertEqual(result['scores']['Example model'], ['73.8','60.0','10.0','2.1','1.7','0.0'])
        for url, models in [('https://public.example/?p=other', ['Example model']),
                            ('https://public.example/?p=original', ['Example model','Missing model'])]:
            with self.assertRaises(ValueError):
                probe.page(ax, url, 'owned', models)
        with self.assertRaises(ValueError):
            probe.page(ax.replace('7 text Example', '7 container (showing 0-1 of 3 items)\n7 text Example'),
                       'https://public.example/?p=original', 'owned', ['Example model'])


if __name__ == '__main__': unittest.main()
