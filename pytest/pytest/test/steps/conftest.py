"""
Common functions for pytest harness

Copyright (c) DEK Technologies 2021 All rights reserved
"""
from datetime import datetime
import logging
import pytest
from pytest_bdd import scenarios, given, when, then
from pytest_bdd import parsers
import time
import re

import testbench.common

import testbench.cmc_int

import testbench.target
from testbench.syslog import SysLog, EventId

# Farm out some of the conftest load to other files
# See https://github.com/pytest-dev/pytest/issues/3582

from .conftest_general_steps import *

LOGGER = logging.getLogger(__name__)


####################################################################################################################
#
# Fixtures
#
####################################################################################################################

# This is for situations where we have to pass data between steps
@pytest.fixture(scope='function')
def context():
    return {}


@pytest.fixture(autouse=True, scope='session')
def sign_controller(pytestconfig):
    sign_controller = testbench.cmc_int.Adc(
        adc_ip=pytestconfig.getoption('adc_ip_addr'),
        cmc_ip=pytestconfig.getoption('cmc_ip_addr'),
        adc_udp_port=pytestconfig.getoption('adc_udp_port'),
        cmc_tcp_port=pytestconfig.getoption('cmc_tcp_port'),
        cmc_man_port=pytestconfig.getoption('cmc_man_port')
    )
    return sign_controller


@pytest.fixture(scope='session')
def cmc(sign_controller):
    cmc = sign_controller
    return cmc

@pytest.fixture(scope='session')
def connector(cmc):
    connector = testbench.connect.EstablishAdcAppConnection(cmc)
    return connector

#####################################################################################################################
#
# Common Steps
#
#####################################################################################################################


DEFAULT_TIME_TABLE = (
    '"01588BA6C0FC82AA02A82A20AA82AA0A282AA0AA828A0AA82AA0A28'
    '2AA0AA822A0AA02AA0AA82A20AA80AA0A882AA0AA828A0AA82AA08A8'
    '2AA0AA822A0AA02AA0AA822A0FF"'
)



@given('the Sign Controller is configured to the default state')
def step_default_config(sign_controller, connector, pytestconfig):
    """
    Applies a default configuration to the Sign Controller

    :param sign_controller: Sign Controller Test Fixture

    :return: n/a
    """

    response =connector.connect()
    LOGGER.info(f'connected "{response}"')

    sign_controller.update_setting('BVL', '"10.21"')
    sign_controller.update_setting('FPN', '"07070707070707070707070707070707"')
    sign_controller.update_setting('TTO', '"28800,0,0"')
    sign_controller.update_setting('SGN', '"ABC1234"')
    sign_controller.update_setting('TMO', '"86400"')
    sign_controller.update_setting('TTB', DEFAULT_TIME_TABLE)
    sign_controller.update_setting('TTV', '"00001"')
    sign_controller.update_setting('CTD', '"600"')
    sign_controller.update_setting('STD', '"200"')
    sign_controller.update_setting('SOP', '"1"')
    sign_controller.update_setting('ECT', '"0435,0435,1237"')
    sign_controller.update_setting('PWM', '"100"')
    sign_controller.run_cmd('CLG', 'STS=')


@when('the Sign Controllers log has been cleared')
@given('the Sign Controllers log has been cleared')
def step_clear_log(sign_controller):
    time.sleep(10)
    sign_controller.run_cmd('LOG?', 'LOG=')
    sign_controller.run_cmd('CLG', 'STS=')


# def check_alarm(status_word_expected, sign_controller):
#     LOGGER.info('Starting check alarm')
#     LOGGER.info('Looking for Status Word: {}'.format(status_word_expected))
#     sts_re = re.compile(r'STS="(?P<status_word>[0-9A-F]{4})"')
#     crnt_status_word = sign_controller.run_cmd('STS?', 'STS=')
#     m = sts_re.match(crnt_status_word)
#     assert m
#     assert ('0x{}'.format(m.group('status_word')) == (status_word_expected))


def check_alarm_raised(status_word_expected, sign_controller):
    LOGGER.info('Looking for Status Word: {}'.format(status_word_expected))
    sts_re = re.compile(r'<SGN=\"[a-zA-Z0-9\.\-_\/]{1,32}\";(?P<status_field>STS=\"[0-9A-F]+\")>')
    greeting = sign_controller.listen(timeout=180)  #TEMP: was 60
    match = sts_re.match(greeting)
    check_status_word(match.group('status_field'), status_word_expected)
    LOGGER.info('Alarm was raised as expected')

