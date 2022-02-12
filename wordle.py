import os
import argparse
import random
import collections
import string


def generate_word_list(input_file_name, output_file_name):
    """Util function to generate the initial word list. I had to run this once."""

    if not os.path.exists(input_file_name):
        print(f"I can't find {input_file_name}, can you double check pretty please?")
        exit(1)

    if os.path.exists(output_file_name):
        print(f"{output_file_name} already exists. I refuse to modify it!")
        exit(1)

    valid_words = []
    with open(input_file_name) as word_file:
        words = list(word_file.read().split())
        valid_words = list(filter(lambda w: len(w) == 5, words))

    if not valid_words:
        print("no valid words :(")
        exit()

    with open(output_file_name, "w") as fp:
        fp.write("\n".join(valid_words))

    print(f"Wrote {len(valid_words)} words to {output_file_name}.")


class WordleGame:
    def __init__(self, input_word=None, input_file_name=None):
        self.input_file_name = input_file_name  # assumes valid word list
        if not input_word:
            self.word = self._choose_target_word()
        else:
            self.word = input_word
        self.max_guesses = 5
        self.guess_count = 0
        self.game_over = False
        self.won = False

    def _choose_target_word(self):
        # yeah reservoir sampling would be better, but who cares?
        with open(self.input_file_name) as word_file:
            return random.choice(word_file.read().split())

    def process_guess(self, guessed_word):
        """This one is reponsible for returning the "feedback" for the guess.

        1  -> Green
        0  -> Yellow
        -1 -> Gray
        """
        if self.won or self.game_over:
            return "Sorry, game is over."

        if len(guessed_word) != 5:
            return f"Since you can't count, let me help you: {len(guessed_word)} is not equal to 5."

        self.guess_count += 1
        if guessed_word == self.word:
            self.won = True
            return f"Correct. This was your guess number {self.guess_count}."

        result = []
        # We use this temp buffer to mark green and yellow letters to deal with duplicates.
        temp_word = list(self.word)
        for i, c in enumerate(guessed_word):
            if c == temp_word[i]:
                result.append(1)
                temp_word[i] = "#"
            elif c in temp_word:
                temp_word[temp_word.index(c)] = "!"
                result.append(0)
            else:
                result.append(-1)

        self.game_over = self.guess_count >= 5

        # can return a tuple here to make this more flexible
        return f"Guess #{self.guess_count} -- {guessed_word}: {' '.join(map(str, result))}"

    # TODO: DELETE DELETE DELETE
    def process_guess_for_bot(self, guessed_word):
        """This one is reponsible for returning the "feedback" for the guess.

        1  -> Green
        0  -> Yellow
        -1 -> Gray
        """
        if self.won or self.game_over:
            return []

        if len(guessed_word) != 5:
            print(f"{guessed_word}: {len(guessed_word)}")
            return []

        self.guess_count += 1
        if guessed_word == self.word:
            self.won = True
            print(f"Correct! The word was {guessed_word}")
            return []

        result = []
        # We use this temp buffer to mark green and yellow letters to deal with duplicates.
        temp_word = list(self.word)
        for i, c in enumerate(guessed_word):
            if c == temp_word[i]:
                result.append(1)
                temp_word[i] = "#"
            elif c in temp_word:
                temp_word[temp_word.index(c)] = "!"
                result.append(0)
            else:
                result.append(-1)

        self.game_over = self.guess_count >= 5

        # can return a tuple here to make this more flexible
        return result

    def play(self):
        while not (self.game_over or self.won):
            guess = input("Enter your guess: ")
            print(self.process_guess(guess.lower()))
        # done with the game
        print("-------------- end of game -------------")
        if self.won:
            print("good job, i guess")
        else:
            print(f"Here's the answer: {self.word}")

    def play_with_bot(self, solver):
        print(f"here's the word the bot is trying to guess: {self.word}")
        while not (self.game_over or self.won):
            guess = solver.make_guess()
            feedback = self.process_guess_for_bot(guess.lower())
            solver.process_feedback(feedback)
        print("-------------- end of game -------------")
        if self.won:
            print("good job, i guess")
        else:
            print(f"Here's the answer: {self.word}")


class WordleSolver:
    def __init__(self, input_file_name):
        self.possible_words = []
        self.eliminated_letters = set()  # is this really necessary?
        self.guesses = []
        self.feedbacks = []
        self.possible_locations = collections.defaultdict(lambda: set([0, 1, 2, 3, 4]))
        self.possible_letters = collections.defaultdict(lambda: set(list(string.ascii_lowercase)))

        # this file only has 5-letter words
        with open(input_file_name) as word_file:
            for line in word_file:
                self.possible_words.append(line.strip().lower())

    def make_guess(self):
        if not self.possible_words:
            return "aaaaa"  # this should never happen, obviously
        self.guesses.append(random.choice(self.possible_words))
        print(f"guessing: {self.guesses[-1]}")
        return self.guesses[-1]

    def process_feedback(self, feedback):
        if not feedback:
            return

        last_guess = self.guesses[-1]
        for idx, val in enumerate(feedback):
            letter = last_guess[idx]
            if val == 1:
                self.possible_locations[letter] = set([idx])
                self.possible_letters[idx] = set(letter)
            elif val == 0:
                print(f"{idx} -- letter: {letter}, locations: {self.possible_locations[letter]}")
                self.possible_locations[letter].remove(idx)
                self.possible_letters[idx].remove(letter)
            elif len(self.possible_locations[letter]) == 5:
                self.possible_locations[letter].clear()
                self.possible_letters[idx].remove(letter)

        print(f"guess: {last_guess}, feedback: {feedback}, {self.possible_locations}")

        new_candidates = []
        for candidate in self.possible_words:
            include = True
            # candidates = frees
            for idx, c in enumerate(candidate):
                if idx not in self.possible_locations[c]:
                    include = False
                    break
                if c not in self.possible_letters[idx]:
                    include = False
                    break
            if include:
                new_candidates.append(candidate)

        self.possible_words = new_candidates
        if len(new_candidates) < 10:
            print(new_candidates)


# TODO
# (target: sprat, guess: awiap) -- what's the feedback? does it handle the a's correctly?
def main():
    parser = argparse.ArgumentParser(description="Solves/plays wordle.")
    parser.add_argument(
        "--play_bot",
        default=True,
        action="store_false",
        help="Enables the bot and user becomes the observer.",
    )
    parser.add_argument(
        "--words_file",
        default="common.txt",
        help="A file containing one word per line. It'll be used as the valid word list.",
    )
    parser.add_argument("--wordle_word", help="Sets the target word.")
    parser.add_argument("--debug_mode", default=False, action="store_true")
    args = parser.parse_args()

    output_file_name = f"{args.words_file.split('.')[0]}_wordle.txt"

    if not os.path.exists(output_file_name):
        generate_word_list(args.words_file, output_file_name)

    wg = WordleGame(input_word=args.wordle_word, input_file_name=output_file_name)
    if args.play_bot:
        solver = WordleSolver(output_file_name)
        wg.play_with_bot(solver)
    else:
        wg.play()


if __name__ == "__main__":
    main()
