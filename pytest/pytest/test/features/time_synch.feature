
Feature: Time Synchronization

  The Sign Controller shall adjust its RTC only if:
    a) The RTT M is less than or equal to acceptable round trip time that was
       specified in the RTC synchronisation request; or
    b) The current Sign Controller’s RTC is greater than (T CMC + 3/2 × RTTM) or
    c) The current Sign Controller’s RTC is less than (TCMC - 1⁄2 × RTTM).

  Background:
    Given  the Power Supply is set to supply 12V
    And the door switch is set to closed
    And the app is connected to the CMC
    And the ADC is configured to the default state

  Scenario: Manual Setting the time

    # basic time synchronization
    #
    # Will use JLink to set the current RTC to eliminate some of the timing uncertainty.
    # this shall be done after establishing a CMC session to cut out the delay due to setting up a session
    #
    Given the ADC's realtime clock is set to 1603160000
    And the CMC sends «SYN="999"» to which the ADC responds «DTE?»
    And the CMC sends «DTE="1603160050"» to which the ADC responds «SYN="δ,α"»
    Then the following is true: δ < 5
    And α equals 50 within tolerance (+5 -5)

  Scenario Outline: Setting the time

    # basic time synchronization
    #
    # Will use JLink to set the current RTC to eliminate some of the timing uncertainty.
    # this shall be done after establishing a CMC session to cut out the delay due to setting up a session
    #
    Given <crnt_rtc>, <new_rtc> and <adjustment> are copied to τ_cur, τ_new and α_exp
    And the ADC's realtime clock is set to τ_cur
    Then the CMC sends «SYN="999"» to which the ADC responds «DTE?»
    And the CMC sends «DTE="τ_new"» to which the ADC responds «SYN="δt,α_got"»
    And the following is true: δt < 5
    And α_got equals α_exp within tolerance (+5 -5)
    And this is just a dummy step to consume the <notes> column of the Examples Table

    Examples:
    | crnt_rtc    | new_rtc     | adjustment | notes                          |
    | 1603149000  | 1603149400  | 400        |                                |
    | 1603149999  | 1603149900  | -99        |                                |
    | 1603160000  | 1603150000  | -999       | adjustment saturates at +/-999 |
    | 1603200000  | 1603500000  | 999        | adjustment saturates at +/-999 |


  Scenario Outline: RTT measurement

    #
    # Scenario for exercising the RTT measurement.
    # THis test assumes that the RTT in achievable in the test-setup is < tolerance)
    #
    Given the ADC's realtime clock is set to 1603400000
    And   <delay> is copied to Δ
    Then  the CMC sends «SYN="999"» to which the ADC responds «DTE?»
    And   we pause for Δ seconds
    And   the CMC sends «DTE="1603500000"» to which the ADC responds «SYN="δ,α"»
    And   α equals 999 exactly
    And   δ equals Δ within tolerance (+3 -0)

    Examples:
    | delay |
    | 10    |
    | 20    |
    | 30    |

  Scenario Outline: Timing adjustment ignored when measured RTT exceeds specified acceptable RTT

    # Test the behaviour if the measured RTT (RTT_M) exceeds the acceptable RTT which is specified when
    # by the CMC in the initial SYN="xxx" request
    # If this happens then the timing change should be ignored by the Sign Controller
    #
    # To verify we probably have to capture SWO output and scan for presence of timing change

    Given the ADC's realtime clock is set to 1603400000
    And   <new_rtc>, <rtt> and <rtc_adjustment> are copied to τ_new, δ_rtt, β
    And   <delay> is copied to Δ
    Then  the CMC sends «SYN="δ_rtt"» to which the ADC responds «DTE?»
    And   we pause for Δ seconds
    When  the CMC sends «DTE="τ_new"» to which the ADC responds «SYN="δ,α_got"»
    Then  the following is true: (α_got != 0) if β else (α_got == 0)


    Examples:
    | new_rtc     | rtt | delay | rtc_adjustment |
    | 1603400000  | 999 |  30   | yes            |
    | 1603400000  | 050 |  60   | no             |


  @xfail: https://redmine.dektech.com.au/issues/381 https://redmine.dektech.com.au/issues/383
  Scenario Outline: Sign Controller only adjusts the RTC if measured RTT is small enough and the change exceeds threshold defined

    # The Sign Controller shall only adjyst it's RTC if the measured RTT is below a threshold defined in the
    # Synchronization request that initiates a timing change and:
    # - it's current RTC_SC > (T_CMC + 3/2 × RTT_M) or
    # - it's RTC_SC is less than (T_CMC - 1⁄2 × RTT_M).
    #
    # The SYN=... response from the Sign Controller indicates whether or not a timing adjustment happened.
    # We might want to capture SWO to make sure that timing changes do/don't occur though

    Given the Sign Controllers RTC is set to 1603400000
    Then  the Sign Controller shall respond with DTE? when CMC sends the command SYN="999"
    When  the CMC now sends DTE="<new_rtc>" after a delay of <delay> seconds
    Then  the Sign Controller shall adjust it's RTC: <rtc_adjustment>
    And   this is just a dummy step to consume the <notes> column of the Examples Table

    # Note: Examples 1 & 2 will fail due to Issue 383 (see Redmine)

    Examples:
    | new_rtc     | delay | rtc_adjustment | notes                                                              |
    | 1603400012  | 10    | no             | pos change too small: current RTC_SC !< (T_CMC - 1⁄2 × RTT_M)      |
    | 1603400005  | 8     | no             | neg change too small: current RTC_SC !> (T_CMC + 3/2 × RTT_M       |
    | 1603400115  | 10    | yes            | current RTC_SC < (T_CMC - 1⁄2 × RTT_M)                             |
    | 1603400005  | 10    | yes            | current RTC_SC > (T_CMC + 3/2 × RTT_M                              |


  Scenario Outline: Reject any attempts to set the time to 2016/07/07 12:00:00 or earlier

    #
    # Workaround for a CMC bug. For details refer to: https://redmine.dektech.com.au/issues/233
    #

    When  the CMC attempts to set the Sign Controllers time to <new_time> which is prior to 2016/07/07 12:00:00
    Then  the Sign Controller shall respond with REJ

    Examples:
    | new_time            |
    | 06-07-2016 11:59:59 |
    | 01-01-2000 00:01:00 |
