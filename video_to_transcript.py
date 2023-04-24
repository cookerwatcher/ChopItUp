# ChopItUp - (c) Hippy, 2023,  WTFPL
# video_to_transcript.py
# take in a video and run speech recognition over it to extract individual words
# results are stored in a ".rec" file alongside the video.

import os
import sys
import json
import appdirs
import zipfile
import requests
import tempfile
import shutil
import glob
from tqdm import tqdm
from vosk import Model, KaldiRecognizer, SetLogLevel
from moviepy.editor import VideoFileClip, AudioFileClip
import subprocess

PROGRESS_PERCENTAGE = 0.85  # space on the terminal to use for status line

def get_terminal_width():
    return shutil.get_terminal_size().columns

def download_and_unzip_model(model_url, model_path, data_dir):
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}. Attempting to download...")

        response = requests.get(model_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        zip_file_path = os.path.join(model_path + ".zip")

        with open(zip_file_path, "wb") as f:
            for chunk in tqdm(response.iter_content(chunk_size=8192), total=total_size // 8192, unit='KB'):
                if chunk:
                    f.write(chunk)

        print(f"Unzipping model at {model_path}...")

        # Create a temporary directory for unzipping
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_file_path, "r") as z:
                z.extractall(temp_dir)
            
            # Move the extracted root directory to the desired model_path
            extracted_model_dir = os.path.join(temp_dir, os.listdir(temp_dir)[0])
            shutil.move(extracted_model_dir, data_dir)

        os.remove(zip_file_path)

    if os.path.exists(model_path):    
        print(f"Using model: {model_path}.")
    else:
        print(f"Vosk model could not be found at {model_path} \nMaybe download or unzip failed, or a permissions or drive space issue?\n")
        sys.exit(1)


# def transcribe_audio(model_path, video_path, quiet=False):
#     model = Model(model_path)
#     rec = KaldiRecognizer(model, 16000)
#     rec.SetWords(True)

#     output_filename = os.path.splitext(video_path)[0] + ".rec"

#     progress = 0

#     terminal_width = get_terminal_width()
#     progress_line_length = int(terminal_width * PROGRESS_PERCENTAGE)

#     with open(output_filename, "w") as f:

#         f.write(f"media={video_path}\n") # add media file name as first line to the transcript

#         # convert video to audio
#         with VideoFileClip(video_path) as video:            
#             audio = video.audio
#             if audio == None:
#                 return
#             audio.write_audiofile("temp_audio.wav", codec="pcm_s16le", fps=16000)
#             total_duration = audio.duration

#         with open("temp_audio.wav", "rb") as stream:
#             while True:
#                 data = stream.read(4000)
#                 if len(data) == 0:
#                     break

#                 progress += len(data)
#                 progress_seconds = progress / 32000

#                 if not quiet:
#                     progress_percentage = 100.0 * progress_seconds / total_duration
#                     sys.stderr.write(f"\rProgress: {progress_percentage:.2f}%")
#                     sys.stderr.flush()

#                 if rec.AcceptWaveform(data):
#                     results = json.loads(rec.Result())
#                     if "result" in results:
#                         for result in results["result"]:
#                             start_time = result["start"]
#                             end_time = result["end"]
#                             word = result["word"]
#                             f.write(f"{word}\t{start_time:.2f}\t{end_time:.2f}\n")

#                 if not quiet:
#                     partial_result = json.loads(rec.PartialResult())
#                     if "partial" in partial_result:
#                         partial = partial_result["partial"]
#                         partial_display = partial[-(progress_line_length - 20):]
#                         if len(partial) > progress_line_length - 20:
#                             partial_display = "..." + partial_display
#                         sys.stderr.write(f" - {partial_display}")
#                         sys.stderr.flush()

#     os.remove("temp_audio.wav")

#     if not quiet:
#         sys.stderr.write("\n")
#         sys.stderr.flush()

#     print(f"Transcription saved to {output_filename}")


def get_media_duration(video_path):
    command = [
        "ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("Error getting media duration:")
        print(result.stderr.decode('utf-8'))
        sys.exit(1)

    return float(result.stdout)




# transcribe audio from a video file
def transcribe_audio(model_path, video_path, quiet=False):
    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)

    output_filename = os.path.splitext(video_path)[0] + ".rec"

    total_duration = get_media_duration(video_path)
    if total_duration == 0:
        print("Error getting input media duration")
        sys.exit(1)

    progress = 0

    terminal_width = get_terminal_width()
    progress_line_length = int(terminal_width * PROGRESS_PERCENTAGE)

    with open(output_filename, "w") as f:

        f.write(f"media={video_path}\n") # add media file name as first line to the transcript

        # convert whatever into audio                
        with subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i",
                               video_path,
                               "-ar", "16000", "-ac", "1", "-f", "s16le", "-"],
                              stdout=subprocess.PIPE).stdout as stream:

            while True:
                data = stream.read(4000)
                if len(data) == 0:
                    break

                progress += len(data)
                progress_seconds = progress / 32000

                if not quiet:
                    progress_percentage = 100.0 * progress_seconds / total_duration
                    sys.stderr.write(f"\rProgress: {progress_percentage:.2f}%")
                    sys.stderr.flush()

                if rec.AcceptWaveform(data):
                    results = json.loads(rec.Result())
                    if "result" in results:
                        for result in results["result"]:
                            start_time = result["start"]
                            end_time = result["end"]
                            word = result["word"]
                            f.write(f"{word}\t{start_time:.2f}\t{end_time:.2f}\n")

                if not quiet:
                    partial_result = json.loads(rec.PartialResult())
                    if "partial" in partial_result:
                        partial = partial_result["partial"]
                        partial_display = partial[-(progress_line_length - 20):]
                        if len(partial) > progress_line_length - 20:
                            partial_display = "..." + partial_display
                        sys.stderr.write(f" - {partial_display}")
                        sys.stderr.flush()

    if not quiet:
        sys.stderr.write("\n")
        sys.stderr.flush()

    print(f"Transcription saved to {output_filename}")


