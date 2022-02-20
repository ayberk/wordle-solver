import argparse
import collections
import logging
import os
import random
import string

MAX_GUESSES = 5  # TODO: make this an arg
WORD_LENGTH = 5  # TODO: make this an arg
DEFAULT_START_WORDS = [
    "stern",
    "adieu",
    "audio",
    "stare",
    "teary",
    "crane",
    "trace",
    "arise",
]


def generate_word_list(input_file_name, output_file_name):
    """Util function to generate the eligible word list."""

    if not os.path.exists(input_file_name):
        logging.error(f"I can't find {input_file_name}, can you double check pretty please?")
        exit(1)

    if os.path.exists(output_file_name):
        logging.error(f"{output_file_name} already exists. I refuse to modify it!")
        exit(1)

    valid_words = []
    with open(input_file_name) as word_file:
        words = list(word_file.read().split())
        valid_words = list(
            filter(
                lambda w: len(w) == WORD_LENGTH,
                words,
            )
        )

    if not valid_words:
        logging.error("no valid words :(")
        exit()

    with open(output_file_name, "w") as fp:
        fp.write("\n".join(valid_words))

    logging.info(f"Wrote {len(valid_words)} words to {output_file_name}.")


class WordleGame:
    def __init__(self, input_word=None, input_file_name=None):
        self._input_file_name = input_file_name
        if not input_word:
            self._word = self._choose_target_word()
        else:
            self._word = input_word.upper()
        self._max_guesses = MAX_GUESSES
        self._guess_count = 0
        self._invalid_guess_count = 0
        self._game_over = False
        self._won = False

    def _choose_target_word(self):
        # yeah reservoir sampling would be better, but who cares?
        with open(self._input_file_name) as word_file:
            words, word = word_file.read().split(), "?"
            while not word.isalpha():
                word = random.choice(words)
            return word.upper()

    def process_guess(self, guessed_word):
        """This one is reponsible for returning the "feedback" for the guess.

        1  -> Green
        0  -> Yellow
        -1 -> Gray
        """
        if self._won or self._game_over:
            return (self._guess_count, guessed_word, [])

        if not guessed_word or len(guessed_word) != WORD_LENGTH:
            logging.warning(f"{guessed_word} doesn't seem to be a valid guess.")
            self._invalid_guess_count += 1
            return (self._invalid_guess_count, guessed_word, [])

        self._guess_count += 1
        guessed_word = guessed_word.upper()  # ew, but necessary
        if guessed_word == self._word:
            self._won = True
            logging.info(f"Correct! The word was {guessed_word}")
            return (self._guess_count, guessed_word, [])

        result = []
        # We use this temp buffer to deal with duplicates
        temp_word = self._word
        for i, c in enumerate(guessed_word):
            position = temp_word.find(c)
            # don't try this at home
            result.append(position if position == -1 else int(position == i))
            if position > -1:
                # I hate py so much
                temp_word = temp_word[:position] + "!" + temp_word[position + 1 :]

        self._game_over = self._guess_count >= MAX_GUESSES

        return (self._guess_count, guessed_word, result)

    def play_loop(self):
        while not (self._game_over or self._won):
            guess = input("Enter your guess: ")
            guess_count, guessed_word, feedback = self.process_guess(guess)
            print(f"Guess #{guess_count} -- {guessed_word}: {' '.join(map(str, feedback))}")

    def bot_play_loop(self, solver):
        logging.info(f"Here's the word the bot is trying to guess: {self._word}")
        while not (self._game_over or self._won):
            guess = solver.make_guess()
            feedback = self.process_guess(guess)
            if feedback[-1]:
                logging.info(f"Guess: {guess}, feedback: {feedback[-1]}")
            solver.process_feedback(feedback)

    def start(self, game_mode, solver):
        if game_mode == "play":
            self.play_loop()
        elif game_mode == "bot_play":
            self.bot_play_loop(solver)
        elif game_mode == "solve":
            # Don't pass a bad solver here. I'll know.
            helper = WordleHelper(solver)
            helper.play()

        if self._guess_count <= 0:
            logging.error("Unknown game mode :(")
            return

        logging.info("-------------- Game Over -------------")
        if self._won:
            logging.info(f"It took you {self._guess_count} guesses. Good job, I guess.")
        else:
            logging.info(f"Here's the answer: {self._word}")


