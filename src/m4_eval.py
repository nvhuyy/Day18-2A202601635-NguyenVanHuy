from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    try:
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )
        from ragas.run_config import RunConfig
        from datasets import Dataset

        from langchain_openai import ChatOpenAI
        from langchain_huggingface import HuggingFaceEmbeddings

        # ---------------------------------------------------------
        # 1. Groq API key
        # ---------------------------------------------------------
        groq_api_key = os.getenv("OPENAI_API_KEY")

        if not groq_api_key:
            raise ValueError(
                "groq_api_key chưa được set trong environment."
            )

        # ---------------------------------------------------------
        # 2. Groq LLM
        # ---------------------------------------------------------
        ragas_llm = ChatOpenAI(
            model="ministral-3b-2512",
            api_key=groq_api_key,
            base_url="https://api.mistral.ai/v1",
            temperature=0,
            n=1,
            max_retries=0,
        )

        # ---------------------------------------------------------
        # 3. Local embeddings
        # ---------------------------------------------------------
        ragas_embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # ---------------------------------------------------------
        # 4. Dataset
        # ---------------------------------------------------------
        dataset = Dataset.from_dict(
            {
                "question": questions,
                "answer": answers,
                "contexts": contexts,
                "ground_truth": ground_truths,
            }
        )

        # ---------------------------------------------------------
        # 5. Conservative RunConfig for Groq Free
        #
        # Ragas mặc định max_workers=16 -> có thể bắn nhiều
        # request đồng thời -> rất dễ 429 trên Free tier.
        # ---------------------------------------------------------
        run_config = RunConfig(
            max_workers=1,
            max_retries=3,
            max_wait=60,
            timeout=180,
            log_tenacity=True,
        )

        # ---------------------------------------------------------
        # 6. Evaluate
        # ---------------------------------------------------------
        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
            llm=ragas_llm,
            embeddings=ragas_embeddings,
            run_config=run_config,
            raise_exceptions=False,
        )

        # ---------------------------------------------------------
        # 7. Convert result -> pandas
        # ---------------------------------------------------------
        df = result.to_pandas()

        per_question = [
            EvalResult(
                question=row["question"],
                answer=row["answer"],
                contexts=row["contexts"],
                ground_truth=row["ground_truth"],
                faithfulness=float(row.get("faithfulness", 0.0)),
                answer_relevancy=float(row.get("answer_relevancy", 0.0)),
                context_precision=float(row.get("context_precision", 0.0)),
                context_recall=float(row.get("context_recall", 0.0)),
            )
            for _, row in df.iterrows()
        ]

        def mean_metric(name: str) -> float:
            values = [getattr(r, name) for r in per_question]
            return sum(values) / len(values) if values else 0.0

        return {
            "faithfulness": mean_metric("faithfulness"),
            "answer_relevancy": mean_metric("answer_relevancy"),
            "context_precision": mean_metric("context_precision"),
            "context_recall": mean_metric("context_recall"),
            "per_question": per_question,
        }

    except Exception as e:
        print(f"  ⚠️  RAGAS evaluation failed: {e}")

        return {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_precision": 0.0,
            "context_recall": 0.0,
            "per_question": [],
        }


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    # : Implement failure analysis
    # 1. diagnostic_tree = {
    #        "faithfulness": ("LLM hallucinating", "Tighten prompt, lower temperature"),
    #        "context_recall": ("Missing relevant chunks", "Improve chunking or add BM25"),
    #        "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filter"),
    #        "answer_relevancy": ("Answer doesn't match question", "Improve prompt template"),
    #    }
    # 2. For each EvalResult: compute avg of 4 metrics, find worst_metric
    # 3. Sort by avg ascending → take bottom_n
    # 4. Return [{"question": ..., "worst_metric": ..., "score": ...,
    #             "diagnosis": ..., "suggested_fix": ...}]
    diagnostic_tree = {
        "faithfulness": (
            "LLM hallucinating",
            "Tighten prompt, lower temperature",
        ),
        "context_recall": (
            "Missing relevant chunks",
            "Improve chunking or add BM25",
        ),
        "context_precision": (
            "Too many irrelevant chunks",
            "Add reranking or metadata filter",
        ),
        "answer_relevancy": (
            "Answer doesn't match question",
            "Improve prompt template",
        ),
    }

    if not eval_results:
        return []

    metric_names = [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ]

    analyzed = []

    for result in eval_results:
        scores = {
            metric: getattr(result, metric)
            for metric in metric_names
        }

        avg_score = sum(scores.values()) / len(scores)

        worst_metric = min(
            scores,
            key=scores.get,
        )

        diagnosis, suggested_fix = diagnostic_tree[worst_metric]

        analyzed.append({
            "question": result.question,
            "worst_metric": worst_metric,
            "score": float(scores[worst_metric]),
            "diagnosis": diagnosis,
            "suggested_fix": suggested_fix,
            "_avg_score": avg_score,
        })

    # Câu có average score thấp nhất đứng trước
    analyzed.sort(key=lambda x: x["_avg_score"])

    failures = analyzed[:bottom_n]

    # Không cần expose field nội bộ
    for failure in failures:
        failure.pop("_avg_score", None)

    return failures


def save_report(results: dict, failures: list[dict], path: str = "ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
