from pytest_bdd import scenario, scenarios, given, when, then, parsers
import logging
import re
import time

LOGGER = logging.getLogger(__name__)

# @scenario(
#     '../features/cmc_protocol_telemetry.feature',
#     #'Minimum Display Current reporting'
#     #'Temperature Reporting'
#     'RSS Reporting'
# )
# def test_wip():
#     pass


scenarios('../features/cmc_protocol_telemetry.feature')


@then(parsers.parse(
    'the Sign Controller should report minimum currents (+/- {margin} mA) based on PSU and\n'
    'Flash Pattern setting as follows:\n{data}'))
def step_check_min_currents(sign_controller, psu, margin, data):
    data_rows = data.split('\n')[1:]
    for row in data_rows:
        [_, fpn, psu_voltage, esc_expected, _] = [c.strip() for c in row.split('|')]
        m = re.match(
            r'"(?P<esc_exp_left>\d{4})?,(?P<esc_exp_right>\d{4})?,(?P<esc_exp_annulus>\d{4})?"', esc_expected)
        assert m, f'Expected ESC value supplied does not match expected pattern: {esc_expected}'
        LOGGER.info(f'Using expected ESC: {esc_expected}')
        esc_exp = (m.group('esc_exp_left'), m.group('esc_exp_right'), m.group('esc_exp_annulus'))
        LOGGER.info(f'Expected ESC after split: {esc_exp}')
        psu.set_output_voltage(psu_voltage)
        time.sleep(5)
        sign_controller.run_cmd(f'TFL="05,{fpn}"', 'ACK')
        time.sleep(1)
        sign_controller.run_cmd('ESC?', 'ESC=')  # why twice?
        time.sleep(2)
        esc_response = sign_controller.run_cmd('ESC?', 'ESC=')
        m = re.match(r'<ESC="(?P<esc_left>\d{4})?,(?P<esc_right>\d{4})?,(?P<esc_annulus>\d{4})?">', esc_response)
        assert m, f'ESC? response does not match expected pattern: {esc_response}'
        esc = (m.group('esc_left'), m.group('esc_right'), m.group('esc_annulus'))

        esc_zip = zip(esc_exp, esc, ('left', 'right', 'annulus'))

        for r in esc_zip:
            LOGGER.info(f'==============: {r}')
            if r[0] is None:
                assert r[1] is None, 'expected asc to be None but found'
            else:
                assert r[1] is not None, 'expected a value but got None'
                assert \
                    abs(int(r[0]) - int(r[1])) < int(margin), \
                    f'Currents for {r[2]} lantern are to different ...' \
                    f'(actual: {r[0]}, expected: {r[1]})'

            LOGGER.info(f'Actual current matches expected for lantern {r[2]}: {r[0]} vs {r[1]}')

        LOGGER.info(f'reported ESC appears OK: actual: {esc}, expected: {esc_expected}')

        # wait 5s to make sure the previous TFL command is over and done
        time.sleep(5)


@then(
    parsers.parse(
        'the Sign Controller shall respond to a TMP? request with a message that matches the\n'
        'following regex: {tmp_re}'
    )
)
def step_check_tmp_response(sign_controller, tmp_re):
    tmp_response = sign_controller.run_cmd('TMP?', 'TMP=')
    m = re.match('<' + tmp_re + '>', tmp_response)
    assert m, f'TMP? response does not match the expected pattern: {tmp_response}'
    LOGGER.info('reported Temperature appears OK')


@then(
    parsers.parse(
        'the Sign Controller shall respond to a RSS? request with a report matching the\n'
        'following regex: {rss_re}')
    )
def step_check_rss_response(sign_controller, rss_re):
    rss_response = sign_controller.run_cmd('RSS?', 'RSS=')
    m = re.match('<' + rss_re + '>', rss_response)
    assert m, f'TMP? response does not match the expected pattern: {rss_response}'
    LOGGER.info(f'The reported RSSI appears to be OK ({rss_response})')
