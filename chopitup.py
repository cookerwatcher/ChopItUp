# ChopItUp - (c) Hippy, 2023,  WTFPL
# see the README.md

import os
import glob
import json
import argparse
from collections import Counter
from moviepy.editor import VideoFileClip, concatenate_videoclips
import appdirs
from difflib import SequenceMatcher

app_name = "ChopItUp"
word_library_path = "words_library.json"
data_dir = appdirs.user_data_dir(app_name)
os.makedirs(data_dir, exist_ok=True)

verbose = False # set to True to print debug messages


class WordSegmentLibrary:
    def __init__(self, word_library_path):
        self.word_library_path = word_library_path
        self.word_library = None

    def load_word_library(self):
        """
        Load the word library from the JSON file specified by word_library_path.
        """
        if os.path.exists(self.word_library_path):
            with open(self.word_library_path, "r") as f:
                self.word_library = json.load(f)
        else:
            # create an empty library
            self.word_library = {"sources": []}            

    def librarian(self, rec_files_path="."):
        """
        Generate the word library from the .rec files in the specified directory
        and save it as a JSON file.
        """
        available = False

        # if it already exists, load it and update it...
        if os.path.exists(self.word_library_path):
            with open(self.word_library_path, "r") as f:
                word_library = json.load(f)
                available = True
        else:
            word_library = {"sources": []}

        # look for .rec files in the specified directory
        rec_files = glob.glob(os.path.join(rec_files_path, "*.rec"))
        sources = word_library["sources"]
        for rec_file in rec_files:
            with open(rec_file, "r") as f:
                first_line = f.readline().strip()
                source_media = first_line.replace("media=", "")

                if source_media not in sources:
                    sources.append(source_media) # add the source to the library

        for rec_file in rec_files:
            with open(rec_file, "r") as f:
                first_line = f.readline().strip()
                source_media = first_line.replace("media=", "")

                for line in f:
                    word, start_time, end_time = line.strip().split('\t')
                    word = word.lower()
                    word_data = {
                        "src": sources.index(source_media),
                        "A": float(start_time),
                        "B": float(end_time)
                    }

                    if word in word_library:
                        word_library[word].append(word_data)
                    else:
                        word_library[word] = [word_data]

        with open(self.word_library_path, "w") as f:
            json.dump(word_library, f, indent=2)

        if available == False:
            print(f"Word library created: {self.word_library_path}")
        else:    
            print(f"Word library updated: {self.word_library_path}")


    def creator(self, input_sentence):
        """
        Select word segments from the library based on the input sentence.
        """
        input_words = input_sentence.lower().split()
        selected_segments = []

        for word in input_words:
            if word in self.word_library:
                selected_segments.append(self.word_library[word][0])
            else:
                print(f"Word '{word}' not found in the library")

        return selected_segments

    def get_word_occurrences(self, word):
        """
        Return a list of occurrences for a given word in the library.
        """
        return self.word_library.get(word, [])

    def library_stats(self, word=None):
        """
        Print statistics about the words in the library.
        """
        if word and word != "":
            word = word.lower()
            count = 0
            if word in self.word_library:
                print(f"Statistics for the word '{word}':")
                occurrences = self.word_library[word]
                for idx, occurrence in enumerate(occurrences):
                    src = occurrence["src"]
                    start_time = occurrence["A"]
                    end_time = occurrence["B"]
                    duration = end_time - start_time
                    source_file = self.word_library["sources"][src]
                    count += 1
                    if verbose == True:
                        print(f"  Occurrence {idx + 1}: File: {source_file}, Start: {start_time}, End: {end_time}, Duration: {duration}")

                print(f"occurrences: {count}")
            else:
                print(f"Word '{word}' not found in the library.")

            return

        word_frequencies = Counter()
        word_lengths = []

        for word, occurrences in self.word_library.items():
            if word != "sources":
                word_frequencies[word] = len(occurrences)
                word_lengths.append((word, len(word)))

        total_words = sum(word_frequencies.values())
        unique_words = len(word_frequencies)

        print(f"Total words in library: {total_words}")
        print(f"Unique words in library: {unique_words}")

        print("\nTop 20 words in the library:")
        for word, frequency in word_frequencies.most_common(20):
            print(f"{word}: {frequency}")

        print("\nTop 20 longest words in the library:")
        for word, length in sorted(word_lengths, key=lambda x: x[1], reverse=True)[:20]:
            print(f"{word}: {length}")

    def check_string(self, input_string):
        """
        Check the input string for available words and suggest alternatives.
        """
        input_string = input_string.replace("?", "").replace("!", "")
        input_words = input_string.lower().split()
        available_words = []
        substituted_words = []
        substitution_made = False

        for word in input_words:
            available_word = self.get_alternative_word(word)
            if available_word:
                available_words.append((word, available_word))
                substituted_words.append(available_word)
                if word != available_word:
                    substitution_made = True
                    print(f"Alternative used for '{word}': '{available_word}'")
            else:
                print(f"Word '{word}' not found in the library, and no suitable alternative found")
                substitution_made = True

        if substituted_words:
            substituted_string = " ".join(substituted_words)
            if substitution_made:
                print(f"\nWe don't have all those words, how about this: {substituted_string}")
            else:
                print(f"\nAll words were found for string: {substituted_string}")

        return available_words

    def get_alternative_word(self, word):
        """
        Find an alternative word in the library with the same starting letter,
        similar length, and the highest similarity ratio.
        """
        if word in self.word_library:
            return word

        alternative_word = None
        highest_similarity = 0

        for available_word in self.word_library.keys():
            if available_word == "sources":
                continue

            # Check if the word has the same starting letter and similar length
            if word[0] == available_word[0] and abs(len(word) - len(available_word)) <= 2:
                similarity = SequenceMatcher(None, word, available_word).ratio()

                if similarity > highest_similarity:
                    highest_similarity = similarity
                    alternative_word = available_word

        return alternative_word

