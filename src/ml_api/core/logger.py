import json
import logging


class JsonFormatter(logging.Formatter):
    """Formats each log record as a single JSON object.

    Designed for production: one line per record makes it trivial for log
    aggregators (CloudWatch, Datadog, Loki …) to parse, index and alert on
    individual fields without regex.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        return json.dumps(payload, default=str)


_TEXT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logger(level: str = "INFO", env: str = "dev") -> None:
    """Configure the root logger.

    Args:
        level: Minimum log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        env:   Runtime environment. Any value other than "dev" selects the JSON
               formatter so that production log pipelines receive structured data.
    """
    handler = logging.StreamHandler()

    if env.lower() == "dev":
        handler.setFormatter(logging.Formatter(_TEXT_FORMAT))
    else:
        handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid adding duplicate handlers if setup_logger is called more than once.
    root.handlers.clear()
    root.addHandler(handler)
