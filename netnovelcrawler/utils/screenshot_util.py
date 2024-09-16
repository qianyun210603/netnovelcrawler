import base64
import json

from selenium import webdriver

FULL_SCREEN_CAPABILITIES = {
    "browserName": "chrome",
    "chromeOptions": {"useAutomationExtension": False, "args": ["--disable-infobars"]},
}


def chrome_takeFullScreenshot(driver: webdriver.Chrome, position: dict):
    def send(cmd, params):
        resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
        url = driver.command_executor._url + resource
        body = json.dumps({"cmd": cmd, "params": params})
        response = driver.command_executor._request("POST", url, body)
        return response.get("value")

    def evaluate(script):
        response = send("Runtime.evaluate", {"returnByValue": True, "expression": script})
        return response["result"]["value"]

    metrics = evaluate(
        "({width: Math.max(window.innerWidth, document.body.scrollWidth, document.documentElement.scrollWidth)|0,"
        + "height: Math.max(innerHeight, document.body.scrollHeight, document.documentElement.scrollHeight)|0,"
        + "deviceScaleFactor: window.devicePixelRatio || 1,"
        + "mobile: typeof window.orientation !== 'undefined'})"
    )

    def getScreen(_metrics, _position):
        send("Emulation.setDeviceMetricsOverride", _metrics)
        _sshot = send("Page.captureScreenshot", {"format": "png", "fromSurface": True, "clip": _position})
        send("Emulation.clearDeviceMetricsOverride", {})
        return _sshot

    for i in range(10):
        sshot = getScreen(metrics, position)
        if "data" in sshot:
            break

    return base64.b64decode(sshot["data"])
