"""
API Testing Tool

Provides HTTP request capabilities for testing REST APIs.
"""
from claude_agent_sdk import tool
from typing import Any, Dict, List, Optional
import json
import time

# Import aiohttp for async HTTP requests
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Import requests as fallback
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@tool(
    "api_test",
    "Make HTTP requests to test API endpoints",
    {
        "url": str,
        "method": str,
        "headers": dict,
        "body": dict,
        "params": dict,
        "timeout": int,
        "expected_status": int,
        "expected_json": dict
    }
)
async def api_test(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make an HTTP request to test an API endpoint.

    Args:
        url: Full URL to request
        method: HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
        headers: Request headers (optional)
        body: Request body for POST/PUT/PATCH (optional)
        params: URL query parameters (optional)
        timeout: Request timeout in seconds (default: 30)
        expected_status: Expected HTTP status code for assertion (optional)
        expected_json: Expected JSON response fields for assertion (optional)

    Returns:
        Response details including status, headers, body, and timing
    """
    url = args.get("url", "")
    method = args.get("method", "GET").upper()
    headers = args.get("headers", {})
    body = args.get("body", None)
    params = args.get("params", {})
    timeout = args.get("timeout", 30)
    expected_status = args.get("expected_status", None)
    expected_json = args.get("expected_json", None)

    if not url:
        return {
            "content": [{"type": "text", "text": "Error: URL is required"}],
            "is_error": True
        }

    # Validate method
    valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    if method not in valid_methods:
        return {
            "content": [{
                "type": "text",
                "text": f"Invalid method: {method}. Must be one of: {valid_methods}"
            }],
            "is_error": True
        }

    # Add default headers
    if "Content-Type" not in headers and body:
        headers["Content-Type"] = "application/json"
    if "User-Agent" not in headers:
        headers["User-Agent"] = "CodeTestingAgent/1.0"

    result = {
        "url": url,
        "method": method,
        "request_headers": headers,
        "request_body": body,
        "assertions": []
    }

    start_time = time.time()

    try:
        if AIOHTTP_AVAILABLE:
            # Use aiohttp for async requests
            async with aiohttp.ClientSession() as session:
                request_kwargs = {
                    "headers": headers,
                    "params": params,
                    "timeout": aiohttp.ClientTimeout(total=timeout)
                }

                if body and method in ["POST", "PUT", "PATCH"]:
                    request_kwargs["json"] = body

                async with session.request(method, url, **request_kwargs) as response:
                    result["status_code"] = response.status
                    result["response_headers"] = dict(response.headers)

                    # Try to get response body
                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            result["response_body"] = await response.json()
                        except:
                            result["response_body"] = await response.text()
                    else:
                        text = await response.text()
                        result["response_body"] = text[:5000]
                        if len(text) > 5000:
                            result["response_body"] += "\n... (truncated)"

        elif REQUESTS_AVAILABLE:
            # Fallback to requests (synchronous)
            request_kwargs = {
                "headers": headers,
                "params": params,
                "timeout": timeout
            }

            if body and method in ["POST", "PUT", "PATCH"]:
                request_kwargs["json"] = body

            response = requests.request(method, url, **request_kwargs)

            result["status_code"] = response.status_code
            result["response_headers"] = dict(response.headers)

            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    result["response_body"] = response.json()
                except:
                    result["response_body"] = response.text[:5000]
            else:
                result["response_body"] = response.text[:5000]

        else:
            return {
                "content": [{
                    "type": "text",
                    "text": "Neither aiohttp nor requests is installed.\n"
                           "Install with: pip install aiohttp requests"
                }],
                "is_error": True
            }

        result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

        # Run assertions
        all_passed = True

        if expected_status is not None:
            passed = result["status_code"] == expected_status
            result["assertions"].append({
                "type": "status_code",
                "expected": expected_status,
                "actual": result["status_code"],
                "passed": passed
            })
            if not passed:
                all_passed = False

        if expected_json is not None and isinstance(result["response_body"], dict):
            for key, expected_value in expected_json.items():
                actual_value = result["response_body"].get(key)
                passed = actual_value == expected_value
                result["assertions"].append({
                    "type": "json_field",
                    "field": key,
                    "expected": expected_value,
                    "actual": actual_value,
                    "passed": passed
                })
                if not passed:
                    all_passed = False

        result["all_assertions_passed"] = all_passed

    except aiohttp.ClientError as e:
        result["error"] = f"Request failed: {e}"
        result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    except requests.RequestException as e:
        result["error"] = f"Request failed: {e}"
        result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    except Exception as e:
        result["error"] = f"Unexpected error: {type(e).__name__}: {e}"
        result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    # Format output
    output = "=== API Test Result ===\n\n"
    output += f"URL: {result['url']}\n"
    output += f"Method: {result['method']}\n"
    output += f"Response Time: {result.get('response_time_ms', 'N/A')}ms\n\n"

    if "error" in result:
        output += f"❌ ERROR: {result['error']}\n"
    else:
        output += f"Status Code: {result['status_code']}\n\n"

        output += "=== Response Headers ===\n"
        for key, value in list(result.get('response_headers', {}).items())[:10]:
            output += f"  {key}: {value[:100]}\n"

        output += "\n=== Response Body ===\n"
        body = result.get('response_body', '')
        if isinstance(body, dict):
            body_str = json.dumps(body, indent=2)[:2000]
        else:
            body_str = str(body)[:2000]
        output += body_str
        if len(str(body)) > 2000:
            output += "\n... (truncated)"

    if result.get("assertions"):
        output += "\n\n=== Assertions ===\n"
        for assertion in result["assertions"]:
            status = "✅" if assertion["passed"] else "❌"
            if assertion["type"] == "status_code":
                output += f"{status} Status Code: expected {assertion['expected']}, got {assertion['actual']}\n"
            elif assertion["type"] == "json_field":
                output += f"{status} Field '{assertion['field']}': expected {assertion['expected']}, got {assertion['actual']}\n"

        if result.get("all_assertions_passed"):
            output += "\n✅ All assertions passed!"
        else:
            output += "\n❌ Some assertions failed!"

    is_error = "error" in result or not result.get("all_assertions_passed", True)

    return {
        "content": [{"type": "text", "text": output}],
        "is_error": is_error
    }


@tool(
    "api_test_suite",
    "Run multiple API tests in sequence",
    {
        "base_url": str,
        "tests": list,
        "headers": dict,
        "stop_on_failure": bool
    }
)
async def api_test_suite(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a suite of API tests.

    Args:
        base_url: Base URL for all tests (e.g., "http://localhost:3000")
        tests: List of test definitions:
            - {"name": "Test Name", "endpoint": "/api/users", "method": "GET", "expected_status": 200}
            - {"name": "Create User", "endpoint": "/api/users", "method": "POST", "body": {...}}
        headers: Common headers for all requests (optional)
        stop_on_failure: Stop suite on first failure (default: False)

    Returns:
        Suite results with pass/fail summary
    """
    base_url = args.get("base_url", "").rstrip("/")
    tests = args.get("tests", [])
    common_headers = args.get("headers", {})
    stop_on_failure = args.get("stop_on_failure", False)

    if not base_url:
        return {
            "content": [{"type": "text", "text": "Error: base_url is required"}],
            "is_error": True
        }

    if not tests:
        return {
            "content": [{"type": "text", "text": "Error: No tests provided"}],
            "is_error": True
        }

    results = {
        "base_url": base_url,
        "total_tests": len(tests),
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "test_results": []
    }

    stopped = False

    for i, test in enumerate(tests):
        if stopped:
            results["test_results"].append({
                "name": test.get("name", f"Test {i+1}"),
                "status": "skipped",
                "reason": "Suite stopped due to previous failure"
            })
            results["skipped"] += 1
            continue

        test_name = test.get("name", f"Test {i+1}")
        endpoint = test.get("endpoint", "/")
        full_url = base_url + endpoint

        # Merge headers
        headers = {**common_headers, **test.get("headers", {})}

        # Run test
        test_result = await api_test({
            "url": full_url,
            "method": test.get("method", "GET"),
            "headers": headers,
            "body": test.get("body"),
            "params": test.get("params"),
            "timeout": test.get("timeout", 30),
            "expected_status": test.get("expected_status"),
            "expected_json": test.get("expected_json")
        })

        is_error = test_result.get("is_error", False)

        results["test_results"].append({
            "name": test_name,
            "endpoint": endpoint,
            "method": test.get("method", "GET"),
            "status": "failed" if is_error else "passed",
            "output": test_result["content"][0]["text"][:500]
        })

        if is_error:
            results["failed"] += 1
            if stop_on_failure:
                stopped = True
        else:
            results["passed"] += 1

    # Format output
    output = "=== API Test Suite Results ===\n\n"
    output += f"Base URL: {base_url}\n"
    output += f"Total Tests: {results['total_tests']}\n"
    output += f"Passed: {results['passed']} ✅\n"
    output += f"Failed: {results['failed']} ❌\n"
    output += f"Skipped: {results['skipped']} ⏭️\n\n"

    output += "=== Test Details ===\n"
    for test_result in results["test_results"]:
        status_icon = {
            "passed": "✅",
            "failed": "❌",
            "skipped": "⏭️"
        }.get(test_result["status"], "?")

        output += f"\n{status_icon} {test_result['name']}\n"
        output += f"   {test_result.get('method', 'GET')} {test_result.get('endpoint', '/')}\n"
        if test_result["status"] == "failed":
            output += f"   Error: {test_result.get('output', '')[:200]}...\n"

    # Summary
    if results["failed"] == 0:
        output += f"\n\n🎉 All {results['passed']} tests passed!"
    else:
        output += f"\n\n⚠️ {results['failed']} of {results['total_tests']} tests failed"

    return {
        "content": [{"type": "text", "text": output}],
        "is_error": results["failed"] > 0
    }


@tool(
    "health_check",
    "Check health of multiple service endpoints",
    {
        "endpoints": list,
        "timeout": int
    }
)
async def health_check(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check health of multiple service endpoints.

    Args:
        endpoints: List of URLs to check (or objects with url and name)
        timeout: Request timeout in seconds (default: 5)

    Returns:
        Health status of all endpoints
    """
    endpoints = args.get("endpoints", [])
    timeout = args.get("timeout", 5)

    if not endpoints:
        return {
            "content": [{"type": "text", "text": "Error: No endpoints provided"}],
            "is_error": True
        }

    results = []

    for endpoint in endpoints:
        if isinstance(endpoint, str):
            url = endpoint
            name = endpoint
        else:
            url = endpoint.get("url", "")
            name = endpoint.get("name", url)

        if not url:
            continue

        result = await api_test({
            "url": url,
            "method": "GET",
            "timeout": timeout
        })

        is_healthy = not result.get("is_error", False)
        output_text = result["content"][0]["text"]

        # Extract status code from output
        status_code = None
        for line in output_text.split("\n"):
            if "Status Code:" in line:
                try:
                    status_code = int(line.split(":")[1].strip())
                except:
                    pass

        results.append({
            "name": name,
            "url": url,
            "healthy": is_healthy and (status_code is None or status_code < 400),
            "status_code": status_code
        })

    # Format output
    output = "=== Health Check Results ===\n\n"

    healthy_count = sum(1 for r in results if r["healthy"])
    output += f"Healthy: {healthy_count}/{len(results)}\n\n"

    for result in results:
        status = "✅" if result["healthy"] else "❌"
        output += f"{status} {result['name']}\n"
        output += f"   URL: {result['url']}\n"
        if result["status_code"]:
            output += f"   Status: {result['status_code']}\n"
        output += "\n"

    all_healthy = all(r["healthy"] for r in results)

    if all_healthy:
        output += "🎉 All services are healthy!"
    else:
        unhealthy = [r["name"] for r in results if not r["healthy"]]
        output += f"⚠️ Unhealthy services: {', '.join(unhealthy)}"

    return {
        "content": [{"type": "text", "text": output}],
        "is_error": not all_healthy
    }
