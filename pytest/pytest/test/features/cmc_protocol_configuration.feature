Feature: Sign Controller Configurability

  The following is a list of commands/parameters that the CMC can configure the Sign Controller with

  - BVL : Set the threshold at which the Battery Low alarm will be generated. Format: BVL="dd.dd"
  - ECT : Set the min current threshold at which the Display Error alarm will be generated.
          Format: ECT="dddd,dddd,dddd" where dddd is a 4 digit decimal number representing mA. The numbers are
          0-padded if less than 4 digits are needed.
  - FPN : Configure the Flash-pattern. Format: FPN="ddd .....d".
          The length of the flash pattern is 1-32 digits.
  - CTD : set the wait period (in RTC ticks) before attempting a Set period between reattempts in the Sign controller
          reconnection. Up to a 4-digit number: CTD="dddd". Number does not have to be 0-padded.
  - STD : Get or set the wait period for closing a connection due to
          inactivity. Up to a 4-digit number: STD="dddd"
  - SGN : Set and get sign ID. Sign ID is up to 32 characters in 0-9, a-z, A-Z,'.','-','/','\'
          SGN="abc ....."
  - TMO : Get/Set the period in ticks when no communications has
          occurred with the CMC, at which point, the SOP is set to 0
          and an alarm raised. If set to 0, the period is infinite. Upto a
          6-digit decimal number, not 0-padded: TMO="dddddd"
  - TTB : Configure the Operating Timetable.
          N=Number of timetable segments (1-byte)
          S1=Start time of the 1 timetable segment in ticks (4-bytes)
          X1=Number of calendar entries in 1 segment (1-byte)
          O1=Calendar for 1 segment (Variable).
          S2=Start time of the 2 timetable segment in ticks (4-bytes)
          X2=Number of calendar entries in 2 segment (1-byte)
          O2=Calendar for 2 segment (Variable)
          S3=Start time of the 3 timetable segment in ticks (4-bytes)
          X3=Number of calendar entries in 3 segment (1-byte)
          O3=Calendar for 3 segment (Variable)
  - TTO : Get/Set operating durations. There will be three operating
          durations (in ticks) specified which are:
          S1=Duration of the 1 timetabled operation
          S2=Duration between 1 and 2 timetabled operation
          S3=Duration of the 2 timetabled operation
          TTO="S1,S2,S3", e.g. TTO="=”5400,18000,5400”
  - TTV : Set/Get timetable version. Timetable version is up to 32
          characters 0-9, a-z, A-Z,'.','-','_','/','\'.

  All of the configurations shall be persistent, i.e. be stored in flash and thus survive any restarts.

  Background:

    # For these tests we don't need to establish a default config since the configuration is the
    # subject of the test. All that needs to be done is to supply power, reset/start the Application FW and
    # then establish a CMC session
    Given the Power Supply is set to supply 12V
    And the Sign Controller Application FW has been started
    And  the Sign Controller has established a CMC session

  Scenario Outline: Battery Voltage Threshold, Display Current Threshold and Flash Pattern Configuration

    Given the CMC configures the Battery Voltage Threshold to <bvl>
    And the CMC configures the Display Current Threshold to <ect>
    And the CMC configures the Flash Pattern to <fpn>
    When the PSU is disabled and then enabled again after a few seconds
    And the Sign Controller Application FW has been started
    Then the Sign Controller shall establish a CMC session
    And the Sign Controller shall report BVL = <bvl>
    And the Sign Controller shall report ECT = <ect>
    And the Sign Controller shall report FPN = <fpn>
    And this is a dummy step to consume <Notes> from the example table

    Examples:
    | bvl   | ect             | fpn                               | Notes                                     |
    | 09.00 | 0001,0001,0001  | 7                                 | shortest possible flash pattern           |
    | 10.31 | 0500,0500,1800  | 70707070707070707070707070707070  | lognest possible flash pattern            |
    | 14.24 | 9999,9999,9999  | 13731214321                       | some inbetween flash pattern lengthwise   |

  Scenario Outline: Reconnection Hold-Off Time, CMC Session No-Activity Timeout and Sign Identity Configuration

    Given the CMC configures the Reconnection Hold-Off Time to <ctd>
    And the CMC configures the CMC Session No Activity Timeout to <std>
    And the CMC configures the Sign ID to <sgn>
    When the PSU is disabled and then enabled again after a few seconds
    And the Sign Controller Application FW has been started
    Then the Sign Controller shall establish a CMC session
    And the Sign Controller shall report CTD = <ctd>
    And the Sign Controller shall report STD = <std>
    And the Sign Controller shall report SGN = <sgn>
    And this is a dummy step to consume <Notes> from the example table

    Examples:
    | ctd  |  std  | sgn                                 | Notes                                   |
    |  0   |   0   | A                                   | shortest possible config - 1 char       |
    |  60  |  60   | ABCDEFGHIJKLMNOPQRSTUVWXYZ.-\/      | Longest possible : 32 Char              |
    | 9999 |  9999 | abcdefghijklmnopqrstuvwxyz0123      |    -"-                                  |
    |  321 |   512 | 0123456789./././\\\.\\.\\\.\34      |    -"-                                  |
    | 0020 |  0020 | Sign-009                            | Something inbetween                     |


  Scenario Outline: No Communication Alarm Duration, Timetable, Operating Duration and Timetable Version Configuration

    # The timetable is already given a good workout in timetabled_operation.feature
    # The scenario here is just to ensure the setting is non-volatile

    Given the CMC configures the No Communication Alarm Duration to <tmo>
    And   the CMC configures the Timetable to <ttb>
    And   the CMC configures the Operating Durations to <tto>
    And   the CMC configures the Timetable Version to <ttv>
    When  the PSU is disabled and then enabled again after a few seconds
    And   the Sign Controller Application FW has been started
    Then  the Sign Controller shall establish a CMC session
    And   the Sign Controller shall report TMO = <tmo>
    And   the Sign Controller shall report TTB = <ttb>
    And   the Sign Controller shall report TTO = <tto>
    And   the Sign Controller shall report TTV = <ttv>
    And   this is a dummy step to consume <Notes> from the example table

    Examples:
    | tmo     |  ttb             | tto               | ttv                            | Notes                       |
    | 0       |  015F7A3ED80101  | 5400,18000,5400   | A                              | shortest possible : 2 char  |
    | 3600    |  015F7A3ED801FF  | 36000,0,0         | ABCDEFGHIJKLMNOPQRSTUVWXYZ.-\/ | Longest possible : 32 Char  |
    | 999999  |  01FFFF0FFF0101  | 86400,86400,86400 | abcdefghijklmnopqrstuvwxyz0123 |    -"-                      |
    | 000300  |  015F7A3ED801FF  | 00001,00001,00001 | 0123456789./././\\\.\\.\\\.\34 |    -"-                      |
    | 000010  |  01FFFF0FFF0101  | 010,010,010       | Sign-009                       | Something inbetween         |


  Scenario Outline: Display Recovery Hold-off duration Configuration

    Given the CMC configures the Display Recovery Hold-Off Duration to <drh>
    When  the PSU is disabled and then enabled again after a few seconds
    And   the Sign Controller Application FW has been started
    Then  the Sign Controller shall establish a CMC session
    And   And the Sign Controller shall report DRH = <drh>

    Examples:
    | drh |
    | 000 |
    | 010 |
    | 999 |
