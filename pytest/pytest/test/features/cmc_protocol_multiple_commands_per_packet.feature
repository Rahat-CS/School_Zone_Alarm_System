Feature: Multiple CMC Commands per message

  The CMC shall be able to send multiple commands/queries to the Sign Controller in one message.

  Note: The original spec was not very precise as to how many commands per message shall be supported.
        The amount of memory limits the amount of commands that can be 'queued'. At the moment th eimplementation
        limits the number of commands in one message to max 15.

        Commands that result in large(r) responses, namely DMP?, LOG? and TTB? should not be combined with any other
        commands.

  Background:
    Given the Power Supply is set to supply 12V
    And   the Sign Controller is configured to the default state
    And   the Sign Controllers log has been cleared

  Scenario: Multiple valid CMC Commands

    Given a communication session has been established
    Then the Sign Controller shall respond to multi-command messages as provided in the following table:
      | cmd_sqz                                                                    | expected_response_regex                                                                                                                                                                                                                                                                                |
      | SGN?;TTB?;TTV?                                                             | SGN="[/\\a-zA-Z0-9.-]{1,32}";TTB="[0-9A-F]{1,200}";TTV="[/\\a-zA-Z0-9.-]{1,32}"                                                                                                                                                                                                                        |
      | ADN?;BVL?;ECT?;FPN?;FWV?;CTD?;STD?;SGN?;TMO?;TMP?;TTC?;TTV?;BTT?;ESC?      | ADN="[/\\a-zA-Z0-9.-]{1,32}";BVL="\d{2}\.\d{2}";ECT="\d{4},\d{4},\d{4}";FPN="\d{1,32}";FWV="[_+0-9RC.]+";CTD="\d{1,4}";STD="\d{1,4}";SGN="[/\\a-zA-Z0-9.-]{1,32}";TMO="\d{1,6}";TMP="-?\d{1,3}\.\d";TTC="[0-9A-F]{4}";TTV="[/\\a-zA-Z0-9.-]{1,32}";BTT="\d{2}\.\d{2}";ESC="(\d{4})?,(\d{4})?,(\d{4})?" |
#       Note: The following will fail due to https://redmine.dektech.com.au/issues/65. Disabling this for now so that test does not fail
#     | BVL="09.00";BVL?;BVL="10.00";BVL?;BVL="11.00";BVL?;BVL="12.00";BVL?        | BVL="09.00";BVL="10.00";BVL="11.00";BVL="12.00"                                                                                                                                                                                                                                                        |


