# ChopItUp Media Library Tool

ChopItUp is a Python-based command-line toolkit designed to create a video based on a user's input sentence using video segments extracted from a media library.
It also provides word usage statistics, library management, and suggests alternative words when necessary.

Written by Hippy in 2023, it's meant for trolling cookers, however it can possibly be useful for other purposes.

## How it works

Firstly ```video_to_transcript.py``` will run speech recognition on the given input video file, and output a ".rec" file.

We can then use ```chopitup.py``` to build a library from one or more ".rec" files, using the ```--generate``` option.

Once we have a library, we can extract video segments from the source videos, based on an input string.

We use the ```--check "I am a dickhead"``` to see if we have those words...

```
Using word library: C:\Users\Hippy\AppData\Local\ChopItUp\ChopItUp\word_library.json
Checking string: I am a dickhead
Alternative used for 'dickhead': 'ducked'

We don't have all those words, how about this: i am a ducked
```

So we'll just have to use that...

using the ```--create "i am a ducked"```, we end up with a choppy video of the input persons saying the given sentence.

Optionally the tool can be used to chop together every occurance of a specified word into a video, by using the ```--words``` option.

## Dependencies

- Python 3.x
- ffmpeg, ffprobe (video processing tool)
- Vosk (speech recognition toolkit)
- MoviePy (video editing toolkit)
- appdirs 
- argparse

## Installation

1. Install Python 3.x on your system.
2. Install the required python packages using the following command:

    `pip install moviepy appdirs argparse vosk requests tqdm`

3. Install ffmpeg on your system, in a accesable system path or in the same directory as the python files.

    This will vary if you are linux / windows / mac - so DuckDuckGo for "ffmpeg install instructions".


## Usage


This script extracts audio from a given video file and generates a time-stamped transcription using the Vosk speech recognition library.
The first time it is run, it will download the specific speech recognition model it requires, and may take some time.

To transcribe a single video file, run:

    python video_to_transcript.py <path_to_video_file>


Replace <path_to_video_file> with the path to the video file you want to transcribe.

To transcribe all video files in a directory, run:

    python video_to_transcript.py -all <directory_path>

Replace <directory_path> with the path to the directory containing the video files you want to transcribe.

The script will generate a time-stamped transcription in a text file with the same name and in the same folder as the input video with a ".rec" extension. 


Finally, we can start using the information from the recognition phase to get creative.
To use ChopItUp, run the script with the desired options as specified below:

    python chopitup.py --help

### Available Options

- `--generate`: Generate/update word library from .rec transcript files.
- `--media RECPATH`: Specify the path to .rec files (for --generate, default: current directory).
- `--label LABEL`: Specify which library to work with (default: 'word').
- `--create SENTENCE`: Create a video using the given input sentence.
- `--words WORD`: Create a video of all instances of a given word.
- `--wordslist "the, words, I, want"`: Create a video of these words, using timestamps for ordering.
- `--output FILENAME`: Specify the output video filename.
- `--verbose`: Enable verbose output.
- `--check_string SENTENCE`: Check the given string for available words and suggest alternatives.
- `--stats [WORD]`: Display statistics, optionally for a specific word.

### Libraries & Labels

Let's say you have videos of Tony, and videos of Tami.   If you do not specify which is which with a LABEL they will get mixed up together.

The ```--label LABEL``` provides a mechanism for maintaining different libraries of words from different sources.

If you do not specify a label, the default 'word' library will be used.  


## Examples

0. Transcribe some cooker Tony videos

    ```python video_to_transcript.py c:\cookers\tony\instabro.mp4``` 
    ```python video_to_transcript.py c:\cookers\tony\long_rant.mp4``` 

    This should produce ```c:\cookers\tony\instabro.rec``` and ```c:\cookers\tony\long_rant.rec``` files.

1. Generate/update word library called "tony" from .rec transcript files:

    ```python chopitup.py --generate --media c:\cookers\tony --label tony```

    This fill find any ".rec" files in c:\cookers\tony and process them into the "tony" library
    (note: the ".rec" files are now no longer required"

2. Create a video using the given input sentence:

    ```python chopitup.py --label tony --create "listen to me"```

3. Create a video of all instances of a given word:

    ```python chopitup.py --label tony --words "bong"```

4. Check the given string for available words and suggest alternatives:

    ```python chopitup.py --label tony --check_string "Is this working Linda?"```

5. Display statistics for the entire library:

    ```python chopitup.py --label tony --stats```

6. Display statistics for a specific word:

    ```python chopitup.py --label tony --stats "example"```


## License

This project is released under the WTFPL.  
Refer to the imported python modules for their licences.

