from pytest_bdd import scenarios, scenario, given, when, then, parsers
import logging
import re
import time

import testbench.common

LOGGER = logging.getLogger(__name__)

# @scenario(
#     '../features/ota_fw_update.feature',
#     # 'Successful Application install if no Application FW was installed to start with'
#     #  'Successful Application install if installed Application FW was corrupted'
#     # 'FW upgrade starting from a valid Application already running'
#     # 'faulty Application FW image is rejected'
#     'Updating the Bootloader'
# )
# def test_wip():
#     pass

scenarios('../features/ota_fw_update.feature')


@given("any existing Application FW is erased from the Sign Controller")
def step_erase_app_fw(j_link):
    import os
    LOGGER.info(f'Current working dir: {os.getcwd()}')
    j_link.stop_swo_capture()
    j_link.halt_mcu()
    time.sleep(5)
    j_link.erase_application_fw()
    LOGGER.info('Application FW has been erased')


@given("the Sign Controller is reset")
def step_reset_mcu(j_link):
    j_link.reset_mcu()
    j_link.run_mcu()
    time.sleep(5)
    j_link.start_swo_capture()


@when("the CMC succeeds in sending the Application FW image and starts the Application")
def step_send_app_ufw(sign_controller, release_pkg):
    if release_pkg is None:
        LOGGER.error("TODO: Dave to fix")
        return

    ufw_fn = release_pkg.get_ufw_as_temp_file()
    LOGGER.info(f'Using UFW file: {ufw_fn}')
    with open(ufw_fn, "rb") as f_in:
        fw_image = f_in.read()
        msg_ufw = b'<UFW=\"'
        msg_ufw += fw_image
        msg_ufw += b'\">'
        resp = sign_controller.send(msg_ufw, timeout=300)
        m = re.match('<ACK>', resp)
        assert m, 'UFW Download failed'
    sign_controller.run_cmd('END', 'ACK')
    sign_controller.end_session()
    LOGGER.info('Succeeded downloading UFW file and started the Application')


@then(
    parsers.parse(
        'the Sign Controller connects to the CMC with a greeting message matching the following regular expression:\n{greeting_re}'
    )
)
def step_ensure_sign_controller_connects(sign_controller, greeting_re):
    LOGGER.info(f'Using regex: **{greeting_re}**')
    greeting_msg = sign_controller.listen(timeout=240)
    m = re.match(greeting_re, greeting_msg)
    assert m, f'Greeting Message did not match expected pattern: {greeting_msg}'
    LOGGER.info(f'Sign Controller established a session and send the greeting message {greeting_msg}')


@given("the release ROM image is programmed onto the Sign Controller")
def step_program_release_rom(j_link, release_pkg):
    rom_image_fn = release_pkg.get_rom_image_as_temp_file()
    j_link.stop_swo_capture()
    time.sleep(2)
    j_link.reset_mcu()
    j_link.flash_ihex(rom_image_fn)
    j_link.reset_mcu()
    #j_link.run_mcu()
    #time.sleep(5)
    #j_link.start_swo_capture()


@given("the Application FW section is corrupted")
def step_corrupt_app(j_link):
    j_link.modify_memory_32(0x10004, 0xdeadbeef)


@given("the Application FW has been started")
def step_start_app_fw_erase_syslog(sign_controller, j_link, release_pkg, psu):
    testbench.common.step_start_application_fw(sign_controller, j_link, release_pkg, psu, erase_syslog=True)


@given("the Sign Controller is left to run for 1 minute so it's idle")
def step_run_1min():
    time.sleep(60)


@then("the Sign Controller should establish a CMC session when triggered")
def step_trigger_and_wait_for_connection(sign_controller):
    trigger_response = sign_controller.trigger()
    m = re.match(r'<SGN="####";STS="0001">', trigger_response)
    assert m, f'Response to trigger does not match expected pattern - the response was: {trigger_response}'
    LOGGER.info('The Sign Controller responded to the trigger as expected!')


@when("the CMC issues the RBT command")
def step_run_reboot_command(sign_controller):
    sign_controller.run_cmd('RBT', 'ACK')


