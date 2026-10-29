
import operator
from typing import Annotated, Literal, TypedDict


class DataNexusState(TypedDict, total=False):
    question: str
    intent: Literal["sql", "documents", "both", "general"]
    sql_result: str
    document_result: str
    final_answer: str

    # Multiple parallel agents may append errors.
    errors: Annotated[list[str], operator.add]
