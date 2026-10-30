
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
)
from deepeval.test_case import LLMTestCase

from app.graph.workflow import workflow

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals" / "rag_dataset.json"
RESULTS_DIR = ROOT / "evals" / "results"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_langfuse():
    """Initialize Langfuse when enabled; allow offline evaluation otherwise."""
    if os.getenv("LANGFUSE_ENABLED", "false").lower() != "true":
        logger.info("Langfuse disabled; running evaluation without tracing.")
        return None

    if not (
        os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
    ):
        logger.warning(
            "Langfuse is enabled but credentials are missing. "
            "Continuing without Langfuse."
        )
        return None

    try:
        from langfuse import get_client

        client = get_client()
        logger.info("Langfuse client initialized.")
        return client
    except Exception:
        logger.exception("Langfuse initialization failed.")
        return None


def build_metrics():
    return [
        ContextualPrecisionMetric(threshold=0.7),
        ContextualRecallMetric(threshold=0.7),
        ContextualRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.7),
    ]


async def evaluate_case(case, metrics, langfuse):
    """Run one RAG case, record metric scores, and preserve errors."""

    case_result = {
        "id": case["id"],
        "question": case["question"],
        "intent": None,
        "errors": [],
        "metrics": {},
    }

    # Create an evaluation trace when Langfuse is available.
    if langfuse is not None:
        observation_context = langfuse.start_as_current_observation(
            as_type="span",
            name=f"datanexus-rag-eval-{case['id']}",
            input={
                "question": case["question"],
                "dataset_case_id": case["id"],
            },
            metadata={
                "evaluation_type": "rag",
                "dataset_version": "v1",
            },
        )
    else:
        observation_context = None

    try:
        if observation_context is not None:
            span = observation_context.__enter__()
        else:
            span = None

        try:
            output = await workflow.ainvoke({
                "question": case["question"],
                "errors": [],
            })

            answer = str(
                output.get("document_result")
                or output.get("final_answer")
                or ""
            )

            retrieved_context = output.get("retrieved_context", [])
            retrieved_context = [
                str(item) for item in retrieved_context
            ]

            case_result["intent"] = output.get("intent")
            case_result["errors"].extend(
                output.get("errors", [])
            )

            test_case = LLMTestCase(
                input=case["question"],
                actual_output=answer,
                expected_output=case["expected_answer"],
                context=case["reference_context"],
                retrieval_context=retrieved_context,
            )

            case_result["retrieved_context_count"] = len(
                retrieved_context
            )

            case_result["metrics"] = {}

            for metric in metrics:
                metric_name = metric.__class__.__name__

                try:
                    metric.measure(test_case)

                    score = metric.score
                    passed = metric.is_successful()
                    reason = metric.reason

                    case_result["metrics"][metric_name] = {
                        "score": score,
                        "passed": passed,
                        "reason": reason,
                    }

                    # Attach the score to this evaluation observation.
                    if span is not None and score is not None:
                        try:
                            span.score(
                                name=metric_name,
                                value=float(score),
                                data_type="NUMERIC",
                                comment=str(reason or "")[:500] or None,
                            )
                        except Exception as exc:
                            logger.exception(
                                "Could not record %s in Langfuse",
                                metric_name,
                            )
                            case_result["errors"].append(
                                f"Langfuse score error ({metric_name}): "
                                f"{type(exc).__name__}: {exc}"
                            )

                except Exception as exc:
                    logger.exception(
                        "Metric %s failed for case %s",
                        metric_name,
                        case["id"],
                    )
                    case_result["metrics"][metric_name] = {
                        "error": f"{type(exc).__name__}: {exc}"
                    }

            if span is not None:
                span.update(output={
                    "answer": answer,
                    "intent": case_result["intent"],
                    "retrieved_context_count": len(retrieved_context),
                    "metrics": case_result["metrics"],
                    "errors": case_result["errors"],
                })

        except Exception as exc:
            logger.exception(
                "Evaluation case %s failed", case["id"]
            )
            case_result["errors"].append(
                f"{type(exc).__name__}: {exc}"
            )

            if span is not None:
                try:
                    span.update(
                        level="ERROR",
                        status_message=str(exc)[:500],
                        output={"errors": case_result["errors"]},
                    )
                except Exception:
                    logger.exception(
                        "Could not update failed evaluation span"
                    )

    finally:
        if observation_context is not None:
            try:
                observation_context.__exit__(None, None, None)
            except Exception:
                logger.exception(
                    "Could not close Langfuse observation"
                )

    return case_result


async def main():
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    langfuse = initialize_langfuse()
    results = []

    try:
        for case in cases:
            result = await evaluate_case(
                case=case,
                metrics=build_metrics(),
                langfuse=langfuse,
            )
            results.append(result)

        metric_names = [
            metric.__class__.__name__
            for metric in build_metrics()
        ]

        metric_summary = {}

        for metric_name in metric_names:
            scores = [
                result["metrics"][metric_name]["score"]
                for result in results
                if metric_name in result["metrics"]
                and isinstance(
                    result["metrics"][metric_name].get("score"),
                    (int, float),
                )
            ]

            metric_summary[metric_name] = {
                "mean_score": (
                    sum(scores) / len(scores) if scores else None
                ),
                "scored_cases": len(scores),
            }

        report = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset_version": "v1",
            "total_cases": len(results),
            "metric_summary": metric_summary,
            "results": results,
        }

        timestamp = datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
        report_path = RESULTS_DIR / f"rag_eval_{timestamp}.json"

        report_path.write_text(
            json.dumps(report, indent=2, default=str),
            encoding="utf-8",
        )

        print(json.dumps({
            "total_cases": report["total_cases"],
            "metric_summary": metric_summary,
            "report": str(report_path),
        }, indent=2))

    finally:
        if langfuse is not None:
            try:
                langfuse.flush()
                logger.info("Langfuse events flushed.")
            except Exception:
                logger.exception("Langfuse flush failed.")


if __name__ == "__main__":
    asyncio.run(main())
