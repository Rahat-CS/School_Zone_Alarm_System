import logging
import re
import time
from pytest_bdd import scenario, scenarios, given, when, then
from pytest_bdd import parsers
from testbench.syslog import SysLog, EventId

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/alert_display_self_check.feature',
#     'Successful self-check whilst idle (no scheduled flashing in progress)')
# @scenario(
#     '../features/alert_display_self_check.feature',
#     'Self-check failure whilst idle - no scheduled flashing in progress'
# )
# @scenario(
#     '../features/alert_display_self_check.feature',
#     'Self-check failure during scheduled operation'
# )
# def test_work():
#     pass


scenarios('../features/alert_display_self_check.feature')


@given("the lantern thresholds are configured as 300mA, 300mA, 1700mA (left, right, annulus respectively)")
def step_set_lantern_thresholds(sign_controller):
    LOGGER.info('Starting set lantern thresholds')
    sign_controller.update_setting('ECT', '"0300,0300,1700"')
    LOGGER.info('Completed set lantern thresholds')


@given('the lantern thresholds for left, right and annulus are configured as <current_thresholds>')
def step_set_lantern_thresholds_so(sign_controller, current_thresholds):
    LOGGER.info('Starting set lantern thresholds (Scenario Outline)')
    thresholds_re = re.compile(r'(?P<left>\d{1,4})mA,\s(?P<right>\d{1,4})mA,\s(?P<annulus>\d{1,4})mA')
    m = thresholds_re.search(current_thresholds)
    assert m, 'Could not decode Current Thresholds from Scenario Step'
    thr_left_int    = int(m.group('left'))
    thr_right_int   = int(m.group('right'))
    thr_annulus_int = int(m.group('annulus'))
    sign_controller.update_setting('ECT', '"{:04d},{:04d},{:04d}"'.format(thr_left_int, thr_right_int, thr_annulus_int))
    LOGGER.info('Completed set lantern thresholds (Scenario Outline)')


@then("the Self Check command should succeed")
def step_check_self_check_succeeds(sign_controller):
    LOGGER.info('Starting check that Self Check succeeds')
    sign_controller.run_cmd('SCK', 'SCK="1"')
    LOGGER.info('Completed check that self check succeeds')


@then("the Self Check command should fail")
def step_check_self_check_fail(sign_controller):
    LOGGER.info('Starting check that Self Check fails')
    sck_resp = sign_controller.run_cmd('SCK', 'SCK')
    assert sck_resp == '<SCK="0">', 'Self Check did not fail as expected'
    LOGGER.info('Self Check failed as expected')
    LOGGER.info('Completed check that Self Check fails')
