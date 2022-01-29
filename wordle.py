import os
import random


def generate_word_list(input_file_name, output_file_name):
    """Util function to generate the initial word list."""

    if not os.path.exists(input_file_name):
        print(f'I can\'t find {input_file_name}, can you double check pretty please?')
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

    with open(output_file_name, 'w') as fp:
        fp.write('\n'.join(valid_words))

    print(f"Wrote {len(valid_words)} words to {output_file_name}.")


class WordleGame():
    def __init__(self, input_file_name):
        self.input_file_name = input_file_name  # assumes valid word list
        self.word = self._choose_target_word()
        self.max_guesses = 5
        self.guess_count = 0

    def _choose_target_word(self):
        # yeah reservoir sampling would be better, but who cares?
        with open(self.input_file_name) as word_file:
            return random.choice(word_file.read().split())

    def process_guess(self, guessed_word):
        pass


def main():
    wordle_words_file_name = "wordle_words.txt"
    if not os.path.exists(wordle_words_file_name):
        generate_word_list("words_alpha.txt", wordle_words_file_name)
    wg = WordleGame(wordle_words_file_name)
    print(wg.word)


if __name__ == '__main__':
    main()
