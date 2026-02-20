# Insight: 60s timeout is too short for Claude

**Date**: 2026-02-20
**Agent**: Claude (Haiku 4.5, default)
**Config**: 60s timeout, no turn cap, canonical catalogs
**Scope**: humanize repo, 5 bugs × 5 styles × with_tests (+ 2 without_tests before rate limit)

## Key Finding

60s timeout causes 78% of trials to timeout before the agent can finish.

## Numbers

- Total trials: 27 (hit rate limit mid-run)
- Timeouts: 21/27 (78%)
- PASS: 3 (11%)
- FAIL: 3 (11%)
- Successful completion times: 37s, 52s, 54s, 54s, 57s, 60s

## Implication

Claude needs ~50-160s to complete a fix attempt. The 6 trials that did finish
took 37-60s (barely under the wire). Earlier uncapped runs took 94-162s.

A timeout of 180s is more appropriate to give the agent enough time while
still providing a hard stop.