# ------------------------------

# assemble segments into a video    
def assemble_video(media_library, segments, output_filename):
    clips = []
    for segment in segments:
        src = segment["src"]
        start_time = segment["A"]
        end_time = segment["B"]
        video_path = media_library.word_library["sources"][src]

        print(f"({src}){video_path}: {start_time}-{end_time}")

        clip = VideoFileClip(video_path).subclip(start_time, end_time)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_filename)

    for clip in clips:
        clip.close()
    final_clip.close()

# all instances of "word" are output into a video
def create_word_instances_video(word_segment_library, word, output_filename):
    word_library = word_segment_library.word_library    

    if word in word_library:
        segments = word_library[word]
        assemble_video(word_segment_library, segments, output_filename)
        print(f"Video with all instances of '{word}' saved to {output_filename}")
    else:
        print(f"Word '{word}' not found in the library")


# Main 
def main(args):

    if args.verbose:
        global verbose
        verbose = True
        print("Verbose output is enabled.")

    if args.label:
        label = args.label
        word_library_path = os.path.join(data_dir, f"{label}_library.json")
    else:
        word_library_path = os.path.join(data_dir, "word_library.json")
    print(f"Using word library: {word_library_path}")

    word_segment_library = WordSegmentLibrary(word_library_path)
    word_segment_library.load_word_library()

    if args.generate:
        word_segment_library.librarian(args.media)
        exit(0)

    if args.stats is not None:
        word_segment_library.library_stats(word=args.stats if isinstance(args.stats, str) else None)
        exit(0)

    if not os.path.exists(word_library_path):
        print(f"Generating word library {word_library_path} from .rec files directory '{args.media}'...")
        word_segment_library.librarian(args.media)

    if args.words:
        word = args.words.lower()
        sanitized_word = "".join(c for c in word if c.isalnum() or c == " ")
        occurrences = word_segment_library.get_word_occurrences(word)
        count = len(occurrences)
        output_filename = f"{count}-{sanitized_word}-words.mp4"
        create_word_instances_video(word_segment_library, word, output_filename)
        exit(0)

    if args.create:
        input_sentence = args.create
        segments = word_segment_library.creator(input_sentence)
        print("Selected segments:")
        for segment in segments:
            print(segment)

        if args.output:
            output_filename = args.output
        else:
            output_filename = "output_video.mp4"

        assemble_video(word_segment_library, segments, output_filename)
        print(f"Video assembled and saved to {output_filename}")
        exit(0)

    if args.check_string:
        input_sentence = args.check_string
        print(f"Checking string: {input_sentence}")
        word_segment_library.check_string(input_sentence)
        exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChopItUp Media Library Tool")
    parser.add_argument("--generate", action="store_true", help="Generate/update word library from .rec transcript files")
    parser.add_argument("--media", metavar="RECPATH", type=str, default=".", help="Specify the path to .rec files (for --generate, default: current directory)")

    parser.add_argument("--label", metavar="LABEL", type=str, help="Specify which library to work with (default: 'word')")
    
    parser.add_argument("--create", metavar="SENTENCE", type=str, help="Create a video using the given input sentence")
    parser.add_argument("--words", metavar="WORD", type=str, help="Create a video of all instances of a given word")
    parser.add_argument("--output", metavar="FILENAME", type=str, help="Specify the output video filename")

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--check_string", metavar="SENTENCE", type=str, help="Check the given string for available words and suggest alternatives")
    parser.add_argument("--stats", nargs='?', const=True, type=str, help="Display statistics, optionally for a specific word", required=False)

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
    
    else:
        main(args)   

