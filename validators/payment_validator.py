from __future__ import annotations

import logging
from dataclasses import dataclass, field

from validators.errors import RuleViolation

LOGGER = logging.getLogger("checkout-api")

ALLOWED_TYPES = {"online", "wallet", "bnpl"}
ALLOWED_PRICE_TYPES = {"CASH_PRICE", "CREDIT_PRICE"}
METHOD_REQUIRED = ("id", "type", "title", "is_clickable")
OPTION_REQUIRED = ("source_id", "title", "credit", "is_active", "is_default", "price_type")


@dataclass
class ValidationResult:
    selectable_methods: list[dict] = field(default_factory=list)
    eligible_options_by_method: dict[int, list[dict]] = field(default_factory=dict)


class PaymentValidator:
    def __init__(self, node=None) -> None:
        self._node = node

    def _record(self, line: str) -> None:
        current = getattr(self._node, "current_step", None) if self._node is not None else None
        if isinstance(current, dict):
            rules = current.setdefault("rules", [])
            if line not in rules:
                rules.append(line)
        LOGGER.info(line)

    def log_passed(self, rule: str, message: str) -> None:
        self._record(f"{rule} passed: {message}")

    def log_expected_fail(self, rule: str, message: str) -> None:
        self._record(f"{rule} failed as expected: {message}")

    def require_success(self, http_status: int, body) -> None:
        if http_status != 200:
            raise RuleViolation(
                "HTTP",
                "request must return HTTP 200",
                actual=http_status,
            )
        if not isinstance(body, dict):
            raise RuleViolation("CONTRACT", "response body must be a JSON object", actual=type(body).__name__)
        status = body.get("status")
        if status != 200:
            raise RuleViolation(
                "BODY.status",
                "body.status must be 200",
                actual=status,
            )
        self.log_passed("HTTP", "status 200")
        self.log_passed("BODY.status", "status 200")

    def validate(self, body: dict) -> ValidationResult:
        methods = body.get("payment_methods")
        if not isinstance(methods, list):
            raise RuleViolation(
                "R1",
                "payment_methods must be an array",
                actual=type(methods).__name__,
            )

        result = ValidationResult()
        for index, method in enumerate(methods):
            self._validate_method(method, index, result)
        self.log_passed("R1", "required method fields and types")
        return result

    def _validate_method(self, method, index: int, result: ValidationResult) -> None:
        if not isinstance(method, dict):
            raise RuleViolation(
                "R1",
                f"payment_methods[{index}] must be an object",
                actual=type(method).__name__,
            )

        for field_name in METHOD_REQUIRED:
            if field_name not in method:
                raise RuleViolation(
                    "R1",
                    f"missing required field {field_name}",
                    method=method,
                    actual=None,
                )

        self._assert_type(method, "id", int, "R1")
        self._assert_type(method, "type", str, "R1")
        self._assert_type(method, "title", str, "R1")
        self._assert_type(method, "is_clickable", bool, "R1")

        method_type = method["type"]
        if method_type not in ALLOWED_TYPES:
            raise RuleViolation(
                "R1",
                "type must be online, wallet or bnpl",
                method=method,
                actual=method_type,
            )

        if method["is_clickable"] is True:
            result.selectable_methods.append(method)

        if method_type in {"wallet", "bnpl"}:
            if "source_id" not in method:
                raise RuleViolation(
                    "R3",
                    "source_id is required for wallet and bnpl",
                    method=method,
                )
            self._assert_type(method, "source_id", int, "R3")
            self.log_passed("R3", "source_id present and int for wallet/bnpl")

        if method_type == "bnpl":
            self._validate_bnpl_options(method, result)

    def _validate_bnpl_options(self, method: dict, result: ValidationResult) -> None:
        if "options" not in method:
            raise RuleViolation("R4", "options is required for bnpl", method=method)
        options = method["options"]
        if not isinstance(options, list):
            raise RuleViolation(
                "R4",
                "options must be an array",
                method=method,
                actual=type(options).__name__,
            )
        if method["is_clickable"] is True and len(options) == 0:
            raise RuleViolation(
                "R4",
                "options may be empty only when the method is not clickable",
                method=method,
                actual=[],
            )
        self.log_passed("R4", "bnpl options present and valid")

        eligible: list[dict] = []
        for option in options:
            if not isinstance(option, dict):
                raise RuleViolation(
                    "R4",
                    "each option must be an object",
                    method=method,
                    actual=type(option).__name__,
                )
            for field_name in OPTION_REQUIRED:
                if field_name not in option:
                    raise RuleViolation(
                        "R4",
                        f"missing required option field {field_name}",
                        method=method,
                        option=option,
                    )
            self._assert_type(option, "source_id", int, "R4", method=method)
            self._assert_type(option, "title", str, "R4", method=method)
            self._assert_type(option, "credit", int, "R4", method=method)
            self._assert_type(option, "is_active", bool, "R4", method=method)
            self._assert_type(option, "is_default", bool, "R4", method=method)
            self._assert_type(option, "price_type", str, "R7", method=method)

            if option["price_type"] not in ALLOWED_PRICE_TYPES:
                raise RuleViolation(
                    "R7",
                    "price_type must be CASH_PRICE or CREDIT_PRICE",
                    method=method,
                    option=option,
                    actual=option["price_type"],
                )
            self.log_passed("R7", "price_type is CASH_PRICE or CREDIT_PRICE")

            if self.is_eligible(option):
                eligible.append(option)
            else:
                self.log_passed(
                    "R5",
                    f"option.source_id={option.get('source_id')} is ineligible",
                )

        self.log_passed("R5", "inactive or zero-credit options are not eligible")
        result.eligible_options_by_method[method["id"]] = eligible
        if eligible:
            defaults = [opt for opt in eligible if opt["is_default"] is True]
            if len(defaults) != 1:
                raise RuleViolation(
                    "R6",
                    "exactly one eligible option must have is_default=true",
                    method=method,
                    actual=len(defaults),
                )
            self.log_passed("R6", "exactly one eligible option is default")

    @staticmethod
    def is_eligible(option: dict) -> bool:
        return option.get("is_active") is True and isinstance(option.get("credit"), int) and option["credit"] > 0

    @staticmethod
    def is_selectable(method: dict) -> bool:
        return method.get("is_clickable") is True

    def _assert_type(self, obj: dict, field_name: str, expected, rule: str, method=None) -> None:
        value = obj.get(field_name)
        if expected is int and isinstance(value, bool):
            raise RuleViolation(
                rule,
                f"{field_name} must be {expected.__name__}",
                method=method or obj,
                option=obj if "price_type" in obj or "credit" in obj else None,
                actual=f"{type(value).__name__}:{value!r}",
            )
        if not isinstance(value, expected):
            raise RuleViolation(
                rule,
                f"{field_name} must be {expected.__name__}",
                method=method or obj,
                option=obj if "credit" in obj or "price_type" in obj else None,
                actual=f"{type(value).__name__}:{value!r}",
            )
