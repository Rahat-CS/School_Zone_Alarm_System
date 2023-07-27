from pytest_bdd import scenarios, given, when, then
import logging
import re
import time
from testbench.syslog import SysLog, EventId

LOGGER = logging.getLogger(__name__)

scenarios('../features/display_error_recovery_holdoff.feature')


@given("the Display Recovery Hold-Off period is programmed to <drh>")
def step_impl(sign_controller, drh):
    m = re.match(r'\d{3}', drh)
    assert m, f'the <drh> step parameter supplied does not match the required format'
    sign_controller.update_setting('DRH', f'"{drh}"')
    LOGGER.info(f'The DRH setting has been updated to "{drh}"')


@when(
    "the Power Supply Voltage is reduced to 9V and then increased to 15V 3 times with <psu_interval> inbetween changes")
def step_impl(psu, psu_interval):
    for i in range(3):
        psu_interval_float = float(psu_interval)
        psu.set_output_voltage('9.00')
        time.sleep(psu_interval_float)
        psu.set_output_voltage('15.00')
        time.sleep(psu_interval_float)


@then("after 30s the Sign Controllers System Log shall contain exactly <num_der> Display Error and <num_rec> Recovery events")
def step_impl(sign_controller, num_der, num_rec):
    num_display_error_events_exp = int(num_der)
    num_display_recovery_events_exp = int(num_rec)
    time.sleep(30)
    log_resp = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_resp)
    num_display_error_events = len(syslog.get_events_by_id(EventId.ALERT_DISPLAY_FAILURE))
    num_display_recovery_events = len(syslog.get_events_by_id(EventId.ALERT_DISPLAY_FAILURE_RECOVERY))
    assert num_display_error_events == num_display_error_events_exp, \
        f'Number of Display Error Events in log ({num_display_error_events}) is not as expected ' \
        f'({num_display_error_events_exp})'
    assert num_display_recovery_events == num_display_recovery_events_exp, \
        f'Number of Display Recovery Events in log ({num_display_recovery_events}) is not as expected ' \
        f'({num_display_recovery_events_exp})'


@then("after 30s the display should be operating")
def step_impl(sign_controller):
    # we allow a bit more than 30s to account for timing uncertainties
    time.sleep(30 + 3)
    sts_resp = sign_controller.run_cmd('STS?', 'STS=')
    m = re.match(r'<STS="(?P<sts>[0-9A-F]{4})">', sts_resp)
    assert m, f'Sign Controller response to STS? not as expected: {sts_resp}'
    sts = int(m.group('sts'), 16)
    assert (sts & 0x40 != 0), f'Display does not appear to be active (Status Word returned: {sts_resp}'
