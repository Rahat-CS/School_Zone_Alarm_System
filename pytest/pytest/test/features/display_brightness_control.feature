Feature: Display Brightness Control

  The Sign Controller provides the ability to control the display brightness by using Pulse Width Modulation.
  For the CMC to utilize this feature the Sign Controller provides the <PWM="xxx"> command where xxx specifies the
  PWM duty cycle in %. Accepted values range from 050 (50%) to 100 (100%)

  PWM configuration applies to all forms of flashing, be it scheduled operation or test-flashing

  Note that the display current measurement shall not be affected by the PWM duty cycle configured

  Background:
    Given the Power Supply is set to supply 12V
    Given the Sign Controller is configured to the default state
    And   the Sign Controllers log has been cleared

  Scenario Outline: Display Brightness Control during scheduled operation

    # At the moment the testbed does not have the ability to verify PWM operation directly, but the
    # test as a good approximation can observe the overall current drawn by the device (the current drawn
    # can be read from the PSU)
    #
    # At 12V the load resistors should be drawing 3.2A
    # Since the equipment is not terribly accurate and we don't consider the draw of the control circuit
    # we allow +/- 200mA tolerance
    #
    # Note that PWM is configured at the start of a flashing cycle and changing the setting while flashing
    # is in progress will not have any effect

    Given a communication session has been established
    And   the Sign Controller is configured with the following time table:
      01 5F7A3ED8 01 FF
    And   the Sign Controller is configured with the following Operating Durations: 30, 30, 30
    And   the Sign Controller is configured with the following flash pattern: 777
    And   the Sign Controller is configured with the following display pwm value: <pwm_setting>
    And   the device is enabled
    When  the Sign Controllers time is set to 05-10-2020 08:29:30
    Then  after 30s the Display should start operating
    And   the average current drawn by the Sign Controller shall be <avg_current_draw>

    Examples:
      | pwm_setting | avg_current_draw |
      | 100         | 3.2              |
      | 075         | 2.4              |
      | 050         | 1.6              |


  Scenario Outline: Display Brightness Control during test flash

    # Same approach as above Scenario

    Given a communication session has been established
    And   the Sign Controller is configured with the following display pwm value: <pwm_setting>
    When  the CMC sends the command TFL="10,777" and the Sign Controller responds with ACK
    Then  the Displays should start operating immediately
    And   the average current drawn by the Sign Controller shall be <avg_current_draw>

    Examples:
      | pwm_setting | avg_current_draw |
      | 100         | 3.2              |
      | 075         | 2.4              |
      | 050         | 1.6              |



  Scenario Outline: Invalid Display Brightness Settings Caught
    Given a communication session has been established
    And  <pwm_setting> is copied α
    Then the CMC sends «PWM="α"» to which the ADC responds «REJ»

    Examples:
      | pwm_setting |
      | 101         |
      | 049         |
      | 010         |
      | 000         |
      | 0           |
      | 50          |
