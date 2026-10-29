
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.graph.workflow import workflow

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "evals" / "dataset.json"
RESULTS_DIR = ROOT / "evals" / "results"


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


async def evaluate_case(case: dict) -> dict:
    try:
        result = await workflow.ainvoke({
            "question": case["question"],
            "errors": [],
        })

        predicted_intent = result.get("intent", "unknown")
        answer = (
            result.get("final_answer")
            or result.get("document_result")
            or result.get("sql_result")
            or ""
        )

        expected_keywords = case.get("expected_keywords", [])
        normalized_answer = normalize(str(answer))

        matched_keywords = [
            keyword
            for keyword in expected_keywords
            if normalize(keyword) in normalized_answer
        ]

        keyword_coverage = (
            len(matched_keywords) / len(expected_keywords)
            if expected_keywords
            else None
        )

        errors = result.get("errors", [])

        return {
            "id": case["id"],
            "question": case["question"],
            "expected_intent": case["expected_intent"],
            "predicted_intent": predicted_intent,
            "routing_correct": (
                predicted_intent == case["expected_intent"]
            ),
            "answer": str(answer),
            "expected_keywords": expected_keywords,
            "matched_keywords": matched_keywords,
            "keyword_coverage": keyword_coverage,
            "errors": errors,
            "execution_success": not errors and bool(answer),
        }

    except Exception as exc:
        return {
            "id": case["id"],
            "question": case["question"],
            "expected_intent": case["expected_intent"],
            "predicted_intent": "error",
            "routing_correct": False,
            "answer": "",
            "expected_keywords": case.get("expected_keywords", []),
            "matched_keywords": [],
            "keyword_coverage": 0.0,
            "errors": [f"{type(exc).__name__}: {exc}"],
            "execution_success": False,
        }


async def main():
    dataset = json.loads(DATASET_PATH.read_text())

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for case in dataset:
        print(f"Evaluating {case['id']}...")
        results.append(await evaluate_case(case))

    routing_accuracy = (
        sum(row["routing_correct"] for row in results) / len(results)
        if results else 0.0
    )

    keyword_scores = [
        row["keyword_coverage"]
        for row in results
        if row["keyword_coverage"] is not None
    ]

    mean_keyword_coverage = (
        sum(keyword_scores) / len(keyword_scores)
        if keyword_scores else None
    )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(results),
        "routing_accuracy": routing_accuracy,
        "mean_keyword_coverage": mean_keyword_coverage,
        "execution_success_rate": (
            sum(row["execution_success"] for row in results) / len(results)
            if results else 0.0
        ),
        "results": results,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = RESULTS_DIR / f"eval_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=2))

    print(json.dumps({
        "total_cases": report["total_cases"],
        "routing_accuracy": report["routing_accuracy"],
        "mean_keyword_coverage": report["mean_keyword_coverage"],
        "execution_success_rate": report["execution_success_rate"],
        "report": str(report_path),
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
