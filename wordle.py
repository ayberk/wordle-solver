import os
import argparse
import random
import collections
import string
import logging


def generate_word_list(input_file_name, output_file_name):
    """Util function to generate the initial word list. I had to run this once."""

    if not os.path.exists(input_file_name):
        logging.error(f"I can't find {input_file_name}, can you double check pretty please?")
        exit(1)

    if os.path.exists(output_file_name):
        logging.error(f"{output_file_name} already exists. I refuse to modify it!")
        exit(1)

    valid_words = []
    with open(input_file_name) as word_file:
        words = list(word_file.read().split())
        valid_words = list(filter(lambda w: len(w) == 5, words))

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
            self._word = input_word
        self._max_guesses = 5
        self._guess_count = 0
        self._game_over = False
        self._won = False

    def _choose_target_word(self):
        # yeah reservoir sampling would be better, but who cares?
        with open(self._input_file_name) as word_file:
            words, word = word_file.read().split(), "?"
            while not word.isalpha():
                word = random.choice(words)
            return word

    def process_guess(self, guessed_word):
        """This one is reponsible for returning the "feedback" for the guess.

        1  -> Green
        0  -> Yellow
        -1 -> Gray
        """
        if self._won or self._game_over:
            return "Sorry, game is over."

        if len(guessed_word) != 5:
            return f"Since you can't count, let me help you: {len(guessed_word)} is not equal to 5."

        self._guess_count += 1
        if guessed_word == self._word:
            self._won = True
            return f"Correct. This was your guess number {self._guess_count}."

        result = []
        # We use this temp buffer to mark green and yellow letters to deal with duplicates.
        temp_word = list(self._word)
        for i, c in enumerate(guessed_word):
            if c == temp_word[i]:
                result.append(1)
                temp_word[i] = "#"
            elif c in temp_word:
                temp_word[temp_word.index(c)] = "!"
                result.append(0)
            else:
                result.append(-1)

        self._game_over = self._guess_count >= 5

        # can return a tuple here to make this more flexible
        return f"Guess #{self._guess_count} -- {guessed_word}: {' '.join(map(str, result))}"

    # TODO: DELETE DELETE DELETE
    def process_guess_for_bot(self, guessed_word):
        """This one is reponsible for returning the "feedback" for the guess.

        1  -> Green
        0  -> Yellow
        -1 -> Gray
        """
        if self._won or self._game_over:
            return []

        if len(guessed_word) != 5:
            logging.warning(f"{guessed_word}: {len(guessed_word)}")
            return []

        self._guess_count += 1
        if guessed_word == self._word:
            self._won = True
            logging.info(f"Correct! The word was {guessed_word}")
            return []

        result = []
        # We use this temp buffer to mark green and yellow letters to deal with duplicates.
        temp_word = list(self._word)
        for i, c in enumerate(guessed_word):
            if c == temp_word[i]:
                result.append(1)
                temp_word[i] = "#"
            elif c in temp_word:
                temp_word[temp_word.index(c)] = "!"
                result.append(0)
            else:
                result.append(-1)

        self._game_over = self._guess_count >= 5

        # can return a tuple here to make this more flexible
        return result

    def play(self):
        while not (self._game_over or self._won):
            guess = input("Enter your guess: ")
            print(self.process_guess(guess.lower()))
        # done with the game
        logging.info("-------------- end of game -------------")
        if self._won:
            logging.info("good job, i guess")
        else:
            logging.info(f"Here's the answer: {self._word}")

    def play_with_bot(self, solver):
        logging.info(f"here's the word the bot is trying to guess: {self._word}")
        while not (self._game_over or self._won):
            guess = solver.make.guess()
            logging.info(f"Guess: {guess}")
            feedback = self.process_guess_for_bot(guess.lower())
            solver.process_feedback(feedback)
        logging.info("-------------- end of game -------------")
        if self._won:
            logging.info("good job, i guess")
        else:
            logging.info(f"Here's the answer: {self._word}")


