from __future__ import annotations

"""
Module 5: Enrichment Pipeline
==============================
Làm giàu chunks TRƯỚC khi embed: Summarize, HyQA, Contextual Prepend, Auto Metadata.

Test: pytest tests/test_m5.py
"""

import os, sys, re
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENAI_API_KEY


@dataclass
class EnrichedChunk:
    """Chunk đã được làm giàu."""
    original_text: str
    enriched_text: str
    summary: str
    hypothesis_questions: list[str]
    auto_metadata: dict
    method: str  # "contextual", "summary", "hyqa", "full"


# ─── Technique 1: Chunk Summarization ────────────────────


def summarize_chunk(text: str) -> str:
    """
    Tạo summary ngắn cho chunk.
    Embed summary thay vì (hoặc cùng với) raw chunk → giảm noise.
    """
    # : Implement chunk summarization
    # if OPENAI_API_KEY:
    #     try:
    #         from openai import OpenAI
    #         client = OpenAI()
    #         resp = client.chat.completions.create(
    #             model="gpt-4o-mini",
    #             messages=[
    #                 {"role": "system", "content": "Tóm tắt đoạn văn sau trong 2-3 câu ngắn gọn bằng tiếng Việt."},
    #                 {"role": "user", "content": text},
    #             ],
    #             max_tokens=150,
    #         )
    #         return resp.choices[0].message.content.strip()
    #     except Exception as e:
    #         print(f"  ⚠️  OpenAI summarize failed: {e}")
    #
    # Extractive fallback (không cần API):
    # sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    # return ". ".join(sentences[:2]) + "." if sentences else text
    if not text.strip():
        return ""

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI

            client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=OPENAI_API_KEY)

            resp = client.chat.completions.create(
                model="ministral-8b-2512",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tóm tắt đoạn văn sau trong 2-3 câu ngắn gọn "
                            "bằng tiếng Việt."
                        ),
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                max_tokens=150,
            )

            content = resp.choices[0].message.content
            return content.strip() if content else ""

        except Exception as e:
            print(f"  ⚠️  OpenAI summarize failed: {e}")

    # Extractive fallback
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+|\n+", text)
        if s.strip()
    ]

    if not sentences:
        return text.strip()

    selected = sentences[:2]
    summary = " ".join(selected)

    if summary and summary[-1] not in ".!?":
        summary += "."

    return summary


# ─── Technique 2: Hypothesis Question-Answer (HyQA) ─────


def generate_hypothesis_questions(text: str, n_questions: int = 3) -> list[str]:
    """
    Generate câu hỏi mà chunk có thể trả lời.
    Index cả questions lẫn chunk → query match tốt hơn (bridge vocabulary gap).
    """
    # : Implement HyQA generation
    # if OPENAI_API_KEY:
    #     try:
    #         from openai import OpenAI
    #         client = OpenAI()
    #         resp = client.chat.completions.create(
    #             model="gpt-4o-mini",
    #             messages=[
    #                 {"role": "system", "content": f"Dựa trên đoạn văn, tạo {n_questions} câu hỏi mà đoạn văn có thể trả lời. Trả về mỗi câu hỏi trên 1 dòng."},
    #                 {"role": "user", "content": text},
    #             ],
    #             max_tokens=200,
    #         )
    #         questions = resp.choices[0].message.content.strip().split("\n")
    #         return [q.strip().lstrip("0123456789.-) ") for q in questions if q.strip()][:n_questions]
    #     except Exception as e:
    #         print(f"  ⚠️  OpenAI HyQA failed: {e}")
    #
    # Extractive fallback:
    # import re
    # sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if len(s.strip()) > 10]
    # return [f"{s.rstrip('.')}?" for s in sentences[:n_questions]]
    if not text.strip() or n_questions <= 0:
        return []

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI

            client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=OPENAI_API_KEY)

            resp = client.chat.completions.create(
                model="ministral-8b-2512",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Dựa trên đoạn văn, tạo {n_questions} câu hỏi "
                            "mà đoạn văn có thể trả lời. "
                            "Trả về mỗi câu hỏi trên 1 dòng."
                        ),
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                max_tokens=200,
            )

            content = resp.choices[0].message.content or ""

            questions = content.strip().splitlines()

            return [
                q.strip().lstrip("0123456789.-) ")
                for q in questions
                if q.strip()
            ][:n_questions]

        except Exception as e:
            print(f"  ⚠️  OpenAI HyQA failed: {e}")

    # Extractive fallback
    sentences = [
        s.strip()
        for s in re.split(r"[.!?\n]", text)
        if len(s.strip()) > 10
    ]

    return [
        f"{sentence.rstrip('.')}?"
        for sentence in sentences[:n_questions]
    ]