def main(argv):
    if len(argv) < 1:
        print("""
        This script extracts audio from a given video file and generates a time-stamped transcription
        using the Vosk speech recognition library. The transcription is saved in a text file with the
        same name and in the same folder as the input video with '.rec' extension.  Intended for use
        with the creator.py script, and part of the ChopItUp tool kit. 

        Usage: video_to_transcript.py -all <directory_path> OR video_to_transcript.py <video_path>
        """)
        sys.exit(1)

    if argv[0] == "-all":
        directory_path = os.path.abspath(argv[1])

        if not os.path.isdir(directory_path):
            print(f"{directory_path} is not a valid directory.")
            sys.exit(1)

        video_extensions = ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.flv", "*.wmv"]
        video_files = []

        for ext in video_extensions:
            video_files.extend(glob.glob(os.path.join(directory_path, ext)))

        if not video_files:
            print(f"No video files found in {directory_path}")
            sys.exit(1)

        for video_path in video_files:
            print(f"Processing {video_path}")
            transcribe_audio(model_path, video_path)
    else:
        video_path = os.path.abspath(argv[0])

        if not os.path.isfile(video_path):
            print(f"{video_path} is not a valid file.")
            sys.exit(1)

        transcribe_audio(model_path, video_path)

if __name__ == "__main__":

    app_name = "ChopItUp"
    data_dir = appdirs.user_data_dir(app_name)
    os.makedirs(data_dir, exist_ok=True)

    # the recognition model we require (has to be this one as it returns sample times)
    model_url = "https://alphacephei.com/vosk/models/vosk-model-en-us-aspire-0.2.zip"
    model_dir_name = "vosk-model-en-us-aspire-0.2"

    model_path = os.path.join(data_dir, model_dir_name)
    download_and_unzip_model(model_url, model_path, data_dir)

    SetLogLevel(-1)

    main(sys.argv[1:])