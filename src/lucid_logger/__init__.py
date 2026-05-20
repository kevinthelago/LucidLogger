from logging.handlers import TimedRotatingFileHandler
from os import environ
import os
import shutil
import logging
from datetime import datetime

RESET = "\033[0m"

grey = "\033[38;2;200;200;200m"
white = "\033[38;2;255;255;255m"
red = "\033[38;2;255;0;0m"
yellow = "\033[38;2;255;255;0m"
green = "\033[38;2;0;150;0m"
lime = "\033[38;2;0;255;0m"
cyan = "\033[38;2;0;255;255m"
blue = "\033[38;2;0;0;255m"
purple = "\033[38;2;0;0;150m"

COLORS = {
    "grey": grey,
    "white": white,
    "red": red,
    "yellow": yellow,
    "green": green,
    "lime": lime,
    "cyan": cyan,
    "blue": blue,
    "purple": purple,
}


class LucidLogger(logging.Logger):
    def __init__(
            self, name, log_lowest_level, colored_logs,
            rotating_file_handler=None, stream_handler=None
    ):
        logging.Logger.__init__(self, name=name)
        self.name = name
        self.log_lowest_level = log_lowest_level
        self.colored_logs = colored_logs
        self.rotating_file_handler = rotating_file_handler
        self.stream_handler = stream_handler

    def add_loading_bar(self, loading_bar):
        self.stream_handler.loading_bars[loading_bar.name] = loading_bar

    def get_loading_bar(self, name):
        return self.stream_handler.loading_bars[name]

    def add_logging_level(self, level_name, level_num, color, method_name=None):
        if not method_name:
            method_name = level_name.lower()

        if hasattr(self, level_name):
            raise AttributeError('Level "{}" already defined in logging module'.format(level_name))
        if hasattr(LucidLogger, method_name):
            raise AttributeError('Method "{}" already defined in logging module'.format(method_name))
        if hasattr(self, method_name):
            raise AttributeError('Method "{}" already defined in logging class'.format(method_name))

        def log_for_level(self, message, *args, **kwargs):
            if self.isEnabledFor(level_num):
                self._log(level=level_num, msg=message, args=args, **kwargs)

        def log_to_root(message, *args, **kwargs):
            logging.log(level_num, message, *args, **kwargs)

        if not self.stream_handler.get_stream_formatter().LEVEL_COLORS.get(level_num):
            self.stream_handler.get_stream_formatter().LEVEL_COLORS[level_num] = color

        logging.addLevelName(level_num, level_name)
        setattr(logging, level_name, level_num)
        setattr(LucidLogger, method_name, log_for_level)
        setattr(logging, method_name, log_to_root)

    def basic_config(self, rotating_file_handler=None, stream_handler=None):
        self.rotating_file_handler = rotating_file_handler if rotating_file_handler else LucidTimedRotatingFileHandler()
        self.rotating_file_handler.setFormatter(LucidFileFormatter())

        self.stream_handler = stream_handler if stream_handler else LucidStreamHandler()
        self.stream_handler.setFormatter(LucidStreamFormatter(colored_logs=self.colored_logs))

        self.handlers = [
            self.rotating_file_handler, self.stream_handler
        ]


