import json
import os
from pathlib import Path


def summary(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    metrics = data['metrics']
    checks = data['root_group']['checks']
    required = {
        'checks': 'rate==1', 'http_req_failed': 'rate==0',
        'http_reqs': 'count==9', 'iterations': 'count==3',
        **{f'http_req_duration{{operation:{name}}}': 'max<3000'
           for name in ('vegetarian', 'restricted', 'unauthorized')},
    }
    passed = sum(c['passes'] for c in checks)
    failed = sum(c['fails'] for c in checks)
    if (len(checks) != 12 or passed + failed != 36
            or any(c['passes'] < 0 or c['fails'] < 0 or c['passes'] + c['fails'] != 3 for c in checks)
            or metrics['http_reqs']['values']['count'] != 9
            or metrics['iterations']['values']['count'] != 3):
        raise ValueError('Incomplete run: expected 12 checks x 3 iterations and 9 HTTP requests')
    lines = ['| Check | Passed | Failed |', '| --- | ---: | ---: |']
    lines += [f"| {c['name']} | {c['passes']} | {c['fails']} |" for c in checks]
    lines += ['', '| Metric | Threshold | Result |', '| --- | --- | --- |']
    ok = failed == 0
    for metric, expression in required.items():
        result = metrics[metric]['thresholds'][expression]['ok']
        if not isinstance(result, bool):
            raise ValueError('Invalid threshold result')
        ok = ok and result
        lines.append(f"| {metric} | {expression} | {'PASS' if result else 'FAIL'} |")
    lines += ['', '| Operation | Average (ms) | Max (ms) |', '| --- | ---: | ---: |']
    for operation in ('vegetarian', 'restricted', 'unauthorized'):
        values = metrics[f'http_req_duration{{operation:{operation}}}']['values']
        lines.append(f"| {operation} | {values['avg']:.2f} | {values['max']:.2f} |")
    return ok, '\n'.join(lines)


if __name__ == '__main__':
    lines = ['# k6 — QuickPizza smoke', '',
             'Target: https://quickpizza.grafana.com. 1 VU, 3 iterations, 9 requests.',
             '36 check executions. 3000 ms is a demo smoke budget, not a production SLA or capacity estimate.', '']
    try:
        ok, report = summary(Path('results/k6-summary.json'))
        lines.append(report)
    except (OSError, ValueError, KeyError, TypeError) as error:
        ok = False
        lines.append(f'Missing, invalid or incomplete report: {error}')
    outcome = os.environ.get('TEST_OUTCOME', 'success')
    ok = ok and outcome == 'success'
    lines += ['', f"Test step: {outcome}. Gate: {'PASS' if ok else 'FAIL'}."]
    if url := os.environ.get('ARTIFACT_URL'):
        lines.append(f'[Download results]({url})')
    output = '\n'.join(lines) + '\n'
    Path('results').mkdir(exist_ok=True)
    Path('results/summary.md').write_text(output, encoding='utf-8')
    if destination := os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(destination, 'a', encoding='utf-8') as handle:
            handle.write(output)
    print(output)
    raise SystemExit(0 if ok else 1)
