import sys
import os
import fileinput
from pathlib import Path
import logging
import argparse
import time

import yaml
from eventhooks import event_helper


logger_formatter = logging.Formatter(
    "%(asctime)s - %(name)s [%(levelname)s] - %(pathname)s [line: %(lineno)s]: method: %(funcName)s - %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S %Z"
)
logger_formatter.converter = time.gmtime

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logger_formatter)
console_handler.setLevel(logging.ERROR)

logger = logging.getLogger("AwsMail")
logger.setLevel(logging.ERROR)
logger.addHandler(console_handler)
logger.propagate = False

event_logger = logging.getLogger("EventHooks")
logger.setLevel(logging.ERROR)
event_logger.addHandler(console_handler)


def load_config(file_name):
    config = None
    try:
        if os.path.exists(file_name):
            with open(os.path.realpath(file_name), "r") as file_handler:
                config = yaml.load(file_handler, Loader=yaml.FullLoader)
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
        "--config",
        default="/etc/aws_mail/config.yml",
        help="Configuration file to use.",
    )

    parser.add_argument(
        "--region",
        default="us-east-1",
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
        "--debug",
        action="store_true",
        help="Show debug info.",
    )

    args, unknown = parser.parse_known_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        # 'SttreamHandler', in order of appearance.
        console_handler = logger.handlers[0]
        console_handler.setLevel(logging.DEBUG)

        logger.debug("Show DEBUG information.")

    if unknown and args.debug:
        logger.debug(f"Unprocessed arguments: '{unknown}'.")

    os.environ["AWS_DEFAULT_REGION"] = args.region

    # Resolve possible symlink to config file.
    config_file = os.path.expanduser(args.config)

    if not os.path.exists(config_file):
        logger.error(f"Cannot find config file '{config_file}'.")
        return 1

    logger.info(f"Using config file: '{config_file}'")
    config = load_config(config_file)

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
                    if line_.startswith("###################") and line_.strip("#").strip().lower().startswith("logwatch"):
                        found_tool_log = True
                        coming_in = []
                    elif line_.lower().startswith("unattended upgrade result:"):
                        found_tool_log = True
                        coming_in = []
                    elif line_.lower().startswith("x-cron-env:"):
                        found_tool_log = True
                        coming_in = []
                coming_in.append(line)

        data = "".join(coming_in)
        logger.info("Send mail.")
        for event in events:
            event.trigger(data=data)
    except Exception as e_general:  # pylint: disable=W0703
        logger.error(str(e_general))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
