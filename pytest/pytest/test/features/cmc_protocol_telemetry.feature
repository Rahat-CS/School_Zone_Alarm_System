Feature: CMC Protocol - Telemetry

  The Sign Controller shall provide the following commands for the CMC to interrogate the status and operating
  Environment of the device:

  - BTT?: Report current Battery Voltage
  - ESC?: report display minimum current.
          The minimum current reported is the minimum sampled current since the last time ESC was requested by CMC
          (i.e. min tracking is reset every time ESC results are submitted to the CMC)
  - DER?: report Display Error Byte
  - DTE?: report the current time
  - LOG?: Sing Controller to report the current System Log to the CMC
  - TMP?: report the current temperature
  - RSS?: report the current RSSI
  - STS?: report the current Status Word

  Some of these commands are already covered by other feature/scenarios, namely
  - BTT? -> battery_voltage_monitoring.feature
  - DER? -> alert_display_error_detection.feature
  - LOG? -> syslog.feature
  - DTE? -> time_synch.feature
  - STS? -> alert_display_error_detection.feature
            syslog.feature
            doorswitch_monitoring.feature
            battery_voltage_monitoring.feature

  For these no new scenarios will be defined.

  Background:
    Given the Power Supply is set to supply 12V
    Given the Sign Controller is configured to the default state
    And the Sign Controllers log has been cleared


  @xfail: reported currents are about 30% too low.
  Scenario: Minimum Display Current reporting

    # Note that if no current has been measured during the last period (e.g. because lantern was not
    # illuminated due to flash pattern configured) the Sign Controller will return an empty string in
    # the corresponding position

    Given a communication session has been established
    Then the Sign Controller should report minimum currents (+/- 100 mA) based on PSU and
      Flash Pattern setting as follows:
      | Flash Pattern | PSU Voltage   |  ESC reported    |
      | 77777777      | 9.0           | "0450,0450,1500" |
      | 77777777      | 12.0          | "0600,0600,2000" |
      | 11111111      | 9.0           | "0450,,"         |
      | 11111111      | 12.0          | "0600,,"         |
      | 22222222      | 9.0           | ",0450,"         |
      | 22222222      | 12.0          | ",0600,"         |
      | 44444444      | 9.0           | ",,1500"         |
      | 44444444      | 12.0          | ",,2000"         |


  Scenario: Temperature Reporting

    # At the moment the Testbed does not have any means for comparing the actual vs the
    # measured temperature - therefore we only excercise the TMP? command and ensure that the
    # Sign Controller reponds with something sensible
    Given a communication session has been established
    Then the Sign Controller shall respond to a TMP? request with a message that matches the
      following regex: TMP="-?\d{1,3}.\d{1}"


  Scenario: RSS Reporting

    # As with Temperature the testbed does not have any means to compare actual RSSI against
    # reported RSSI, so we can just make sure the Sign Controller responds and that the
    # returned values make sense
    Given a communication session has been established
    Then the Sign Controller shall respond to a RSS? request with a report matching the
      following regex: RSS="-?\d{1,3}"
