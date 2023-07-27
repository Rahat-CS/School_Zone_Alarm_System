import logging
from pytest_bdd import scenario, scenarios, given, when, then
from pytest_bdd import parsers
import testbench
from testbench.syslog import SysLog, EventId
import re
import time

LOGGER = logging.getLogger(__name__)


# @scenario('../features/alert_display_error_detection.feature', 'Lantern failure during Self Check')
# @scenario('../features/alert_display_error_detection.feature', 'Lantern Failure during Test Flash')
# @scenario('../features/alert_display_error_detection.feature', 'Lantern recovery')
# @scenario('../features/alert_display_error_detection.feature', 'Multiple lanterns failing at the same time')
# @scenario('../features/alert_display_error_detection.feature', 'Partial only recovery')
# def test_under_development():
#     pass


scenarios('../features/alert_display_error_detection.feature')


@when('the Sign Controller starts a scheduled flashing cycle')
def step_start_scheduled_flashing(sign_controller):
    LOGGER.info('Starting start scheduled flashing')
    # the following timetable is the same as the default.
    # Sending it again, just to make sure this is the one used for the following step
    # The start time for this one is 0x588BA6C0=1485547200=Friday, January 27, 2017 20:00:00 (GMT)
    #
    time_table = (
        '"01588BA6C0FC82AA02A82A20AA82AA0A282AA0AA828A0AA82AA0A28'
        '2AA0AA822A0AA02AA0AA82A20AA80AA0A882AA0AA828A0AA82AA08A8'
        '2AA0AA822A0AA02AA0AA822A0FF"'
    )
    sign_controller.update_setting('TTB', time_table)
    # Now we just set the time to ~15 sec prior to scheduled start
    sign_controller.run_cmd('SYN="999"', 'DTE?')
    sign_controller.run_cmd('DTE="1485547185"', 'SYN=')
    time.sleep(30)
    LOGGER.info('Completed start scheduled flashing')


@given('an <lantern> lantern display error has occurred')
def step_create_diplay_error(lantern, sign_controller):
    LOGGER.info('Starting create lantern display error')
    assert lantern == 'right' or lantern == 'left' or lantern == 'annulus'
    if lantern == 'left':
        ect = '5000,0000,0000'
        der_expected = 1
    elif lantern == 'right':
        der_expected = 2
        ect = '0000,5000,0000'
    else:
        der_expected = 4
        ect = '0000,0000,5000'
    sign_controller.run_cmd('ECT="{}"'.format(ect), 'ACK')
    sign_controller.run_cmd('SCK', 'SCK="0"')
    der_re = re.compile('<DER="(?P<der_byte>[0-9A-F]{2})"')
    der_response = sign_controller.run_cmd('DER?', 'DER=')
    m = der_re.match(der_response)
    assert m

    assert '0x{}'.format(m.group('der_byte')) == '0x{:02x}'.format(der_expected)
    sign_controller.run_cmd('LOG?', 'LOG=')
    sign_controller.run_cmd('CLG', 'STS=')
    LOGGER.info('Completed create lantern display error')


@then('the Sign Controllers log contains a Display Failure Recovery event')
def check_display_error_recovery(sign_controller):
    LOGGER.info('Starting check for display recovery log event')
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    events = syslog.get_events_by_id(EventId.ALERT_DISPLAY_FAILURE_RECOVERY)
    LOGGER.info('Checking for correct length of Log retrieved')
    assert len(events) == 1
    LOGGER.info('Completed check for display recovery log event')


@when('the CMC requests a Self Check')
def step_self_check(sign_controller, context):
    LOGGER.info('Starting Self Check')
    context['sck_response'] = sign_controller.run_cmd('SCK', 'SCK=')
    LOGGER.info('Self-Check Result: {}'.format(context['sck_response']))
    LOGGER.info('Completed Self Check')


@then("the Sign Controller responds that the Self Check failed")
def step_check_self_test_response(context):
    """
    Note that we assume that the self check response has been
    stored in context['sck_response'] in a previous step
    """
    LOGGER.info('Starting check Self Check response')
    assert context['sck_response'] == '<SCK="0">'
    LOGGER.info('Completed check Self Check response')


@when("the CMC requests a Test Flash")
def step_run_test_flash(sign_controller):
    LOGGER.info('Starting Run Test Flash')
    resp = sign_controller.run_cmd('TFL="10,7070"', 'ACK')
    assert resp == '<ACK>'
    time.sleep(15)
    LOGGER.info('Completed Run Test Flash')


@then("the Sign Controllers log shall not contain any Display Failure Recover events")
def step_check_log_no_recovery(sign_controller):
    LOGGER.info('Starting check for lack of display recovery log event')
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    events = syslog.get_events_by_id(EventId.ALERT_DISPLAY_FAILURE_RECOVERY)
    LOGGER.info('Checking for correct length of Log retrieved')
    assert (len(events) == 0)
    LOGGER.info('Completed check for lack of display recovery log event')
