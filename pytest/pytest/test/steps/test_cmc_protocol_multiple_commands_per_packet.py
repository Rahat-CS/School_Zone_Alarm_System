import logging
from pytest_bdd import scenarios, given, when, then, parsers
import re

LOGGER = logging.getLogger(__name__)


scenarios('../features/cmc_protocol_multiple_commands_per_packet.feature')


@then(parsers.parse(
    "the Sign Controller shall respond to multi-command messages as provided in the following table:\n{message_data}"))
def step_impl(sign_controller, message_data):
    data_rows = message_data.split('\n')[1:]
    for row in data_rows:
        [_, msg, resp_regex, _] = [c.strip() for c in row.split('|')]
        LOGGER.info(f'Sending: "{msg}", expecting response to be matched by: "{resp_regex}"')
        response = sign_controller.run_cmd(msg, '')
        m = re.search(resp_regex, response)
        assert m, f'Response does not match expectation\n***{response}***\n***{resp_regex}***'
        LOGGER.info(f'Sign Controller response ({response}) OK, matching expected ({resp_regex})')
