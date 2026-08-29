# services/core/app/api/v1/schemas/puzzle.py
from datetime import date, datetime
from pydantic import BaseModel, field_validator


class PuzzleOptionOut(BaseModel):
    option_id: int
    label: str

    model_config = {"title": "Puzzle.Option"}


class PuzzleDistributionOut(BaseModel):
    option_id: int
    label: str
    count: int
    pct: float

    model_config = {"title": "Puzzle.Distribution"}


class PuzzleAnswerOut(BaseModel):
    prompt_id: int
    puzzle_date: date
    question: str
    setup: str | None = None
    family: str
    closes_at: datetime
    options: list[PuzzleOptionOut] = []
    already_answered: bool = False
    your_option_id: int | None = None

    model_config = {"title": "Puzzle.Answer"}

    # jsonb_agg over zero rows returns NULL, not []
    @field_validator("options", mode="before")
    @classmethod
    def _coerce_null(cls, v):
        return v or []


class PuzzleRevealOut(BaseModel):
    was_correct: bool
    winning_option_id: int
    winning_share: float
    runner_up_share: float | None = None
    distribution: list[PuzzleDistributionOut] = []
    your_own_answer_id: int | None = None

    model_config = {"title": "Puzzle.Reveal"}

    @field_validator("distribution", mode="before")
    @classmethod
    def _coerce_null(cls, v):
        return v or []


class PuzzlePlayOut(BaseModel):
    prompt_id: int
    puzzle_date: date
    question: str
    setup: str | None = None
    family: str
    total_answers: int = 0
    options: list[PuzzleOptionOut] = []
    already_played: bool = False
    your_guess_id: int | None = None
    reveal: PuzzleRevealOut | None = None

    model_config = {"title": "Puzzle.Play"}

    @field_validator("options", mode="before")
    @classmethod
    def _coerce_null(cls, v):
        return v or []


class PuzzleDailyOut(BaseModel):
    as_of: datetime
    puzzle_date: date
    answer: PuzzleAnswerOut | None = None
    play: PuzzlePlayOut | None = None

    model_config = {"title": "Puzzle.Daily"}