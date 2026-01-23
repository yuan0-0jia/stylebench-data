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
└── badnames/           # Descriptive names → single-letter (a, b, c)
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

### BadNaming (`badnames/`)

Transforms local variable names to single-letter names:
- `result = x + y` → `a = x + y`
- Only renames within function scopes
- Preserves parameters, class attributes, and public APIs

**Validation**: 100% test pass rate across all projects.

## Usage

Clone this repository alongside the main StyleBench repo:

```bash
git clone https://github.com/yuan0-0jia/stylebench.git
git clone https://github.com/yuan0-0jia/stylebench-data.git
```

Run tests on a transformed project:

```bash
cd stylebench-data/camelcase/humanize
PYTHONPATH=src python -m pytest tests/ -q
```

## Regenerating Variants

To regenerate the style variants from scratch using the transformers:

```bash
cd stylebench
python scripts/transform_all.py --output ../stylebench-data
```

## License

Each project retains its original license. See individual project directories for license information.