# ─── Technique 3: Contextual Prepend (Anthropic style) ──


def contextual_prepend(text: str, document_title: str = "") -> str:
    """
    Prepend context giải thích chunk nằm ở đâu trong document.
    Anthropic benchmark: giảm 49% retrieval failure (alone).
    """
    # : Implement contextual prepend
    # if OPENAI_API_KEY:
    #     try:
    #         from openai import OpenAI
    #         client = OpenAI()
    #         resp = client.chat.completions.create(
    #             model="gpt-4o-mini",
    #             messages=[
    #                 {"role": "system", "content": "Viết 1 câu ngắn mô tả đoạn văn này nằm ở đâu trong tài liệu và nói về chủ đề gì. Chỉ trả về 1 câu."},
    #                 {"role": "user", "content": f"Tài liệu: {document_title}\n\nĐoạn văn:\n{text}"},
    #             ],
    #             max_tokens=80,
    #         )
    #         context = resp.choices[0].message.content.strip()
    #         return f"{context}\n\n{text}"
    #     except Exception as e:
    #         print(f"  ⚠️  OpenAI contextual failed: {e}")
    #
    # Simple fallback:
    # prefix = f"Trích từ {document_title}. " if document_title else ""
    # return f"{prefix}{text}"
    if not text.strip():
        return ""

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI

            client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=OPENAI_API_KEY)

            resp = client.chat.completions.create(
                model="ministral-8b-2512",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Viết 1 câu ngắn mô tả đoạn văn này nằm ở đâu "
                            "trong tài liệu và nói về chủ đề gì. "
                            "Chỉ trả về 1 câu."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Tài liệu: {document_title}\n\n"
                            f"Đoạn văn:\n{text}"
                        ),
                    },
                ],
                max_tokens=80,
            )

            context = resp.choices[0].message.content

            if context and context.strip():
                return f"{context.strip()}\n\n{text}"

        except Exception as e:
            print(f"  ⚠️  OpenAI contextual failed: {e}")

    # Simple fallback
    prefix = f"Trích từ {document_title}. " if document_title else ""

    return f"{prefix}{text}"


# ─── Technique 4: Auto Metadata Extraction ──────────────


def extract_metadata(text: str) -> dict:
    """
    LLM extract metadata tự động: topic, entities, date_range, category.
    """
    # : Implement auto metadata extraction
    if not text.strip():
        return {
            "topic": "general",
            "entities": [],
            "category": "policy",
            "language": "vi",
        }

    if OPENAI_API_KEY:
        try:
            import json as _json
            from openai import OpenAI

            client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=OPENAI_API_KEY)

            resp = client.chat.completions.create(
                model="ministral-8b-2512",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            'Trích xuất metadata từ đoạn văn. '
                            'Trả về JSON hợp lệ với schema: '
                            '{"topic": "...", '
                            '"entities": ["..."], '
                            '"category": "policy|hr|it|finance", '
                            '"language": "vi|en"}'
                        ),
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                max_tokens=150,
                response_format={"type": "json_object"},
            )
            print(repr(resp.choices[0].message.content))
            content = resp.choices[0].message.content or ""
            parsed = _json.loads(content)

            if not isinstance(parsed, dict):
                raise ValueError("Metadata response không phải object")

            # Đảm bảo schema tối thiểu
            return {
                "topic": parsed.get("topic", "general"),
                "entities": parsed.get("entities", []),
                "category": parsed.get("category", "policy"),
                "language": parsed.get("language", "vi"),
            }

        except Exception as e:
            print(f"  ⚠️  OpenAI metadata failed: {e}")

    return {
        "topic": "general",
        "entities": [],
        "category": "policy",
        "language": "vi",
    }


# ─── Combined Single-Call Mode ───────────────────────────


