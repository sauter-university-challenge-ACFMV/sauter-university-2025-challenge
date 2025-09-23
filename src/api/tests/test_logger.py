from _pytest.capture import CaptureFixture
from utils.logger import log, LogLevel


def test_log_levels_do_not_crash(capsys: CaptureFixture[str]) -> None:
    log("info message", level=LogLevel.INFO)
    log("error message", level=LogLevel.ERROR)
    log("debug message", level=LogLevel.DEBUG)
    # default level
    log("default message")

    out = capsys.readouterr().out
    assert "info message" in out
    assert "error message" in out
    assert "debug message" in out
    assert "default message" in out
