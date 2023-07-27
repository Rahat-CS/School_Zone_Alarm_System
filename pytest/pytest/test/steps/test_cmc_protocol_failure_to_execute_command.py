from pytest_bdd import scenarios, scenario, given, when, then
import logging
import time
import re

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/cmc_protocol_failure_to_execute_command.feature',
#     'Remote Testflash not executed because it would overlap with scheduled operation')
# def test_wip():
#     pass

scenarios('../features/cmc_protocol_failure_to_execute_command.feature')


@then('the command TFL="60,0707" shall fail to execute')
def step_impl(sign_controller):
    tfl_response = sign_controller.run_cmd('TFL="60,0707"', 'TFL#')
    assert tfl_response == '<TFL#>', f'Sign Controller response ({tfl_response}) does not match expected pattern'
    LOGGER.info('TFL command failed to execute as expected')