# @given("The application is running")
# def step_dave_test(sign_controller):
#     if sign_controller.is_session_active():
#         response = sign_controller.send("STS?", timeout=10)
#         if not response:
#     sign_controller.trigger()
#     LOGGER.info("DAVE TEST")


# class ResultProc:

#     def register(self, expected, response):
#         variables = [c for c in expected if ord(c) > 126]
#         exp_re_text = expected
#         for var in variables:
#             exp_re_text = exp_re_text.replace(var, rf'(?P<{var}>[^"]*)')
#         exp_re = re.compile(exp_re_text)
#         match = exp_re.match(response)

#         self.results = match.groupdict()






# #                 And the CMC sends 'DTE? ' to which the ADC responds 'DTE="123"'
# @given(parsers.parse("the CMC sends '{cmd}' to which the ADC responds '{expected}'"))
# @then(parsers.parse("the CMC sends '{cmd}' to which the ADC responds '{expected}'"))
# @when(parsers.parse("the CMC sends '{cmd}' to which the ADC responds '{expected}'"))
# def step_send_command(sign_controller, cmd, expected, results):

#     resp = sign_controller.send('{}'.format(cmd), '{}'.format(resp))
#     LOGGER.info('Command sent: {} expected response: {}'.format(cmd, resp))

# @given(parsers.parse('the ADC sends "{expected}"'))
# @when(parsers.parse('the ADC sends "{expected}"'))
# @then(parsers.parse('the ADC sends "{expected}"'))
# def step_send_command(sign_controller, expected):
#     output = sign_controller.read_adc_output()
#     assert \
#         expected == output, \
#         f"Expected {expected}; got {output}"


@then(parsers.re(
    r'the Sign Controller raises an alarm with status (?P<status_word_expected>0x[0-9A-F]{2,4})'))
def step_check_alarm_raised_re(status_word_expected, sign_controller):
    check_alarm_raised(status_word_expected, sign_controller)


@then('the Sign Controller raises an alarm with status <status_word_expected>')
def step_check_alarm_raised_ol(status_word_expected, sign_controller):
    check_alarm_raised(status_word_expected, sign_controller)


@given('the device is enabled')
def step_enable_device(sign_controller):
    sign_controller.update_setting('SOP', '"1"')


@given("the device has been disabled")
def step_disable_device(sign_controller):
    sign_controller.update_setting('SOP', '"0"')


@then("the device remains disabled")
@then("the device has been disabled")
def step_check_device_disabled(sign_controller):
    response = sign_controller.run_cmd('SOP?', 'SOP=')
    assert (response == '<SOP="0">')


@when("a communication session has been established")
@given("a communication session has been established")
def step_establish_cmc_session(sign_controller):
    if not sign_controller.is_session_active():
        LOGGER.info('Sending trigger, then waiting for Sign Controller to make contact')
        sign_controller.trigger()
        return
    LOGGER.info('CMC session already in progress')
    resp = sign_controller.send('<STS?>')
    if 'STS=' in resp:
        return

    assert False, "FIXME we need to handle this"
    # resp = sign_controller.send('<END>')
    # if resp != '<ACK>':





@given("the Sign Controller has established a CMC session")
@then("the Sign Controller shall establish a CMC session")
def step_wait_for_connection(sign_controller):
    sign_controller.listen(timeout=300)


@given(parsers.re(
    r'the device clock is set to (?P<datetime_str>\d{1,2}-\d{1,2}-\d{4}\s\d{1,2}:\d{2}:\d{2})'))
def step_set_clock(sign_controller, datetime_str):
    LOGGER.info('Extracted Date-Time string: {}'.format(datetime_str))
    date_time = datetime.strptime(datetime_str, '%d-%m-%Y %H:%M:%S')
    LOGGER.info('As Unix Timestamp: {}'.format(int(date_time.timestamp())))
    sign_controller.run_cmd('SYN="999"', 'DTE?')
    sign_controller.run_cmd('DTE={}'.format(date_time.timestamp()), 'SYN=')
    dte_response = sign_controller.run_cmd('DTE?', 'DTE=')
    m = re.match(r'<DTE="(?P<dte_val>\d{1,10)"')
    assert m, f'Response to DTE? ({dte_response}) did not match expected pattern'
    dte = int(m.group('dte_val'))
    dte_fmt = datetime.fromtimestamp(dte).strftime('%d-%m-%Y %H:%M:%S')
    LOGGER.info(f'Sign Controllers time is now {dte} ({dte_fmt})')


@when("the communication session is terminated")
def step_terminate_cmc_session(sign_controller):
    sign_controller.end_session()


