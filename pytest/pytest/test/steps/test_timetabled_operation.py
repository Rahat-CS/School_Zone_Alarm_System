from pytest_bdd import scenario, scenarios, given, when, then, parsers
import logging
from datetime import datetime
import re
import time
from testbench.syslog import SysLog, EventId

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/timetabled_operation.feature',
#     # '1 Segment Timetable utilizing the maximum capacity'
#     # 'Smallest Possible Timetable (1 segment with 1 day only)'
#     # 'Realistic Schedule'
#     # 'Maximum Number of segments utilized'
#     # 'First and Second display operation control'
#     # 'Clock adjustments resulting in scheduled flashing to start or stop immediately'
#     # 'Display Operation based on State of Operation Setting'
#     'Scheduled operation stopping prematurely due to low battery'
# )
# def test_wip():
#     pass


scenarios('../features/timetabled_operation.feature')


def event_type_to_id(event_type:str) -> EventId:
    event_type_stripped = event_type.strip()
    if event_type_stripped == 'COMMENCEMENT':
        return EventId.TIMETABLED_OPERATION_STARTED
    elif event_type_stripped == 'CESSATION':
        return EventId.TIMETABLED_OPERATION_ENDED
    else:
        raise Exception('unknown event type supplied')


def get_display_operating_state(sign_controller) -> str:
    """

    Extract the Display Operating Status from the Status Word

    :param   sign_controller:
    :return: 'ON'  if displays are operating,
             'OFF' otherwise
    """
    sts_resp = sign_controller.run_cmd('STS?', 'STS=')
    m = re.match(r'<STS="(?P<sts>[0-9A-F]{4})">', sts_resp)
    assert m, f'response to STS? does not match expected format'
    return 'ON' if int(m.group('sts'), 16) & 0x40 == 0x40 else 'OFF'


@when("the Sign Controllers clock is set as per table below")
def step_dummy_set_clock():
    """
    This is just a dummy step to make the scenario readable. The entire process of setting the time
    and then wainting for the events to occur will happen in the implementation of the next step.
    """
    pass


@then(
    parsers.parse(
        'the Sign Controller after 30s shall record the events as outlined in the table:\n{data}'
    )
)
def step_check_events_occurring(sign_controller, data):
    data_table = data
    data_rows = data_table.split('\n')[1:]  # skip the 1st row (just column headers)
    for row in data_rows:
        LOGGER.info(100 * '=')
        LOGGER.info(f'Now testing: {row}')
        LOGGER.info(100 * '=')
        [_, crnt_time, crnt_display_state, new_display_state, event_type, event_timestamp, notes, _] = \
            [c.strip() for c in row.split('|')]

        # set the time
        LOGGER.info(f'Setting Sign Controllers time to {crnt_time}')
        crnt_rtc = int(datetime.strptime(crnt_time, '%a %d-%m-%Y %H:%M:%S').timestamp())
        sign_controller.run_cmd('SYN="999"', 'DTE?')
        sign_controller.run_cmd(f'DTE="{crnt_rtc}"', 'SYN=')
        LOGGER.info(f'Sign Controllers time has been updated to {crnt_rtc} ({crnt_time})')

        # Setting the Time might result in an event by itself.
        # clear those out ...
        # wait for 2s to give the SC time to make the transition.
        time.sleep(2)
        sign_controller.run_cmd('LOG?', 'LOG=')
        sign_controller.run_cmd('CLG', 'STS=')

        # check current status
        LOGGER.info('Checking the current Display State (pre-event)')
        time.sleep(2) # wait 2s so Controller can change state if needed
        actual_display_state = get_display_operating_state(sign_controller)
        assert actual_display_state == crnt_display_state, f'Display Operating State not as expected to start with.' \
                                                           f'expected {crnt_display_state} but observed ' \
                                                           f'{actual_display_state}'
        LOGGER.info('Waiting for 30s')
        # wait for 30s
        time.sleep(30.0)

        # Check that the display state is as expected
        LOGGER.info('Checking the current Display State (post-event)')
        actual_display_state = get_display_operating_state(sign_controller)
        assert actual_display_state == new_display_state, f'Display Operating State not as expected after 30s' \
                                                          f'expected {new_display_state} but observed ' \
                                                          f'{actual_display_state}'

        # and finally make sure the event is logged properly
        LOGGER.info('Now checking the Sign Controllers Log')
        log_resp = sign_controller.run_cmd('LOG?', 'LOG=')
        syslog = SysLog(log_resp)
        num_events = syslog.get_num_events()
        if event_type == 'NONE':
            assert num_events == 0, f'Expected no events but found {num_events}'
        else:
            assert num_events == 1, f'Expected exactly 1 event in log but found {num_events}'
            evt = syslog.get_all_events()[0]
            if event_type == 'COMMENCEMENT':
                assert evt.event_id == EventId.TIMETABLED_OPERATION_STARTED, f'Event not as expected: {evt.event_id}' \
                                                                             f'(expected TIMETABLED_OPERATION_STARTED)'
            else:
                assert evt.event_id == EventId.TIMETABLED_OPERATION_ENDED, f'Event not as expected: {evt.event_id}' \
                                                                           f'(expected TIMETABLED_OPERATION_ENDED)'
            event_rtc_expected = int(datetime.strptime(event_timestamp, '%a %d-%m-%Y %H:%M:%S').timestamp())
            event_rtc_actual = int(evt.time_stamp)

            assert event_rtc_actual == event_rtc_expected, f'Event Timestamp not as expected!' \
                                                           f'(exepcted: {event_rtc_expected}, ' \
                                                           f'actual: {event_rtc_actual}'

        # to finish clear out the log for the next iteration
        LOGGER.info('Clearing the Sign Controllers Log')
        sign_controller.run_cmd('CLG', 'STS=')


