import unittest
from ..game_logic import LetterState, check_guess


class CheckGuessTestCase(unittest.TestCase):
    # Note to self: unittest only runs functions that begin with `test`

    def test_all_correct(self):
        guess = "OCAML"
        answer = "OCAML"
        expected = [LetterState.CORRECT] * 5
        self.assertEqual(check_guess(guess, answer), expected)

    def test_all_incorrect(self):
        guess = "AAAAA"
        answer = "XXXXX"
        expected = [LetterState.INCORRECT] * 5
        self.assertEqual(check_guess(guess, answer), expected)

    def test_mismatching_lengtsh(self):
        guess = "AAAA"
        answer = "AAAAA"
        with self.assertRaises(ValueError):
            check_guess(guess, answer)

    def test_partial_correct(self):
        guess = "AAAAA"
        answer = "OCAML"
        expected = [
            LetterState.INCORRECT,
            LetterState.INCORRECT,
            LetterState.CORRECT,
            LetterState.INCORRECT,
            LetterState.INCORRECT,
        ]
        self.assertEqual(check_guess(guess, answer), expected)

    def test_exists(self):
        guess = "ABCDE"
        answer = "XXAXX"
        expected = [
            LetterState.EXISTS,
            LetterState.INCORRECT,
            LetterState.INCORRECT,
            LetterState.INCORRECT,
            LetterState.INCORRECT,
        ]
        self.assertEqual(check_guess(guess, answer), expected)

    def test_guess_repeat(self):
        guess = "AAAAA"
        answer = "AXAXX"
        expected = [
            LetterState.CORRECT,
            LetterState.INCORRECT,
            LetterState.CORRECT,
            LetterState.INCORRECT,
            LetterState.INCORRECT,
        ]
        self.assertEqual(check_guess(guess, answer), expected)

    def test_answer_repeat(self):
        guess = "AXAXX"
        answer = "AAAAA"
        expected = [
            LetterState.CORRECT,
            LetterState.INCORRECT,
            LetterState.CORRECT,
            LetterState.INCORRECT,
            LetterState.INCORRECT,
        ]
        self.assertEqual(check_guess(guess, answer), expected)

    def test_repeat_exists_and_correct(self):
        guess = "OOXXX"
        answer = "ROBOT"
        expected = [
            LetterState.EXISTS,
            LetterState.CORRECT,
            LetterState.INCORRECT,
            LetterState.INCORRECT,
            LetterState.INCORRECT,
        ]
        self.assertEqual(check_guess(guess, answer), expected)

    def test_repeat_correct_and_exists(self):
        guess = "XOOXX"
        answer = "ROBOT"
        expected = [
            LetterState.INCORRECT,
            LetterState.CORRECT,
            LetterState.EXISTS,
            LetterState.INCORRECT,
            LetterState.INCORRECT,
        ]
        self.assertEqual(check_guess(guess, answer), expected)


if __name__ == "__main__":
    unittest.main()
