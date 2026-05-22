# logslice

Fast log file slicer that filters by time range and severity without loading the full file.

## Installation

```bash
pip install logslice
```

## Usage

```bash
# Filter logs by time range
logslice app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00"

# Filter by severity level
logslice app.log --level ERROR

# Combine time range and severity
logslice app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" --level WARNING

# Save output to a file
logslice app.log --start "2024-01-15 08:00:00" --level ERROR --output errors.log
```

You can also use logslice as a Python library:

```python
from logslice import slice_log

results = slice_log(
    filepath="app.log",
    start="2024-01-15 08:00:00",
    end="2024-01-15 09:00:00",
    level="ERROR"
)

for entry in results:
    print(entry)
```

## Why logslice?

- **Fast** — uses binary search to locate time boundaries, no full file scan
- **Memory efficient** — streams results line by line
- **Flexible** — supports common log formats out of the box

## Requirements

- Python 3.8+

## License

This project is licensed under the [MIT License](LICENSE).