def _enrich_single_call(text: str, source: str) -> dict:
    """Single LLM call to get summary + questions + context + metadata.

    ⚠️ Cost optimization: 1 API call thay vì 4 calls riêng lẻ.
    """
    # : Implement combined enrichment (1 call/chunk)
    if not text.strip():
        return {}

    if not OPENAI_API_KEY:
        # Fallback không gọi API
        return {
            "summary": summarize_chunk(text),
            "questions": generate_hypothesis_questions(text),
            "context": (
                f"Trích từ {source}."
                if source
                else ""
            ),
            "metadata": extract_metadata(text),
        }

    try:
        import json as _json
        from openai import OpenAI

        client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=OPENAI_API_KEY)

        resp = client.chat.completions.create(
            model="ministral-8b-2512",
            messages=[
                {
                    "role": "system",
                    "content": """Phân tích đoạn văn và trả về JSON hợp lệ:

{
  "summary": "tóm tắt 2-3 câu",
  "questions": [
    "câu hỏi 1",
    "câu hỏi 2",
    "câu hỏi 3"
  ],
  "context": "1 câu mô tả đoạn văn nằm ở đâu trong tài liệu",
  "metadata": {
    "topic": "...",
    "entities": ["..."],
    "category": "policy|hr|it|finance",
    "language": "vi|en"
  }
}

Chỉ trả về JSON, không thêm markdown hoặc giải thích.
""",
                },
                {
                    "role": "user",
                    "content": (
                        f"Tài liệu: {source}\n\n"
                        f"Đoạn văn:\n{text}"
                    ),
                },
            ],
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        print(repr(resp.choices[0].message.content))
        content = resp.choices[0].message.content or ""
        result = _json.loads(content)

        if not isinstance(result, dict):
            raise ValueError("Enrichment response không phải object")

        return {
            "summary": result.get("summary", ""),
            "questions": result.get("questions", [])[:3],
            "context": result.get("context", ""),
            "metadata": result.get("metadata", {}),
        }

    except Exception as e:
        print(f"  ⚠️  Enrichment API failed: {e}")

        # Graceful fallback
        return {
            "summary": summarize_chunk(text),
            "questions": generate_hypothesis_questions(text),
            "context": (
                f"Trích từ {source}."
                if source
                else ""
            ),
            "metadata": extract_metadata(text),
        }


# ─── Full Enrichment Pipeline ────────────────────────────


def enrich_chunks(
    chunks: list[dict],
    methods: list[str] | None = None,
) -> list[EnrichedChunk]:
    """
    Chạy enrichment pipeline trên danh sách chunks. (Đã implement sẵn — dùng functions ở trên)

    Có 2 chế độ:
    - methods cụ thể (["summary"], ["contextual"]...): gọi từng function riêng (tốt cho học/debug)
    - methods=["combined"] hoặc None: 1 API call duy nhất cho tất cả (tốt cho production)

    Args:
        chunks: List of {"text": str, "metadata": dict}
        methods: Default None → combined mode (1 call/chunk).
                 Options: "summary", "hyqa", "contextual", "metadata", "combined"
    """
    if methods is None:
        methods = ["combined"]

    use_combined = "combined" in methods

    enriched = []
    for i, chunk in enumerate(chunks):
        text = chunk["text"]
        source = chunk.get("metadata", {}).get("source", "")

        if use_combined:
            result = _enrich_single_call(text, source)
            summary = result.get("summary", "")
            questions = result.get("questions", [])
            context_line = result.get("context", "")
            enriched_text = f"{context_line}\n\n{text}" if context_line else text
            auto_meta = result.get("metadata", {})
        else:
            summary = summarize_chunk(text) if "summary" in methods else ""
            questions = generate_hypothesis_questions(text) if "hyqa" in methods else []
            enriched_text = contextual_prepend(text, source) if "contextual" in methods else text
            auto_meta = extract_metadata(text) if "metadata" in methods else {}

        enriched.append(EnrichedChunk(
            original_text=text,
            enriched_text=enriched_text,
            summary=summary,
            hypothesis_questions=questions,
            auto_metadata={**chunk.get("metadata", {}), **auto_meta},
            method="+".join(methods),
        ))

        if (i + 1) % 10 == 0 or (i + 1) == len(chunks):
            print(f"  Enriched {i + 1}/{len(chunks)} chunks...", flush=True)

    return enriched


# ─── Main ────────────────────────────────────────────────

if __name__ == "__main__":
    sample = "Nhân viên chính thức được nghỉ phép năm 12 ngày làm việc mỗi năm. Số ngày nghỉ phép tăng thêm 1 ngày cho mỗi 5 năm thâm niên công tác."

    print("=== Enrichment Pipeline Demo ===\n")
    print(f"Original: {sample}\n")

    s = summarize_chunk(sample)
    print(f"Summary: {s}\n")

    qs = generate_hypothesis_questions(sample)
    print(f"HyQA questions: {qs}\n")

    ctx = contextual_prepend(sample, "Sổ tay nhân viên VinUni 2024")
    print(f"Contextual: {ctx}\n")

    meta = extract_metadata(sample)
    print(f"Auto metadata: {meta}")
