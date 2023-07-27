Feature: Battery Level

  Check that the sign's battery level assigned valid values.
  Check that those values can be read back.
  Check that invalid values are rejected.

  Background:
    Given a communication session has been established

  Scenario: Levels can be read
    When the CMC sends «BVL?»
    And the ADC responds with BVL="μ"»
    Then μ matches regex "\d\d\.\d\d"


  Scenario Outline: Valid levels can be set
    Given <level> is copied to μ
    When the CMC sends «BVL="μ"»
    Then the ADC responds with «ACK»
    When the CMC sends «BVL?»
    And the ADC responds with «BVL="τ"»
    Then μ equals τ

    Examples:

    | level | notes |
    | 10.00 |       |
    | 12.00 |       |


