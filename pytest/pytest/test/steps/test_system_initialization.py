from pytest_bdd import scenarios, scenario, given, when, then, parsers
import time
import logging
import re

import testbench.common
from testbench.syslog import SysLog, EventId

LOGGER = logging.getLogger(__name__)


# @scenario(
#     '../features/system_initialization.feature',
#     # 'Failed installed FW integrity Test'
#     # 'Failed Configuration or Timetable Integrity and Sign ID corruption'
#     # 'Failed Configuration or Timetable Integrity and Sign ID corruption'
#     'Successful Boot'
# )
# def test_wip():
#     pass


scenarios('../features/system_initialization.feature')


@given("that the installed FW image is corrupt")
def step_corrupt_fw(j_link):
    j_link.stop_swo_capture()
    j_link.halt_mcu()
    j_link.reset_mcu()
    j_link.modify_memory_32(0x10004, 0xdeadbeef)
    j_link.run_mcu()


@when("the Sign Controller is power-cycled")
def step_powercycle(psu, j_link):
    j_link.stop_swo_capture()
    psu.off()
    time.sleep(5)
    psu.on()
    time.sleep(5)
    j_link.start_swo_capture()


@then(
    'the Sign Controller shall connect to the CMC with a greeting message indicating '
    'that no valid Application FW is installed'
)
def step_ensure_connection_with_missing_fw_indicator(sign_controller, release_pkg):
    greeting_msg = sign_controller.listen(timeout=240)
    m = re.match(r'<SGN="####";ADN="\d{8}";FWV="0.00_(?P<boot_version>\d\.\d{2}(?:RC\d+)?\+?)">', greeting_msg)
    assert m, f'Bootloader Greeting Message does not conform to required format'
    bootloader_version = m.group('boot_version')
    if release_pkg is not None:
        assert \
            bootloader_version == release_pkg.get_version_id(), \
            f'Bootloader Version ID ({bootloader_version}) is not as expected ({release_pkg.get_version_id()})'
    else:
        LOGGER.error("TODO: Dave to work out how to do this...")

    LOGGER.info('The Sign Controller made contact and indicated that no valid Application FW was installed')


@given("the release ROM image is programmed onto the Sign Controller")
def step_program_release_rom(j_link, release_pkg):
    rom_image_fn = release_pkg.get_rom_image_as_temp_file()
    j_link.stop_swo_capture()
    time.sleep(2)
    j_link.reset_mcu()
    j_link.flash_ihex(rom_image_fn)
    j_link.reset_mcu()
    LOGGER.info('Release ROM Image has been installed successfully')


@given("the Sign Configuration <address> is corrupted with <value>")
def step_impl(j_link, address, value):
    m = re.match(r'0x[0-9A-Fa-f]+', address)
    assert m, f'the parameter address does not conform to the required format (supplied: {address})'
    m = re.match(r'0x[0-9A-Fa-f]+', value)
    assert m, f'the parameter value does not conform to the required format (supplied: {value})'
    j_link.modify_memory_32(
        int(address, 16),
        int(value, 16)
    )
    LOGGER.info(f'Memory location {address} has been updated with value: {value}')


@when("the Application Firmware is started")
def step_start_application_fw_erase_syslog(sign_controller, j_link, release_pkg, psu):
    testbench.common.step_start_application_fw(sign_controller, j_link, release_pkg, psu, erase_syslog=True)


@then("the Sign Controller shall contact the with greeting message indicating that the configuration is corrupted")
def step_ensure_greeting_indicates_config_error(sign_controller):
    greeting_msg = sign_controller.listen(timeout=240)
    # we have to check for Alarm bit [0] and Config Error bit [2] being set -> 0x5
    m = re.match(r'<SGN="####";STS="0005">', greeting_msg)
    #assert m, f'Greeting message does not conform to requirement (message received: {greeting_msg}'


@then("add a Configuration Error event to the Sign Controllers System Log")
def step_ensure_log_contains_config_error_event(sign_controller):
    log_response = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_response)
    num_config_err_events = len(syslog.get_events_by_id(EventId.CONFIG_ERROR))
    assert num_config_err_events == 1, f'Number of config error events is not correct. ' \
                                       f'Should be 1 but found {num_config_err_events}'



@then("the Bootloader will contact the CMC and report that valid FW is installed")
def step_ensure_bootloader_contacts_cmc(sign_controller, release_pkg):
    greeting_msg = sign_controller.listen(timeout=240)
    m = re.match(
        r'<SGN="####";ADN="\d{8}";FWV="(?P<app_version>\d\.\d{2}(?:RC\d+))_(?P<boot_version>\d\.\d{2}(?:RC\d+))">',
        greeting_msg
    )
    assert m, f'Greeting message received does not conform to required format ({greeting_msg})'
    assert m.group('app_version') == release_pkg.get_version_id(), 'incorrect App version found'
    assert m.group('boot_version') == release_pkg.get_version_id(), 'incorrect Bootloader version found'
    LOGGER.info('Bootloader contacted CMC as expected')


@when("the CMC instructs the Sign Controller to boot the installed Application FW")
def step_boot_app(sign_controller):
    sign_controller.run_cmd('END', 'ACK')
    time.sleep(5)
    sign_controller.end_session()
    LOGGER.info('Application FW started')


@then(
    parsers.parse(
        'the Sign Controller will contact the CMC and send a valid greeting message with the Status '
        'Word set to {status_word}'
    )
)
def step_ensure_app_contacts_cmc(sign_controller, status_word):
    m = re.match(r'0x(?P<sts>[0-9A-Fa-f)]+)', status_word)
    assert m, 'Status word supplied as step parameter is invalid'
    sts = m.group('sts')
    greeting_msg = sign_controller.listen(timeout=240)
    m = re.match(r'<SGN="ABC1234";STS="(?P<sts_rcvd>[0-9A-F]{4})">', greeting_msg)
    assert m, 'Greeting message not as expected'
    sts_rcvd = m.group('sts_rcvd')
    assert sts_rcvd == sts, f'Status word in greeting message not as expected (received: {sts_rcvd}, expected: {sts})'
    LOGGER.info('Application FW contacted CMC as expected')


@then("the Sign Controllers System Log will only contain one event which is an Unexpected Initialization Event")
def step_impl(sign_controller):
    log_resp = sign_controller.run_cmd('LOG?', 'LOG=')
    syslog = SysLog(log_resp)
    num_events = syslog.get_num_events()
    num_restart_events = len(syslog.get_events_by_id(EventId.ADC_UNEXPECTED_INIT))
    assert num_events == 1, 'Number of events in log is not as exptected'
    assert num_restart_events == 1, 'Number of unexpected init events is not as expected'
    LOGGER.info('Sign Controller log is ok')


@given("the device is reset")
def step_reset(j_link):
    j_link.stop_swo_capture()
    j_link.reset_mcu()
    j_link.run_mcu()
    time.sleep(1)
    j_link.start_swo_capture()
    LOGGER.info('Sign Controller has been reset')
