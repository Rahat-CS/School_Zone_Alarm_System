
Feature: Door Switch monitoring

  The Sign Controller continuously monitors the Door Switch and raises an alarm whenever the
  door is opened or closed - the Sign Controller shall attempt to establish a CMC session

  The door switch however may also be used to trigger a 30s testflash cycle. For this the doorswitch
  has to 3x closed and opened  in 1s intervals

  Background:

    # This will set the Sign Controller into a known, well configured state at the start
    # of each test/scenario

    Given  the Power Supply is set to supply 12V
    And    the door switch is set to closed
    And    the Sign Controller is configured to the default state
    And    the Sign Controllers log has been cleared

  Scenario Outline: Door opened or closed when idle

    Given a communication session has been established
    And   the Sign Controllers State of Operation is set to "<sop>"
    And   the door switch is set to <door_state>
    And   the Sign Controllers log has been cleared
    When  the communication session is terminated
    And   after 28 seconds the door switch is <door_action>
    Then  the Sign Controller raises an alarm with status <status_word_expected>
    And   the Sign Controller Log should contain exactly one <syslog_event> event

    Examples:
    | sop | door_state | door_action | status_word_expected | syslog_event |
    | 0   | closed     | opened      | 0x0101               | DOOR_OPENED  |
    | 0   | open       | closed      | 0x0001               | DOOR_CLOSED  |
    | 1   | closed     | opened      | 0x0181               | DOOR_OPENED  |
    | 1   | open       | closed      | 0x0081               | DOOR_CLOSED  |


  Scenario: Door opened or closed when scheduled flashing is in progress

    # Note: current Door Status is reflected in bit #8 of the Status Word which is not yet documented in the
    # Specification – ITS-SZAS-SD-022: Management Protocol for Type-1 Sign Controller (21 June 2013) or
    # Ts-szas-sd-022 Management Protocol for type-1 sign controller Addendum# 1 (July 2013)

    Given the Sign Controller is configured with the following time table:
      01 5F7A3ED8 01 01
    And   the Sign Controller is configured with the following Operating Durations: 300, 300, 300
    And   the Sign Controllers State of Operation is set to "1"
    When  the Sign Controllers time is set to 05-10-2020 08:29:30
    Then  after 30s the Display should start operating
    When  the communication session is terminated
    And   the door switch is opened
    Then  the Sign Controller raises an alarm with status 0x01C1
    And   the Sign Controller Log should contain exactly one DOOR_OPENED event
    When  the Sign Controllers log has been cleared
    And   the communication session is terminated
    When  the door switch is closed
    Then  the Sign Controller raises an alarm with status 0x00C1
    And   the Sign Controller Log should contain exactly one DOOR_CLOSED event


  Scenario: Local Testflash

    # Ensure that a local testflash can be triggered by means of door switch toggling

    Given a communication session has been established
    And   the Sign Controller is configured with the following flash pattern: 7070
    And   the door switch is set to open
    And   the Sign Controllers log has been cleared
    When  the Sign Controllers door switch is closed and opened 3 times with 1s interval between closing/opening
    Then  the Sign Controller shall respond with a 30s test flash cycle
    And   the Sign Controllers log shall not contain any events indicating flashing has occurred




