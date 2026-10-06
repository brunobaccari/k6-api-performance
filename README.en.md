# QuickPizza — k6

[Versão em português](README.md)

Performance and contract smoke against **https://quickpizza.grafana.com**, Grafana's hosted application for learning k6. One virtual user, three iterations, nine requests. This is not a stress test.

## Run

k6 **2.3.0** and Python **3.12+** (report validation only). No Python dependencies or local server.

```bash
cp .env.example .env
set -a; source .env; set +a
mkdir -p results
k6 run tests/smoke.js
python ci_summary.py
```

In PowerShell, copy `.env.example` to `.env` and export both values with `$env:BASE_URL` and `$env:DEMO_TOKEN` before running the same k6/Python commands. k6 does not load `.env` automatically. The example token is public and published in the official examples; it is not a private credential. Do not use real tokens in this demo.

The script accepts only the demo URL. Increasing load or changing the target requires reviewing code, authorization and budget. Fixed configuration prevents accidentally turning this smoke into high load.

## Scenarios

| Operation | Expected behavior |
| --- | --- |
| Vegetarian | HTTP 200, JSON, valid identity and ingredients, all vegetarian, at most 500 calories per slice |
| Restricted | Same contract checks, no Pepperoni or Knife, at most 500 calories per slice |
| No token | HTTP 401, authentication error and no pizza |

12 checks repeated three times: **36 check executions**. Exclusions use exact catalog names: the implementation compares case-sensitive strings. A one-second pause between operations limits request frequency; it does not hide instability. No retries.

The recommendation POST stores the pizza in the demo's history, as in the official examples. We do not create accounts or ratings, or delete shared history. Pizza names and IDs are dynamic; checks verify properties rather than a specific random response.

## Failure criteria

- Every check must pass; unexpected responses fail. HTTP 401 is expected only for the request without a token.
- Exactly nine requests and three iterations; interrupted execution cannot pass.
- Each of the three operations must remain below a **3000 ms maximum**.

3000 ms is an educational budget chosen to detect obvious stalls in a demo smoke, not the service's SLA. Three samples per operation cannot estimate capacity, production p95 or performance improvement. Public infrastructure, network and cold starts affect measurements. Inspect operation, checks and latency before attributing a failure to the service; do not raise the limit simply to get a green build.

## CI and results

[Actions](https://github.com/brunobaccari/k6-api-performance/actions) runs the same workload on pushes, PRs and manual dispatch, one run at a time. The native k6 exit code is preserved. The additional gate rejects missing/invalid JSON, incomplete counts and failed thresholds.

The Summary lists checks by operation, thresholds and observed average/maximum latency. The `k6-results` artifact contains `k6-summary.json` and `summary.md`, including on failures, retained for 30 days. Reports and `.env` stay outside Git; HTTP bodies and tokens are not exported.

Check the report gate without making requests:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## References

- [QuickPizza and official examples](https://github.com/grafana/quickpizza)
- [Restriction implementation](https://github.com/grafana/quickpizza/blob/main/pkg/http/http.go)
- [k6 thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/)
- [Custom summary](https://grafana.com/docs/k6/latest/results-output/end-of-test/custom-summary/)

References checked on 2026-10-06. The former `test-api.k6.io` redirected to QuickPizza; this suite uses the current target directly.
