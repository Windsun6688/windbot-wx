from PIL import Image, ImageDraw, ImageFont
from .game_logic import LetterState, check_guess
from .. import moduleHelper
import numpy as np

mh = moduleHelper.ModuleHelper()


class COLORS:
    BACKGROUND = "#202020"
    CORRECT = "#008000"
    EXISTS = "#acac00"
    INCORRECT = "#333333"
    TEXT = "#ffffff"
    OUTLINE = "#888888"

    STATES = {
        LetterState.CORRECT: CORRECT,
        LetterState.EXISTS: EXISTS,
        LetterState.INCORRECT: INCORRECT,
    }


SQUARE_SIZE = 256
SQUARE_SIZE_HALF = SQUARE_SIZE // 2
SQUARE_PADDING = 16
SQUARE_INNER_HALF = SQUARE_SIZE_HALF - SQUARE_PADDING
BORDER_WIDTH = 12

FONT_SIZE = int(SQUARE_SIZE * 0.6)
FONT_PATH = mh.compose_static_path("wordle/NotoSans-Bold.ttf")
FONT = ImageFont.truetype(FONT_PATH, size=FONT_SIZE)


def draw_row(guess, answer):
    num_squares = len(guess)
    square_states = check_guess(guess, answer)
    im = Image.new(
        mode="RGB",
        size=(SQUARE_SIZE * num_squares, SQUARE_SIZE),
        color=COLORS.BACKGROUND,
    )
    draw = ImageDraw.Draw(im)

    for idx in range(num_squares):
        state = square_states[idx]
        guess_ch = guess[idx]
        center = (SQUARE_SIZE_HALF + SQUARE_SIZE * idx, SQUARE_SIZE_HALF)
        draw.rectangle(
            (
                (center[0] - SQUARE_INNER_HALF, center[1] - SQUARE_INNER_HALF),
                (center[0] + SQUARE_INNER_HALF, center[1] + SQUARE_INNER_HALF),
            ),
            fill=COLORS.STATES[state],
            outline=COLORS.OUTLINE,
            width=BORDER_WIDTH,
        )
        draw.text(center, guess_ch, anchor="mm", font=FONT)

    return im


def generate_image(guesses: list[str], answer: str):
    for guess in guesses:
        if len(guess) != len(answer):
            raise ValueError(f"{guess=} not the same length as {answer=}")

    imgs = []
    for guess in guesses:
        imgs.append(draw_row(guess, answer))

    final_img = Image.fromarray(np.vstack(imgs))

    final_img.show()

    return final_img


def generate_image_with_blanks(guesses: list[str], answer: str, max_guesses: int):
    if len(guesses) < max_guesses:
        blank = " " * len(answer)
        guesses += [blank] * (max_guesses - len(guesses))
    generate_image(guesses, answer)


generate_image_with_blanks(["IWANT", "FRIES", "HELLO"], "HELLO", 6)
