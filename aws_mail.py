#!{{ deploy_path }}/venv/bin/python

import sys
import os
import syslog
import fileinput
from pathlib import Path
import logging
import argparse

import yaml
from eventhooks import event_helper

logging.getLogger("EventHooks").setLevel(logging.ERROR)


def load_config(file_name):
    config = None
    try:
        if os.path.exists(file_name):
            with open(os.path.realpath(file_name), "r") as file_handler:
                config = yaml.load(file_handler, Loader=yaml.FullLoader)
    except (yaml.parser.ParserError) as e_yaml_load:
        syslog.syslog(f"Check the format '{file_name}'. Error: '{str(e_yaml_load)}'.")
        print(f"Check the format '{file_name}'. Error: '{str(e_yaml_load)}'.")
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
        default="./config.yml",
        help="Configuration file to use.",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="If set, considers every line, otherwise only supported: '[logwatch, unattended-upgrade]'.",
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
        "--debug",
        action="store_true",
        help="Show debug info.",
    )

    args, unknown = parser.parse_known_args()
    if unknown and args.debug:
        syslog.syslog(f"Unprocessed arguments: '{unknown}'.")
        print(f"Unprocessed arguments: '{unknown}'.")

    os.environ["AWS_DEFAULT_REGION"] = args.region

    # Resolve possible symlink to config file.
    config_file = os.path.expanduser(args.config)
    if not os.path.isabs(config_file):
        # Relative path to config file given.
        file_name = os.path.split(args.config)[-1]
        # Get real path of config file
        # by following the executable's symlink.
        resolved_path = Path(__file__).resolve()
        script_path = os.path.dirname(resolved_path)
        config_file = os.path.join(script_path, file_name)

    if not os.path.exists(config_file):
        syslog.syslog(f"Cannot find config file '{config_file}'.")
        print(f"Cannot find config file '{config_file}'.")
        return 1

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
        get_info = False
        subject_found = False
        for line in fileinput.input(sys.argv[len(sys.argv) :]):  # noqa: E203
            line_ = line.strip()
            if line_:
                # Subject
                if not subject_found and not args.default_subject:
                    if line_.lower().startswith("subject:"):
                        subject_found = True
                        events[0].email.subject = " ".join(line_.split()[1:])
                # Process everything.
                if args.all:
                    coming_in.append(line)
                else:
                    # Consider interesting lines only.
                    # Supported tools:
                    # * logwatch
                    # * unattended-upgrade
                    if not get_info:
                        if line_.startswith("###################") and line_.strip("#").strip().lower().startswith("logwatch"):
                            get_info = True
                        elif line_.lower().startswith("unattended upgrade result:"):
                            get_info = True

                    if get_info:
                        coming_in.append(line)

        data = "".join(coming_in)
        for event in events:
            event.trigger(data=data)
    except Exception as e_general:  # pylint: disable=W0703
        syslog.syslog(str(e_general))
        print(str(e_general))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
