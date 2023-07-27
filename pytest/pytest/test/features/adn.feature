Feature: Serial Numbers

  Check that the sign's serial number can be assigned to valid values.
  Check that those values can be read back.
  Check that invalid values are rejected.

  Background:
    Given a communication session has been established

  Scenario: Serial numbers can't be set
    When the CMC sends «ADN="12345678"»
    Then the ADC responds with «REJ»

  Scenario: Serial numbers can be read
    When the CMC sends «ADN?»
    And the ADC responds with «ADN="μ"»
    Then μ matches regex "\d{8,32}"
