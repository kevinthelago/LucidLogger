"""Tests for lucid_logger."""

import io
import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from lucid_logger import (
    LucidFileFormatter,
    LucidLoadingBar,
    LucidLogger,
    LucidStreamFormatter,
    LucidStreamHandler,
    LucidTimedRotatingFileHandler,
    cyan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_logger(colored: bool = False) -> LucidLogger:
    """Return a LucidLogger with a stream handler only (no file I/O)."""
    logger = LucidLogger(name="test", log_lowest_level=logging.DEBUG, colored_logs=colored)
    stream_handler = LucidStreamHandler()
    stream_handler.setFormatter(LucidStreamFormatter(colored_logs=colored))
    logger.stream_handler = stream_handler
    logger.handlers = [stream_handler]
    logger.setLevel(logging.DEBUG)
    return logger


# ---------------------------------------------------------------------------
# LucidLogger
# ---------------------------------------------------------------------------

class TestLucidLogger:
    def test_basic_config_attaches_two_handlers(self, tmp_path):
        logger = LucidLogger(name="cfg", log_lowest_level=logging.DEBUG, colored_logs=False)
        with patch.object(LucidTimedRotatingFileHandler, "__init__", return_value=None) as mock_init:
            # Patch the parent __init__ so no file is created
            mock_handler = MagicMock(spec=LucidTimedRotatingFileHandler)
            mock_handler.setFormatter = MagicMock()
            with patch("lucid_logger.LucidTimedRotatingFileHandler", return_value=mock_handler):
                logger.basic_config()
        assert len(logger.handlers) == 2

    def test_info_log_reaches_stream(self):
        buf = io.StringIO()
        logger = make_logger()
        logger.handlers[0].stream = buf
        logger.info("hello world")
        assert "hello world" in buf.getvalue()

    def test_warning_log_reaches_stream(self):
        buf = io.StringIO()
        logger = make_logger()
        logger.handlers[0].stream = buf
        logger.warning("watch out")
        assert "watch out" in buf.getvalue()

    def test_debug_log_reaches_stream(self):
        buf = io.StringIO()
        logger = make_logger()
        logger.handlers[0].stream = buf
        logger.debug("debugging")
        assert "debugging" in buf.getvalue()

    def test_error_log_reaches_stream(self):
        buf = io.StringIO()
        logger = make_logger()
        logger.handlers[0].stream = buf
        logger.error("something broke")
        assert "something broke" in buf.getvalue()

    def test_add_and_get_loading_bar(self):
        logger = make_logger()
        bar = LucidLoadingBar(name="mybar")
        logger.add_loading_bar(bar)
        assert logger.get_loading_bar("mybar") is bar

    def test_add_logging_level_callable(self):
        logger = make_logger()
        logger.add_logging_level("VERBOSE", 15, cyan)
        assert hasattr(logger, "verbose")
        buf = io.StringIO()
        logger.handlers[0].stream = buf
        logger.verbose("verbose message")
        assert "verbose message" in buf.getvalue()

    def test_add_logging_level_duplicate_raises(self):
        logger = make_logger()
        logger.add_logging_level("TRACE", 5, cyan)
        with pytest.raises(AttributeError):
            logger.add_logging_level("TRACE", 5, cyan)


# ---------------------------------------------------------------------------
# LucidLoadingBar
# ---------------------------------------------------------------------------

class TestLucidLoadingBar:
    def test_init_bar_sets_is_loading_and_total(self):
        bar = LucidLoadingBar(name="test")
        items = list(range(10))
        bar.init_bar(iterable=items, prefix="Loading")
        assert bar.is_loading is True
        assert bar.total == 10

    def test_init_bar_with_explicit_total(self):
        bar = LucidLoadingBar(name="test")
        bar.init_bar(total=50, prefix="Processing")
        assert bar.total == 50

    def test_progress_bar_increments(self):
        bar = LucidLoadingBar(name="test")
        bar.init_bar(total=5, prefix="Work")
        bar.progress_bar()
        bar.progress_bar()
        assert bar.progress == 2

    def test_get_bar_returns_string_with_fill(self):
        bar = LucidLoadingBar(name="test", fill="X", length=10, colored_logs=False)
        bar.init_bar(total=10, prefix="Test")
        bar.progress = 5
        result = bar.get_bar()
        assert "X" in result

    def test_finish_loading_resets_state(self):
        bar = LucidLoadingBar(name="test")
        bar.init_bar(total=5, prefix="Work")
        bar.progress = 3
        bar.finish_loading()
        assert bar.is_loading is False
        assert bar.total == 0
        assert bar.progress == 0
        assert bar.prefix == ''

    def test_get_clear_bar_length(self):
        # Patch the tput subprocess so terminal_length is predictable (100).
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value.communicate.return_value = (b"100", b"")
            bar = LucidLoadingBar(name="test", length=20)
            bar.init_bar(total=5, prefix="Hi")
        # init_bar computes length as terminal_width - len(old_prefix "Loading...") - 10
        expected_length = 100 - len("Loading...") - 10
        clear = bar.get_clear_bar()
        assert len(clear) == len("Hi") + expected_length + 9


# ---------------------------------------------------------------------------
# LucidStreamFormatter
# ---------------------------------------------------------------------------

class TestLucidStreamFormatter:
    def _make_record(self, level: int) -> logging.LogRecord:
        return logging.LogRecord(
            name="test", level=level, pathname="test_file.py",
            lineno=42, msg="test message", args=(), exc_info=None,
        )

    def test_no_ansi_when_colored_false(self):
        formatter = LucidStreamFormatter(colored_logs=False)
        record = self._make_record(logging.INFO)
        output = formatter.format(record)
        assert "\033[" not in output

    def test_file_and_line_omitted_below_threshold(self):
        # INFO (20) <= default threshold (20), so no filename/lineno
        formatter = LucidStreamFormatter(colored_logs=False, detailed_view_threshold=20)
        record = self._make_record(logging.INFO)
        output = formatter.format(record)
        assert "test_file.py" not in output

    def test_file_and_line_included_above_threshold(self):
        # WARNING (30) > threshold (20)
        formatter = LucidStreamFormatter(colored_logs=False, detailed_view_threshold=20)
        record = self._make_record(logging.WARNING)
        output = formatter.format(record)
        assert "test_file.py" in output
        assert "42" in output

    def test_message_in_output(self):
        formatter = LucidStreamFormatter(colored_logs=False)
        record = self._make_record(logging.DEBUG)
        output = formatter.format(record)
        assert "test message" in output


# ---------------------------------------------------------------------------
# LucidFileFormatter
# ---------------------------------------------------------------------------

class TestLucidFileFormatter:
    def _make_record(self, level: int) -> logging.LogRecord:
        return logging.LogRecord(
            name="test", level=level, pathname="myfile.py",
            lineno=99, msg="file log", args=(), exc_info=None,
        )

    def test_no_ansi_codes_ever(self):
        formatter = LucidFileFormatter()
        for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
            record = self._make_record(level)
            assert "\033[" not in formatter.format(record)

    def test_filename_included_for_warning_and_above(self):
        formatter = LucidFileFormatter()
        for level in [logging.WARNING, logging.ERROR, logging.CRITICAL]:
            record = self._make_record(level)
            output = formatter.format(record)
            assert "myfile.py" in output
            assert "99" in output

    def test_filename_omitted_for_info_and_debug(self):
        formatter = LucidFileFormatter()
        for level in [logging.DEBUG, logging.INFO]:
            record = self._make_record(level)
            output = formatter.format(record)
            assert "myfile.py" not in output


# ---------------------------------------------------------------------------
# LucidTimedRotatingFileHandler
# ---------------------------------------------------------------------------

class TestLucidTimedRotatingFileHandler:
    def test_generate_file_name_is_date_format(self):
        import re
        with patch.object(LucidTimedRotatingFileHandler, "__init__", return_value=None):
            handler = LucidTimedRotatingFileHandler.__new__(LucidTimedRotatingFileHandler)
        name = handler.generateFileName()
        assert re.match(r"\d{4}-\d{2}-\d{2}", name), f"Unexpected filename: {name}"

    def test_creates_log_directory(self, tmp_path):
        log_dir = str(tmp_path / "new_logs") + os.sep
        handler = LucidTimedRotatingFileHandler(directory=log_dir)
        assert os.path.isdir(log_dir)
        handler.stream.close()
