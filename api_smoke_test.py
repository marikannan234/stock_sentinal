from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
OPENAPI_URL = f"{BASE_URL}/openapi.json"
TIMEOUT = 15


@dataclass
class EndpointResult:
    method: str
    path: str
    status_code: int | None
    elapsed_ms: int
    success: bool
    error: str | None = None


class SmokeTester:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.spec: dict[str, Any] = {}
        self.components: dict[str, Any] = {}
        self.state: dict[str, Any] = {
            "symbol": "AAPL",
            "ticker": "AAPL",
            "trade_id": 1,
            "ticket_id": 1,
            "alert_id": 1,
            "email": f"smoke-{int(time.time())}@example.com",
            "password": "SmokeTest123!",
            "new_password": "SmokeTest456!",
        }
        self.results: list[EndpointResult] = []

    def wait_for_openapi(self, retries: int = 60, delay: float = 2.0) -> None:
        for _ in range(retries):
            try:
                response = self.session.get(OPENAPI_URL, timeout=TIMEOUT)
                if response.ok:
                    self.spec = response.json()
                    self.components = self.spec.get("components", {}).get("schemas", {})
                    return
            except requests.RequestException:
                pass
            time.sleep(delay)
        raise RuntimeError(f"Unable to fetch OpenAPI spec from {OPENAPI_URL}")

    def bootstrap_auth(self) -> None:
        register_payload = {
            "email": self.state["email"],
            "full_name": "Smoke Test User",
            "password": self.state["password"],
        }
        self._request("POST", "/api/auth/register", json_body=register_payload, allow_fail=True)

        login_payload = {
            "email": self.state["email"],
            "password": self.state["password"],
        }
        login_result = self._request("POST", "/api/auth/login-json", json_body=login_payload, allow_fail=True)
        if login_result.success:
            try:
                token = self.session.post(
                    f"{BASE_URL}/api/auth/login-json",
                    json=login_payload,
                    timeout=TIMEOUT,
                ).json().get("access_token")
            except Exception:
                token = None
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})

    def run(self) -> int:
        self.wait_for_openapi()
        self.bootstrap_auth()

        paths: dict[str, Any] = self.spec.get("paths", {})
        for path, methods in paths.items():
            for method in ["get", "post", "put", "patch", "delete"]:
                operation = methods.get(method)
                if not operation:
                    continue
                self.exercise_operation(path, method.upper(), operation)

        self.print_report()
        return 0 if all(result.success for result in self.results) else 1

    def exercise_operation(self, path: str, method: str, operation: dict[str, Any]) -> None:
        if path in {"/openapi.json"}:
            return

        json_body = self.build_request_body(operation, path, method)
        params = self.build_query_params(operation, path)
        resolved_path = self.resolve_path(path)

        result = self._request(method, resolved_path, params=params, json_body=json_body, allow_fail=True)
        self.results.append(result)

        if result.success:
            try:
                response = self.session.request(method, f"{BASE_URL}{resolved_path}", params=params, json=json_body, timeout=TIMEOUT)
                body = response.json() if response.content else None
                self.capture_state(path, method, body)
            except Exception:
                pass

    def build_query_params(self, operation: dict[str, Any], path: str) -> dict[str, Any]:
        params: dict[str, Any] = {}
        for parameter in operation.get("parameters", []):
            if parameter.get("in") != "query":
                continue
            name = parameter["name"]
            schema = self.resolve_schema(parameter.get("schema", {}))
            params[name] = self.sample_value(name, schema)

        if path == "/api/trade/{trade_id}/close":
            params["exit_price"] = 125.5
        return params

    def build_request_body(self, operation: dict[str, Any], path: str, method: str) -> Any:
        overrides: dict[tuple[str, str], Any] = {
            ("POST", "/api/auth/register"): {
                "email": self.state["email"],
                "full_name": "Smoke Test User",
                "password": self.state["password"],
            },
            ("POST", "/api/auth/login-json"): {
                "email": self.state["email"],
                "password": self.state["password"],
            },
            ("POST", "/api/auth/forgot-password"): {"email": self.state["email"]},
            ("POST", "/api/auth/forgot-password/verify"): {
                "email": self.state["email"],
                "otp": "123456",
                "new_password": self.state["new_password"],
            },
            ("POST", "/api/support/ticket"): {
                "subject": "Smoke test ticket",
                "message": "Smoke test support ticket body.",
                "priority": "medium",
            },
            ("POST", "/api/news/sentiment/analyze"): {
                "articles": [
                    {
                        "title": "Apple stock rises on strong earnings",
                        "summary": "Investors reacted positively after Apple reported strong quarterly growth.",
                    }
                ]
            },
            ("PUT", "/api/user/profile"): {"full_name": "Smoke Test Updated"},
            ("PUT", "/api/user/settings"): {
                "email_notifications": True,
                "dark_mode": False,
                "preferred_currency": "USD",
                "two_factor_enabled": False,
            },
            ("POST", "/api/portfolio"): {"ticker": "AAPL", "quantity": 5, "price": 100},
            ("POST", "/api/portfolio/remove"): {"ticker": "AAPL"},
            ("POST", "/api/watchlist"): {"ticker": "AAPL"},
            ("POST", "/api/trade/"): {
                "symbol": "AAPL",
                "quantity": 2,
                "entry_price": 100,
                "trade_type": "BUY",
                "notes": "Smoke test trade",
            },
            ("PUT", "/api/trade/{trade_id}"): {
                "current_price": 125.0,
                "status": "executed",
                "notes": "Updated by smoke test",
            },
            ("POST", "/api/alerts"): {
                "stock_symbol": "AAPL",
                "condition": ">",
                "target_value": 150,
                "alert_type": "price",
            },
        }
        if (method, path) in overrides:
            if (method, path) == ("POST", "/api/auth/register"):
                return {
                    "email": f"register-{int(time.time() * 1000)}@example.com",
                    "full_name": "Smoke Test User",
                    "password": self.state["password"],
                }
            return overrides[(method, path)]

        request_body = operation.get("requestBody", {})
        content = request_body.get("content", {})
        json_content = content.get("application/json") or content.get("application/x-www-form-urlencoded")
        if not json_content:
            return None
        schema = self.resolve_schema(json_content.get("schema", {}))
        return self.sample_from_schema(schema)

    def resolve_path(self, path: str) -> str:
        if "{alert_id}" in path:
            self.state["alert_id"] = self.lookup_latest_alert_id()

        replacements = {
            "symbol": self.state.get("symbol", "AAPL"),
            "ticker": self.state.get("ticker", "AAPL"),
            "trade_id": self.state.get("trade_id", 1),
            "ticket_id": self.state.get("ticket_id", 1),
            "alert_id": self.state.get("alert_id", 1),
        }
        resolved = path
        for key, value in replacements.items():
            resolved = resolved.replace(f"{{{key}}}", str(value))
        return resolved

    def lookup_latest_alert_id(self) -> int:
        try:
            response = self.session.get(f"{BASE_URL}/api/alerts", timeout=TIMEOUT)
            if response.ok:
                payload = response.json()
                if isinstance(payload, list) and payload:
                    first = payload[0]
                    if isinstance(first, dict) and first.get("id"):
                        return int(first["id"])
        except requests.RequestException:
            pass
        return int(self.state.get("alert_id", 1))

    def resolve_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            return self.components.get(ref_name, {})
        return schema

    def sample_from_schema(self, schema: dict[str, Any]) -> Any:
        schema = self.resolve_schema(schema)
        if "default" in schema:
            return schema["default"]
        if "enum" in schema:
            return schema["enum"][0]

        schema_type = schema.get("type")
        if schema_type == "object" or "properties" in schema:
            data: dict[str, Any] = {}
            properties = schema.get("properties", {})
            required = schema.get("required", list(properties.keys()))
            for name, prop_schema in properties.items():
                if name in required or "default" in prop_schema:
                    data[name] = self.sample_value(name, self.resolve_schema(prop_schema))
            return data
        if schema_type == "array":
            item_schema = self.resolve_schema(schema.get("items", {}))
            return [self.sample_from_schema(item_schema)]
        return self.sample_value("value", schema)

    def sample_value(self, name: str, schema: dict[str, Any]) -> Any:
        schema = self.resolve_schema(schema)
        if "default" in schema:
            return schema["default"]
        if "enum" in schema:
            return schema["enum"][0]

        lowered = name.lower()
        if lowered.endswith("email") or lowered == "email":
            return self.state["email"]
        if "password" in lowered and "current" not in lowered and "new" not in lowered:
            return self.state["password"]
        if lowered == "current_password":
            return self.state["password"]
        if lowered == "new_password":
            return self.state["new_password"]
        if lowered == "otp":
            return "123456"
        if lowered in {"symbol", "ticker", "q"}:
            return "AAPL"
        if lowered == "range":
            return "1w"
        if lowered == "exit_price":
            return 125.5
        if lowered == "status_filter":
            return "open"
        if lowered == "status":
            return "executed"
        if lowered == "priority":
            return "medium"
        if lowered == "trade_type":
            return "BUY"
        if lowered == "subject":
            return "Smoke test ticket"
        if lowered == "message":
            return "Smoke test message"
        if lowered == "full_name":
            return "Smoke Test User"
        if lowered == "preferred_currency":
            return "USD"

        schema_type = schema.get("type")
        if schema_type == "string":
            return "sample"
        if schema_type == "integer":
            return max(schema.get("minimum", 1), 1)
        if schema_type == "number":
            minimum = schema.get("minimum")
            exclusive_minimum = schema.get("exclusiveMinimum")
            if exclusive_minimum is not None:
                return float(exclusive_minimum) + 1
            if minimum is not None:
                return float(minimum) if float(minimum) > 0 else 1.0
            return 1.0
        if schema_type == "boolean":
            return True
        if schema_type == "array":
            return []
        if schema_type == "object":
            return {}
        return "sample"

    def capture_state(self, path: str, method: str, body: Any) -> None:
        if not isinstance(body, (dict, list)):
            return
        if path == "/api/support/ticket" and method == "POST" and isinstance(body, dict) and body.get("id"):
            self.state["ticket_id"] = body["id"]
        if path == "/api/trade/" and method == "POST" and isinstance(body, dict) and body.get("id"):
            self.state["trade_id"] = body["id"]
        if path in {"/api/alerts", "/api/alerts/"} and method == "POST" and isinstance(body, dict) and body.get("id"):
            self.state["alert_id"] = body["id"]

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        allow_fail: bool = False,
    ) -> EndpointResult:
        url = f"{BASE_URL}{path}"
        started = time.perf_counter()
        try:
            request_kwargs: dict[str, Any] = {"params": params, "timeout": TIMEOUT}
            if method == "POST" and path == "/api/auth/login":
                request_kwargs["data"] = {"username": self.state["email"], "password": self.state["password"]}
                request_kwargs["headers"] = {"Content-Type": "application/x-www-form-urlencoded"}
            elif json_body is not None:
                request_kwargs["json"] = json_body

            response = self.session.request(method, url, **request_kwargs)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            success = 200 <= response.status_code < 300
            error = None
            if not success:
                try:
                    error = json.dumps(response.json(), ensure_ascii=True)
                except Exception:
                    error = response.text[:200]
            return EndpointResult(method=method, path=path, status_code=response.status_code, elapsed_ms=elapsed_ms, success=success, error=error)
        except requests.RequestException as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            result = EndpointResult(method=method, path=path, status_code=None, elapsed_ms=elapsed_ms, success=False, error=str(exc))
            if not allow_fail:
                self.results.append(result)
            return result

    def print_report(self) -> None:
        pass_count = 0
        fail_count = 0
        for result in self.results:
            status_text = result.status_code if result.status_code is not None else "ERR"
            if result.success:
                pass_count += 1
                print(f"[PASS] {result.method} {result.path} -> {status_text} ({result.elapsed_ms}ms)")
            else:
                fail_count += 1
                suffix = f' -> "{result.error}"' if result.error else ""
                print(f"[FAIL] {result.method} {result.path} -> {status_text} ({result.elapsed_ms}ms){suffix}")
        print(f"\nSummary: {pass_count} passed, {fail_count} failed")


if __name__ == "__main__":
    tester = SmokeTester()
    try:
        sys.exit(tester.run())
    except Exception as exc:
        print(f"[FAIL] smoke test bootstrap -> {exc}")
        sys.exit(1)
