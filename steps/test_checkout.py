from pytest_bdd import parsers, scenarios, given, when, then

from validators.errors import RuleViolation

scenarios("checkout_payment.feature")


@given(parsers.parse('a checkout customer with cell number "{cell_number}"'))
def checkout_customer(cell_number, payment_api):
    payment_api.cell_number = cell_number


@when("the payment methods are requested")
def request_payment_methods(payment_api):
    http_status, body = payment_api.get_payment_methods(payment_api.cell_number)
    payment_api.http_status = http_status
    payment_api.body = body


@then("the payment response should succeed")
def payment_response_succeeds(payment_api, validator):
    validator.require_success(payment_api.http_status, payment_api.body)


@then("all payment method rules should pass")
def all_rules_pass(payment_api, validator):
    payment_api.validation = validator.validate(payment_api.body)


@then(parsers.parse('methods "{types}" should be selectable'))
def methods_are_selectable(types, payment_api, validator):
    expected = {item.strip() for item in types.split(",") if item.strip()}
    actual = {method["type"] for method in payment_api.validation.selectable_methods}
    missing = expected - actual
    if missing:
        raise AssertionError(
            f"R2: expected selectable types {sorted(expected)}, actual {sorted(actual)}"
        )
    validator.log_passed("R2", f"selectable types {sorted(actual)}")


@then(parsers.parse('method "{method_type}" should not be selectable'))
def method_not_selectable(method_type, payment_api, validator):
    actual = {method["type"] for method in payment_api.validation.selectable_methods}
    if method_type in actual:
        raise AssertionError(f"R2: method {method_type} must not be selectable | actual={actual}")
    validator.log_passed("R2", f"{method_type} is not selectable")


@then("bnpl options may be empty")
def bnpl_options_may_be_empty(payment_api, validator):
    bnpl = next(method for method in payment_api.body["payment_methods"] if method["type"] == "bnpl")
    if bnpl["is_clickable"] is False and not isinstance(bnpl.get("options"), list):
        raise AssertionError("R4: blocked bnpl must still expose an options array")
    validator.log_passed("R4", "blocked bnpl may have empty options")


@then(parsers.parse("the bnpl option with source_id {source_id:d} should be ineligible"))
def option_is_ineligible(source_id, payment_api, validator):
    bnpl = next(method for method in payment_api.body["payment_methods"] if method["type"] == "bnpl")
    option = next(item for item in bnpl["options"] if item["source_id"] == source_id)
    if validator.is_eligible(option):
        raise AssertionError(
            f"R5: option.source_id={source_id} must be ineligible | actual={option}"
        )
    eligible = payment_api.validation.eligible_options_by_method.get(bnpl["id"], [])
    if any(item["source_id"] == source_id for item in eligible):
        raise AssertionError(f"R5: option.source_id={source_id} was marked eligible")
    validator.log_passed("R5", f"option.source_id={source_id} is ineligible")


@then(parsers.parse('validation should fail with rule "{rule}"'))
def validation_fails_with_rule(rule, payment_api, validator):
    try:
        validator.validate(payment_api.body)
    except RuleViolation as error:
        if error.rule != rule:
            raise AssertionError(f"expected rule {rule}, got {error.rule}: {error}") from error
        validator.log_expected_fail(error.rule, str(error))
        return
    raise AssertionError(f"expected {rule} to fail, but validation passed")


@then(parsers.parse('the payment response should fail fast with rule "{rule}"'))
def fail_fast(rule, payment_api, validator):
    try:
        validator.require_success(payment_api.http_status, payment_api.body)
    except RuleViolation as error:
        if error.rule != rule:
            raise AssertionError(f"expected rule {rule}, got {error.rule}: {error}") from error
        validator.log_expected_fail(error.rule, str(error))
        return
    raise AssertionError(f"expected fast failure {rule}, but the response was accepted")
