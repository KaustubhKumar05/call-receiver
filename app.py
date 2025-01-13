import os
import logging
from flask import Flask, Response, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
import threading
import time
from playwright.sync_api import sync_playwright

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

repeat_count = 0
context = {
    "exit_phrases": [
        "bye",
        "have a good day",
        "have a great day",
        "thank you for your time",
    ],
    "trigger_responses": {
        "full date of birth": "Sure it is 5 December 2001",
        "do you have hyper tension": "No I do not have either",
        "or both": "No I do not have either",
        "bye": "Bye",
        "have a good day": "Bye",
        "have a great day": "Bye",
        "thank you for your time": "Bye",
        "do you take medication for blood pressure": "No, nothing of that sort",
    },
    "name":"Alice",
    "dob": "2001-12-05",
    "phone": "+14013005666",
    "url": "https://demo-qa.100ms.ai/",
}

# This should also
#   accept the endpoint
#   manage queueing
#   generate a report on completion
#   send a slack message to internal channels?
@app.route("/test", methods=["POST"])
def set_context():
    tester_status = app.config.get("status", "available")
    if tester_status != "available":
        return jsonify({"message": "Cannot update context while tester is busy"}), 400
    
    data = request.get_json()
    for key, value in context.items():
        app.config[key] = data.get(key, value)
    app.config["status"] = "busy"

    thread = threading.Thread(target=make_call)
    thread.start()

    return jsonify({"message": "Context updated successfully"}), 200

def make_call():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        target = app.config["url"]
        logger.info(f"debug> Navigating to {target}")
        page.goto(target)
        time.sleep(2)

        try:
            # Check if elements for login are present
            if (
                page.locator("#org-name").is_visible()
                and page.locator("#password").is_visible()
            ):
                logger.info("debug> Filling login form")
                page.fill("#org-name", "100ms-in")
                page.fill("#password", "hmsai")
                page.click("#login button[type='submit']")
            time.sleep(2)
            submit_call_form(page)

        except Exception as e:
            logger.info(f"debug> Error interacting with the page: {e}")

        logger.info("debug> Closing the browser in 10s")
        time.sleep(10)
        # Close browser
        browser.close()


def submit_call_form(page):
    if page.locator("#name").is_visible() and page.locator("#dob").is_visible():
        logger.info("debug> Filling make call form")

        for key in ["name", "dob", "phone"]:
            page.fill("#"+key, app.config.get(key, context[key]))

        page.click("button:has(+ .message)")
        logger.info("debug> Clicked make_call")


@app.route("/answer", methods=["POST"])
def voice():
    logger.info("debug> Received a call. Sending initial response.")
    response = VoiceResponse()
    gather = response.gather(input="speech", action="/process-speech", timeout=3)
    gather.say("Hi")
    return Response(str(response), mimetype="application/xml")

def end_call(response):
    logger.info("debug> Hanging up")
    response.hangup()
    return Response(str(response), mimetype="application/xml")

@app.route("/process-speech", methods=["POST"])
def process_speech():
    """Process speech input and respond or loop back."""
    global repeat_count, exit_phrases, trigger_responses
    exit_phrases = app.config.get("exit_phrases", exit_phrases)
    trigger_responses = app.config.get("trigger_responses", trigger_responses)

    speech_result = request.form.get("SpeechResult", "").lower()
    logger.info(f"debug> Received speech input: {speech_result}")

    response = VoiceResponse()

    if repeat_count > 3:
        logger.info("debug> Repeat count limit reached")
        return end_call(response)

    for trigger, reply in trigger_responses.items():
        if trigger in speech_result:
            logger.info(
                f"debug> Matched trigger phrase: '{trigger}' with response: '{reply}'"
            )
            response.say(reply)
            if trigger in exit_phrases:
                logger.info("debug> Exit phrase detected")
                return end_call(response)
            break
    else:
        logger.info("debug> No matching trigger phrase. Asking the bot to repeat.")
        if repeat_count < 2:
            response.say("I am not sure")
        logger.info(f"debug> Incrementing repeat count to {repeat_count + 1}")
        repeat_count += 1

    logger.info("debug> Gathering speech input")
    response.gather(input="speech", action="/process-speech", timeout=3)

    return Response(str(response), mimetype="application/xml")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"debug> Starting server on port {port}")
    app.run(debug=True, host="0.0.0.0", port=port)
