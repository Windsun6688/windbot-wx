from enum import Enum
from collections import Counter
import random
from .. import moduleHelper
from PIL import Image
from .image_generation import generate_image_with_blanks


class LetterState(Enum):
    CORRECT = 0  # Green
    EXISTS = 1  # Yellow
    INCORRECT = 2  # Gray


def check_guess(guess: str, answer: str) -> list[LetterState]:
    """Checks the `guess` against `answer`, with wordle rules.
    Converts the strings to uppercase before comparing them.

    Raises ValueError if guess and answer are not of the same length.

    Takes O(N) time, where N is the length of the word of the current game.

    Returns:
        list[LetterState]: the result of each letter of the guess.
    """
    if len(guess) != len(answer):
        raise ValueError(f"{guess=} and {answer=} should be the same length.")

    guess = guess.upper()
    answer = answer.upper()

    result = [LetterState.INCORRECT] * len(answer)

    answer_counts = Counter(answer)

    # First pass: get the green ones
    for idx, guess_ch in enumerate(guess):
        if guess_ch == answer[idx]:
            result[idx] = LetterState.CORRECT
            answer_counts[guess_ch] -= 1

    # Second pass: mark other letters as either yellow or gray
    for idx, guess_ch in enumerate(guess):
        if result[idx] == LetterState.CORRECT:
            continue
        if answer_counts[guess_ch] > 0:
            answer_counts[guess_ch] -= 1
            result[idx] = LetterState.EXISTS
        else:
            result[idx] = LetterState.INCORRECT

    return result


# Wordlist from https://github.com/3b1b/videos/blob/master/_2022/wordle/data/
class WordlistManager:
    def __init__(self, allowed_words_path, possible_words_path) -> None:

        self.allowed_words: set[str] = set()  # set because we want fast membership test
        with open(allowed_words_path) as f:
            for word in f:
                self.allowed_words.add(word.strip().upper())

        # maps word length to list of words because we want fast sampling
        self.possible_words: dict[int, list[str]] = dict()
        self.min_length = 1000000
        self.max_length = -1
        with open(possible_words_path) as f:
            for word in f:
                word = word.strip().upper()
                word_len = len(word)
                self.min_length = min(self.min_length, word_len)
                self.max_length = max(self.max_length, word_len)
                self.possible_words.setdefault(word_len, [])
                self.possible_words[word_len].append(word)

    def get_random_word(self, desired_length: int) -> str | None:
        if desired_length not in self.possible_words:
            return None
        return random.choice(self.possible_words[desired_length])

    def is_word_allowed(self, word: str) -> bool:
        return word in self.allowed_words


class GameState(Enum):
    FINISHED = 0
    ONGOING = 1


class GameLoop:

    MAX_TRIES = {5: 6, 6: 7, 7: 8, 8: 9}

    def __init__(self, mh: moduleHelper.ModuleHelper) -> None:
        self.state = GameState.FINISHED
        self.n = 5
        self.mh = mh
        wordlist_path = mh.compose_static_path("wordle/common_words_ge_5.txt")
        self.wordlist = WordlistManager(wordlist_path, wordlist_path)
        self.guesses: list[str] = []
        self.max_guesses = 0

    def start(self, n) -> tuple[bool, str, Image.Image | None]:
        answer = self.wordlist.get_random_word(n)
        if answer is None:
            return (
                False,
                f"Invalid word length {n}, expected {self.wordlist.min_length}-{self.wordlist.max_length}",
                None,
            )
        self.answer = answer
        self.n = n
        self.state = GameState.ONGOING
        self.guesses = []
        self.max_guesses = GameLoop.MAX_TRIES[n]
        return (
            True,
            f"Let the games begin :D (length {n})",
            generate_image_with_blanks([], self.answer, self.max_guesses),
        )

    def guess(self, guess: str) -> tuple[bool, str, None | Image.Image]:
        if self.state == GameState.FINISHED:
            return (
                False,
                "Game is not in progress. Use wstart [n] to start a game.",
                None,
            )
        if len(guess) != self.n:
            return (
                False,
                f'The guess "{guess}" is not of correct length. (Expected {self.n})',
                None,
            )
        if not self.wordlist.is_word_allowed(guess):
            return (False, f'The guess "{guess}" is not a valid word.', None)

        self.guesses.append(guess)
        img = generate_image_with_blanks(self.guesses, self.answer, self.max_guesses)

        if guess == self.answer:
            self.state = GameState.FINISHED
            return (True, f"Congrats! You won in {len(self.guesses)} guesses!", img)

        return (True, "", img)
