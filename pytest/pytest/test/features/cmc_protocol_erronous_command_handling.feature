Feature: Erroneous CMC command handling

  If the Sign Controller receives a faulty command (which cannot be successfully decoded) then the Sign Controller
  shall respond with <REJ>. This applies for single commands per message, but also if any one of the commands in a
  multi-command message is faulty.

  Background:

    # For these tests we don't need to establish a default config since the configuration is the
    # subject of the test. All that needs to be done is to supply power, reset/start the Application FW and
    # then establish a CMC session
    # We do however
    # - need the session idle timeout to be sufficiently long
    # - Make sure the Battery Threshold is low enough os that no Alarm is generated
    # - Make sure No Comm timeout is sufficiently large
    # - make sure all Alarms are cleared
    Given the Sign Controller has established a CMC session

  Scenario Outline: Basic commands
    Given the CMC sends <cmc_message>
    Then the ADC responds with <response>

    Examples:

    , <response>, and <notes> are copied to μ, ρ, and ν
    And the CMC sends «PWM="α"» to which the ADC responds «REJ»

    Examples:
      | pwm_setting |
      | 101         |
      | 049         |
      | 010         |
      | 000         |
      | 0           |
      | 50          |

  Scenario:

    Then  the CMC shall respond to faulty messages as shown in the following table:
      | cmc_message      | response          | # notes                                                                     |
      | <LG?>            | <REJ>             | # Typo in command                                                           |
      | <TEMP?>          | <REJ>             | # Typo in command                                                           |
      | <>               | <REJ>             | # empty message                                                             |
      | <                | <REJ>             | # command server will timeout if '>' does not arrive withing a certain time |
      | TMP?>            | <REJ>             | # missing '<'                                                               |
      | <TMP?;SIN?;BTT?> | <REJ>             | # 2nd command in message is invalid                                         |

  @xfail: https://redmine.dektech.com.au/issues/351
  Scenario: Faulty commands received 2
    Then the CMC sends "<<STS?>" and the ADC responds with "<REJ>"
    And the ADC sends "<STS=0081>"

  @xfail: https://redmine.dektech.com.au/issues/351
  Scenario: Faulty commands received 3
    Then the CMC sends "><STS?>" and the ADC responds with "<REJ>"
    And the ADC sends "<STS=0081>"
