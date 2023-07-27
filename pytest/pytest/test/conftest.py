"""Pytest config file

Add command-line arguments for the ADC test code.

Copyright (c) 2021 DEK Technologies All rights reserved
"""
import pytest
from pathlib import Path


def pytest_addoption(parser):
    parser.addoption(
        "--adc-ip-addr",
        help='ADC IP Address'
    )
    parser.addoption(
        '--cmc-ip-addr', default='10.250.2.224',
        help='IP address of local Communication Interface to be used. Default: %(default)s'
    )
    parser.addoption(
        "--adc-udp-port", action="store", default=10090, type=int,
        help='ADC UDP port.  Default: %(default)s'
    )
    parser.addoption(
        '--cmc-tcp-port', action='store', default=8008, type=int,
        help='Port of local Communication Interface to be used.  Default: %(default)s'
    )

    parser.addoption(
        '--cmc-man-port', action='store', default=8808, type=int,
        help='Management port for local CMC service.  Default: %(default)s'
    )