@then(
    parsers.parse(
        'after 120s the Sign Controllers Log shall contain exactly 2 events,\n{dummy}'
    )
)
def step_check_log_for_start_and_stop_events(sign_controller, dummy):
    time.sleep(120)
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    num_events = syslog.get_num_events()
    assert num_events == 2, f'Number of events in log not as expected'
    events = syslog.get_all_events()
    start_rtc_expected = int(datetime.strptime('Mon 05-10-2020 08:30:00', '%a %d-%m-%Y %H:%M:%S').timestamp())
    stop_rtc_expected = start_rtc_expected + 30
    assert events[0].event_id == EventId.TIMETABLED_OPERATION_STARTED, f'First event in log is not a COMMENCE'
    assert int(events[0].time_stamp) == start_rtc_expected, f'COMMENCEMENT event timestamp not as expected' \
                                                       f'(expected {start_rtc_expected} but got {events[0].time_stamp})'
    assert events[1].event_id == EventId.TIMETABLED_OPERATION_ENDED, f'First event in log is not a CESSATE'
    assert int(events[1].time_stamp) == stop_rtc_expected, f'CESSATION event timestamp not as expected' \
                                                      f'(expected {stop_rtc_expected} but got {events[0].time_stamp}'


@then("after 10min the display state should be OFF")
def step_ensure_display_is_not_operating(sign_controller):
    time.sleep(600)
    sign_controller.trigger()
    display_operating_state = get_display_operating_state(sign_controller)
    assert display_operating_state == 'OFF', f'Expected display to be OFF but it appears to be ' \
                                             f'{display_operating_state}!'
    LOGGER.info('As expected the display is not operating')


@then(
    parsers.parse(
        'the Sign Controller log shall contain the following events in order:\n{event_table}'
    )
)
def step_check_log_for_expected_events(sign_controller, event_table):
    events_expected = event_table.split('\n')[1:]  # skip the 1st row (just column headers)

    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    num_events = syslog.get_num_events()
    assert num_events == 80, f'Expected exactly 40 events but observed {num_events}'

    for (evt_actual, evt_expected) in zip(syslog.get_all_events(), events_expected):
        (_, timestamp_expected, eventtype_expected, _) = evt_expected.split('|')
        assert int(evt_actual.time_stamp) == int(timestamp_expected), \
            f'Event Timestamp not as expected ... expected {timestamp_expected} but observed {evt_actual.time_stamp}'
        assert evt_actual.event_id == event_type_to_id(eventtype_expected), \
            f'Event ID not as expected ... expected {event_type_to_id(eventtype_expected)} but ' \
            f'observed {evt_actual.event_id}'

    LOGGER.info('The Sign Controllers log is exactly as expected')


@given("the Sign Controller is configured with the following time table: <timetable>")
def step_impl(sign_controller, timetable):
    timetable_stripped = re.sub(r'\s', '', timetable)
    sign_controller.update_setting('TTB', f'"{timetable_stripped}"')
    LOGGER.info('Timetable has been updated')


@when(parsers.parse('after 30s the Sign Controllers time is set to {time_str}'))
def step_impl(sign_controller, time_str):
    rtc_new = int(datetime.strptime(time_str, '%d-%m-%Y %H:%M:%S').timestamp())
    time.sleep(30.0)
    sign_controller.run_cmd('SYN="999"', 'DTE?')
    sign_controller.run_cmd(f'DTE="{rtc_new}"', 'SYN=')
    LOGGER.info(f'Sign Controllers RTC has been set to {rtc_new} ({time_str})')


@then("after 30s the Sign Controllers event log shall match the following pattern: <evt_log>")
def step_impl(sign_controller, evt_log):
    syslog_expected = SysLog(f'<LOG={evt_log.strip()}>')
    time.sleep(30.0)
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)

    assert syslog.get_num_events() == syslog_expected.get_num_events(), \
        f'Actual log contains a different number of events compared to the reference log ' \
        f'({syslog.get_num_events()} vs {syslog_expected.get_num_events()}'

    for (actual,expected) in zip(syslog.get_all_events(), syslog_expected.get_all_events()):
        LOGGER.info(f'comparing: {actual} - {expected}')
        assert actual == expected, f'Actual Log event is not as expected ({actual} vs {expected})'
    LOGGER.info('Log appears OK')