@when(parsers.parse('the door switch is toggled {num_toggles:d} times'))
def step_toggle_door_switch(num_toggles, door_switch):
    for i in range(num_toggles >> 1):
        door_switch.set_state(testbench.doorswitch.DoorState.OPEN)
        time.sleep(0.5)
        door_switch.set_state(testbench.doorswitch.DoorState.CLOSED)
        time.sleep(0.5)




_check_status_word_re = re.compile(r'STS=\"(?P<status_word>[0-9A-F]{2,4})\"')
def check_status_word(status_response, expected, mask=0xFFFF, message=''):
    match = _check_status_word_re.search(status_response)
    assert match, f'Bad STS response:"{status_response}"'
    if isinstance(expected, str):
        expected = int(expected, base=16)

    received = int(match.group('status_word'), base=16)
    assert \
        received & mask == expected, \
        f'Bad STS value: got 0x{received:04x}, expect 0x{expected:04x}, mask 0x{mask:04x} {message}'


def check_status_response(expected, sign_controller):
    status_response = sign_controller.run_cmd('STS?', 'STS=')
    check_status_word(status_response, expected=expected)
    LOGGER.info('Status Word as expected')


@then(parsers.parse('the Sign Controller reports status {status_word}'))
def step_check_status_word(status_word, sign_controller):
    check_status_response(status_word, sign_controller)


@then(parsers.parse('the Sign Controller reports status <status_word>'))
def step_check_status_word_ol(status_word, sign_controller):
    check_status_response(status_word, sign_controller)


def set_battery_threshold(sign_controller, bvl):
    sign_controller.update_setting('BVL', '"{}"'.format(bvl))


@when(parsers.re(r"the battery threshold is set to (?P<bvlx>\d{2}\.\d{2}) Volt"))
@given(parsers.re(r"the battery threshold is set to (?P<bvlx>\d{2}\.\d{2}) Volt"))
def step_set_battery_threshold_re(sign_controller, bvlx):
    set_battery_threshold(sign_controller, bvlx)


@given('the battery threshold is set to <bvl> Volt')
def step_set_battery_threshold_so(sign_controller, bvl):
    set_battery_threshold(sign_controller, bvl)


@given(parsers.parse('the CMC sends the command {cmd} and the Sign Controller responds with {resp}'))
@when(parsers.parse('the CMC sends the command {cmd} and the Sign Controller responds with {resp}'))
def step_send_command(sign_controller, cmd, resp):
    sign_controller.run_cmd('{}'.format(cmd), '{}'.format(resp))
    LOGGER.info('Command sent: {} expected response: {}'.format(cmd, resp))


@given("the state of operation is <sop>")
def step_set_state_of_operation(sign_controller, sop):
    sign_controller.run_cmd('SOP="{}"'.format(sop), 'ACK')


def der_check(der_byte_expected, sign_controller):
    der = sign_controller.run_cmd('DER?', 'DER=')
    der_re = re.compile('<DER="(?P<der_byte>[0-9A-F]{2})"')
    m = der_re.match(der)
    assert m
    der_byte = m.group('der_byte')
    assert ('0x{}'.format(der_byte) == der_byte_expected), f'Display Error Byte not as expected: 0x{der_byte} ' \
                                                           f'vs {der_byte_expected}'
    LOGGER.info(f'Display Error Byte as expected: {der_byte_expected}')


@then(parsers.parse('the Display Error Byte shows {der_byte}'))
def step_der_check_re(der_byte, sign_controller):
    der_check(der_byte, sign_controller)


@then('the Display Error Byte shows <display_error_byte>')
def step_der_check_so(display_error_byte, sign_controller):
    der_check(display_error_byte, sign_controller)


def check_log_for_display_error(sign_controller, display_error_byte, actual_currents):
    LOGGER.info('Params: DER = {}, Actual Currents = {}'.format(display_error_byte, actual_currents))
    device_log = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(device_log)
    LOGGER.info('Current log: {}'.format(device_log))
    events = syslog.get_events_by_id(EventId.ALERT_DISPLAY_FAILURE)
    LOGGER.info('Checking for correct length of Log retrieved')
    assert (len(events) == 1)
    LOGGER.info('checking the Display Error Byte of the Display Failure event')
    assert ('0x{}'.format(events[0].extra_info[0]) == display_error_byte)
    LOGGER.info('Log was OK')


@then('the Sign Controllers log contains a Display Failure event showing <display_error_byte> and <actual_currents>')
def step_check_log_for_display_error_so(sign_controller, display_error_byte, actual_currents):
    check_log_for_display_error(sign_controller, display_error_byte, actual_currents)


