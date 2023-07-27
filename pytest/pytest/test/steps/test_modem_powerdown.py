import logging
import pytest
from pytest_bdd import scenario, scenarios, given, when, then, parsers
import re
import time
import datetime
import testbench.cmc_int

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/modem_powerdown.feature',
#     # 'MOF ignored if SOP="0"'
#     #'MOF Duration (no upcoming timetabled operations scheduled)'
#     # 'Modem powered up before scheduled operation and powered down after scheduled operation'
#     'Modem is only powered down after a communication session concludes'
# )
# def test_wip():
#     pass


scenarios('../features/modem_powerdown.feature')


def ensure_sc_responds_to_trigger(sign_controller):
    greeting_msg = sign_controller.trigger()
    m = re.match(r'<SGN=\"[a-zA-Z0-9.\-_/]{1,32}\";STS=\"(?P<status_word>[0-9A-F]{4})\"', greeting_msg)
    assert m, f'Sign Controller did not connect despite trigger sent'
    LOGGER.info(f'Sign Controller responded to trigger message: {greeting_msg}')


def ensure_sc_does_not_respond_to_trigger(sign_controller, duration):
    assert duration % 5 == 0, 'duration needs to be a multiple of 5'
    num_retries = int(duration / 5)
    with pytest.raises(testbench.cmc_int.AdcTimeout):
        sign_controller.trigger(retry_interval=5.0, num_retries=num_retries)
        LOGGER.error('Triggered when not meant to')
    LOGGER.info('As expected the Sign Controller did not respond')


@then("the Sign Controller shall still respond to trigger messages after 30s")
def step_check_trigger_response_after_30s(sign_controller):
    time.sleep(30)
    ensure_sc_responds_to_trigger(sign_controller)


@then('the Sign Controller shall respond with MOF# if the CMC issues the command MOF="999999,0000"')
def step_configure_mof1(sign_controller):
    sign_controller.run_cmd('MOF="999999,0000"', 'MOF#')


@when('the CMC issues the command MOF="<mof>,0000"')
def step_impl(sign_controller, mof):
    sign_controller.run_cmd(f'MOF="{mof},0000"', 'ACK')


@then("the Sign Controller shall not respond to any trigger messages for <mof> seconds")
def step_ensure_sc_does_not_respond_to_trigger1(sign_controller, mof):
    ensure_sc_does_not_respond_to_trigger(sign_controller, int(mof))


@then("the Sign Controller shall not respond to trigger messages for the next <no_response_duration_1>")
def step_ensure_sc_does_not_respond_to_trigger1(sign_controller, no_response_duration_1):
    m = re.match(r'(?P<duration>\d+)s', no_response_duration_1)
    assert m, f'Duration proviced in invalid format: {no_response_duration_1}'
    ensure_sc_does_not_respond_to_trigger(sign_controller, int(m.group('duration')))


@then("the Sign Controller shall not respond to trigger messages for the next <no_response_duration_2>")
def step_ensure_sc_does_not_respond_to_trigger2(sign_controller, no_response_duration_2):
    m = re.match(r'(?P<duration>\d+)s', no_response_duration_2)
    assert m, f'Duration proviced in invalid format: {no_response_duration_2}'
    ensure_sc_does_not_respond_to_trigger(sign_controller, int(m.group('duration')))


@then(parsers.parse('the Sign Controller shall not respond to trigger messages for the next {duration}s'))
def step_ensure_sc_does_not_respond_to_trigger3(sign_controller, duration):
    ensure_sc_does_not_respond_to_trigger(sign_controller, int(duration))


@then("the Sign Controller shall respond to trigger messages thereafter")
def step_ensure_sc_responds_to_trigger(sign_controller):
    ensure_sc_responds_to_trigger(sign_controller)


@given('the CMC issues the command MOF="100000,<pre_op_wakeup>"')
def step_configure_mof2(sign_controller, pre_op_wakeup):
    sign_controller.run_cmd(f'MOF="100000,{int(pre_op_wakeup):04d}"', 'ACK')


@then("the Sign Controller shall respond to a trigger message after 60s")
def step_ensure_sc_responds_after_60s(sign_controller):
    time.sleep(60)
    ensure_sc_responds_to_trigger(sign_controller)


@when("the CMC pauses for 30s")
def step_pause():
    time.sleep(30)


@then("the Sign Controller shall respond to a trigger message after 30s")
def step_ensure_sc_responds_after_30s(sign_controller):
    time.sleep(30)
    ensure_sc_responds_to_trigger(sign_controller)


@then("the Sign Controller shall not terminate the session and communicate to CMC commands for 200s")
def step_ensure_sc_does_not_terminate_session(sign_controller):
    end_time = datetime.datetime.now() + datetime.timedelta(seconds=200)
    while True:
        sign_controller.run_cmd('STS?', 'STS=')
        crnt_time = datetime.datetime.now()
        if crnt_time > end_time:
            break
        time.sleep(10)
    LOGGER.info('All good, connection was not severed')


@given('the CMC issues the command MOF="100000,0000"')
def step_issue_mof_cmd(sign_controller):
    sign_controller.run_cmd('MOF="100000,0000"', 'ACK')


