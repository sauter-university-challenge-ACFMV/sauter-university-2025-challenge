import inspect
import os
from datetime import datetime

class LogColors:
    """A class to hold ANSI color codes for terminal output."""
    RESET = '\033[0m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    MAGENTA = '\033[95m'

class LogLevels:
    INFO = "INFO"
    ERROR = "ERROR"
    DEBUG = "DEBUG"

def log(message: str, level: LogLevels = LogLevels.DEBUG) -> None:
    """
    Prints a formatted log message with timestamp, caller script, line number, and colors.
    
    Args:
        message (str): The message to log.
        level (str): The log level (e.g., "INFO", "ERROR", "DEBUG"). 
                     This determines the message color.
    """
    caller_frame = inspect.currentframe().f_back
    
    frame_info = inspect.getframeinfo(caller_frame)
    filename = os.path.basename(frame_info.filename)
    lineno = frame_info.lineno
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    color_map = {
        LogLevels.INFO: LogColors.GREEN,
        LogLevels.ERROR: LogColors.RED,
        LogLevels.DEBUG: LogColors.MAGENTA,
    }
    message_color = color_map.get(level, LogColors.RESET)

    print(
        f"{LogColors.YELLOW}{timestamp}{LogColors.RESET} | "
        f"{LogColors.CYAN}{filename}:{lineno}{LogColors.RESET} - "
        f"[{message_color}{level.upper()}{LogColors.RESET}] {message}"
    )

if __name__ == "__main__":
    print("--- Running Log Examples ---")
    
    my_variable = 42
    log(f"This is an informational message. The value is {my_variable}.")
    
    try:
        result = my_variable / 0
    except ZeroDivisionError as e:
        log(f"An error occurred: {e}", level="ERROR")
        
    log("This is a debug message for troubleshooting.", level="DEBUG")