@given("the current time of the Sign Controller is set to <current_time>")
def step_impl(sign_controller, current_time):
    new_rtc = int(datetime.strptime(current_time, '%a %d-%m-%Y %H:%M:%S').timestamp())
    sign_controller.run_cmd('SYN="999"', 'DTE?')
    sign_controller.run_cmd(f'DTE="{new_rtc}"', 'SYN=')


@when("the CMC changes the Sign Controllers time to <new_time>")
def step_impl(sign_controller, new_time):
    new_rtc = int(datetime.strptime(new_time, '%a %d-%m-%Y %H:%M:%S').timestamp())
    sign_controller.run_cmd('SYN="999"', 'DTE?')
    sign_controller.run_cmd(f'DTE="{new_rtc}"', 'SYN=')


@then("the Display state shall immediately change to <new_display_state>")
def step_impl(sign_controller, new_display_state):
    assert new_display_state == 'ON' or new_display_state == 'OFF', f'Something wrong with the <new_display_state> ' \
                                                                    f'parameter supplied: {new_display_state}'
    # we have to allow 1s for the change to happen
    time.sleep(1)
    actual_display_state = get_display_operating_state(sign_controller)
    assert actual_display_state == new_display_state, f'New display state ({actual_display_state}) is not as ' \
                                                      f'expected ({new_display_state})'


@then("the state of the Display shall be <crnt_display_state>")
def step_impl(sign_controller, crnt_display_state):
    assert crnt_display_state == 'ON' or crnt_display_state == 'OFF', f'Something wrong with the <crnt_display_state> '\
                                                                      f'parameter supplied: {crnt_display_state}'
    actual_display_state = get_display_operating_state(sign_controller)
    assert actual_display_state == crnt_display_state, f'New display state ({actual_display_state}) is not as ' \
                                                       f'expected ({crnt_display_state})'


@then("the Sign Controlers Log should contain an <event_logged> with a timestamp corresponding to <new_time>")
def step_impl(sign_controller, event_logged, new_time):
    assert event_logged == 'COMMENCEMENT' or event_logged == 'CESSATION', f'Something wrong with <event_logged> ' \
                                                                          f'parameter supplied: {event_logged}'
    event_id_expected = event_type_to_id(event_logged)
    new_rtc = int(datetime.strptime(new_time, '%a %d-%m-%Y %H:%M:%S').timestamp())
    log_resp = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_resp)
    num_events = syslog.get_num_events()
    assert num_events == 1, f'expected exactly 1 event but observed {num_events}'
    event = syslog.get_all_events()[0]
    assert event.event_id == event_id_expected, f'Event ID not as expected .. found {event.event_id} but ' \
                                                f'expected {event_id_expected}'
    assert new_rtc - 5 < int(event.time_stamp) < new_rtc + 5, f'Event timestamp not as expected .. ' \
                                                              f'found {event.time_stamp} but expected {new_rtc} +/- 5'
    LOGGER.info(f'Log is OK: found {event_logged} event with timestamp {event.time_stamp} (expected {new_rtc} +/- 5)')


@given("the Sign Controllers State of Operation is set to <sop>")
def step_impl(sign_controller, sop):
    sign_controller.update_setting('SOP', f'"{sop}"')


@then(parsers.parse("after 30s the Sign Controller shall report status word 0x{sts_str}"))
def step_impl(sign_controller, sts_str):
    time.sleep(30.0)
    sts_expected = int(sts_str, 16)
    sts_resp = sign_controller.run_cmd('STS?', 'STS=')
    m = re.match(r'<STS="(?P<sts>[0-9A-F]{4})"', sts_resp)
    assert m, f'Sign Controller response does not match expected pattern'
    sts_actual = int(m.group('sts'), 16)
    assert sts_actual == sts_expected, f'Status Word not as expected: got {sts_actual:02X} but ' \
                                       f'expected {sts_expected:02X}'


@then("the Sign Controller shall report SOP = 0")
def step_impl(sign_controller):
    sign_controller.run_cmd('SOP?', 'SOP="0"')


@then(parsers.parse("the Sign Controller Log should contain exactly one CESSATION event with timestamp {timestamp}"))
def step_impl(sign_controller, timestamp):
    ts_expected =  int(datetime.strptime(timestamp, '%d-%m-%Y %H:%M:%S').timestamp())
    log_resp = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_resp)
    num_events = syslog.get_num_events()
    assert num_events == 2, f'Unexpected number of events in log: {num_events}. Expected exactly 2 event'
    cessation_events = syslog.get_events_by_id(EventId.TIMETABLED_OPERATION_ENDED)
    assert len(cessation_events) == 1, 'Cessation Event not found in log'
    ts_actual = int(cessation_events[0].time_stamp)
    assert ts_expected - 20 <= ts_actual <= ts_expected + 20, f'Timestamp does not look right. Found {ts_actual} but ' \
                                                            f'expected {ts_expected} +/- 20'