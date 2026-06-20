import os
import glob
import sys
import datetime
from loguru import logger


def setup_logger():
    """
    Configures the logger to provide structured JSON logging.
    Maintains only the two most recent execution log files.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Keep only the two most recent execution logs
    log_files = sorted(
        glob.glob(os.path.join(log_dir, "execution_*.log")), key=os.path.getmtime, reverse=True
    )
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


# Initialize the logger immediately upon import
setup_logger()
