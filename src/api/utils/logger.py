import inspect
import os
from datetime import datetime
from enum import Enum
from types import FrameType
from typing import Optional


class LogColors:
    """A class to hold ANSI color codes for terminal output."""

    RESET = "\033[0m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    MAGENTA = "\033[95m"


class LogLevel(str, Enum):
    INFO = "INFO"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


def log(message: str, level: LogLevel = LogLevel.DEBUG) -> None:
    """
    Prints a formatted log message with timestamp, caller script, line number, and colors.

    Args:
        message (str): The message to log.
        level (LogLevel): The log level (e.g., "INFO", "ERROR", "DEBUG").
                     This determines the message color.
    """
    current: Optional[FrameType] = inspect.currentframe()
    caller_frame: Optional[FrameType] = (
        current.f_back if current and current.f_back else None
    )

    if caller_frame is not None:
        frame_info = inspect.getframeinfo(caller_frame)
        filename = os.path.basename(frame_info.filename)
        lineno = frame_info.lineno
    else:
        filename = "<unknown>"
        lineno = 0

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    color_map: dict[LogLevel, str] = {
        LogLevel.INFO: LogColors.GREEN,
        LogLevel.ERROR: LogColors.RED,
        LogLevel.DEBUG: LogColors.MAGENTA,
    }
    message_color: str = color_map.get(level, LogColors.RESET)

    print(
        f"{LogColors.YELLOW}{timestamp}{LogColors.RESET} | "
        f"{LogColors.CYAN}{filename}:{lineno}{LogColors.RESET} - "
        f"[{message_color}{level.value}{LogColors.RESET}] {message}"
    )


if __name__ == "__main__":
    print("--- Running Log Examples ---")

    my_variable = 42
    log(
        f"This is an informational message. The value is {my_variable}.",
        level=LogLevel.INFO,
    )

    try:
        result = my_variable / 0
    except ZeroDivisionError as e:
        log(f"An error occurred: {e}", level=LogLevel.ERROR)

    log("This is a debug message for troubleshooting.", level=LogLevel.DEBUG)
