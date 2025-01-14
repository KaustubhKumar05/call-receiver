## About

This webhook does the following:
- accept metadata and config
- navigte to provided website and login
- accept a phone call
- respond based on the config provided

Sample curl:

```
curl --location 'https://call-receiver.onrender.com/test' \
--header 'Content-Type: application/json' \
--data '{
    "exit_phrases": [
        "bye",
        "have a good day",
        "have a great day",
        "thank you for your time"
    ],
    "trigger_responses": {
        "full date of birth": "Sure it is 5 December 2001",
        "do you have hyper tension": "No I do not have either",
        "or both": "No I do not have either",
        "do you take medication for blood pressure": "No, nothing of that sort"
        "have a great day": "Bye",
        "thank you for your time": "Bye",
    },
    "name": "Alice",
    "dob": "2001-12-05",
    "phone": <twilio phone number>,
    "url": "https://demo-qa.100ms.ai/",
    "org_name": "100ms-in",
    "password": "hmsai"
}'

```

`trigger_responses` keys should be in lower case and can be substrings or complete matches of the transcript twilio generates on hearing the audio. The value will be the response that is spoken out after a brief timeout. 

### Running on local:

The port starts on 5000 by default. To debug playwright navigation, set headless mode to false in app.py L64
```
browser = p.chromium.launch(headless=False)
```

Installation and starting the server:

```
# Create virtual env
python3 -m venv venv
source ./venv/bin/activate

# Install deps
pip install -r requirements.txt

# Start the app
python app.py
```

## Flow:

- `/test`:  sets the metadata in the app config and starts the UI navigation on a separate thread. The UI navigation triggers a call from the target website to the configured phone number
- `/answer`:  accepts the phone call and hands off control to `/process-speech`
- `/process-speech`:  maintains a loop where the bot listens to the caller, responds based on the `trigger_responses` and then starts listening again

## Todo

- Transcript verification
- Queueing?
- Test reports?
- Slack notifs in case of failures?