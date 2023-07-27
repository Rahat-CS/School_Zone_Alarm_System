from pytest_bdd import scenarios, given, when, then
import logging
import re
import time
from testbench.syslog import SysLog, EventId

LOGGER = logging.getLogger(__name__)

scenarios('../features/display_error_hysteresis.feature')


@given('the Display Error Recovery Hysteresis value is set to <drt>')
def step_configure_drt(sign_controller, drt):
    sign_controller.update_setting('DRT', f'"{drt.strip()}"')


@when("the PSU Voltage is gradually increased")
def step_increase_voltage():
    """
    This is just a dummy step to increase readibility of the test.
    The actual increase of PSU Voltage is done in the step that checks for the
    Display Recovery condition
    """
    pass


def check_status_word_for_display_error_bit_set(sign_controller) -> bool:
    sts_response = sign_controller.run_cmd('STS?', 'STS=')
    m = re.match(r'<STS="(?P<sts_word>[0-9A-F]{4})"', sts_response)
    assert m, f'Response to STS? does not match the expected pattern (received: {sts_response})'
    sts_word_int = int(m.group('sts_word'), 16)
    if sts_word_int & 0x02:
        return True
    else:
        return False


@then("a Display Error Alarm should be shown in the Status Word")
def step_check_disp_error_in_status_word(sign_controller):
    time.sleep(5)
    sts_response = sign_controller.run_cmd('STS?', 'STS=')
    m = re.match(r'<STS="(?P<sts_word>[0-9A-F]{4})"', sts_response)
    assert m, f'Response to STS? does not match the expected pattern (received: {sts_response})'
    sts_word_int = int(m.group('sts_word'), 16)
    assert sts_word_int & 0x1, f'The Alarm bit of the Status word is not set (status word received:{sts_word_int:02x})'
    assert sts_word_int & 0x2, f'The Display Error bit of the Status word is not set ' \
                               f'(status word received:{sts_word_int:02x})'
    LOGGER.info('Display Error has been flagged as expected!')


@then("the display recovery alarm should not occur until the PSU Voltage reaches <recovery_voltage>")
def step_impl(sign_controller, psu, recovery_voltage):
    psu_voltage = float(psu.get_output_voltage_setting())
    assert psu_voltage == 9.00, f'PSU Output Voltage Setting is not as expected (expected 9.00V, ' \
                                f'but read {psu_voltage}V)'
    recovery_observed = False
    while psu_voltage < 15.0:
        psu_voltage += 0.25
        psu.set_output_voltage(psu_voltage)
        LOGGER.info(f'PSU Voltage now is set to {psu_voltage}V')
        time.sleep(1)
        if not check_status_word_for_display_error_bit_set(sign_controller):
            recovery_observed = True
            break
        sign_controller.run_cmd('BTT?', 'BTT=')  #DAVE
        sign_controller.run_cmd('DER?', 'DER=')  #DAVE
    assert recovery_observed, f'No Display recovery observed'
    assert \
        (float(recovery_voltage) - 0.5) <= psu_voltage <= (float(recovery_voltage) + 0.5), \
        f"PSU Voltage when recovery was observed ({psu_voltage}V) not in expected range " \
        f"({float(recovery_voltage)-0.5} to {float(recovery_voltage)+0.5} V)"

    LOGGER.info(f'Display Recovery was observed at {psu_voltage}V')


@then("The Sign Controllers log should contain a display failure as well as recovery event")
def step_impl(sign_controller):
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    display_failure_events = syslog.get_events_by_id(EventId.ALERT_DISPLAY_FAILURE)
    fail_count = len(display_failure_events)
    display_recovery_events = syslog.get_events_by_id(EventId.ALERT_DISPLAY_FAILURE_RECOVERY)
    recover_count = len(display_recovery_events)
    assert \
        fail_count == recover_count, \
        f'Mismatch of Failure Events ({fail_count}) and Recovery Events ({recover_count})' \
        'found in Syslog'
    assert recover_count >= 1, 'No recovery reported in Syslog'