class WordleSolver:
    # TODO clean this up ffs
    def __init__(self, input_file_name, start_words=[]):
        self._word_letters = set()
        self._guesses = []
        # each letter can be at any position initially
        self._letter_locations = collections.defaultdict(lambda: set(i for i in range(WORD_LENGTH)))
        # and each position can have any letter initially
        self._position_to_letters = collections.defaultdict(
            lambda: set(list(string.ascii_uppercase))
        )

        self._possible_words = []
        self._start_words = start_words

        with open(input_file_name) as word_file:
            for line in word_file:
                self._possible_words.append(line.strip().upper())

    def make_guess(self):
        if not self._possible_words:
            logging.info("No way. I have been defeated!")  # a word that's not in our dictionary...
            exit(0)

        if self._start_words:
            self._guesses.append(random.choice(self._start_words).upper())
            self._start_words = []  # ugh
        else:
            self._guesses.append(random.choice(self._possible_words).upper())

        return self._guesses[-1]

    def process_feedback(self, raw_feedback):
        if not raw_feedback[-1]:
            return

        guess_count, last_guess, feedback = raw_feedback
        # I thought about making this loop nicer, but then I realized I don't really care enough.
        for idx, val in enumerate(feedback):
            letter = last_guess[idx].upper()
            if val == 1:
                self._position_to_letters[idx] = {letter}
                for l in string.ascii_uppercase:
                    self._letter_locations[l].discard(idx)
                if letter in self._word_letters:
                    self._letter_locations[letter].add(idx)
                else:
                    self._letter_locations[letter] = {idx}
                self._word_letters.add(letter)
            elif val == 0:
                if idx in self._letter_locations[letter]:
                    self._letter_locations[letter].remove(idx)
                self._position_to_letters[idx].remove(letter)
                self._word_letters.add(letter)
            else:
                if letter not in self._word_letters:
                    self._letter_locations[letter].clear()
                self._position_to_letters[idx].discard(letter)

        new_candidates = []
        for candidate in self._possible_words:
            for idx, c in enumerate(candidate.upper()):
                # eliminate the words that don't contain all "found" letters
                if not all(w in candidate for w in self._word_letters):
                    break
                # eliminate the words that conflict with the feedback
                if not self._letter_locations[c] or c not in self._position_to_letters[idx]:
                    break
            else:
                new_candidates.append(candidate)

        if guess_count >= MAX_GUESSES:
            logging.info(
                f"I lost? :( Final possible word list before the last guess: {self._possible_words}"
            )
        logging.debug(f"guess: {last_guess}, feedback: {feedback}, {self._letter_locations}")
        self._possible_words = new_candidates


# Honestly, it should be possible to get rid of this, but why would I waste time on that?
class WordleHelper:
    def __init__(self, solver, max_guesses=MAX_GUESSES):
        self._solver = solver
        self._max_guesses = max_guesses
        self._number_of_guesses = 0

    def play(self):
        logging.info("Here's how this works: I give you a guess, and you give me the feedback.")
        logging.info(
            "Enter space-separated 1 for green, 0 for yellow and -1 for gray letters, eg, 1 1 -1 0 0"
        )
        logging.info("I'll handle the rest.")

        while self._number_of_guesses < self._max_guesses:
            self._number_of_guesses += 1
            guess = self._solver.make_guess()
            logging.info(f"Guess: {guess}")
            feedback = []
            while len(feedback) < WORD_LENGTH:
                raw_feedback = input("Enter the feedback: ")
                feedback = self._convert_raw_feedback(raw_feedback)
            self._solver.process_feedback(feedback)

    def _convert_raw_feedback(self, feedback):
        result = []
        for c in feedback.split():
            if c in {"-1", "0", "1"}:
                result.append(int(c))
            else:
                logging.warning("I have no idea what that means. Enter it again please.")
                return []
        return result


# TODO
# (target: sprat, guess: awiap) -- [0, -1, -1, -1, 0] doesn't handle the A's correctly here
def main():
    parser = argparse.ArgumentParser(
        description="Solves/plays wordle. It supports multiple modes so you can use it as a solver or just play the game as usual."
    )
    parser.add_argument(
        "--game_mode",
        choices=["solve", "bot_play", "play"],
        default="play",
        type=str.lower,
        help="play: play against the computer [default] | solve: use it as a solver | bot_play: plays against itself",
    )
    parser.add_argument(
        "--wordle_word",
        help="Sets the target word. Useful for bot_play mode. If not set, a random world will be chosen instead.",
    )
    parser.add_argument(
        "--words_file",
        default="dictionaries/google-10000-english-usa-no-swears-medium.txt",
        help="A file containing one word per line. It'll be used as the valid word list.",
    )
    parser.add_argument(
        "--log_level",
        default="INFO",
        help="Default: INFO. Also case-insensitive, so save yourself a caps lock press.",
        type=str.upper,
        choices=list(logging._nameToLevel.keys()),
    )
    parser.add_argument(
        "--start_words",
        default=DEFAULT_START_WORDS,
        nargs="*",
        type=str,
        help="Space separated list of words. First guess will be chosen from this list. If not set, a random world will be chosen instead.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=getattr(logging, args.log_level.upper()),
        datefmt="%I:%M:%S",
    )

    output_file_name = f"{args.words_file.split('.')[0]}_wordle.txt"

    if not os.path.exists(output_file_name):
        generate_word_list(args.words_file, output_file_name)

    wg = WordleGame(input_word=args.wordle_word, input_file_name=output_file_name)
    wg.start(args.game_mode, WordleSolver(output_file_name, args.start_words))


if __name__ == "__main__":
    main()
