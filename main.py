from twitchio.ext import commands
from twitchio.ext import routines
from chat import *
from google.cloud import texttospeech_v1beta1 as texttospeech
import vlc
import ctypes
import os 
import time
import nltk
import phrases
import logging
import datetime
import cred
import argparse
import secrets
import jellyfish
import sys

class Kyumnii(commands.Bot):
    
    conversation = list()

    version = '0.4.3'

    # Initialize the bot
    def __init__(self):

        # download the words corpus
        nltk.download('words', quiet=True)

        # Get the current date
        now = datetime.datetime.now()
        date_string = now.strftime("%Y-%m-%d %H-%M-%S")
        
        # Parse the command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--debug', action='store_true', help='enable debug mode')
        args = parser.parse_args()

        # Set the logging level and title
        if args.debug:
            logging_level = logging.DEBUG
            Kyumnii.set_console_title(f"kyumnii version {Kyumnii.version} - DEBUG MODE")
        else:
            Kyumnii.set_console_title(f"kyumnii version {Kyumnii.version}")
            logging_level = logging.INFO

        # Set the log file name
        logging_file = f'kyumnii log {date_string}{" - DEBUG MODE" if args.debug else ""}.txt'

        # create path to log file
        logging_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'kyumnii', 'logs')
        os.makedirs(logging_dir, exist_ok=True)

        # configure logging to write to file
        logging.basicConfig(filename=os.path.join(logging_dir, logging_file), level=logging_level, format='%(asctime)s %(levelname)s: %(message)s', 
                            datefmt='%Y-%m-%d %H:%M:%S')
        
        # configure logging to write to console
        if args.debug:
            Kyumnii.log('Debug mode enabled. Make sure to disable it before going live. To disable debug mode, run the program without the --debug flag.')
        else:
            logging.info('Debug mode disabled. To enable debug mode, run the program with the --debug flag.')
        
        audio_file = os.path.expanduser('~/Documents/kyumnii/output.mp3')
        text_file = os.path.expanduser('~/Documents/kyumnii/output.txt')

        # Check if the text file exists, and create it if it doesn't
        if not os.path.exists(text_file):
            if args.debug:
                Kyumnii.log('Text file not found. Maybe it was deleted? or maybe this is the first time you\'ve run the program? Make sure it is found in OBS.', level="warning")
                Kyumnii.log('Creating text file.')
            open(text_file, 'w').close()

        # Check if the audio file exists, and delete it if it does
        if os.path.exists(audio_file):
            logging.warning('Audio file exists. Deleting it.')
            os.remove(audio_file)
            Kyumnii.log('Audio file deleted.')

        Kyumnii.clear(debuglevel=True)

        Kyumnii.log('Connecting...')

        # Initialize kyumnii with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        #                                                  change this to your channel name
        super().__init__(token=cred.twi_token, prefix='?', initial_channels=['kyumnii'])

    # This is called when the kyumnii is ready to start accepting messages.
    async def event_ready(self):      
        parser = argparse.ArgumentParser()
        parser.add_argument('--debug', action='store_true', help='enable debug mode')
        args = parser.parse_args()

        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        if(args.debug):
            Kyumnii.log(f"kyumnii version {Kyumnii.version} - DEBUG MODE")
        else:
            Kyumnii.clear(debuglevel=False)
            Kyumnii.log(f"kyumnii version {Kyumnii.version}")


        Kyumnii.log(f'Logged in as "{self.nick}"')
        Kyumnii.log(f'{len(phrases.phrases)} questions loaded.')

    # This is called every 23 seconds.
    @routines.routine(seconds=23, wait_first=0.1)
    async def ai_phrases():

        # Choose a random message from the list of phrases
        message = secrets.choice(phrases.phrases)
        
        # Check if the message contains english words
        if not any(word in message for word in nltk.corpus.words.words()):
            Kyumnii.log(f'Message does not contain english words: {message}', level="warning")
            return
        
        # Check if the message contains any banned words
        similar, similarity_percentage, max_similarity_word = Kyumnii.is_similar_to_bannedword(message, phrases.bannedword_list)
        if similar:
            Kyumnii.log(f"Banned word detected. message: {message}, similarity: {similarity_percentage:.2f}, simliar to: {max_similarity_word}", level="warning")
            return
        
        # Check if the message is too long
        if len(message) > 140:
            Kyumnii.log(f'Message too long. length: {len(message)}', level="warning")
            return

        Kyumnii.log('------------------------------------------------------')
        Kyumnii.log(f"Question: {message}")

        Kyumnii.conversation.append(f'Chatter: {message}')

        # keep only the most recent messages in the conversation history
        num_messages_to_keep = 1
        if len(Kyumnii.conversation) > num_messages_to_keep:
            logging.info(f"{len(Kyumnii.conversation)}")
            Kyumnii.conversation = Kyumnii.conversation[-num_messages_to_keep:]

        # concatenate the most recent messages into a single block
        text_block = '\n'.join(Kyumnii.conversation)

        # generate the prompt using the concatenated message block
        prompt = open_file('prompt_chat.txt').replace('<<BLOCK>>', text_block)

        prompt = prompt + '\nKyumnii:'
        response = gpt3_completion(prompt)
        Kyumnii.log('Kyumnii: ' + response)
        if(Kyumnii.conversation.count('Kyumnii: ' + response) == 0):
            Kyumnii.conversation.append(f'Kyumnii: {response}')

        # Check if the response contains any banned words
        similar, similarity_percentage, max_similarity_word = Kyumnii.is_similar_to_bannedword(response, phrases.bannedword_list)
        if similar:
            Kyumnii.log(f"Banned word detected. message: {response}, similarity: {similarity_percentage:.2f}, simliar to: {max_similarity_word}", level="warning")
            return
        
        # Check if the response is too long
        if len(response) > 4500:
            Kyumnii.log(f'Response too long. length: {len(response)}', level="warning")
            return
        
        client = texttospeech.TextToSpeechClient()

        response = response
        ssml_text = '<speak>'
        response_counter = 0
        mark_array = []
        for s in response.split(' '):
            ssml_text += f'<mark name="{response_counter}"/>{s}'
            mark_array.append(s)
            response_counter += 1
        ssml_text += '</speak>'

        input_text = texttospeech.SynthesisInput(ssml = ssml_text)

        # Note: the voice can also be specified by name.
        # Names of voices can be retrieved with client.list_voices().
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name= "en-US-Neural2-H",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )

        audio_config = texttospeech.AudioConfig(    
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )
        

        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config, "enable_time_pointing": ["SSML_MARK"]}
        )

        audio_file = os.path.expanduser('~/Documents/kyumnii/output.mp3')
        text_file = os.path.expanduser('~/Documents/kyumnii/output.txt')

        # The response's audio_content is binary.
        with open(audio_file, "wb") as out:
            out.write(response.audio_content)

        media = vlc.MediaPlayer(audio_file)
        media.play()
        #playsound(audio_file, winsound.SND_ASYNC)

        count = 0
        current = 0
        for i in range(len(response.timepoints)):
            count += 1
            current += 1
            with open(text_file, "a", encoding="utf-8") as out:
                out.write(mark_array[int(response.timepoints[i].mark_name)] + " ")
            if i != len(response.timepoints) - 1:
                total_time = response.timepoints[i + 1].time_seconds
                time.sleep(total_time - response.timepoints[i].time_seconds)
            if current == 25:
                    open(text_file, 'w', encoding="utf-8").close()
                    current = 0
                    count = 0
            elif count % 7 == 0:
                with open(text_file, "a", encoding="utf-8") as out:
                    out.write("\n")
        time.sleep(2)
        open(text_file, 'w').close()

        # Print the contents of our message to console...
        Kyumnii.log('------------------------------------------------------')


        Kyumnii.remove_audio_file(audio_file)

    # This is called whenever a message is sent in chat...
    async def event_message(self, message):

        if message.echo:
            return

        # Ignore messages from nightbot and streamlabs
        if message.author.name == "nightbot" or message.author.name == "streamlabs":
            Kyumnii.log(f'Ignoring message from {message.author.name}: {message.content}')
            return
        
        # Ignore commands (probably a better way to do this, this like spaghetti)
        if message.content.startswith('!'):
            if message.content == "!hug":
                pass
        elif message.content.startswith('!'):
            Kyumnii.log(f'Ignoring command {message.content}')
            return     

        # Check if the message contains english words
        if not any(word in message.content for word in nltk.corpus.words.words()):
            Kyumnii.log(f'Message does not contain english words. {message.author.name}: {message.content}', level="warning")
            return
        
        # Check if the message contains any banned words
        similar, similarity_percentage, max_similarity_word = Kyumnii.is_similar_to_bannedword(message.content, phrases.bannedword_list)
        if similar:
            Kyumnii.log(f"Banned word detected. Twitch username: {message.author.name}, message: {message.content}, similarity: {similarity_percentage:.2f}, similar to: {max_similarity_word}", level="warning")
            return

        # Check if the message is too long
        if len(message.content) > 140:
            Kyumnii.log(f"Message too long. Twitch username: {message.author.name}, message: {message.content}, length: {len(message.content)}", level="warning")
            return
        
        # Log the message the log file
        Kyumnii.log('------------------------------------------------------')
        Kyumnii.log(f"{message.author.name}: {message.content}")

        Kyumnii.conversation.append(f'Chatter: {message.content}')

        # keep only the most recent messages in the conversation history
        num_messages_to_keep = 1
        if len(Kyumnii.conversation) > num_messages_to_keep:
            Kyumnii.conversation = Kyumnii.conversation[-num_messages_to_keep:]

        # concatenate the most recent messages into a single block
        text_block = '\n'.join(Kyumnii.conversation)

        # generate the prompt using the concatenated message block
        prompt = open_file('prompt_chat.txt').replace('<<BLOCK>>', text_block)

        prompt = prompt + '\nKyumnii:'
        response = gpt3_completion(prompt)
        Kyumnii.log('Kyumnii: ' + response)
        if(Kyumnii.conversation.count('Kyumnii: ' + response) == 0):
            Kyumnii.conversation.append(f'Kyumnii: {response}')

        # Check if the response contains any banned words
        similar, similarity_percentage, max_similarity_word = Kyumnii.is_similar_to_bannedword(response, phrases.bannedword_list)
        if similar:
            Kyumnii.log(f"Banned word detected. Twitch username: {message.author.name}, message: {message.content}, response: {response}, similarity: {similarity_percentage:.2f}, similar to: {max_similarity_word}", level="warning")
            return
        
        # Check if the response is too long
        if len(response) > 4500:
            Kyumnii.log(f'Response too long. length: {len(response)}', level="warning")
            return
        
        client = texttospeech.TextToSpeechClient()

        response = message.content + "? " + response
        ssml_text = '<speak>'
        response_counter = 0
        mark_array = []
        for s in response.split(' '):
            ssml_text += f'<mark name="{response_counter}"/>{s}'
            mark_array.append(s)
            response_counter += 1
        ssml_text += '</speak>'

        input_text = texttospeech.SynthesisInput(ssml = ssml_text)

        # Note: the voice can also be specified by name.
        # Names of voices can be retrieved with client.list_voices().
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name= "en-US-Neural2-H",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )

        audio_config = texttospeech.AudioConfig(    
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )
        

        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config, "enable_time_pointing": ["SSML_MARK"]}
        )

        audio_file = os.path.expanduser('~/Documents/kyumnii/output.mp3')
        text_file = os.path.expanduser('~/Documents/kyumnii/output.txt')

        # The response's audio_content is binary.
        with open(audio_file, "wb") as out:
            out.write(response.audio_content)

        media = vlc.MediaPlayer(audio_file)
        media.play()
        #playsound(audio_file, winsound.SND_ASYNC)

        count = 0
        current = 0
        for i in range(len(response.timepoints)):
            count += 1
            current += 1
            with open(text_file, "a", encoding="utf-8") as out:
                out.write(mark_array[int(response.timepoints[i].mark_name)] + " ")
            if i != len(response.timepoints) - 1:
                total_time = response.timepoints[i + 1].time_seconds
                time.sleep(total_time - response.timepoints[i].time_seconds)
            if current == 25:
                    open(text_file, 'w', encoding="utf-8").close()
                    current = 0
                    count = 0
            elif count % 7 == 0:
                with open(text_file, "a", encoding="utf-8") as out:
                    out.write("\n")
        time.sleep(2)
        open(text_file, 'w').close()

        # Print the contents of our message to console...
        Kyumnii.log('------------------------------------------------------')

        Kyumnii.remove_audio_file(audio_file)

        # Since we have commands and are overriding the default `event_message`
        # We must let kyumnii know we want to handle and invoke our commands...
        await self.handle_commands(message)

    # This is a function to remove the audio file after it has been played
    def remove_audio_file(audio_file):
        while True:
            try:
                os.remove(audio_file)
                Kyumnii.log('Audio file deleted.')
                break
            except PermissionError:
                Kyumnii.log('File is being used, waiting for 1 second...', level='warning')
                time.sleep(1)
                os.remove(audio_file)
                Kyumnii.log('Audio file deleted.')
                break
            except FileNotFoundError:
                Kyumnii.log("False positive: 'FileNotFoundError'. kyumnii continued")
                break

    # Returns the similarity between two strings
    def get_similarity(message, word):
        return jellyfish.jaro_winkler(message.lower(), word.lower())

    # Returns the maximum similarity and the word that has the maximum similarity
    def get_max_similarity(message, bannedword_list):
        max_similarity = 0
        max_similarity_word = ''
        for word in bannedword_list:
            similarity = Kyumnii.get_similarity(message, word)
            if similarity > max_similarity:
                max_similarity = similarity
                max_similarity_word = word
        return max_similarity, max_similarity_word

    # Returns whether the message is similar to a bannedword word
    def is_similar_to_bannedword(message, bannedword_list, similarity_threshold=0.85):
        max_similarity, max_similarity_word = Kyumnii.get_max_similarity(message, bannedword_list)
        return max_similarity >= similarity_threshold, max_similarity * 100, max_similarity_word

    # Sets the console title 
    def set_console_title(title):
        if os.name == 'nt':  # for Windows
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        else:  # for macOS
            sys.stdout.write(f"\x1b]2;{title}\x07")

    # Clears the console
    def clear(debuglevel=False):
        if debuglevel:
            parser = argparse.ArgumentParser()
            parser.add_argument('--debug', action='store_true', help='enable debug mode')
            args = parser.parse_args()

            os.system('cls' if os.name == 'nt' else 'clear') if not args.debug else None
        else:
            os.system('cls' if os.name == 'nt' else 'clear')

    # Logs a message to the console and to a log file
    def log(message, level="info"):
        print(message)
        if level == "info":
            logging.info(message)
        elif level == "warning":
            logging.warning(message)
        elif level == "error":
            logging.error(message)
        elif level == "critical":
            logging.critical(message)
        else:
            raise ValueError(f"Invalid logging level: {level}")

    # Restart command for the bot (not working yet, issue: unknown)
    @commands.command()
    async def restart(self, ctx: commands.Context):
        await ctx.send(f'Restarting {self.user.name}...')
        if os.name == 'nt':  # for Windows
            python = sys.executable
            os.close(sys.stdin.fileno())
            os.close(sys.stdout.fileno())
            os.close(sys.stderr.fileno())
            os.execl(python, python, *sys.argv)
        else:  # for macOS
            python = sys.executable
            os.close(sys.stdin.fileno())
            os.close(sys.stdout.fileno())
            os.close(sys.stderr.fileno())
            os.execl(python, python, *sys.argv)

Kyumnii.ai_phrases.start()

# get your own credentials from https://cloud.google.com/text-to-speech/docs/quickstart-client-libraries
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'yourgooglekeys.json'
kyumnii = Kyumnii()
kyumnii.run()

# kyumnii.run() is blocking and will stop execution of any below code here until stopped or closed.