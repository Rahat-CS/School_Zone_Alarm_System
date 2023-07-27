from pytest_bdd import scenario, given, when, then, parsers, scenarios
from testbench.syslog import SysLog, EventId
import testbench.doorswitch
import logging
import time

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/doorswitch_monitoring.feature',
#     # 'Door opened or closed when idle'
#     # 'Door opened or closed when scheduled flashing is in progress'
#     'Local Testflash'
# )
# def test_wip():
#     pass

scenarios('../features/doorswitch_monitoring.feature')


@given('the Sign Controllers State of Operation is set to "<sop>"')
def step_impl(sign_controller, sop):
    assert sop == '0' or sop == '1', f'Unknown value for <sop>: {sop}'
    sign_controller.update_setting('SOP', f'"{sop}"')


@given(parsers.parse('the Sign Controllers State of Operation is set to "{sop}"'))
def step_impl(sign_controller, sop):
    assert sop == '0' or sop == '1', f'Unknown value for <sop>: {sop}'
    sign_controller.update_setting('SOP', f'"{sop}"')


def check_syslog_for_exaclty_one_event(sign_controller, syslog_event):
    syslog_event_expected = syslog_event.strip()
    assert \
        syslog_event_expected == 'DOOR_OPENED' or syslog_event_expected == 'DOOR_CLOSED', \
        f'unknown event: {syslog_event_expected}'

    syslog_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog_retrieved = SysLog(syslog_response)

    if syslog_event_expected == 'DOOR_OPENED':
        events = syslog_retrieved.get_events_by_id(EventId.DOOR_OPEN)
    else:
        events = syslog_retrieved.get_events_by_id(EventId.DOOR_CLOSE)
    assert len(events) == 1, f'Number of events in Syslog is not as expected (found {len(events)} events)'
    LOGGER.info('Syslog content appears to be OK')


@then("the Sign Controller Log should contain exactly one <syslog_event> event")
def step_check_syslog_for_exactly_one_door_event(sign_controller, syslog_event):
    check_syslog_for_exaclty_one_event(sign_controller, syslog_event)


@then(parsers.parse("the Sign Controller Log should contain exactly one {syslog_event_x} event"))
def step_check_syslog_for_exactly_one_door_event(sign_controller, syslog_event_x):
    check_syslog_for_exaclty_one_event(sign_controller, syslog_event_x)


@when(parsers.parse("after {delay} seconds the door switch is <door_action>"))
def step_impl(door_switch, delay, door_action):
    action = door_action.strip()
    assert action == 'closed' or action == 'opened', f'Unknown door action: {door_action}'

    time.sleep(int(delay))
    if action == 'closed':
        door_switch.set_state(testbench.doorswitch.DoorState.CLOSED)
    else:
        door_switch.set_state(testbench.doorswitch.DoorState.OPEN)


@when('the Sign Controllers door switch is closed and opened 3 times with 1s interval between closing/opening')
def step_toggle_door_switch_to_trigger_testflash(door_switch):
    time.sleep(5)
    for i in range(3):
        time.sleep(0.5)
        door_switch.set_state(testbench.doorswitch.DoorState.CLOSED)
        time.sleep(0.5)
        door_switch.set_state(testbench.doorswitch.DoorState.OPEN)


@then('the Sign Controller shall respond with a 30s test flash cycle')
def step_check_for_testflash(sign_controller, psu):
    # we want to wait for the cycle to complete
    time.sleep(10)
    sts_response = sign_controller.run_cmd('STS?', 'STS=')
    current_draw = float(psu.get_output_current())
    assert \
        current_draw > 0.2, f'Current draw not sufficiently high ({current_draw}A), ' \
        f'does not look like flashing is happening (expected > 0.2A)'
    time.sleep(10)
    sts_response = sign_controller.run_cmd('STS?', 'STS=')
    time.sleep(10)
    sts_response = sign_controller.run_cmd('STS?', 'STS=')
    time.sleep(10)
    sts_response = sign_controller.run_cmd('STS?', 'STS=')


@then('the Sign Controllers log shall not contain any events indicating flashing has occurred')
def step_check_syslog_for_no_flashing_events(sign_controller):
    syslog_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog_retrieved = SysLog(syslog_response)
    # the only events in the Syslog at this stage should be door open/close events
    num_door_open_events = len(syslog_retrieved.get_events_by_id(testbench.syslog.EventId.DOOR_OPEN))
    num_door_close_events = len(syslog_retrieved.get_events_by_id(testbench.syslog.EventId.DOOR_CLOSE))
    num_flash_request_events = len(syslog_retrieved.get_events_by_id(testbench.syslog.EventId.LOCAL_TEST_FLASH_REQUEST))
    num_all_events = syslog_retrieved.get_num_events()

    assert num_door_open_events == 3, f'{num_door_open_events} DOOR_OPEN events, not 3: {syslog_retrieved}'
    assert num_door_close_events == 3, f'{num_door_close_events} DOOR_CLOSE events, not 3: {syslog_retrieved}'
    assert num_flash_request_events == 1, f'{num_flash_request_events} LOCAL_TEST_FLASH_REQUEST events, not 1: {syslog_retrieved}'
    assert num_all_events == 7, f'There appear to be some events other than Door Open and Door Closed in the System Log: {syslog_retrieved}'


