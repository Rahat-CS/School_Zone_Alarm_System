from pytest_bdd import scenarios, given, when, then, parsers
import logging
import time
import re
from statistics import mean

import testbench.common
LOGGER = logging.getLogger(__name__)


scenarios('../features/power_consumption.feature')




@then(
    parsers.parse(
        "the Sign Contoller shall not draw more current than outlined by the following table:\n{data_table}"
    )
)
def step_impl(sign_controller, j_link, release_pkg, psu, data_table):
    avg_currents = {}
    data_rows = data_table.split('\n')[1:]
    for row in data_rows:
        [_, state, target_current_str, _] = [c.strip() for c in row.split('|')]

        target_current = int(target_current_str)/1000

        LOGGER.info(f'Now measuring current consumption when in state {state}')

        testbench.common.step_start_application_fw(sign_controller, j_link, release_pkg, psu, erase_syslog=True, stop_capture=True)
        sign_controller.listen(timeout=240)

        if state == 'flashing_no_comm':
            sign_controller.update_setting('FPN', '"00"')
            sign_controller.update_setting('TTB', '"0100000000FFFF"')
            sign_controller.update_setting('TTO', '"300,60,60"')
            sign_controller.update_setting('SOP', '"1"')
            # the Display should start operating right away
            time.sleep(5)
            sts_response = sign_controller.run_cmd('STS?', 'STS=')
            m = re.match(r'<STS="(?P<status_word>[0-9A-F]{4})">', sts_response)
            assert m, f'Response to STS? not as expected'
            sts = int(m.group('status_word'), 16)
            assert sts & 0xC0 != 0, f'Status word not as expected: {sts:04x}'
            LOGGER.info('Displays are operating')
            LOGGER.info('Now ending Communication Session')
            sign_controller.run_cmd('END', 'ACK')
            time.sleep(5)
            sign_controller.end_session()
            LOGGER.info('Waiting for 60s (let the modem reboot if it wants to ...)')
            time.sleep(60)
            actual_currents = []
            for i in range(10):
                actual_current = float(psu.get_output_current())
                LOGGER.info(f'Actual current draw observed: {actual_current}A')
                actual_currents.append(actual_current)
            avg_current = mean(actual_currents)
            assert \
                avg_current < target_current, \
                f'Actual current draw ({avg_current}A) is higher than target'

            LOGGER.info(f'Current Draw when flashing without CMC communication: {avg_current}A')
            avg_currents[state] = avg_current

        elif state == 'flashing_with_comm':
            sign_controller.update_setting('FPN', '"00"')
            sign_controller.update_setting('TTB', '"0100000000FFFF"')
            sign_controller.update_setting('TTO', '"300,60,60"')
            sign_controller.update_setting('SOP', '"1"')
            # the Display should start operating right away
            time.sleep(5)
            sts_response = sign_controller.run_cmd('STS?', 'STS=')
            m = re.match(r'<STS="(?P<status_word>[0-9A-F]{4})">', sts_response)
            assert m, f'Response to STS? not as expected'
            sts = int(m.group('status_word'), 16)
            assert sts & 0xC0 != 0, f'Status word not as expected: {sts:04x}'
            LOGGER.info('Displays are operating')
            actual_currents = []
            for i in range(10):
                sign_controller.run_cmd('STS?', 'STS=')
                sign_controller.run_cmd('LOG?', 'LOG=')
                sign_controller.run_cmd('CLG', 'STS=')
                actual_current = float(psu.get_output_current())
                LOGGER.info(f'Actual current draw observed: {actual_current}A')
                actual_currents.append(actual_current)
            avg_current = mean(actual_currents)
            assert \
                avg_current < target_current, \
                f'Actual current draw ({mean(actual_currents)}A) is higher than target'

            LOGGER.info(f'Current draw when flashing with CMC communication: {avg_current}A')
            avg_currents[state] = avg_current

        elif state == 'no_flashing_with_com':
            actual_currents = []
            for i in range(10):
                sign_controller.run_cmd('STS?', 'STS=')
                sign_controller.run_cmd('LOG?', 'LOG=')
                sign_controller.run_cmd('CLG', 'STS=')
                actual_current = float(psu.get_output_current())
                LOGGER.info(f'Actual current draw observed: {actual_current}A')
                actual_currents.append(actual_current)
            avg_current = mean(actual_currents)
            assert \
                avg_current < target_current, \
                f'Actual current draw ({avg_current}A) is higher than target'

            LOGGER.info(f'Current draw not flashing with CMC Communication: {avg_current}A')
            avg_currents[state] = avg_current

        elif state == 'no_flashing_no_comm':
            sign_controller.run_cmd('END', 'ACK')
            time.sleep(5)
            sign_controller.end_session()
            actual_currents = []
            for i in range(10):
                actual_current = float(psu.get_output_current())
                LOGGER.info(f'Actual current draw observed: {actual_current}A')
                actual_currents.append(actual_current)
            avg_current = mean(actual_currents)
            assert \
                avg_current < target_current, \
                f'Actual current draw ({avg_current}A) is higher than target'

            LOGGER.info(f'Current draw when not flashing and without CMC Communication: {avg_current}A')
            avg_currents[state] = avg_current

        else:
            assert False, f'Unknown state: {state}'

    LOGGER.info(f'Currents observed: {avg_currents}')
