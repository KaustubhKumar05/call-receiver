import os
import logging
from flask import Flask, Response, request
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

repeat_count = 0
context = {}

exit_phrases = ["bye", "have a good day", "have a great day", "thank you for your time"]
# This can be configured as a script, should use values from the context
trigger_responses = {
    "full date of birth": "Sure it is 5 December 2001",
    "do you have hyper tension": "No I do not have either",
    "or both": "No I do not have either",
    "bye": "Bye",
    "have a good day": "Bye",
    "have a great day": "Bye",
    "thank you for your time": "Bye",
}

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
    global repeat_count

    speech_result = request.form.get("SpeechResult", "").lower()
    logger.info(f"debug> Received speech input: {speech_result}")

    response = VoiceResponse()

    if repeat_count > 3:
        logger.info("debug> Repeat count limit reached")
        return end_call(response)

    for trigger, reply in trigger_responses.items():
        if trigger in speech_result:
            logger.info(f"debug> Matched trigger phrase: '{trigger}' with response: '{reply}'")
            response.say(reply)
            if trigger in exit_phrases:
                logger.info("debug> Exit phrase detected")
                return end_call(response)
            break
    else:
        logger.info("debug> No matching trigger phrase. Asking the bot to repeat.")
        if repeat_count < 2:
            response.say("I am not sure")
        logger.info("debug> incrementing repeat count to", repeat_count + 1)
        repeat_count += 1

    logger.info("debug> Gathering speech input")
    response.gather(input="speech", action="/process-speech", timeout=3)
    
    return Response(str(response), mimetype="application/xml")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"debug> Starting server on port {port}")
    app.run(debug=True, host="0.0.0.0", port=port)
