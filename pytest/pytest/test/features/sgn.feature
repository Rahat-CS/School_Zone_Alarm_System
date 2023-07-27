Feature: Sign Naming

  Check that the sign name can be assigned to valid values.
  Check that those values can be read back.
  Check that invalid values are rejected.

  Background:
    Given a communication session has been established

  Scenario Outline: Good sign names are accepted
    Given <name> is copied to ό
    When the CMC sends «SGN="ό"» to which the ADC responds «ACK»
    And the CMC sends «SGN?»
    Then the ADC responds with «SGN="ό"»

    Examples:
      | name     |
      | A        |
      | a        |
      | 1        |
      | .        |
      | -        |
      | //       |
      | \        |
      | ABC1234  |
      | ABC-1234 |


  Scenario Outline: Invalid Characters in Names Caught

    Given <char> is copied to λ
    And we run this python code:
      ό = f"A{λ}B"
    And the CMC sends «SGN="ό"»
    Then the ADC responds with «REJ»

    Examples:
      | char |
      | !    |
      | @    |
      | #    |
      | $    |
      | %    |
      | ^    |
      | &    |
      | *    |
      | (    |
      | )    |
      | _    |
      | +    |
      | ~    |
      | `    |
      # | <    |
      # | >    |
      | ,    |
      | ?    |
      | [    |
      | ]    |
      | {    |
      | }    |
      | \|   |
      | 😊   |

  Scenario Outline: Invalid Names Caught
    Given <name> is copied to ό
    And the CMC sends «SGN="ό"»
    Then the ADC responds with «REJ»

    Examples:
      | name  |
      | AB&C  |
      | όνομα |
      | A@B   |

  Scenario: Maximum length names are accepted
    Given we run this python code:
      ό = "a" * 32
    When the CMC sends «SGN="ό"» to which the ADC responds «ACK»
    And  the CMC sends «SGN?»
    Then the ADC responds with «SGN="ό"»

  Scenario: Overly long names are caught
    Given we run this python code:
      ό = "a" * 33
    When the CMC sends «SGN="ό"»
    Then the ADC responds with «REJ»

  Scenario: Empty names are caught
    When the CMC sends «SGN=""»
    Then the ADC responds with «REJ»
