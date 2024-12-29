from flask import Flask
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route("/answer", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    response.say('Hello world')
    return str(response)

if __name__ == "__main__":
    app.run(debug=True)