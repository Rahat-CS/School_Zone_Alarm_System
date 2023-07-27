from pytest_bdd import scenario, scenarios, given, when, then, parsers
import logging
import re
import time
from datetime import datetime

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/time_synch.feature',
#     # 'Setting the time'
#     # 'RTT measurement'
#     # 'Timing adjustment ignored when measured RTT exceeds specified acceptable RTT'
#     # 'Sign Controller only adjusts the RTC if measured RTT is small enough and the change exceeds threshold defined'
#     'Reject any attempts to set the time to 2016/07/07 12:00:00 or earlier'
# )
# def test_wip():
#     pass


scenarios('../features/time_synch.feature')


def set_rtc(j_link, crnt_rtc):
    m = re.match(r'\d{1,10}', crnt_rtc)
    assert m, f'Something is wrong with the <crnt_time> step parameter supplied'
    j_link.stop_swo_capture()
    j_link.halt_mcu()
    j_link.set_rtc(int(crnt_rtc))
    j_link.run_mcu()
    j_link.start_swo_capture()


@given("the Sign Controllers RTC is set to <crnt_rtc>")
def step_set_rtc(j_link, crnt_rtc):
    set_rtc(j_link, crnt_rtc)


@given(parsers.parse("the ADC's realtime clock is set to {rtc}"))
def step_set_rtc(j_link, sign_controller, results, rtc):
    if j_link.in_use():
        set_rtc(j_link, crnt_rtc_x)
    else:

        resp = sign_controller.send('<SYN="999">')
        assert resp == '<DTE?>'
        rtc = results.substitute(rtc)
        resp = sign_controller.send(f'<DTE="{rtc}">')
        assert '<SYN="' in resp

@given(parsers.parse('<delay> is copied to {vars}'))
def copy_delay(delay, vars, results):
    results.set(vars, [delay])


@given(parsers.parse('<crnt_rtc>, <new_rtc> and <adjustment> are copied to {vars}'))
def copy(crnt_rtc, new_rtc, adjustment, vars, results):
    results.set(vars, [crnt_rtc, new_rtc, adjustment])

@given(parsers.parse('<new_rtc>, <rtt> and <rtc_adjustment> are copied to {vars}'))
def copy(new_rtc, rtt, rtc_adjustment, vars, results):
    results.set(vars, [new_rtc, rtt, rtc_adjustment])


@then('the Sign Controller shall respond with DTE? when CMC sends the command SYN="999"')
def step_initiate_sync(sign_controller):
    sign_controller.run_cmd('SYN="999"', 'DTE?')


@then('the Sign Controller shall respond with DTE? when CMC sends the command SYN="<rtt>"')
def step_initiate_sync2(sign_controller, rtt):
    m = re.match(r'\d{3}', rtt)
    assert m, 'Format for <rtt> step parameter is not correct'
    sign_controller.run_cmd(f'SYN="{rtt}"', 'DTE?')


# @then('the Sign Controller shall respond with SYN="xxx,<adjustment>" when the CMC sends DTE="<new_rtc>"')
# def step_check_syn_response(sign_controller, adjustment, new_rtc):
#     m = re.match(r'-?\d+', adjustment)
#     assert m, f'Step parameter <adjustment> does not conform to required format'
#     m = re.match(r'\d{1,10}', new_rtc)
#     assert m, f'Step parameter <new_rtc> does not conform to required format'
#     dte_response = sign_controller.run_cmd(f'DTE="{new_rtc}"', 'SYN=')
#     m = re.match(r'<SYN="\d{3},(?P<actual_adj>-?\d{1,10})">', dte_response)
#     assert m, f'Sign Controller response ({dte_response}) does not match expected format'
#     actual_adj = int(m.group('actual_adj'))
#     expect_adj = int(adjustment)
#     assert expect_adj - 5 < actual_adj < expect_adj + 5, f'actual adjustment ({actual_adj}) not close' \
#                                                          f'enough to expected adjustment ({expect_adj})'
#     LOGGER.info(f'Adjustment observed ({actual_adj}) was as expected ({expect_adj} +/- 5)')


# @then("this is just a dummy step to consume the <notes> column of the Examples Table")
# def step_dummy(notes):
#     pass




# @when('the CMC now sends DTE="1603500000" after a delay of <delay> seconds')
# def step_send_timestamp_with_delay(sign_controller, delay, context):
#     time.sleep(float(delay))
#     dte_response = sign_controller.run_cmd('DTE="1603500000"', 'SYN=')
#     context['dte_response'] = dte_response


# @then('the Sign Controller shall respond with SYN="<delay>,999"')
# def step_impl(context, delay):
#     m = re.match(r'<SYN="(?P<rtt>\d{3}),-?\d{3}"', context['dte_response'])
#     assert m, f'response to DTE=.... is not as expected'
#     rtt = int(m.group('rtt'))
#     assert int(delay) - 2 < rtt < int(delay) + 2, f'measured RTT outside of expected range'
#     LOGGER.info(f'Measured RTT is OK: {rtt} (expected: {delay} +/- 2')


@when('the CMC now sends DTE="<new_rtc>" after a delay of <delay> seconds')
def step_send_timestamp_with_delay(sign_controller, new_rtc, delay, context):
    time.sleep(float(delay))
    dte_response = sign_controller.run_cmd(f'DTE="{new_rtc}"', 'SYN=')
    context['dte_response_2'] = dte_response


@then("the Sign Controller shall adjust it's RTC: <rtc_adjustment>")
def step_check_rtc_adjustment(context, rtc_adjustment):
    assert rtc_adjustment == 'yes' or rtc_adjustment == 'no', f'expecting yes/no for <rtc_adjustment> parameter but ' \
                                                              f'received: {rtc_adjustment}'
    m = re.match(r'<SYN="\d{3},(?P<adj>-?\d{1,3})"', context['dte_response_2'])
    assert m, f'Response to DTE= ... is not matching expected format'
    adj = int(m.group('adj'))
    if rtc_adjustment == 'no':
        assert adj == 0, 'RTC was adjusted even though it should not have been'
    else:
        assert adj != 0, 'RTC was not adjusted even through it should have been'
    LOGGER.info('RTC adjustment was performed as expected')


@when("the CMC attempts to set the Sign Controllers time to <new_time> which is prior to 2016/07/07 12:00:00")
def step_attempt_to_set_time_to_early(sign_controller, new_time, context):
    new_rtc = int(datetime.strptime(new_time, '%d-%m-%Y %H:%M:%S').timestamp())
    sign_controller.run_cmd('SYN="999"', 'DTE?')
    context['dte_response'] = sign_controller.run_cmd(f'DTE="{new_rtc}"', 'REJ')


@then("the Sign Controller shall respond with REJ")
def step_impl(context):
    assert context['dte_response'] == '<REJ>', f'Sign Controller did not respond with DTE# but' \
                                               f' with {context["dte_response"]}'
