import os
import glob
import sys
import datetime
import json
from pathlib import Path
from loguru import logger


def setup_logger():
    """
    Configures the logger to provide structured JSON logging.
    Maintains only the two most recent execution log files.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Keep only the two most recent execution logs
    log_files = sorted(glob.glob(os.path.join(log_dir, "execution_*.log")), key=os.path.getmtime, reverse=True)
    for old_file in log_files[1:]:
        try:
            os.remove(old_file)
        except OSError:
            pass

    # Remove default Loguru handler
    logger.remove()

    # Console handler - Structured JSON
    logger.add(sys.stderr, serialize=True, level="INFO", backtrace=True, diagnose=True)

    # File handler - Structured JSON, new file per execution
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"execution_{timestamp}.log")
    logger.add(log_path, serialize=True, level="INFO", backtrace=True, diagnose=True)


def log_token_usage(provider: str, model_name: str, input_tokens: int, output_tokens: int):
    """Logs token usage to data/token_usage.json."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    log_file = data_dir / "token_usage.json"

    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "provider": provider,
        "model": model_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }

    usage_data = []
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                usage_data = json.load(f)
        except json.JSONDecodeError:
            pass

    usage_data.append(entry)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(usage_data, f, indent=2)


# Initialize the logger immediately upon import
setup_logger()
