from pytest_bdd import scenarios, scenario, given, when, then, parsers
import logging
import time


LOGGER = logging.getLogger(__name__)

# @scenario(
#     '../features/display_brightness_control.feature',
#     #'Display Brightness Control during scheduled operation'
#     'Display Brightness Control during test flash'
# )
# def test_wip():
#     pass


scenarios('../features/display_brightness_control.feature')


@given('the Sign Controller is configured with the following display pwm value: <pwm_setting>')
def step_configure_pwm(sign_controller, pwm_setting):
    sign_controller.update_setting('PWM', f'"{pwm_setting.strip()}"')


@then('the average current drawn by the Sign Controller shall be <avg_current_draw>')
def step_check_psu_current(psu, avg_current_draw):
    permitted_error_percent = 15
    psu_current_expected = float(avg_current_draw)
    psu_current = float(psu.get_output_current())
    error_abs = abs(psu_current_expected - psu_current)
    error_percent = 100 * error_abs / psu_current_expected
    assert \
        error_percent < permitted_error_percent, \
        f'Current drawn from PSU is outside the expected range' \
        f'(actual current drawn: {psu_current}A, expected range:' \
        f' {psu_current_expected-0.2}A +/- {permitted_error_percent}%'

    LOGGER.info(f'Sign Controller current draw as reported by PSU is as expected: {psu_current}A'
                f'(expected: {psu_current_expected}A +/- {permitted_error_percent}%')


@then("the Displays should start operating immediately")
def step_impl():
    # not much to test here ... That the displays are operating will be verified by the
    # observed current draw in the next step. We just use this step to insert a small delay
    # to give the SC the chance to act upon the command and the PSU to settle
    time.sleep(5)
