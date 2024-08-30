from enum import Enum
from typing import List
from collections import Counter


class LetterState(Enum):
    CORRECT = 0  # Green
    EXISTS = 1  # Yellow
    INCORRECT = 2  # Gray


def check_guess(guess: str, answer: str) -> List[LetterState]:
    """Checks the `guess` against `answer`, with wordle rules.
    Converts the strings to uppercase before comparing them.

    Raises ValueError if guess and answer are not of the same length.

    Takes O(N) time, where N is the length of the word of the current game.

    Returns:
        List[LetterState]: the result of each letter of the guess.
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
