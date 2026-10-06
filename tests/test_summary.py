import copy
import json
from pathlib import Path
import tempfile
import unittest

from ci_summary import summary


class SummaryTests(unittest.TestCase):
    def test_gate_rejects_missing_invalid_empty_failed_and_partial_reports(self):
        metrics = {}
        for name, expression in [('checks', 'rate==1'), ('http_req_failed', 'rate==0'), ('http_reqs', 'count==9'), ('iterations', 'count==3')]:
            metrics[name] = {'thresholds': {expression: {'ok': True}}, 'values': {'count': 9 if name == 'http_reqs' else 3}}
        for name in ('vegetarian', 'restricted', 'unauthorized'):
            metrics[f'http_req_duration{{operation:{name}}}'] = {'thresholds': {'max<3000': {'ok': True}}, 'values': {'avg': 100, 'max': 200}}
        valid = {'metrics': metrics, 'root_group': {'checks': [{'name': f'check {i}', 'passes': 3, 'fails': 0} for i in range(12)]}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'summary.json'
            with self.assertRaises(OSError):
                summary(path)
            for raw in ('broken', '{}', '{"metrics":{},"root_group":{"checks":[]}}'):
                path.write_text(raw, encoding='utf-8')
                with self.assertRaises((ValueError, KeyError)):
                    summary(path)
            path.write_text(json.dumps(valid), encoding='utf-8')
            self.assertTrue(summary(path)[0])
            for metric in metrics:
                data = copy.deepcopy(valid)
                next(iter(data['metrics'][metric]['thresholds'].values()))['ok'] = False
                path.write_text(json.dumps(data), encoding='utf-8')
                self.assertFalse(summary(path)[0])
            for mutation in ('partial', 'failure'):
                data = copy.deepcopy(valid)
                data['root_group']['checks'][0]['passes'] = 2
                data['root_group']['checks'][0]['fails'] = 1 if mutation == 'failure' else 0
                path.write_text(json.dumps(data), encoding='utf-8')
                if mutation == 'partial':
                    with self.assertRaises(ValueError):
                        summary(path)
                else:
                    self.assertFalse(summary(path)[0])
