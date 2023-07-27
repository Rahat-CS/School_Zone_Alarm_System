from pytest_bdd import scenario, scenarios, given, when, then
import re
import time
import logging
from testbench.syslog import SysLog, EventId
import testbench.doorswitch

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/testflash.feature',
#     #'Remote Testflash'
#     'Local Testflash'
# )
# def test_wip():
#     pass


scenarios('../features/testflash.feature')


@when('the CMC issues the Command: TFL="<tfl_duration>,70"')
def step_issue_tfl_cmd(sign_controller, tfl_duration):
    m = re.match(r'\d{2}', tfl_duration)
    assert m, f'supplied parameter tfl_duration does not match the required format'
    sign_controller.run_cmd(f'TFL="{tfl_duration},70"', 'ACK')


@then("the Sign Controller shall operate the displays for the next <tfl_duration> seconds")
def step_ensure_display_operating(sign_controller, tfl_duration):
    m = re.match(r'\d{2}', tfl_duration)
    assert m, f'supplied parameter tfl_duration does not match the required format'
    time.sleep(float(tfl_duration) - 5.0)
    sts_resp = sign_controller.run_cmd('STS?', 'STS=')
    m = re.match(r'<STS="(?P<sts>[0-9A-F]{4})">', sts_resp)
    assert m, f'format of STS? response is not OK'
    sts_int = int(m.group('sts'), 16)
    assert (sts_int & 0x40) != 0, f'FLH bit is not set'
    LOGGER.info('Display appears to be operating as expected')
    # We need to wait until testflash completes to have the cessation event in the log!
    LOGGER.info('waiting for 10s (Testflash should stop by this time)')
    time.sleep(10)
    LOGGER.info('10s wait complete, continuing ...')


@then("the System Log shall contain Testflash Start and Stop events exactly <tfl_duration> seconds apart")
def step_check_log(sign_controller, tfl_duration):
    m = re.match(r'\d{2}', tfl_duration)
    assert m, f'supplied parameter tfl_duration does not match the required format'
    tfl_duration_int = int(tfl_duration)
    log_resp = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_resp)
    LOGGER.info(f'Log received: {syslog}')
    # Note: at the moment the Test-flash will create regular COMMENCEMENT/CESSATION events.
    # this will chang to dedicated events in the near future
    start_evt = syslog.get_events_by_id(EventId.TESTFLASH_STARTED)
    num_start_evt = len(start_evt)
    stop_evt = syslog.get_events_by_id(EventId.TESTFLASH_ENDED)
    num_stop_evt = len(stop_evt)
    assert num_start_evt == 1, f'Log should contain exactly 1 start event, but found {num_start_evt}'
    assert num_stop_evt == 1, f'Log should contain exactly 1 stop event, but found {num_stop_evt}'
    tf_start_time = int(start_evt[0].time_stamp)
    tf_stop_time = int(stop_evt[0].time_stamp)
    tfl_duration_actual = (tf_stop_time - tf_start_time)
    assert \
        -1 <= (tfl_duration_actual - tfl_duration_int) <= 1, \
        f'TFL start/stop time difference ({tfl_duration_actual})' \
        f'from log does not match (within 1 second)' \
        f'the requested duration ({tfl_duration_int})'
    LOGGER.info('Log is OK - Events logged match expectation')


@when('the Sign Controllers door switch is closed and opened 3 times with 1s interval between closing/opening')
def step_toggle_door_switch_to_trigger_testflash(door_switch):
    time.sleep(5)
    for i in range(3):
        time.sleep(0.5)
        door_switch.set_state(testbench.doorswitch.DoorState.CLOSED)
        time.sleep(0.5)
        door_switch.set_state(testbench.doorswitch.DoorState.OPEN)


@then("the Sign Controller shall operate the displays for 30s")
def step_ensure_display_operating(psu):
    time.sleep(2)
    current_draw = float(psu.get_output_current())
    assert current_draw > 0.2, f'Does\'t look like the display is operating, the current draw is ' \
                               f'too low ({current_draw}A)'
    time.sleep(27)
    current_draw = float(psu.get_output_current())
    assert current_draw > 0.2, f'Does\'t look like the display is operating, the current draw is ' \
                               f'too low ({current_draw}A)'
    time.sleep(5)
    current_draw = float(psu.get_output_current())
    assert current_draw < 0.2, f'Looks like the display is still operating, the current draw is ' \
                               f'too high for idle state ({current_draw}A)'


@given("there shall be only Door Open and Door Close Events in the System Log once the testflashing completes")
def step_impl(sign_controller):
    log_resp = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_resp)
    num_events = syslog.get_num_events()
    num_door_open_events = len(syslog.get_events_by_id(EventId.DOOR_OPEN))
    num_door_closed_events = len(syslog.get_events_by_id(EventId.DOOR_CLOSE))
    assert num_events == num_door_closed_events + num_door_open_events, \
        f'The number of door open events ({num_door_open_events}) and door close events ({num_door_closed_events}) ' \
        f'does not add up to the total number of events in the Sign Controllers log ({num_events})'


