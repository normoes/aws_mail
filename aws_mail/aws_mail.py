import sys
import os
import fileinput
import logging
from logging.handlers import TimedRotatingFileHandler
import syslog
import argparse
import time

import yaml
from eventhooks import event_helper

from ._version import __version__


LOG_LEVEL_DEFAULT = logging.ERROR
LOG_LEVELS_ = [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
LOG_LEVELS = {logging.getLevelName(level): level for level in LOG_LEVELS_}
LOG_PATH_DEFAULT = "/var/log/aws_mail"

logger_formatter = logging.Formatter(
    "%(asctime)s - %(name)s [%(levelname)s] - %(pathname)s [line: %(lineno)s]: method: %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %Z",
)
logger_formatter.converter = time.gmtime

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logger_formatter)
console_handler.setLevel(LOG_LEVEL_DEFAULT)

logger = logging.getLogger("AwsMail")
logger.setLevel(LOG_LEVEL_DEFAULT)
logger.addHandler(console_handler)
logger.propagate = False


def load_config(file_name):
    config = None
    try:
        if os.path.exists(file_name):
            with open(os.path.realpath(file_name), "r") as file_handler:
                config = yaml.load(file_handler, Loader=yaml.SafeLoader)
    except (yaml.parser.ParserError) as e_yaml_load:
        logger.error(f"Check the format '{file_name}'. Error: '{str(e_yaml_load)}'.")
        raise e_yaml_load
    return config


def main():  # noqa: C901
    parser = argparse.ArgumentParser(
        description="AWS mail client.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        allow_abbrev=False,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )

    parser.add_argument(
        "--log-path",
        default=LOG_PATH_DEFAULT,
        const=LOG_PATH_DEFAULT,
        nargs="?",
        type=str,
        help="Folder to store logs in.",
    )

    parser.add_argument(
        "--config",
        default="/etc/aws_mail/config.yml",
        const="/etc/aws_mail/config.yml",
        nargs="?",
        type=str,
        help="Configuration file to use.",
    )

    parser.add_argument(
        "--region",
        default="us-east-1",
        const="us-east-1",
        nargs="?",
        help="AWS region to use.",
    )

    parser.add_argument(
        "--default-subject",
        action="store_true",
        help="If set, uses event name (config.yml) as subject, otherwise searches for a line starting with 'Subject:'.",
    )

    parser.add_argument(
        "--default-recipients",
        action="store_true",
        help="If set, uses recipients from config.yml, otherwise searches for a line starting with 'To:'.",
    )

    parser.add_argument(
        "--log-level",
        # No default value.
        # If not set, use config file value.
        const=logging.getLevelName(LOG_LEVEL_DEFAULT),
        nargs="?",
        choices=LOG_LEVELS,
        help="Log level to use (default: %(default)s)",
    )

    args, unknown = parser.parse_known_args()

    logger.info("Start.")
    # Logger not completely set up, yet.
    # Send to 'syslog' as well.
    syslog.syslog("Start.")

    log_path = os.path.expanduser(args.log_path)
    log_file = os.path.join(log_path, "aws_mail.log")
    if not os.path.exists(log_path) or not os.path.isdir(log_path):
        logger.error(f"Cannot find log path: '{log_path}'.")
        # Logger not completely set up, yet.
        # Send to 'syslog' as well.
        syslog.syslog(syslog.LOG_ERR, f"Cannot find log path: '{log_path}'.")
        return 1

    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        backupCount=5,
        utc=True,
    )
    file_handler.setFormatter(logger_formatter)
    file_handler.setLevel(LOG_LEVEL_DEFAULT)

    logger.addHandler(file_handler)

    event_logger = logging.getLogger("EventHooks")
    event_logger.setLevel(LOG_LEVEL_DEFAULT)
    event_logger.addHandler(console_handler)
    event_logger.addHandler(file_handler)

    config_file = os.path.expanduser(args.config)
    if not os.path.exists(config_file):
        logger.error(f"Cannot find config file: '{config_file}'.")
        return 1

    config = load_config(config_file)

    log_level_ = args.log_level

    if log_level_:
        log_level = LOG_LEVELS[log_level_]
        logger.setLevel(log_level)
        event_logger.setLevel(log_level)
        # Stream handler, in order of appearance.
        _console_handler = logger.handlers[0]
        _console_handler.setLevel(log_level)
        # File handler, in order of appearance.
        _file_handler = logger.handlers[1]
        _file_handler.setLevel(log_level)

    logger.info(f"Using config file: '{config_file}'")

    if unknown:
        logger.debug(f"Unprocessed arguments: '{unknown}'.")

    os.environ["AWS_DEFAULT_REGION"] = args.region

    events = []
    events_config = config.get("events", {})
    if events_config:
        for event, event_config in events_config.items():
            if event_config and event_config.get("enabled", False):
                hook = event_helper.eventhook_factory(event, event_config)
                if hook:
                    events.append(hook)

    try:
        coming_in = []
        found_tool_log = False
        subject_found = False
        recipients_found = False
        for line in fileinput.input(sys.argv[len(sys.argv) :]):  # noqa: E203
            line_ = line.strip()
            if line_:
                # Process everything by default.
                if not found_tool_log:
                    # Subject
                    if not subject_found and not args.default_subject:
                        if line_.lower().startswith("subject:"):
                            subject_found = True
                            events[0].email.subject = " ".join(line_.split()[1:])
                    # Recipients
                    if not recipients_found and not args.default_recipients:
                        if line_.lower().startswith("to:"):
                            recipients_found = True
                            # TODO: Make 'recipients_' a property in 'eventhooks'.
                            events[0].email.recipients = "".join(line_.split()[1:]).split(",")
                    # Consider interesting lines only.
                    # From that point on get everything.
                    # Supported tools:
                    # * logwatch
                    # * unattended-upgrade
                    # * cron
                    if line_.startswith("###################") and line_.strip("#").strip().lower().startswith(
                        "logwatch"
                    ):
                        found_tool_log = True
                        logger.info("Found 'logwatch' logs.")
                        coming_in = []
                    elif line_.lower().startswith("unattended upgrade result:"):
                        found_tool_log = True
                        logger.info("Found 'unattended-upgrade' logs.")
                        coming_in = []
                    elif line_.lower().startswith("x-cron-env:"):
                        found_tool_log = True
                        logger.info("Found 'cron' logs.")
                        coming_in = []
                coming_in.append(line)

        data = "".join(coming_in)
        logger.info("Send mail.")
        for event in events:
            event.trigger(data=data)
        logger.info("Done.")
    except Exception as e_general:  # pylint: disable=W0703
        logger.error(str(e_general))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
