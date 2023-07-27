from pytest_bdd import scenario, scenarios, given, when, then
import logging
import time
import testbench.cmc_int
from testbench.syslog import SysLog, EventId
import pytest
import re
import datetime

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/no_comms.feature',
#     # 'Active session timeout'
#     # 'No communication session for a set time'
#     'Connection retry after failure to establish a connection'
# )
# def test_wip():
#     pass


scenarios('../features/no_comms.feature')


@when('the CMC does not issue any requests for <no_req_period>')
def step_no_requests(no_req_period):
    m = re.match(r'(?P<period>\d+)s', no_req_period)
    assert m, f'Invalid format for <no_req_period> parameter: {no_req_period}'
    time.sleep(float(m.group('period')) - 2) # -2 to allow for some timing uncertaintly


@then('the Sign Controller shall close the active session')
def step_ensure_sc_terminates_session(sign_controller):
    assert sign_controller.is_session_active(), 'There is no active session'
    with pytest.raises(testbench.cmc_int.AdcRemoteSocketClosed):
        time.sleep(5)
        sign_controller.run_cmd('STS?', 'STS=')
    LOGGER.info('As expected the Sign Controller terminated the active session')


@given('the Sign Controller is configured with STD="<std>"')
def step_config_std(sign_controller, std):
    sign_controller.update_setting('STD', f'"{std.strip()}"')
    sign_controller.run_cmd('STD?', 'STD=')


@given('the Sign Controller is configured with TMO="<tmo>"')
def step_config_tmo(sign_controller, tmo):
    m = re.match(r'(?P<duration>\d+)', tmo)
    assert m, f'Invalid format for <tmo> parameter: {tmo}'
    sign_controller.update_setting('TMO', f'"{tmo}"')


@when('there is no communication for <no_comm_period>')
def step_no_comm(no_comm_period):
    m = re.match(r'(?P<period>\d+)s', no_comm_period)
    assert m, f'Invalid format for <no_req_period> parameter: {no_comm_period}'
    time.sleep(float(m.group('period')))


@then("the System Log shall contain exactly one CMC Communication Timeout event")
def step_check_syslog_for_nocomm_event(sign_controller):
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    evt = syslog.get_events_by_id(EventId.CMC_COMMUNICATION_TIMEOUT)
    assert len(evt) == 1, f'More than one CMC Communication Timeout found in log: {len(evt)} events'
    assert syslog.get_num_events() == 1, f'More than one event found in Syslog: {syslog.get_num_events()} events'
    LOGGER.info('Log contains exactly 1 CMC Communication Timeout event as expected: {}'.format(evt))
    sign_controller.run_cmd('CLG', 'STS=')


@given('the Sign Controller is configured with CTD="<ctd>"')
def step_configure_ctd(sign_controller, ctd):
    m = re.match(r'(?P<duration>\d{1,4})', ctd)
    assert m, f'Invalid format for the <ctd> parameter: {ctd}'
    sign_controller.update_setting('CTD', f'"{ctd}"')


@then("the Sign Controller shall attempt to establish a CMC session")
def step_monitor_for_connection_attemmpt(sign_controller):
    assert \
        sign_controller.listen_for_connection_attempt(10), \
        'No connection attempt observed'

    LOGGER.info('A connection attempt was observed - as expected')
    # this is to allow time for the modem to 'detect rejection'
    time.sleep(10)


@when("the CMC rejects the connection attempt")
def step_reject_connection():
    """
    THis is just a dummy step to make the scenario more readable.
    The connection attempt is not accepted in the previous step already
    :return:
    """
    pass


@then("the Sign Controller shall not attempt another connection until <holdoff_duration> after the first attempt")
def step_monitor_for_connection_attempt(sign_controller, holdoff_duration):
    m = re.match(r'(?P<ho_duration>\d+)s', holdoff_duration)
    assert m, f'<holdoff_duration> parameter format is wrong: {holdoff_duration}'
    duration = int(m.group('ho_duration'))
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(seconds=duration)
    greeting_msg = sign_controller.listen(timeout=duration + 30)
    crnt_time = datetime.datetime.now()
    assert crnt_time >= end_time, f'Observed another connection attempt after only {crnt_time-start_time}'
    LOGGER.info(f'As expected another connection attempt was observed after {crnt_time-start_time}')


@when("the CMC does nothing for 30s")
def step_impl():
    time.sleep(30)
