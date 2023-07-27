from pytest_bdd import scenario, scenarios, given, when, then, parsers
import logging
import time

LOGGER = logging.getLogger(__name__)


scenarios('../features/cmc_protocol_erronous_command_handling.feature')


@then(parsers.parse("the CMC shall respond to faulty messages as shown in the following table:\n{test_table}"))
def step_impl(sign_controller, test_table):
    data_rows = test_table.split('\n')[1:]
    for row in data_rows:
        [_, command, expected, note, _] = [c.strip() for c in row.split('|')]
        LOGGER.info(f'Sending: "{command}", expected response: "{expected}"')
        response = sign_controller.send_raw(command)
        assert response == expected, f'Actual response {response} does not match expected response {expected}'
        LOGGER.info(f'Sign Controller response ({response}) OK, matching expected ({expected})')
        time.sleep(5)



