# StyleBench Data

Code style variants for benchmarking coding agents. This repository contains Python projects transformed into different coding styles for use with [StyleBench](https://github.com/yuan0-0jia/stylebench).

## Structure

```
stylebench-data/
├── original/           # Unmodified source repositories
│   ├── humanize/
│   ├── validators/
│   ├── python-markdown/
│   └── more-itertools/
├── camelcase/          # snake_case → camelCase naming
│   └── ...
├── snakecase/          # camelCase → snake_case (roundtrip from camelcase)
│   └── ...
├── badnames/           # Descriptive names → single-letter (a, b, c)
│   └── ...
└── formatting/         # Compact formatting (79 char lines, single quotes)
    └── ...
```

## Source Projects

| Project | LOC | Tests | Description | Source |
|---------|-----|-------|-------------|--------|
| humanize | 1,650 | 684 | String humanization | [GitHub](https://github.com/python-humanize/humanize) |
| validators | 3,144 | 878 | Input validation | [GitHub](https://github.com/python-validators/validators) |
| python-markdown | 8,293 | 1,087 | Markdown parser | [GitHub](https://github.com/Python-Markdown/markdown) |
| more-itertools | 6,822 | 701 | Extended itertools | [GitHub](https://github.com/more-itertools/more-itertools) |

## Style Variants

### CamelCase (`camelcase/`)

Transforms `snake_case` identifiers to `camelCase`:
- `get_user_name` → `getUserName`
- `total_count` → `totalCount`

**Validation**: 98-100% test pass rate across all projects.

### SnakeCase (`snakecase/`)

Transforms `camelCase` identifiers back to `snake_case` (roundtrip from camelcase variant):
- `getUserName` → `get_user_name`
- `totalCount` → `total_count`

**Validation**: 99-100% test pass rate across all projects.

### BadNaming (`badnames/`)

Transforms local variable names to single-letter names:
- `result = x + y` → `a = x + y`
- Only renames within function scopes
- Preserves parameters, class attributes, and public APIs

**Validation**: 100% test pass rate across all projects.

### Formatting (`formatting/`)

Applies compact formatting style using ruff:
- 79 character line length
- Single quotes for strings
- PEP 8 compliant

**Validation**: 100% test pass rate across all projects.

## Usage

Clone this repository alongside the main StyleBench repo:

```bash
git clone https://github.com/yuan0-0jia/stylebench.git
git clone https://github.com/yuan0-0jia/stylebench-data.git
```

The code repo has symlinks to this data repo for convenient access:

```bash
cd stylebench
ls data/original/        # Points to ../stylebench-data/original
ls data/camelcase/       # Points to ../stylebench-data/camelcase
```

Run tests on a transformed project:

```bash
cd stylebench-data/camelcase/humanize
uv run --with pytest pytest tests/ -q

# Or from the code repo via symlinks
cd stylebench/data/camelcase/humanize
uv run --with pytest pytest tests/ -q
```

## Validation Results

All variants have been validated to ensure tests still pass after transformation:

| Project | Original | CamelCase | SnakeCase | BadNaming | Formatting |
|---------|----------|-----------|-----------|-----------|------------|
| humanize | 684 pass | 681 (99.6%) | 684 (100%) | 684 (100%) | 684 (100%) |
| validators | 878 pass | 878 (100%) | 878 (100%) | 878 (100%) | 878 (100%) |
| python-markdown | 776 pass | 776 (100%) | 776 (100%) | 776 (100%) | 776 (100%) |
| more-itertools | 701 pass | 693 (98.9%) | 700 (99.9%) | 701 (100%) | 701 (100%) |

*Minor CamelCase/SnakeCase failures are due to dynamic imports that can't be tracked statically.*

## Regenerating Variants

To regenerate the style variants from scratch using the transformers:

```bash
cd stylebench

# CamelCase
python scripts/transform.py camelcase stylebench-data/original/humanize stylebench-data/camelcase/humanize --packages humanize

# SnakeCase (from camelcase)
python scripts/transform.py snakecase stylebench-data/camelcase/humanize stylebench-data/snakecase/humanize --packages humanize

# BadNaming
python scripts/transform.py badnames stylebench-data/original/humanize stylebench-data/badnames/humanize

# Formatting
python scripts/transform.py formatting stylebench-data/original/humanize stylebench-data/formatting/humanize --style compact
```

## License

Each project retains its original license. See individual project directories for license information.
