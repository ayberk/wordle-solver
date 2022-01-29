import os
import random

WORDLE_WORDS_FILE_NAME = "wordle_words.txt"


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
    # TODO: there's no game state yet. number of guesses so far etc
    # TODO: i return at failures, gotto keep the game going
    def __init__(self, input_word=None, input_file_name=None):
        self.input_file_name = input_file_name  # assumes valid word list
        if not input_file_name:
            self.word = self._choose_target_word()
        else:
            self.word = input_word
        self.max_guesses = 5
        self.guess_count = 0

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
        if len(guessed_word) != 5:
            print(f"Since you can't count, let me help you: {len(guessed_word)} is not equal to 5.")
            return

        result = []

        # TODO: doesn't work with duplicate letters, might need to count
        for i, c in enumerate(guessed_word):
            if c == self.word[i]:
                result.append(1)
            elif c in self.word:
                result.append(0)
            else:
                result.append(-1)

        return f"{guessed_word}: {' '.join(map(str, result))}"


def main():
    if not os.path.exists(WORDLE_WORDS_FILE_NAME):
        generate_word_list("words_alpha.txt", WORDLE_WORDS_FILE_NAME)

    wg = WordleGame(input_word="abcde", input_file_name=WORDLE_WORDS_FILE_NAME)
    print(f"word: ${wg.word}")
    # poor man's unit tests
    print(wg.process_guess("abcae"))
    print(wg.process_guess("axxxx"))
    print(wg.process_guess("xxxax"))
    print(wg.process_guess("axxxa"))  # should return 1 -1 -1 -1 -1


if __name__ == "__main__":
    main()