class LucidLoadingBar:
    def __init__(
            self, name, iterable=None, prefix='Loading...', suffix='', colored_logs=True,
            prefix_color=grey,
            suffix_color=grey,
            bar_color=grey,
            percent_color=grey,
            bar_format="$RESET$PREFIX_COLOR$PREFIX$RESET |$BAR_COLOR$BAR$RESET| $PERCENT_COLOR$PERCENT$RESET",
            fill='\xdb' if environ.get('SHELL') else '\u2588',
            decimals=1, length=100, print_end='\r', is_loading=None, total=0
    ):
        self.name = name
        self.iterable = iterable
        self.prefix = prefix
        self.suffix = suffix
        self.colored_logs = colored_logs
        self.prefix_color = prefix_color
        self.suffix_color = suffix_color
        self.bar_color = bar_color
        self.percent_color = percent_color
        self.bar_format = bar_format
        self.fill = fill
        self.decimals = decimals
        self.length = length
        self.print_end = print_end
        self.is_loading = is_loading
        self.progress = 0
        self.total = total

    def get_bar(self):
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.progress / float(self.total)))
        filled_length = int(self.length * self.progress // self.total)
        bar = self.fill * filled_length + "-" * (self.length - filled_length)

        return self.format_bar(bar=bar, percent=percent)

    def get_clear_bar(self):
        return ''.join(' ' for i in range(len(self.prefix) + self.length + 9))

    def format_bar(self, bar, percent):
        formatted_bar = self.bar_format\
            .replace('$RESET', RESET) \
            .replace('$PREFIX_COLOR', self.prefix_color if self.prefix_color and self.colored_logs else '') \
            .replace('$PREFIX', self.prefix) \
            .replace('$BAR_COLOR', self.bar_color if self.bar_color and self.colored_logs else '') \
            .replace('$BAR', bar) \
            .replace('$PERCENT_COLOR', self.percent_color if self.percent_color and self.colored_logs else '') \
            .replace('$PERCENT', percent)

        return formatted_bar

    def init_bar(self, iterable=None, prefix="Loading...", total=None):
        terminal_length = shutil.get_terminal_size(fallback=(100, 24)).columns
        self.is_loading = True
        self.total = len(iterable) if iterable else total
        self.length = (terminal_length - len(self.prefix) - 10)
        self.prefix = prefix
        return self

    def finish_loading(self):
        self.is_loading = False
        self.total = 0
        self.prefix = ''
        self.progress = 0

    def progress_bar(self):
        self.progress += 1


class LucidStreamFormatter(logging.Formatter):
    def __init__(
            self, datefmt="%m/%d/%Y %H:%M:%S", colored_logs=True, detailed_view_threshold=20,
            log_format="[$TIME_COLOR%(asctime)s$RESET][$LEVEL_COLOR%(levelname)s$RESET]$FILE$LINE $MESSAGE_COLOR%(message)s$RESET"
    ):
        self.time_color = grey
        self.message_color = grey
        self.datefmt = datefmt
        self.colored_logs = colored_logs
        self.detailed_view_threshold = detailed_view_threshold
        self.log_format = log_format

        self.LEVEL_COLORS = {
            logging.CRITICAL: red,
            logging.ERROR: red,
            logging.WARNING: yellow,
            logging.INFO: cyan,
            # 15: cyan,
            logging.DEBUG: green
        }

    def get_level_color(self, level_no):
        if self.LEVEL_COLORS.get(level_no) and self.colored_logs:
            return self.LEVEL_COLORS.get(level_no)
        return ''

    def get_formatted_string(self, level_no):
        formatted_string = self.log_format.replace("$RESET", RESET)\
            .replace("$FILE", "" if level_no <= self.detailed_view_threshold else "[%(filename)s:")\
            .replace("$LINE", "" if level_no <= self.detailed_view_threshold else "%(lineno)d]")\

        if self.colored_logs:
            formatted_string = formatted_string \
                .replace("$TIME_COLOR", self.time_color)\
                .replace("$LEVEL_COLOR", self.get_level_color(level_no))\
                .replace("$MESSAGE_COLOR", self.message_color)
        else:
            formatted_string = formatted_string \
                .replace("$TIME_COLOR", '') \
                .replace("$LEVEL_COLOR", '') \
                .replace("$MESSAGE_COLOR", '')

        return formatted_string

    def format(self, record):
        formatted_string = self.get_formatted_string(record.levelno)
        formatter = logging.Formatter(formatted_string)
        formatter.datefmt = self.datefmt
        return formatter.format(record=record)


class LucidStreamHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.return_carriage = '\r'
        self.loading_bars = {}

    def get_stream_formatter(self):
        return self.formatter

    def emit(self, record):
        for loading_bar in self.loading_bars:
            if self.loading_bars[loading_bar].is_loading:
                self.stream.write(self.return_carriage + self.loading_bars[loading_bar].get_clear_bar() + self.return_carriage)
        message = self.format(record)
        self.stream.write(self.return_carriage + message + self.terminator)
        for loading_bar in self.loading_bars:
            if self.loading_bars[loading_bar]:
                self.stream.write(self.return_carriage + self.loading_bars[loading_bar].get_bar() + self.return_carriage)


class LucidFileFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno in [logging.CRITICAL, logging.ERROR, logging.WARNING]:
            return logging.Formatter("[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] %(message)s").format(record)
        return logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s").format(record)


class LucidTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, directory='./logs/', when='midnight', interval=1, file_extension='log'):
        self.directory = directory
        self.when = when
        self.interval = interval
        self.file_extension = file_extension
        os.makedirs(directory, exist_ok=True)
        filename = f"{self.directory}{self.generateFileName()}.{self.file_extension}"
        TimedRotatingFileHandler.__init__(self, filename=filename, when=when, interval=interval)

    def doRollover(self):
        self.stream.close()
        self.baseFilename = f"{self.directory}{self.generateFileName()}.{self.file_extension}"
        self.stream = open(self.baseFilename, 'a')
        self.rolloverAt = self.rolloverAt + self.interval

    def generateFileName(self):
        date_format = "%Y-%m-%d"
        return datetime.now().strftime(date_format)

