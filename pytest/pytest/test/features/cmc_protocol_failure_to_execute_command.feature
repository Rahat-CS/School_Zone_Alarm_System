
Feature: Failure to execute commands

  If the Sign Controller is not able to execute an instruction from the CMC then it shall respond with the
  command that failed to execute and an # appended. E.g. if the CMC issues <TFL="10,70"> the Sing Controller may respond
  with <TFL#>

  Note: at the moment the only command that can fail to exectute is TFL - if the testflash period happens to overlap
  with a scheduled operation. Other commands should never fail to be executed.

  Background:
    Given the Power Supply is set to supply 12V
    And the Sign Controller is configured to the default state
    And the Sign Controllers log has been cleared
    And a communication session has been established


  Scenario: Remote Testflash not executed because it would overlap with scheduled operation

    Given the Sign Controller is configured with the following time table:
      01 5F7A3ED8 01 FF
    And   the CMC sends the command TTO="30,30,30" and the Sign Controller responds with ACK
    And   the device is enabled
    When  the Sign Controllers time is set to 05-10-2020 08:29:30
    Then  the command TFL="60,0707" shall fail to execute


  Scenario: Remote Testflash not executed because requested during scheduled operation

    Given the Sign Controller is configured with the following time table:
      01 5F7A3ED8 01 01
    And   the CMC sends the command TTO="30,30,30" and the Sign Controller responds with ACK
    And   the device is enabled
    When  the Sign Controllers time is set to 05-10-2020 08:29:30
    Then  after 30s the Display should start operating
    Then  the command TFL="60,0707" shall fail to execute

