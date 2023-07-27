
"""
General step functions for pytest harness

Everything in this file needs to imported into ./conftest.py with
    from .conftest_general_steps import *


Copyright (c) DEK Technologies 2021 All rights reserved
"""

import logging
import time

import pytest
from pytest_bdd import scenarios, given, when, then
from pytest_bdd import parsers

import testbench.common
import testbench.connect
import testbench.result_store
from testbench.guillemet_parser import GuillemetParser
import re

LOGGER = logging.getLogger(__name__)


@given('the app is connected to the CMC')
def app_connected(connector):
    response = connector.connect()
    LOGGER.info(f'connected with "{response}"')



@given('the ADC is configured to the default state')
def step_default_config(cmc):

    DEFAULT_TIME_TABLE = (
        '"01588BA6C0FC82AA02A82A20AA82AA0A282AA0AA828A0AA82AA0A28'
        '2AA0AA822A0AA02AA0AA82A20AA80AA0A882AA0AA828A0AA82AA08A8'
        '2AA0AA822A0AA02AA0AA822A0FF"'
    )

    cmc.update_setting('BVL', '"10.21"')
    cmc.update_setting('FPN', '"07070707070707070707070707070707"')
    cmc.update_setting('TTO', '"28800,0,0"')
    cmc.update_setting('SGN', '"ABC1234"')
    cmc.update_setting('TMO', '"86400"')
    cmc.update_setting('TTB', DEFAULT_TIME_TABLE)
    cmc.update_setting('TTV', '"00001"')
    cmc.update_setting('CTD', '"600"')
    cmc.update_setting('STD', '"200"')
    cmc.update_setting('SOP', '"1"')
    cmc.update_setting('ECT', '"0435,0435,1237"')
    cmc.update_setting('PWM', '"100"')
    cmc.run_cmd('CLG', 'STS=')

@pytest.fixture(scope='session')
def results():
    results = testbench.result_store.ResultStore()
    return results


@given(parsers.parse("the CMC sets '{cmd_name}' to {value}"))
@when(parsers.parse("the CMC sets '{cmd_name}' to {value}"))
@then(parsers.parse("the CMC sets '{cmd_name}' to {value}"))
def step_set_value(cmc, cmd_name, value, results):
    LOGGER.debug(f'XXXX {cmd_name}  {value} {results.results}')

    if value in results.results:
        value = results.results[value]

    LOGGER.debug(f'XXXX {cmd_name}  {value} {results.results}')

    resp = cmc.send(f'<{cmd_name}="{value}">')
    assert resp == '<ACK>'

@given(parsers.parse("we pause for {var} seconds"))
@when(parsers.parse("we pause for {var} seconds"))
@then(parsers.parse("we pause for {var} seconds"))
def pause(var, results):
    time.sleep(float(results.substitute(var)))

@given(parsers.parse("the CMC requests '{cmd_name}', result stored as {var}"))
@when(parsers.parse("the CMC requests '{cmd_name}', result stored as {var}"))
@then(parsers.parse("the CMC requests '{cmd_name}', result stored as {var}"))
def step_get_value(cmc, cmd_name, var, results):
    resp = cmc.send(f'<{cmd_name}?>')
    LOGGER.debug(f'Request for: {cmd_name}  response: {resp}')
    results.check_format(f'<{cmd_name}="{var}">', resp)

@then(parsers.parse("{var} equals {exp} exactly"))
def step_check_exact(var, exp, results):
    return step_check_tol(var, exp, 0, 0, results)

@then(parsers.parse("{var} equals {exp} within tolerance (+{plus:g} -{minus:g})"))
def step_check_tol(var, exp, plus, minus, results):
    got_str = results.results[var]
    got = float(got_str)
    if exp in results.results:
        exp = results.results[exp]
    exp = float(exp)
    assert exp - minus <= got <= exp + plus, f'{var} ({got}) outside {exp - minus}:{exp + plus}'

@then(parsers.re(r'^the following is true: (?P<statement>.*)$'))
def step_check(statement, results):
    statement = results.substitute(statement, adjust_types=True)
    assert eval(statement)

@given(GuillemetParser(r'^we run this python code:\n(?P<snippet>.*)$'))
@when(GuillemetParser(r'^we run this python code:\n(?P<snippet>.*)$'))
def step_check(snippet, results):
    results.exec(snippet)




# Scenario Outline stuff
@given(GuillemetParser('{item} is copied to {var}'))
def copy(item, var, results):
    results.set(var, [item])


@given(GuillemetParser("the CMC sends <{cmd}>"))
@when(GuillemetParser("the CMC sends <{cmd}>"))
@then(GuillemetParser("the CMC sends <{cmd}>"))
def send_command(cmc, cmd, results):
    cmd = results.substitute(cmd)
    LOGGER.debug(f'Sending: {cmd}')
    cmc.send_only(f'<{cmd}>')

@given(GuillemetParser("the ADC responds with <{expected}>"))
@when(GuillemetParser("the ADC responds with <{expected}>"))
@then(GuillemetParser("the ADC responds with <{expected}>"))
def copy(cmc, expected, results):
    # expected_subs = "<" + results.substitute(expected) + ">"
    resp = cmc.read_response(timeout=30)
    results.check_format(f'<{expected}>', resp)
    # assert expected_subs == actual, f"{expected} ({expected_subs}) != {actual}"

@given(GuillemetParser("the CMC sends <{cmd}> to which the ADC responds <{expected}>"))
@when(GuillemetParser("the CMC sends <{cmd}> to which the ADC responds <{expected}>"))
@then(GuillemetParser("the CMC sends <{cmd}> to which the ADC responds <{expected}>"))
def step_send_command(cmc, cmd, expected, results):
    cmd = results.substitute(cmd)
    LOGGER.debug(f'Sending: {cmd}')
    resp = cmc.send(f'<{cmd}>')
    LOGGER.debug(f'Command sent: {cmd}  response: {resp}')
    results.check_format(f'<{expected}>', resp)




@then(parsers.re(r'(?P<var>\w+) matches regex "(?P<regex>.*)"'))
def step(var, regex, results):
    value = results.eval(var)
    match = re.match(regex, value)
    assert match, f"No such match {regex} for {value}"