@when("the CMC terminates the communication session")
def step_terminat_session(sign_controller):
    sign_controller.end_session()


@then("the Sign Controller shall execute the programmed bootloader")
def step_run_bootloader():
    """
    This is again just a dummy step to make the scenario more readable.
    That the bootloader is running will be ascertained by matching the greeting message when the
    Sign Controller establishes contact in the following step

    :return:
    """
    time.sleep(10)


@when("the CMC sends a faulty Application FW image")
def step_send_faulty_fw(sign_controller, release_pkg, context):
    ufw_fn = release_pkg.get_ufw_as_temp_file()
    LOGGER.info(f'Using UFW file: {ufw_fn}')
    with open(ufw_fn, "rb") as f_in:
        fw_image = bytearray(f_in.read())
        fw_image[1000] += 1
        msg_ufw = b'<UFW=\"'
        msg_ufw += bytes(fw_image)
        msg_ufw += b'\">'
        resp = sign_controller.send(msg_ufw, timeout=300)
        context['ufw_response'] = resp
    LOGGER.info('Faulty UFW file was sent ... ')


@then("the Sign Controller shall respond with UFW#")
def step_check_ufw_response(context):
    resp = context['ufw_response']
    assert resp == '<UFW#>', f'Sign Controller did not respond with <UFW#> (actual response: {resp})'


@when("the CMC issues the END command")
def step_start_app(sign_controller):
    sign_controller.run_cmd('END', 'ACK')
    sign_controller.end_session()


@given("the old release ROM image has been programmed onto the Sign Controller")
def step_program_old_image(j_link):
    """
    We just use V1.21RC3 as old ROM image (this one works good enough for the purpose of this test)
    """
    rom_image_fn = './steps/ADC_Type-1_ROM_V1.21RC3_97e1b1d.hex'
    j_link.stop_swo_capture()
    time.sleep(2)
    j_link.reset_mcu()
    j_link.flash_ihex(rom_image_fn)
    j_link.reset_mcu()
    LOGGER.info('Old ROM Image has been programmed')


@then("the Sign Controller connects to the CMC with a greeting message indicating the bootloader has been updated")
def step_ensure_bootloader_updated(sign_controller, release_pkg):
    greeting_msg = sign_controller.listen(timeout=240)
    m = re.match(r'<SGN="####";ADN="\d{8}";FWV="0.00_(?P<boot_version>\d\.\d{2}(?:RC\d+)?\+?)">', greeting_msg)
    assert m, f'Bootloader Greeting Message does not conform to required format'
    bootloader_version = m.group('boot_version')
    assert bootloader_version == release_pkg.get_version_id(), \
        f'Bootloader Version ID ({bootloader_version}) is not as expected ({release_pkg.get_version_id()})'


@when("the CMC successfully sends the bootloader update FW image")
def step_impl(sign_controller, release_pkg):
    boot_ufw_fn = release_pkg.get_bootloader_ufw_as_temp_file()
    LOGGER.info(f'Using Bootloader UFW file: {boot_ufw_fn}')
    with open(boot_ufw_fn, "rb") as f_in:
        fw_image = f_in.read()
        msg_ufw = b'<UFW=\"'
        msg_ufw += fw_image
        msg_ufw += b'\">'
        resp = sign_controller.send(msg_ufw, timeout=300)
        m = re.match('<ACK>', resp)
        assert m, 'Bootloader UFW Download failed'
    LOGGER.info('Succeeded downloading Bootloader UFW file')


@then("the Sign Controller response shall indicate the current FW release version when issued the SVN? command")
def step_impl(sign_controller):
    svn_response = sign_controller.run_cmd('SVN?', 'SVN=')


@then("the Sign Controller connects to the CMC with a greeting message indicating the old bootloader is running")
def step_ensure_old_bootloader_connects(sign_controller):
    old_bootloader_version_id = '1.21RC3'
    greeting_msg = sign_controller.listen(timeout=240)
    m = re.match(r'<SGN="####";ADN="\d{8}";FWV="1.21RC3_1.21RC3">', greeting_msg)
    assert m, f'Bootloader Greeting Message not as expected'

