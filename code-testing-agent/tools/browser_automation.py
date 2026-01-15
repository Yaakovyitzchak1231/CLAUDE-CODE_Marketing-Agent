"""
Browser Automation Tool

Provides Playwright-based browser automation for UI testing.
"""
from claude_agent_sdk import tool
from typing import Any, Dict, List, Optional
import asyncio
import json
import base64
from pathlib import Path
import tempfile

# Global browser instance for reuse
_browser = None
_playwright = None


async def get_browser():
    """Get or create browser instance"""
    global _browser, _playwright

    if _browser is None:
        try:
            from playwright.async_api import async_playwright
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
        except ImportError:
            raise ImportError(
                "Playwright is not installed. Install with: pip install playwright && playwright install chromium"
            )

    return _browser


async def cleanup_browser():
    """Close browser and playwright"""
    global _browser, _playwright

    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


@tool(
    "browser_test",
    "Automate browser interactions for UI testing using Playwright",
    {
        "url": str,
        "actions": list,
        "viewport": dict,
        "screenshot": bool,
        "wait_timeout": int
    }
)
async def browser_test(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute browser automation tests.

    Args:
        url: URL to navigate to
        actions: List of actions to perform:
            - {"type": "click", "selector": "button#submit"}
            - {"type": "fill", "selector": "input[name='email']", "value": "test@example.com"}
            - {"type": "select", "selector": "select#country", "value": "US"}
            - {"type": "check", "selector": "input[type='checkbox']"}
            - {"type": "wait", "selector": ".loaded"}
            - {"type": "wait_time", "ms": 1000}
            - {"type": "screenshot", "name": "step1"}
            - {"type": "evaluate", "script": "document.title"}
            - {"type": "press", "key": "Enter"}
            - {"type": "scroll", "direction": "down", "amount": 500}
        viewport: {"width": 1920, "height": 1080} (optional)
        screenshot: Take final screenshot (default: True)
        wait_timeout: Default timeout for waits in ms (default: 5000)

    Returns:
        Test results with action outcomes, screenshots, and any errors
    """
    url = args.get("url", "")
    actions = args.get("actions", [])
    viewport = args.get("viewport", {"width": 1920, "height": 1080})
    take_screenshot = args.get("screenshot", True)
    wait_timeout = args.get("wait_timeout", 5000)

    if not url:
        return {
            "content": [{"type": "text", "text": "Error: URL is required"}],
            "is_error": True
        }

    results = {
        "url": url,
        "viewport": viewport,
        "actions": [],
        "screenshots": [],
        "errors": [],
        "console_logs": [],
        "network_errors": []
    }

    try:
        browser = await get_browser()
        context = await browser.new_context(
            viewport=viewport,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # Capture console logs
        page.on("console", lambda msg: results["console_logs"].append({
            "type": msg.type,
            "text": msg.text
        }))

        # Capture network errors
        page.on("requestfailed", lambda req: results["network_errors"].append({
            "url": req.url,
            "failure": req.failure
        }))

        # Navigate to URL
        try:
            response = await page.goto(url, timeout=wait_timeout * 2)
            results["actions"].append({
                "action": "navigate",
                "url": url,
                "status": response.status if response else "unknown",
                "success": True
            })
        except Exception as e:
            results["errors"].append(f"Navigation failed: {e}")
            results["actions"].append({
                "action": "navigate",
                "url": url,
                "success": False,
                "error": str(e)
            })

        # Execute actions
        for i, action in enumerate(actions):
            action_type = action.get("type", "")
            action_result = {"action": action_type, "index": i}

            try:
                if action_type == "click":
                    selector = action.get("selector", "")
                    await page.click(selector, timeout=wait_timeout)
                    action_result["selector"] = selector
                    action_result["success"] = True

                elif action_type == "fill":
                    selector = action.get("selector", "")
                    value = action.get("value", "")
                    await page.fill(selector, value, timeout=wait_timeout)
                    action_result["selector"] = selector
                    action_result["success"] = True

                elif action_type == "select":
                    selector = action.get("selector", "")
                    value = action.get("value", "")
                    await page.select_option(selector, value, timeout=wait_timeout)
                    action_result["selector"] = selector
                    action_result["success"] = True

                elif action_type == "check":
                    selector = action.get("selector", "")
                    await page.check(selector, timeout=wait_timeout)
                    action_result["selector"] = selector
                    action_result["success"] = True

                elif action_type == "wait":
                    selector = action.get("selector", "")
                    await page.wait_for_selector(selector, timeout=wait_timeout)
                    action_result["selector"] = selector
                    action_result["success"] = True

                elif action_type == "wait_time":
                    ms = action.get("ms", 1000)
                    await asyncio.sleep(ms / 1000)
                    action_result["ms"] = ms
                    action_result["success"] = True

                elif action_type == "screenshot":
                    name = action.get("name", f"screenshot_{i}")
                    screenshot_bytes = await page.screenshot()
                    results["screenshots"].append({
                        "name": name,
                        "data": base64.b64encode(screenshot_bytes).decode()[:100] + "...",
                        "size": len(screenshot_bytes)
                    })
                    action_result["name"] = name
                    action_result["success"] = True

                elif action_type == "evaluate":
                    script = action.get("script", "")
                    result = await page.evaluate(script)
                    action_result["script"] = script[:100]
                    action_result["result"] = str(result)[:500]
                    action_result["success"] = True

                elif action_type == "press":
                    key = action.get("key", "Enter")
                    await page.keyboard.press(key)
                    action_result["key"] = key
                    action_result["success"] = True

                elif action_type == "scroll":
                    direction = action.get("direction", "down")
                    amount = action.get("amount", 500)
                    if direction == "down":
                        await page.evaluate(f"window.scrollBy(0, {amount})")
                    elif direction == "up":
                        await page.evaluate(f"window.scrollBy(0, -{amount})")
                    action_result["direction"] = direction
                    action_result["amount"] = amount
                    action_result["success"] = True

                elif action_type == "get_text":
                    selector = action.get("selector", "")
                    text = await page.text_content(selector)
                    action_result["selector"] = selector
                    action_result["text"] = text[:500] if text else None
                    action_result["success"] = True

                elif action_type == "assert_visible":
                    selector = action.get("selector", "")
                    is_visible = await page.is_visible(selector)
                    action_result["selector"] = selector
                    action_result["visible"] = is_visible
                    action_result["success"] = is_visible

                elif action_type == "assert_text":
                    selector = action.get("selector", "")
                    expected = action.get("expected", "")
                    actual = await page.text_content(selector)
                    action_result["selector"] = selector
                    action_result["expected"] = expected
                    action_result["actual"] = actual[:200] if actual else None
                    action_result["success"] = expected in (actual or "")

                else:
                    action_result["error"] = f"Unknown action type: {action_type}"
                    action_result["success"] = False

            except Exception as e:
                action_result["success"] = False
                action_result["error"] = str(e)
                results["errors"].append(f"Action {i} ({action_type}): {e}")

            results["actions"].append(action_result)

        # Take final screenshot
        if take_screenshot:
            try:
                screenshot_bytes = await page.screenshot(full_page=True)
                results["screenshots"].append({
                    "name": "final",
                    "data": base64.b64encode(screenshot_bytes).decode()[:100] + "...",
                    "size": len(screenshot_bytes)
                })
            except:
                pass

        # Get page info
        results["page_title"] = await page.title()
        results["page_url"] = page.url

        await context.close()

    except ImportError as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Playwright not installed: {e}\n"
                       f"Install with: pip install playwright && playwright install chromium"
            }],
            "is_error": True
        }
    except Exception as e:
        results["errors"].append(f"Browser error: {e}")

    # Format output
    output = "=== Browser Test Results ===\n\n"
    output += f"URL: {results.get('url')}\n"
    output += f"Final URL: {results.get('page_url', 'N/A')}\n"
    output += f"Page Title: {results.get('page_title', 'N/A')}\n"
    output += f"Viewport: {results.get('viewport')}\n\n"

    output += "=== Actions ===\n"
    for action in results["actions"]:
        status = "✅" if action.get("success") else "❌"
        output += f"{status} {action.get('action')}"
        if action.get("selector"):
            output += f" ({action['selector'][:50]})"
        if action.get("error"):
            output += f" - Error: {action['error'][:100]}"
        if action.get("result"):
            output += f" - Result: {action['result'][:100]}"
        output += "\n"

    if results["errors"]:
        output += f"\n=== Errors ({len(results['errors'])}) ===\n"
        for error in results["errors"][:5]:
            output += f"- {error}\n"

    if results["console_logs"]:
        output += f"\n=== Console Logs ({len(results['console_logs'])}) ===\n"
        for log in results["console_logs"][:10]:
            output += f"[{log['type']}] {log['text'][:100]}\n"

    if results["network_errors"]:
        output += f"\n=== Network Errors ({len(results['network_errors'])}) ===\n"
        for err in results["network_errors"][:5]:
            output += f"- {err['url'][:50]}: {err['failure']}\n"

    output += f"\n=== Screenshots ({len(results['screenshots'])}) ===\n"
    for ss in results["screenshots"]:
        output += f"- {ss['name']}: {ss['size']} bytes\n"

    has_errors = bool(results["errors"]) or any(
        not a.get("success") for a in results["actions"]
    )

    return {
        "content": [{"type": "text", "text": output}],
        "is_error": has_errors
    }


@tool(
    "browser_screenshot",
    "Take a screenshot of a web page",
    {
        "url": str,
        "viewport": dict,
        "full_page": bool
    }
)
async def browser_screenshot(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take a screenshot of a web page.

    Args:
        url: URL to screenshot
        viewport: {"width": 1920, "height": 1080} (optional)
        full_page: Capture full scrollable page (default: False)

    Returns:
        Screenshot info and base64 preview
    """
    url = args.get("url", "")
    viewport = args.get("viewport", {"width": 1920, "height": 1080})
    full_page = args.get("full_page", False)

    if not url:
        return {
            "content": [{"type": "text", "text": "Error: URL is required"}],
            "is_error": True
        }

    try:
        browser = await get_browser()
        context = await browser.new_context(viewport=viewport)
        page = await context.new_page()

        await page.goto(url, timeout=30000)
        await asyncio.sleep(1)  # Wait for page to settle

        screenshot_bytes = await page.screenshot(full_page=full_page)
        title = await page.title()

        # Save to temp file
        temp_path = Path(tempfile.gettempdir()) / f"screenshot_{hash(url) % 10000}.png"
        with open(temp_path, 'wb') as f:
            f.write(screenshot_bytes)

        await context.close()

        output = f"=== Screenshot Captured ===\n"
        output += f"URL: {url}\n"
        output += f"Title: {title}\n"
        output += f"Viewport: {viewport['width']}x{viewport['height']}\n"
        output += f"Full Page: {full_page}\n"
        output += f"Size: {len(screenshot_bytes)} bytes\n"
        output += f"Saved to: {temp_path}\n"

        return {
            "content": [{"type": "text", "text": output}],
            "is_error": False
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Screenshot failed: {e}"
            }],
            "is_error": True
        }
