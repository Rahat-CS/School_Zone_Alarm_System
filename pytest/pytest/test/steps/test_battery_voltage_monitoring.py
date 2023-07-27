import logging
import re
import time
from pytest_bdd import scenario, scenarios, given, when, then
from pytest_bdd import parsers
from testbench.syslog import SysLog, EventId

LOGGER = logging.getLogger(__name__)


# @scenario('../features/battery_voltage_monitoring.feature', 'Battery low voltage when idle')
# @scenario('../features/battery_voltage_monitoring.feature', 'Battery Voltage Recovery')
# @scenario(
#     '../features/battery_voltage_monitoring.feature',
#     'Battery Voltage Threshold changed from a value above to a value below current Battery Voltage and vice versa')
# def test_work():
#     pass

scenarios('../features/battery_voltage_monitoring.feature')


@then(
    parsers.parse("the battery voltage reported by the Sign Controller should match the PSU settings +/-0.2V\n{data}"))
def step_impl(sign_controller, psu, data):
    LOGGER.info('Starting Battery Voltage reporting test')
    row_re = re.compile(r'\s*\|\s*(?P<voltage>\d{1,2}\.\d{2})V\s*\|')
    btt_re = re.compile(r'<BTT="(?P<btt>\d{2}\.\d{2})">')
    data_rows = data.split('\n')[1:]
    for row in data_rows:
        LOGGER.info('Row ==>>{}<<=='.format(row))
        m1 = row_re.match(row)
        assert m1
        print(m1)
        psu_voltage = m1.group('voltage')
        LOGGER.info('PSU Setting => {}'.format(psu_voltage))
        psu.set_output_voltage(psu_voltage)
        psu_float = float(m1.group('voltage'))
        for i in range(3):
            time.sleep(2)
            btt_resp = sign_controller.run_cmd('BTT?', 'BTT=')
        m2 = btt_re.match(btt_resp)
        assert m2
        btt_float = float(m2.group('btt'))
        assert((btt_float > (psu_float - 0.2)) and (btt_float < (psu_float + 0.1)))
        LOGGER.info('Reported Battery Voltage OK: reported: {} - psu setting: {}'.format(btt_float, psu_voltage))

    LOGGER.info('Completed Battery Voltage reporting test')


def check_low_batt_event(sign_controller, psu_voltage):
    LOGGER.info('Starting check log for Low Battery Voltage event')
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    evt = syslog.get_events_by_id(EventId.BATT_VOLT_BELOW_THRESHOLD)
    assert (len(evt) == 1)
    LOGGER.info('Log contains exactly 1 Low Battery Voltage event as expected: {}'.format(evt))
    voltage_reported_float = float(evt[0].extra_info[0])
    psu_voltage_float = float(psu_voltage)
    assert((voltage_reported_float > (psu_voltage_float - 0.5)) and
           (voltage_reported_float < (psu_voltage_float + 0.5)))
    LOGGER.info('Logged Voltage is OK: {}V (should be {}V)'.format(voltage_reported_float, psu_voltage_float))
    sign_controller.run_cmd('CLG', 'STS=')
    LOGGER.info('Completed check log for Low Battery Voltage event')


@then("the Sign Controllers log contains a Low Battery Voltage event with measured voltage <psu_voltage_new>V")
def step_check_low_batt_event_so(sign_controller, psu_voltage_new):
    check_low_batt_event(sign_controller, psu_voltage_new)


@then(parsers.re(
    r"the Sign Controllers log contains a Low Battery Voltage event with measured " +
    r"voltage (?P<psu_voltage_x>\d{2}\.\d{2})V"))
def step_check_low_batt_event_re(sign_controller, psu_voltage_x):
    check_low_batt_event(sign_controller, psu_voltage_x)


@then("the Sign Controllers log contains a Battery Voltage above threshold event")
def step_check_batt_above_threshold_event(sign_controller):
    LOGGER.info('Starting to check Log for Battery above Threshold event')
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    evt = syslog.get_events_by_id(EventId.BATT_VOLT_ABOVE_THRESHOLD)
    assert (len(evt) == 1)
    LOGGER.info('The log contains exactly one Battery Voltage above Threshold as expected')
    sign_controller.run_cmd('CLG', 'STS=')
    LOGGER.info('Completed check Log for Battery above Threshold event')