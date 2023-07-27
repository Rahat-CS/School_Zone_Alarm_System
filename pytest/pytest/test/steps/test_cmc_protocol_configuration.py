import logging
from pytest_bdd import scenario, scenarios, given, when, then
import time
import re


LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/cmc_protocol_configuration.feature',
#     # 'Battery Voltage Threshold, Display Current Threshold and Flash Pattern Configuration'
#     # 'Reconnection Hold-Off Time, CMC Session No-Activity Timeout and Sign Identity Configuration'
#     # 'No Communication Alarm Duration, Timetable, Operating Duration and Timetable Version Configuration'
#     'Display Recovery Hold-off duration Configuration'
# )
# def test_wip():
#     pass

scenarios('../features/cmc_protocol_configuration.feature')


@given("the CMC configures the Battery Voltage Threshold to <bvl>")
def step_config_bvl(sign_controller, bvl):
    sign_controller.update_setting('BVL', '"{}"'.format(bvl))


@given("the CMC configures the Display Current Threshold to <ect>")
def step_impl(sign_controller,ect):
    sign_controller.update_setting('ECT', '"{}"'.format(ect))


@given("the CMC configures the Flash Pattern to <fpn>")
def step_config_fpn(sign_controller, fpn):
    sign_controller.update_setting('FPN', '"{}"'.format(fpn))


@when("the PSU is disabled and then enabled again after a few seconds")
def step_pwrcycle(psu, j_link):
    j_link.stop_swo_capture()
    j_link.disconnect()
    psu.off()
    time.sleep(5)
    psu.on()
    time.sleep(3)
    j_link.connect()


@then("the Sign Controller shall report BVL = <bvl>")
def step_check_bvl(sign_controller, bvl):
    bvl_response = sign_controller.run_cmd('BVL?', 'BVL=')
    m = re.match(r'<BVL="(?P<bvl_val>\d{2}\.\d{2})"', bvl_response)
    assert m, 'BVL? response format did not match expectation'
    crnt_bvl = m.group('bvl_val')
    assert bvl == crnt_bvl, 'Actual BVL value does not match the expected'
    LOGGER.info('BVL is OK (expected/actual = {}/{}'.format(bvl, crnt_bvl))


@then("the Sign Controller shall report ECT = <ect>")
def step_check_ect(sign_controller, ect):
    ect_response = sign_controller.run_cmd('ECT?', 'ECT=')
    m = re.match(r'<ECT="(?P<ect_val>\d{4},\d{4},\d{4})"', ect_response)
    assert m, 'ECT? response format did not match expectation'
    crnt_ect = m.group('ect_val')
    assert ect == crnt_ect, 'Actual BVL value does not match the expected'
    LOGGER.info('All good, actual ECT ({}) matches expected value ({})'.format(crnt_ect, ect))


@then("the Sign Controller shall report FPN = <fpn>")
def step_check_fpn(sign_controller, fpn):
    fpn_response = sign_controller.run_cmd('FPN?', 'FPN=')
    m = re.match(r'<FPN="(?P<fpn_val>\d{1,32})"', fpn_response)
    assert m, 'FPN? response format did not match expectation'
    crnt_fpn = m.group('fpn_val')
    assert fpn == crnt_fpn, 'Actual BVL value does not match the expected'
    LOGGER.info('All good, actual FPN ({}) matches expected value ({})'.format(crnt_fpn, fpn))


@given("the CMC configures the Reconnection Hold-Off Time to <ctd>")
def step_impl(sign_controller, ctd):
    sign_controller.update_setting('CTD', f'"{ctd}"')


@given("the CMC configures the CMC Session No Activity Timeout to <std>")
def step_impl(sign_controller, std):
    sign_controller.update_setting('STD', f'"{std}"')


@given("the CMC configures the Sign ID to <sgn>")
def step_impl(sign_controller, sgn):
    sign_controller.update_setting('SGN', f'"{sgn}"')


@then("the Sign Controller shall report CTD = <ctd>")
def step_impl(sign_controller, ctd):
    ctd_response = sign_controller.run_cmd('CTD?', 'CTD=')
    m = re.match(r'<CTD="(?P<ctd_val>\d{1,4})">', ctd_response)
    assert m, 'CTD? response does not match the expected pattern'
    current_ctd = m.group('ctd_val')
    assert int(current_ctd) == int(ctd), f'Actual CTD value ({current_ctd}) does not match the expected ({ctd})'
    LOGGER.info(f'CTD is OK, actual value ({current_ctd}) matches expected value ({ctd})')


@then("the Sign Controller shall report STD = <std>")
def step_impl(sign_controller, std):
    std_response = sign_controller.run_cmd('STD?', 'STD=')
    m = re.match(r'<STD="(?P<std_val>\d{1,4})">', std_response)
    assert m, 'STD? response does not match the expected pattern'
    current_std = m.group('std_val')
    assert int(current_std) == int(std), f'Actual CTD value ({current_std}) does not match the expected ({std})'
    LOGGER.info(f'CTD is OK, actual value ({current_std}) matches expected value ({std})')


