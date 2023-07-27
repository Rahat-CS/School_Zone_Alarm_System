from pytest_bdd import scenario, scenarios, given, when, then
import logging
import time
import testbench.cmc_int
from testbench.syslog import SysLog, EventId
import pytest
import re
import datetime
from .conftest_general_steps import *

scenarios('../features/try_out.feature')

"""
Quoted Variable Step Parser
"""

@given(MyParser("I have <{start}>"))
def given_cucumbers(start):
    LOGGER.debug(f'Sending: "{start}"')

@given(MyParser("I have <{start}> and {end} too"))
def given_cucumbers(start, end):
    LOGGER.debug(f'fsfas: "{start}" and "{end}"')


