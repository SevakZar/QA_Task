Feature: Checkout payment methods
  The checkout page renders methods returned by GET /payment/.
  Invalid methods or BNPL options must not pass validation.

  Scenario: S01 happy path with online, wallet and bnpl clickable
    Given a checkout customer with cell number "09121111111"
    When the payment methods are requested
    Then the payment response should succeed
    And all payment method rules should pass
    And methods "online,wallet,bnpl" should be selectable

  Scenario: S02 BNPL is blocked and not selectable
    Given a checkout customer with cell number "09122222222"
    When the payment methods are requested
    Then the payment response should succeed
    And all payment method rules should pass
    And method "bnpl" should not be selectable
    And bnpl options may be empty

  Scenario: S03 option with zero credit is ineligible
    Given a checkout customer with cell number "09123333333"
    When the payment methods are requested
    Then the payment response should succeed
    And all payment method rules should pass
    And the bnpl option with source_id 386 should be ineligible

  Scenario: S04 non-active option is ineligible
    Given a checkout customer with cell number "09124444444"
    When the payment methods are requested
    Then the payment response should succeed
    And all payment method rules should pass
    And the bnpl option with source_id 386 should be ineligible

  Scenario: S05 several eligible defaults violate R6
    Given a checkout customer with cell number "09125555555"
    When the payment methods are requested
    Then the payment response should succeed
    And validation should fail with rule "R6"

  Scenario: S06 missing required method field violates R1
    Given a checkout customer with cell number "09126666666"
    When the payment methods are requested
    Then the payment response should succeed
    And validation should fail with rule "R1"

  Scenario: S07 wrong field types fail type validation
    Given a checkout customer with cell number "09127777777"
    When the payment methods are requested
    Then the payment response should succeed
    And validation should fail with rule "R1"

  Scenario: S08 HTTP 500 fails fast
    Given a checkout customer with cell number "09128888888"
    When the payment methods are requested
    Then the payment response should fail fast with rule "HTTP"

  Scenario: S09 non-success body status fails fast
    Given a checkout customer with cell number "09129999999"
    When the payment methods are requested
    Then the payment response should fail fast with rule "BODY.status"

  Scenario: S10 wallet without source_id violates R3
    Given a checkout customer with cell number "09120000009"
    When the payment methods are requested
    Then the payment response should succeed
    And validation should fail with rule "R3"

  Scenario: S11 invalid price_type violates R7
    Given a checkout customer with cell number "09120000010"
    When the payment methods are requested
    Then the payment response should succeed
    And validation should fail with rule "R7"

  Scenario: S12 clickable BNPL with empty options violates R4
    Given a checkout customer with cell number "09120000011"
    When the payment methods are requested
    Then the payment response should succeed
    And validation should fail with rule "R4"
