from pytest_bdd import scenario, scenarios, given, when, then, parsers
from testbench.syslog import SysLog, EventId, Event
import logging
import time
import re

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/syslog.feature',
#     'Syslog capacity and overflow'
#     # 'Event Numbering'
#     # 'Alarm generation if alarm events remain in the SystemLog when a CMC session is concluded'
#     # 'Retaining of un-retrieved events'
#     # 'System Log is retained when sending fails'
#     # 'System Log is retained across reboots'
# )
# def test_wip():
#     pass

scenarios('../features/syslog.feature')


@given("the Sign Controller is idle")
def step_make_sc_idle(sign_controller):
    if sign_controller.is_session_active():
        sign_controller.run_cmd('END', 'ACK')
        time.sleep(5)
        sign_controller.end_session()


@then(parsers.parse('the System Log shall contain exactly 250 events numbered from {sqz_first} to {sqz_last}'))
def step_check_log_cap_and_evt_numbering(sign_controller, sqz_first, sqz_last):
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    num_events = syslog.get_num_events()
    assert num_events == 250, f'Syslog does not contain 250 Events (it contains {num_events} events)'
    # the first Event Sqz Num will be consumed by the Restart Event which should have been cleared
    # as part of the Background. The first event now (sqz_num = 001) has to be a DOOR_OPEN
    idx = int(sqz_first)
    for evt in syslog.get_all_events():
        if idx % 2 != 0:
            assert evt.event_id == EventId.DOOR_OPEN, f'Unexpected Event Type found'
        else:
            assert evt.event_id == EventId.DOOR_CLOSE, f'Unexpected Event Type found'
        assert evt.sqz_num == f'{idx:03d}', f'Event Sequence Number not as expected'
        LOGGER.info(f'Event Sequence Number and Type is OK: {evt.sqz_num}:{evt.event_id}')
        if idx == 999:
            idx = 0
        else:
            idx += 1
    LOGGER.info('System Log appears to be OK')


@then(
    parsers.parse(
        'the Sign Controller shall attempt to establish a communication session and send STS="{status_word}"'
    )
)
def step_wait_for_connection_and_check_status(sign_controller, status_word):
    greeting_msg = sign_controller.listen(timeout=240)
    m = re.match(r'<SGN="ABC1234";STS="(?P<status_word>\d{4})">', greeting_msg)
    assert m, f'Greeting Message did not match expected format (greeting received: {greeting_msg})'
    status_word_actual = m.group('status_word')
    assert \
        status_word_actual == status_word, \
        f'Status Word different than expected  - actual: {status_word_actual}, expected {status_word}'

    LOGGER.info('Sign Controller established connection and Status Word is as expected')


@then("the Sign Controller shall return a log with exactly 1 low battery event when the CMC requests the log")
def step_ensure_log_contains_one_low_battery_event(sign_controller):
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    assert syslog.get_num_events() == 1, f'More than 1 event in log ({syslog.get_num_events()}'
    num_low_batt_events = len(syslog.get_events_by_id(EventId.BATT_VOLT_BELOW_THRESHOLD))
    assert \
        num_low_batt_events == 1, \
        f'Event in log is not a low battery event'

    LOGGER.info('Log contains exactly 1 low battery event as expected')


@when("the CMC issues the CLG command")
def step_issue_clg(sign_controller):
    sign_controller.run_cmd('CLG', 'STS=')


@then("the Sign Controller shall return a log with exactly 1 battery OK event when the CMC requests the log")
def step_ensure_log_contains_one_battery_ok_event(sign_controller):
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    assert syslog.get_num_events() == 1, f'More than 1 event in log ({syslog.get_num_events()}'
    num_batt_ok_events = len(syslog.get_events_by_id(EventId.BATT_VOLT_ABOVE_THRESHOLD))
    assert \
        num_batt_ok_events == 1, \
        f'Event in log is not a battery voltage above threshold event'

    LOGGER.info('Log contains exactly 1 battery above threshold event as expected')


@when("the CMC terminates the communication session after issuing the LOG? command but before receiving the response")
def step_terminate_session_before_sc_can_respond(sign_controller):
    sign_controller.send('<LOG?>', wait_for_response=False)
    sign_controller.end_session()


@when("the CMC issues the command RBT")
def step_reboot(sign_controller):
    sign_controller.run_cmd('RBT', 'ACK')
    sign_controller.end_session()
    LOGGER.info('Reboot command has been successfully sent')


@then(
    parsers.parse(
        'the Sign Controller connects to the CMC with a greeting message indicating the {fw} is running'
    )
)
def step_ensure_sign_controller_connects(sign_controller, fw):
    assert fw == 'Application' or fw == 'Bootloader', f'unknown FW type specified: {fw}'
    greeting_msg = sign_controller.listen(timeout=240)
    if fw == 'Bootloader':
        greeting_regex = (
            r'<SGN="####";ADN="\d{8}";FWV="(?P<app_version>\d\.\d{2}(?:RC\d+)?\+?)_(?P<boot_version>\d\.\d{2}(?:RC\d+)?\+?)">'
        )
    else:
        greeting_regex = r'<SGN="ABC1234";STS="0001">'
    m = re.match(greeting_regex, greeting_msg)
    assert m, f'Greeting message received ({greeting_msg}) does not conform to expected format ({greeting_regex})'
    LOGGER.info(f'Received greeting message {greeting_msg} as expected')


@when('the CMC issues the END command')
def step_issue_end_command(sign_controller):
    sign_controller.run_cmd('END', 'ACK')
    sign_controller.end_session()


@then("the Sign Controller shall return a log with exactly 3 events, one each for Restart, Commencement and Cessation")
def step_impl(sign_controller):
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    num_events_total = syslog.get_num_events()
    num_restart_events = len(syslog.get_events_by_id(EventId.ADC_UNEXPECTED_INIT))
    num_commencement_events = len(syslog.get_events_by_id(EventId.TIMETABLED_OPERATION_STARTED))
    num_cessation_events = len(syslog.get_events_by_id(EventId.TIMETABLED_OPERATION_ENDED))
    assert num_events_total == 3, f'Log does not contain exactly 3 events (it contains {num_events_total} events)'
    assert num_commencement_events == 1, f'Log does not contain exactly 1 Commencement ' \
                                         f'event (actual number: {num_commencement_events})'
    assert num_cessation_events == 1, f'Log does not contain exactly 1 Cessation event ' \
                                      f'(actual number: {num_cessation_events})'
    assert num_restart_events == 1, f'Log does not contain exactly 1 Restart event ' \
                                    f'(actual number: {num_restart_events})'
    LOGGER.info(
        f'Log contains exactly {num_events_total} events, {num_commencement_events} Commencment,'
        f'{num_cessation_events} Cessation and {num_restart_events} Events'
    )


