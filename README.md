# LucidLogger

A Python library for standardized terminal logging with ANSI color support, progress bars, and timed rotating file output.

---

## Features

- Colored log output per level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Custom log levels with configurable colors
- Inline progress/loading bars that coexist with log output
- Auto-resizing progress bars based on terminal width
- Cross-platform (Windows CMD, PowerShell, Bash)
- Timed rotating file handler with dated filenames
- File logs strip ANSI — clean output for log aggregators

---

## Installation

```bash
pip install lucid-logger
```

---

## Quick Start

```python
from lucid_logger import LucidLogger, LucidLoadingBar

logger = LucidLogger(name="app", log_lowest_level=10, colored_logs=True)
logger.basic_config()

logger.info("Server started")
logger.warning("High memory usage")
logger.error("Failed to connect")
```

### With a Progress Bar

```python
from lucid_logger import LucidLogger, LucidLoadingBar

logger = LucidLogger(name="app", log_lowest_level=10, colored_logs=True)
logger.basic_config()

items = list(range(50))
bar = LucidLoadingBar(name="import")
bar.init_bar(iterable=items, prefix="Importing")
logger.add_loading_bar(bar)

for item in items:
    # do work...
    bar.progress_bar()
    logger.info(f"Processing item {item}")

bar.finish_loading()
logger.info("Import complete")
```

---

## API Reference

### `LucidLogger`

Extends `logging.Logger`.

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Logger name |
| `log_lowest_level` | `int` | Minimum log level (e.g. `10` = DEBUG) |
| `colored_logs` | `bool` | Enable ANSI color output |

**Methods:**

| Method | Description |
|---|---|
| `basic_config()` | Attach default stream and file handlers |
| `add_loading_bar(bar)` | Register a `LucidLoadingBar` with the stream handler |
| `get_loading_bar(name)` | Retrieve a registered bar by name |
| `add_logging_level(level_name, level_num, color)` | Register a custom log level with a color |

---

### `LucidLoadingBar`

A terminal progress bar that renders inline with log output.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | — | Unique identifier |
| `iterable` | `iterable` | `None` | Collection to iterate over |
| `prefix` | `str` | `'Loading...'` | Label shown before the bar |
| `suffix` | `str` | `''` | Label shown after the bar |
| `colored_logs` | `bool` | `True` | Enable ANSI color |
| `fill` | `str` | `█` | Fill character |
| `decimals` | `int` | `1` | Decimal places on the percent |
| `length` | `int` | `100` | Bar width in characters |

**Methods:**

| Method | Description |
|---|---|
| `init_bar(iterable, prefix, total)` | Start the bar, auto-sizes to terminal width |
| `progress_bar()` | Advance progress by one step |
| `finish_loading()` | Mark the bar complete and clear it |
| `get_bar()` | Return the current formatted bar string |

---

### `LucidStreamFormatter`

Custom `logging.Formatter` that injects ANSI color codes per log level.

Levels below `detailed_view_threshold` omit the filename/line number from the output to keep routine logs terse. Warnings and above include the source location.

---

### `LucidTimedRotatingFileHandler`

Extends `TimedRotatingFileHandler`. Rotates at midnight and names files by date (`YYYY-MM-DD.log`).

| Parameter | Default | Description |
|---|---|---|
| `directory` | `'./logs/'` | Output directory |
| `when` | `'midnight'` | Rotation schedule |
| `file_extension` | `'log'` | File extension |

---

## Color Reference

Built-in named colors available for custom levels and bar segments:

| Name | Hex |
|---|---|
| `grey` | `#C8C8C8` |
| `white` | `#FFFFFF` |
| `red` | `#FF0000` |
| `yellow` | `#FFFF00` |
| `green` | `#009600` |
| `lime` | `#00FF00` |
| `cyan` | `#00FFFF` |
| `blue` | `#0000FF` |
| `purple` | `#000096` |

---

## Custom Log Levels

```python
logger.add_logging_level("TRACE", 5, cyan)
logger.trace("Entering request handler")
```

---

## Log Output Format

Stream (colored):
```
[MM/DD/YYYY HH:MM:SS][LEVEL] message
[MM/DD/YYYY HH:MM:SS][WARNING][filename.py:42] message
```

File (plain):
```
[MM/DD/YYYY HH:MM:SS][INFO] message
[MM/DD/YYYY HH:MM:SS][ERROR][filename.py:42] message
```

---

## License

MIT
