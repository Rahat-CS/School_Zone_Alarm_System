Feature: Brightness

  Check that the sign brightness can be set to valid values.
  Check that invalid values are rejected.

  Background:
    Given a communication session has been established


  Scenario Outline: Valid Display Brightness Settings Can be Applied
    Given <pwm> is copied to α
    When the CMC sends «PWM="α"» to which the ADC responds «ACK»
    And the CMC sends «PWM?»
    Then the ADC responds with «PWM="α"»

    Examples:
      | pwm         | notes |
      | 100         | max   |
      | 050         | min   |
      | 075         |       |


  Scenario Outline: Invalid Display Brightness Settings Caught
    Given <pwm> is copied to α
    And the CMC sends «PWM="α"»
    Then the ADC responds with «REJ»

    Examples:
      | pwm   | notes       |
      | 049   | too small   |
      | 010   | too small   |
      | 000   | too small   |
      | 0     | ill formed  |
      | -50   | ill formed  |
      | -75   | ill formed  |
      | -075  | ill formed  |
      | 1000  | ill formed  |
      | abc   | non numeric |

  @xfail: https://redmine.dektech.com.au/issues/410
  Scenario Outline: Excess Display Brightness Settings Caught
    Given <pwm> is copied to α
    And the CMC sends «PWM="α"»
    Then the ADC responds with «REJ»

    Examples:
      | pwm         | notes    |
      | 101         | too big  |
      | 150         | too big  |
      | 200         | too big  |
