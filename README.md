<h3 align="center">kyumnii</h3>

![wow](vts-2023-03-26_06h18_36.png)

### Some info about kyumnii.

A Twitch Chat AI that reads twitch chat and creates a text to speech response using Google Cloud API and OpenAI's GPT-3 text completion model.

Kyumnii is coded in Python.

I use TwitchIO, A fully asynchronous Python IRC, API, EventSub and PubSub library for Twitch to check for messages, pull the contents and feeds it to GPT-3 where it responds.

There is a profanity filter that uses the [Jaro-Winkler distance algorithm](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance) thats used to detect whether a given message or response contains profanity. It checks the similarity of the given message or response to a list of profanity words stored.

The bot checks that the message contains English words, is not too long, and then concatenates the most recent messages to generate a prompt. The prompt is used to generate a response using the OpenAI GPT-3 API.

I use Google's Text-to-Speech API to generate an audio file of the response, which is then played using VLC. The bot also sends the response to the Twitch chat and logs it to a file.

This code is a fork of [Kuebiko](https://github.com/adi-panda/Kuebiko).

## Getting Started

To get a local copy up and running follow these simple example steps.

### Prerequisites

- VLC must be in installed on your computer!

In order to install the prerequisites you will need to do:  
* pip
  ```sh
  pip install -r requirements.txt
  ```

### Installation

1. Install VLC 64-bit from [here](https://www.videolan.org/vlc/)
2. Get a OpenAI API Key [here](https://beta.openai.com/account/api-keys)
3. Get a Twitch API Token [here](https://twitchapps.com/tmi)
4. Create a Google Cloud Project with TTS Service enabled and download JSON credentials file.
5. Clone the repo
   ```sh
   git clone https://github.com/idkanymre/kyumnii.git
   ``` 
6. Enter your Twitch Username in `main.py > initial_channels`
   ```python
   super().__init__(token='cred.twi_token', prefix='?', initial_channels=[''])
   ```
7. Add the Google Cloud JSON file into the project folder. 
8. Add the name of the Google Cloud JSON File into `main.py`
   ```python
   os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''
   ```
9. Add the OpenAI API and Twitch OAuth token into `cred.py`
    ```python
    # get your twitch oauth token here: https://twitchapps.com/tmi/
    twi_token="oauth:xxxxxxxxxxxxxxxxxx"

    # get your openai token here: https://beta.openai.com/account/api-keys
    openai_token="sk-xxxxxxxxxxxxxxxxxx"
    ```
10. Download VTube Studio and use VBAudio Cable to route audio coming from the program to Vtube Studio using params. 
11. Add the following [script](https://gist.github.com/kkartaltepe/861b02882056b464bfc3e0b329f2f174) to OBS
12. Create a new text source for captions, and set it to read from a file, select the `output.txt` file in \your documents folder\kyumnii (may need to run the script first in order to see it.)
13. In the script options put the name of your text source.
14. Set the script in transform options to scale to inner bounds, and adjust the size of the captions.
15. In order to change the voice of your AI, you will need to change the following parameters in main.py
    Here is a list of [supported voices](https://cloud.google.com/text-to-speech/docs/voices)
    
  ```python
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name= "en-US-Neural2-H",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
   ```

I made this code public due to discontinuing the "kyumnii" social media and thought to share what I made for others!
If you want to continue kyumnii's social media please message me on [twitter](https://twitter.com/unslyu) here for enquiries.
  
https://twitch.tv/kyumnii
https://youtube.com/@kyumnii

**made with 💖 by unslyu with idkanymore**