@then(parsers.re(
    r'the Sign Controllers log contains a Display Failure event showing (?P<display_error_byte_x>0x[0-9A-F]{2}) ' +
    r'and (?P<actual_currents_x>\d{1,4}mA, \d{1,4}mA, \d{1,4}mA)'))
def step_check_log_for_display_error_re(sign_controller, display_error_byte_x, actual_currents_x):
    check_log_for_display_error(sign_controller, display_error_byte_x, actual_currents_x)


@given(parsers.parse("the Sign Controllers time is set to {time_str}"))
@when(parsers.parse("the Sign Controllers time is set to {time_str}"))
def step_impl(sign_controller, time_str):
    """
    expects a time string in the following format
     '28-04-2020 10:00:00'
    :return:
    """
    target_time = datetime.strptime(time_str, '%d-%m-%Y %H:%M:%S')
    target_timestamp = int(target_time.timestamp())
    sign_controller.run_cmd('SYN="999"', 'DTE?')
    sign_controller.run_cmd('DTE="{}"'.format(target_timestamp), 'SYN=')
    dte_response = sign_controller.run_cmd('DTE?', 'DTE=')
    m = re.match(r'<DTE="(?P<dte_val>\d{1,10})">', dte_response)
    assert m, f'Response to DTE? ({dte_response}) did not match expected pattern'
    dte = int(m.group('dte_val'))
    dte_fmt = datetime.fromtimestamp(dte).strftime('%d-%m-%Y %H:%M:%S')
    LOGGER.info(f'Sign Controllers time is now {dte} ({dte:08x}) ({dte_fmt})')


@given(parsers.parse('the Sign Controller is configured with the following time table:\n{timetable}'))
@when(parsers.parse('the Sign Controller is configured with the following time table:\n{timetable}'))
def step_configure_timetable(sign_controller, timetable):
    LOGGER.info('Timetable: [{}]'.format(timetable))
    timetable_stripped = re.sub(r'\s', '', timetable)
    sign_controller.update_setting('TTB', f'"{timetable_stripped}"')


@given(parsers.parse('the Sign Controller is configured with the following Operating Durations: {tto}'))
def step_configure_tto(sign_controller, tto):
    tto_stripped = re.sub(r'\s', '', tto)
    sign_controller.update_setting('TTO', f'"{tto_stripped}"')


@given(parsers.parse('the Sign Controller is configured with the following flash pattern: {fpn}'))
def step_configure_fpn(sign_controller, fpn):
    fpn_stripped = re.sub(r'\s', '', fpn)
    sign_controller.update_setting('FPN', f'"{fpn_stripped}"')




@then("the CMC ends the session")
def cmc_ends_session(sign_controller):
    sign_controller.run_cmd('END', 'ACK')
    sign_controller.end_session()
##################################################################################################################
#
# pytest-bdd hooks
#
##################################################################################################################

# def dynamic_status_updates(enable):
#     if enable:
#         on_the_fly = DynamicStatusUpdate()
#         on_the_fly_update = on_the_fly.update
#     else:
#         def dummy(x, y):
#             pass
#         on_the_fly_update = dummy

def pytest_bdd_before_scenario(request, feature, scenario):
    LOGGER.info(f'SCENARIO {feature.name}:{scenario.name} BEGIN')
    scenario.any_step_failures_dek = False
    # on_the_fly_update({request.node.name}, 'begin')

def pytest_bdd_after_scenario(request, feature, scenario):
    status = 'FAILED' if scenario.any_step_failures_dek else 'PASSED'  # scenario.failed is still always False at this point
    LOGGER.info(f'SCENARIO {feature.name}:{scenario.name} {status}')
    # on_the_fly_update({request.node.name}, 'end')


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    step_title = step.name.split("\n")[0]
    LOGGER.info(f'STEP "{step_title}" ({feature.filename.split("/")[-1]}, line: {step.line_number})')


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    # on_the_fly_update({request.node.name}, 'error')
    scenario.any_step_failures_dek = True
    LOGGER.error(f'STEP FAILED {feature.name}:{scenario.name}:{step.name} {step_func.__name__}({step_func_args}), "{exception}"')


def pytest_bdd_apply_tag(tag, function):

    m = re.match('xfail:(?P<reason>.*)', tag)
    if m:
        marker = pytest.mark.xfail(reason=m.group('reason').strip())
        marker(function)
        return True

    m = re.match('skip(?::(?P<reason>.*))?', tag)
    if m:
        if m.group('reason'):
            marker = pytest.mark.skip(reason=m.group('reason').strip())
        else:
            marker = pytest.mark.skip()
        marker(function)
        return True
    return None
