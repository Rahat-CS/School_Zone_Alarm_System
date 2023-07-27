Feature: Framework Checking

  Stuff

  Background:
    Given we pause for 1 seconds

  Scenario: Regex
    Given 123 is copied to μ
    Then μ equals 123 exactly
    And μ matches regex "\d\d\d"