@then("the Sign Controller shall report SGN = <sgn>")
def step_impl(sign_controller, sgn):
    sgn_response = sign_controller.run_cmd('SGN?', 'SGN=')
    m = re.match(r'<SGN="(?P<sgn_val>[a-zA-Z0-9.\-\/\\]{1,32})">', sgn_response)
    assert m, 'SGN? response does not match the expected pattern'
    current_sgn = m.group('sgn_val')
    assert current_sgn == sgn, f'Actual SGN value ({current_sgn}) does not match the expected ({sgn})'
    LOGGER.info(f'CTD is OK, actual value ({current_sgn}) matches expected value ({sgn})')


@given("the CMC configures the No Communication Alarm Duration to <tmo>")
def step_configure_tmo(sign_controller, tmo):
    sign_controller.update_setting('TMO', f'"{tmo}"')


@given("the CMC configures the Timetable to <ttb>")
def step_configure_ttb(sign_controller, ttb):
    sign_controller.update_setting('TTB', f'"{ttb}"')


@given("the CMC configures the Operating Durations to <tto>")
def step_configure_tto(sign_controller, tto):
    sign_controller.update_setting('TTO', f'"{tto}"')


@given("the CMC configures the Timetable Version to <ttv>")
def step_configure_ttv(sign_controller, ttv):
    sign_controller.update_setting('TTV', f'"{ttv}"')


@then("the Sign Controller shall report TMO = <tmo>")
def step_check_tmo(sign_controller, tmo):
    tmo_response = sign_controller.run_cmd('TMO?', 'TMO=')
    m = re.match(r'<TMO="(?P<tmo_val>\d{1,6})">', tmo_response)
    assert m, f'TMO? response ({tmo_response}) does not match the expected pattern (TMO="dddddd")'
    current_tmo = m.group('tmo_val')
    assert int(current_tmo) == int(tmo), f'Actual TMO value ({current_tmo}) does not match the expected ({tmo})'
    LOGGER.info(f'TMO is OK, actual value ({current_tmo}) matches expected value ({tmo})')


@then("the Sign Controller shall report TTB = <ttb>")
def step_check_ttb(sign_controller, ttb):
    ttb_response = sign_controller.run_cmd('TTB?', 'TTB=')
    m = re.match(r'<TTB="(?P<ttb_val>[0-9A-F]{1,64})">', ttb_response)
    assert m, f'TTB? response ({ttb_response}) does not match the expected pattern'
    current_ttb = m.group('ttb_val')
    assert current_ttb == ttb, f'Actual TTB value ({current_ttb}) does not match the expected ({ttb})'
    LOGGER.info(f'TMO is OK, actual value ({current_ttb}) matches expected value ({ttb})')


@then("the Sign Controller shall report TTO = <tto>")
def step_check_tto(sign_controller, tto):
    tto_response = sign_controller.run_cmd('TTO?', 'TTO=')
    m = re.match(r'<TTO="(?P<tto1_val>\d{1,6}),(?P<tto2_val>\d{1,6}),(?P<tto3_val>\d{1,6})">', tto_response)
    assert m, f'TTB? response ({tto_response}) does not match the expected pattern'
    current_tto = [int(m.group('tto1_val')), int(m.group('tto2_val')), int(m.group('tto3_val'))]
    expected_tto = [int(t) for t in tto.split(',')]
    assert current_tto == expected_tto, f'Actual TTB value ({current_tto}) does not match the expected ({expected_tto})'
    LOGGER.info(f'TTO is OK, actual value ({current_tto}) matches expected value ({expected_tto})')


@then("the Sign Controller shall report TTV = <ttv>")
def step_impl(sign_controller, ttv):
    ttv_response = sign_controller.run_cmd('TTV?', 'TTV=')
    m = re.match(r'<TTV="(?P<ttv_val>[a-zA-Z0-9.\-\/\\]{1,32})">', ttv_response)
    assert m, 'TTV? response does not match the expected pattern'
    current_ttv = m.group('ttv_val')
    assert current_ttv == ttv, f'Actual SGN value ({current_ttv}) does not match the expected ({ttv})'
    LOGGER.info(f'CTD is OK, actual value ({current_ttv}) matches expected value ({ttv})')


@given("the CMC configures the Display Recovery Hold-Off Duration to <drh>")
def step_impl(sign_controller, drh):
    sign_controller.update_setting('DRH', f'"{drh}"')


@then("And the Sign Controller shall report DRH = <drh>")
def step_impl(sign_controller, drh):
    drh_resp = sign_controller.run_cmd('DRH?', 'DRH=')
    m = re.match(r'<DRH="(?P<drh>\d{3})">', drh_resp)
    assert m, f'Response to <DRH?> not as expected (actual response: {drh_resp})'
