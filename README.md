# StyleBench Data

Code style variants, bug catalogs, and benchmark results for [StyleBench](https://github.com/yuan0-0jia/stylebench).

## Structure

```
stylebench-data/
├── original/              # Unmodified source repositories
│   ├── humanize/
│   ├── validators/
│   ├── python-markdown/
│   └── more-itertools/
├── camelcase/             # snake_case → camelCase naming
│   └── ...
├── badnames/              # Descriptive names → single-letter (a, b, c)
│   └── ...
├── formatting/            # Ruff default formatting (88-char lines, double quotes)
│   └── ...
├── nodocstrings/          # Docstrings removed (module, class, function)
│   └── ...
├── nodocs_full/           # All documentation removed (docstrings + inline comments)
│   └── ...
├── bugs/                  # Ad-hoc validated bug catalogs (762 total bugs)
│   ├── humanize-original.json
│   └── ...
├── bugs_canonical/        # Canonical bug catalogs for benchmark (960 bugs)
│   ├── humanize-original.json
│   ├── humanize-camelcase.json
│   ├── humanize-nodocstrings.json
│   └── ...                # 24 catalogs (4 repos × 6 styles), 40 bugs each
└── results/               # Benchmark results
    ├── benchmark_claude_haiku/                 # Canonical pilot (200 trials, Week 7)
    ├── benchmark_claude_haiku_{repo}_{mode}/   # Full benchmark — 4 naming/formatting styles (640 trials)
    ├── benchmark_claude_haiku_nds_{mode}/      # Doc-style benchmark — nodocstrings + nodocs_full (320 trials)
    └── benchmark_codex/                        # Codex partial results (160 trials)
```

## Source Projects

| Project | LOC | Tests | Description | Source |
|---------|-----|-------|-------------|--------|
| humanize | 1,650 | 684 | String humanization | [GitHub](https://github.com/python-humanize/humanize) |
| validators | 3,144 | 878 | Input validation | [GitHub](https://github.com/python-validators/validators) |
| python-markdown | 8,293 | 776 | Markdown parser | [GitHub](https://github.com/Python-Markdown/markdown) |
| more-itertools | 6,822 | 701 | Extended itertools | [GitHub](https://github.com/more-itertools/more-itertools) |

## Style Variants

### CamelCase (`camelcase/`)

Transforms `snake_case` identifiers to `camelCase`:
- `get_user_name` → `getUserName`
- `total_count` → `totalCount`

**Validation**: 98-100% test pass rate across all projects.

### BadNaming (`badnames/`)

Transforms local variable names to single-letter names:
- `result = x + y` → `a = x + y`
- Only renames within function scopes
- Preserves parameters, class attributes, and public APIs

**Validation**: 100% test pass rate across all projects.

### Formatting (`formatting/`)

Applies ruff default formatting:
- 88 character line length
- Double quotes for strings
- PEP 8 compliant

**Validation**: 100% test pass rate across all projects.

### NoDocstrings (`nodocstrings/`)

Removes all docstrings (module-level, class-level, and function-level):
- `def foo():\n    """Does something."""\n    ...` → `def foo():\n    ...`
- Preserves inline comments and type hints

**Validation**: 100% test pass rate across all projects.

### NoDocsFull (`nodocs_full/`)

Removes all natural-language documentation — both docstrings and inline comments:
- Strips all docstrings (like `nodocstrings`)
- Also strips `# inline comments`
- Code with zero natural-language documentation

**Validation**: 100% test pass rate across all projects.

## Validation Results

All variants have been validated to ensure tests still pass after transformation:

| Project | Original | CamelCase | BadNaming | Formatting | NoDocstrings | NoDocsFull |
|---------|----------|-----------|-----------|------------|--------------|------------|
| humanize | 684 pass | 681 (99.6%) | 684 (100%) | 684 (100%) | 684 (100%) | 684 (100%) |
| validators | 878 pass | 878 (100%) | 878 (100%) | 878 (100%) | 878 (100%) | 878 (100%) |
| python-markdown | 776 pass | 776 (100%) | 776 (100%) | 776 (100%) | 776 (100%) | 776 (100%) |
| more-itertools | 701 pass | 693 (98.9%) | 701 (100%) | 701 (100%) | 701 (100%) | 701 (100%) |

*Minor CamelCase failures are due to dynamic imports that can't be tracked statically.*

## Bug Catalogs

### Canonical Catalogs (`bugs_canonical/`)

Used for the benchmark. The same logical mutation is applied consistently across all 6 style variants, ensuring fair comparison.

- **24 catalogs** (4 repos × 6 styles), **40 bugs each** = **960 total bugs**
- All bugs have `line_number` and `context` for precise application
- 14 mutation types across all repos: eq_ne, lt_gt, le_ge, var_swap, add_sub, mul_div, and_or, if_else_swap, in_not_in, is_is_not, plus_one, minus_one, true_false, return_none
- Bugs 001-020: original set; bugs 021-040: naming-changed set (bug lines guaranteed different in camelcase/badnames vs original)
- Doc styles (nodocstrings, nodocs_full) extended via `extend_catalogs.py`

### Ad-Hoc Catalogs (`bugs/`)

Used during development. Contains **762 validated bugs** across 16 repo/style combinations:

| Repo | Bugs (across 4 styles) |
|------|------------------------|
| humanize | 196 |
| validators | 168 |
| python-markdown | 198 |
| more-itertools | 200 |

### Catalog Format

Each `{repo}-{style}.json` contains:
- `bugs[]` — Agent-visible data: test failure output, failing test names
- `_hidden[]` — Scoring data: mutation file, line number, original/mutated text, mutation type

The agent never sees: mutation location, original code, or the diff.

## Results

Benchmark results are stored in `results/` with per-run directories:

```
results/benchmark_claude_haiku_{repo}_{mode}/
├── benchmark_state.json          # Progress tracking (completed bugs, rate limit state)
├── results_YYYYMMDD_HHMMSS_*.json  # Per-batch result files
└── ...
```

Each result file contains:
- `metadata` — catalog, repo, timestamp, `hit_rate_limit` flag
- `results[]` — per-trial evaluation (PASS/FAIL/ERROR/TIMEOUT/NO_FIX)
- `summary` — aggregated stats by agent, mode, evaluation

### Full Benchmark Results (1920 trials, Claude Haiku 4.5)

| Metric | Value |
|--------|-------|
| Overall pass rate | 84.9% (1631/1920) |
| with_tests | 89.3% (857/960) |
| without_tests | 80.6% (774/960) |
| Mode gap | 8.7pp |

**By style** (combined modes, 320 trials each):

| Style | with_tests | without_tests | Combined |
|-------|-----------|---------------|---------|
| original | 89.4% | 81.2% | 85.3% |
| camelcase | 91.9% | 78.8% | 85.3% |
| badnames | 88.8% | 82.5% | 85.6% |
| formatting | 88.1% | 81.2% | 84.7% |
| nodocstrings | 88.1% | 80.6% | 84.4% |
| nodocs_full | 89.4% | 79.4% | 84.4% |

**By repo** (combined modes): validators 96%, humanize 92%, more-itertools 84%, python-markdown 68%.

**By mutation type** (combined modes, all 14 types): `var_swap` 99%, `plus_one` 96%, `and_or`/`eq_ne` 91–92%, `return_none`/`true_false`/`in_not_in` 88–89%, `le_ge` 85%, `mul_div`/`lt_gt`/`minus_one` 82–83%, `if_else_swap` 80%, `is_is_not` 76%, `add_sub` 70%.

**Key findings**: Style has **no statistically significant effect** (p = 0.998, 1pp range). Repository difficulty dominates (28pp range: python-markdown 68% → validators 96%). Mutation type spans 29pp (`var_swap` 99% → `add_sub` 70%). Badnames does not hurt fix rates vs original.

See the [tracking repo overview](https://github.com/masc-ucsc/cse247b_reports_w26) for full analysis.

## Usage

Clone this repository alongside the main StyleBench repo:

```bash
git clone https://github.com/yuan0-0jia/stylebench.git
git clone https://github.com/yuan0-0jia/stylebench-data.git
```

Run the benchmark:

```bash
cd stylebench
python scripts/run_benchmark.py --catalog-dir bugs_canonical
```

## Regenerating Variants

To regenerate the style variants from scratch using the transformers:

```bash
cd stylebench

# CamelCase
python scripts/transform.py camelcase stylebench-data/original/humanize stylebench-data/camelcase/humanize --packages humanize

# BadNaming
python scripts/transform.py badnames stylebench-data/original/humanize stylebench-data/badnames/humanize

# Formatting
python scripts/transform.py formatting stylebench-data/original/humanize stylebench-data/formatting/humanize

# NoDocstrings
python scripts/transform.py nodocstrings stylebench-data/original/humanize stylebench-data/nodocstrings/humanize

# NoDocsFull
python scripts/transform.py nodocs_full stylebench-data/original/humanize stylebench-data/nodocs_full/humanize
```

## License

Each project retains its original license. See individual project directories for license information.
