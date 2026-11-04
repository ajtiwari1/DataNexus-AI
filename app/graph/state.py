
import operator
from typing import Annotated, Literal, TypedDict


class DataNexusState(TypedDict, total=False):
    question: str
    intent: Literal["sql", "documents", "both", "general"]
    sql_query: str
    sql_result: str
    document_result: str
    final_answer: str
    request_id: str
    approval_token: str
    pending_approval: bool
    approval_reason: str
    approval_status: str
    retrieved_context: list[str]
    # Multiple parallel agents may append errors.
    errors: Annotated[list[str], operator.add]