class WordleSolver:
    def __init__(self, input_file_name, start_words=[]):
        self._possible_words = []
        self._eliminated_letters = set()  # is this really necessary?
        self._word_letters = set()
        self._guesses = []
        self._feedbacks = []
        self._possible_locations = collections.defaultdict(lambda: set([0, 1, 2, 3, 4]))
        self._possible_letters = collections.defaultdict(lambda: set(list(string.ascii_lowercase)))
        self.start_words = start_words  # THIS HELPS A LOT

        # this file only has 5-letter words
        with open(input_file_name) as word_file:
            for line in word_file:
                self._possible_words.append(line.strip().lower())

    def make_guess(self):
        if not self._possible_words:
            return "aaaaa"  # this should never happen, obviously

        if not self._guesses and self.start_words:
            self._guesses.append(random.choice(self.start_words))
        else:
            self._guesses.append(random.choice(self._possible_words))
        return self._guesses[-1]

    def process_feedback(self, feedback):
        if not feedback:
            return

        last_guess = self._guesses[-1]
        for idx, val in enumerate(feedback):
            letter = last_guess[idx]
            if val == 1:
                self._possible_locations[letter] = set([idx])
                self._possible_letters[idx] = set(letter)
                self._word_letters.add(letter)
            elif val == 0:
                self._possible_locations[letter].remove(idx)
                self._possible_letters[idx].remove(letter)
                self._word_letters.add(letter)
            elif len(self._possible_locations[letter]) == 5:
                self._eliminated_letters.add(letter)
                self._possible_locations[letter].clear()
                self._possible_letters[idx].remove(letter)

        new_candidates = []
        for candidate in self._possible_words:
            include = True
            for idx, c in enumerate(candidate):
                # this fixes the issue with eliminating clock, when chino is guessed (loc[c] = {0})
                # if idx not in self.possible_locations[c]:
                #     include = False
                #     break

                # this eliminates the words that don't contain all "found" letters.
                if not all(w in candidate for w in self._word_letters):
                    include = False
                    break
                # this eliminates the words that conflicts with the feedback
                if c in self._eliminated_letters or c not in self._possible_letters[idx]:
                    include = False
                    break

            if include:
                new_candidates.append(candidate)

        logging.debug(f"guess: {last_guess}, feedback: {feedback}, {self._possible_locations}")
        logging.debug(f"eliminated: {self._eliminated_letters}, word_letters: {self._word_letters}")
        self._possible_words = new_candidates
        if len(new_candidates) < 10:
            logging.debug(new_candidates)


class WordleHelper:
    def __init__(self, solver, max_guesses=5):
        self._solver = solver
        self._max_guesses = max_guesses
        self._number_of_guests = 0

    def play(self):
        logging.info("Here's how this works: I give you a guess, and you give me the feedback.")
        logging.info(
            "Enter space-separated 1 for green, 0 for yellow and -1 for gray letters: 1 1 -1 0 0"
        )
        logging.info("I'll handle the rest")

        while self._number_of_guests <= self._max_guesses:
            self._max_guesses += 1
            guess = self._solver.make_guess()
            logging.info(f"Guess: {guess}")
            feedback = []
            while len(feedback) < 5:
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
# (target: sprat, guess: awiap) -- what's the feedback? does it handle the a's correctly?
# (target:clock, guess: chino) -- returns [1, -1, -1, -1, 0], which means we set possible location
# for c as {0}, so we eliminate clock, which is wrong.
# good starting words: ["stern", "adieu", "audio", "stare", "teary", "poious", "crane", "trace", "arise"]
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
        default="google-10000-english-usa-no-swears-medium.txt",
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
        default=[],
        nargs="*",
        type=str,
        help="Space separated list of words. First guess will be chosen from this list. If not set, a random world will be chosen instead.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    output_file_name = f"{args.words_file.split('.')[0]}_wordle.txt"

    if not os.path.exists(output_file_name):
        generate_word_list(args.words_file, output_file_name)

    wg = WordleGame(input_word=args.wordle_word, input_file_name=output_file_name)
    if args.game_mode == "bot_play":
        solver = WordleSolver(output_file_name)
        wg.play_with_bot(solver)
    elif args.game_mode == "solve":
        solver = WordleSolver(output_file_name, args.start_words)
        helper = WordleHelper(solver)
        helper.play()
    else:
        wg.play()


if __name__ == "__main__":
    main()
