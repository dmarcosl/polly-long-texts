from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import mimetypes

'''
   FUNCTIONS
'''

# Read the file and return the lines
def read_file(file):
    lines = list()

    with open(file, 'r') as file_reading:
        for line_reading in file_reading.readlines():
            # Check if the line is empty
            if line_reading.replace(' ', '') == '\n':
                continue
            # Split large lines
            if len(line_reading) > 1500:
                for phrase in line_reading.split('.'):
                    lines.append(phrase)
            else:
                lines.append(line_reading)

    return lines


# Combine the lines in texts of length between 1000 and 1500 characters
def append_lines(lines):
    tmp_str = ''
    texts = list()

    for line in lines:
        line_length = int(len(tmp_str)) + int(len(line))

        if line_length < 1000:
            tmp_str += line
        elif 1000 <= line_length <= 1500:
            tmp_str += line
            texts.append(tmp_str)
            tmp_str = ''
        elif line_length > 1500:
            texts.append(tmp_str)
            tmp_str = line

    if tmp_str != '':
        texts.append (tmp_str)

    return texts


# Makes a call to Polly with the text and voice selected and returns the audio file
def call_polly(text, voice):
    try:
        # Create a session
        session = Session(profile_name="default")
        # Initialize Polly
        polly = session.client("polly")
        # Request speech synthesis
        response = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=voice)
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)

    # Access the audio stream from the response
    if "AudioStream" in response:
        with closing(response["AudioStream"]) as stream:
            return stream.read()

    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
        sys.exit(-1)

'''
   MAIN PROGRAM
'''

folder = './assets/'
output_folder = './outputs/'
voice = 'Emma'

if not (os.path.isdir(folder)):
    raise ValueError('The folder doesnt exist')

# Get the list of files
fileList = os.listdir(folder)

if not fileList:
    raise ValueError('The folder is empty')

# Discard those that are not text files
for file in fileList:
    if os.path.isdir(folder + file) or mimetypes.guess_type (folder + file)[0] != 'text/plain':
        fileList.remove(file)

if not fileList:
    raise ValueError('The folder doesnt contain any text file')

for file in fileList:
    # Get a list with all the lines of the file
    lines = read_file(folder + file)

    if not lines:
        raise ValueError('The file doesnt contain any line')

    # Compress the lines in texts of length between 1000 and 1500
    texts = append_lines(lines)

    union_speech = None
    count = 1

    for text in texts:
        # Get the synthesized speech
        speech = call_polly(text, voice)

        # Append the speeches
        if union_speech is None:
            union_speech = speech
        else:
            union_speech += speech

        print('Processing text (' + str(count) + '/' + str(len(texts)) + ')')
        count += 1

    # Export the speech
    audioFinal = open(output_folder + os.path.splitext(file)[0] + '.mp3', 'wb').write(union_speech)
