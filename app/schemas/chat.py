from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    question: str = Field(
        min_length=3,
        max_length=2000,
        description="Question for DataNexus AI",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if not value:
            raise ValueError("Question cannot be empty")

        return value