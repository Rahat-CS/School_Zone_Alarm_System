"""DEK-a-log

Attempt at a common logging config interface.
"""


import logging
import logging.config
import argparse
import yaml
from os.path import expanduser


import dek.config_tools

default_yaml_config = """
  version: 1

  loggers:
    screen:
      handlers: [screen]

  root:
    handlers: [screen, file]

    level: NOTSET

  formatters:
    simple:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    complex:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(module)s : %(lineno)d - %(message)s'

  handlers:
    file:
      class: logging.handlers.TimedRotatingFileHandler
      when: midnight
      backupCount: 50
      formatter: complex
      level: DEBUG
      filename: file.log

    screen:
      class: logging.StreamHandler
      formatter: simple
      level: DEBUG
      stream: ext://sys.stdout

"""

def add_logging_args(parser, default_log_filename=None):
    parser.add_argument(
        "--log-level", type=str,
        help="Adjust python log level"
    )

    parser.add_argument(
        "--log-config-file", type=str,
        help="Python logging config file. YAML/JSON format"
    )

    help_extra = ' Default: %(default)s' if default_log_filename else ''
    parser.add_argument(
        "-L", "--log-file", type=str, default=default_log_filename,
        help=f"File to send logs to.{help_extra}"
    )

    parser.add_argument(
        "-A", "--log-adjustments", nargs="*",
        help="Change the logging config in the form root.level=debug"
    )

def set_up_logging(args):

    if args.log_config_file:
        with open(expanduser(args.log_config_file)) as file:
            config = yaml.safe_load(file)
    else:
        config = yaml.safe_load(default_yaml_config)

    config['disable_existing_loggers'] = False

    if args.log_adjustments:
        for adjustment in args.log_adjustments:
            dek.config_tools.adjust_structure(config, adjustment)

    if args.log_level:
        config['root']['level'] = args.log_level

    if args.log_file:
        config['handlers']['file']['filename'] = expanduser(args.log_file)


    logging.config.dictConfig(config)

