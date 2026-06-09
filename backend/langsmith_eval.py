"""
LangSmith Evaluation Metrics for Medical Report Processing Pipeline
====================================================================
Evaluates each agent stage:
  parse_agent · validation_agent · summary_agent · simplify_agent
  temporal_agent · bayesian_agent · translate_agent

Run:
    pip install langsmith
    export LANGSMITH_API_KEY=<your-key>
    export LANGSMITH_PROJECT=medical-explanation   # optional
    python langsmith_eval.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any

# ── LangSmith imports ─────────────────────────────────────────────────────────
from langsmith import Client, evaluate
from langsmith.schemas import Example, Run

# ── Local agents ──────────────────────────────────────────────────────────────
import agents


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  DATASET  –  synthetic medical reports used as eval inputs
# ═══════════════════════════════════════════════════════════════════════════════

DATASET_NAME = "medical-report-eval-v1"

EVAL_CASES: list[dict] = [
    # ── Case 1: typical CBC report with abnormal values ──────────────────────
    {
        "id": "case_cbc_abnormal",
        "raw_text": """
Patient Name: Ramesh Kumar
Report Date: 2024-01-15
Test Type: Complete Blood Count

Hemoglobin: 8.5 g/dL (Reference: 13.5-17.5 g/dL)
WBC: 12500 /uL (Reference: 4500-11000 /uL)
Platelets: 450000 /uL (Reference: 150000-400000 /uL)
RBC: 3.2 million/uL (Reference: 4.5-5.9 million/uL)
Hematocrit: 28% (Reference: 41-53%)

Findings: Microcytic hypochromic anemia
Diagnosis: Iron Deficiency Anemia
""",
        "target_language": "Hindi",
        "expected": {
            "has_patient_name": True,
            "has_lab_values": True,
            "min_lab_count": 4,
            "has_abnormal_labs": True,
            "has_summary": True,
            "has_simplified": True,
            "has_translation": True,
        },
    },

    # ── Case 2: lipid panel – normal values ──────────────────────────────────
    {
        "id": "case_lipid_normal",
        "raw_text": """
Patient Name: Priya Sharma
Date: 2024-02-10
Lab Type: Lipid Profile

Total Cholesterol: 185 mg/dL (Reference: <200 mg/dL)
LDL: 110 mg/dL (Reference: <130 mg/dL)
HDL: 55 mg/dL (Reference: >40 mg/dL)
Triglycerides: 140 mg/dL (Reference: <150 mg/dL)

Diagnosis: Normal lipid profile
""",
        "target_language": "Hindi",
        "expected": {
            "has_patient_name": True,
            "has_lab_values": True,
            "min_lab_count": 3,
            "has_abnormal_labs": False,
            "has_summary": True,
            "has_simplified": True,
            "has_translation": True,
        },
    },

    # ── Case 3: diabetes panel with critical glucose ──────────────────────────
    {
        "id": "case_diabetes_critical",
        "raw_text": """
Name: Suresh Patel
Report Date: 2024-03-05
Test: Diabetes Panel

Fasting Blood Glucose: 320 mg/dL (Reference: 70-100 mg/dL)
HbA1c: 11.5% (Reference: <5.7%)
Insulin: 45 uIU/mL (Reference: 2-25 uIU/mL)
C-Peptide: 3.8 ng/mL (Reference: 0.5-2.0 ng/mL)

Findings: Severely elevated fasting glucose
Diagnosis: Type 2 Diabetes Mellitus - Poorly Controlled
""",
        "target_language": "Bengali",
        "expected": {
            "has_patient_name": True,
            "has_lab_values": True,
            "min_lab_count": 3,
            "has_abnormal_labs": True,
            "has_summary": True,
            "has_simplified": True,
            "has_translation": True,
        },
    },

    # ── Case 4: thyroid panel ─────────────────────────────────────────────────
    {
        "id": "case_thyroid",
        "raw_text": """
Patient: Anjali Singh
Date: 2024-04-20
Lab Type: Thyroid Function Test

TSH: 8.9 mIU/L (Reference: 0.4-4.0 mIU/L)
Free T4: 0.6 ng/dL (Reference: 0.8-1.8 ng/dL)
Free T3: 2.1 pg/mL (Reference: 2.3-4.2 pg/mL)

Diagnosis: Hypothyroidism
""",
        "target_language": "Tamil",
        "expected": {
            "has_patient_name": True,
            "has_lab_values": True,
            "min_lab_count": 2,
            "has_abnormal_labs": True,
            "has_summary": True,
            "has_simplified": True,
            "has_translation": True,
        },
    },

    # ── Case 5: minimal / ambiguous report ───────────────────────────────────
    {
        "id": "case_minimal",
        "raw_text": "Blood test result: Hemoglobin 10.2. Patient advised to take iron.",
        "target_language": "Hindi",
        "expected": {
            "has_patient_name": False,
            "has_lab_values": True,
            "min_lab_count": 1,
            "has_abnormal_labs": True,
            "has_summary": True,
            "has_simplified": True,
            "has_translation": True,
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  PIPELINE RUNNER  –  executes the full agent chain
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline(inputs: dict) -> dict:
    """
    Execute the complete medical report processing pipeline and return
    the final formatted response.
    """
    raw_text = inputs["raw_text"]
    target_language = inputs.get("target_language", "Hindi")

    state = agents.get_default_state(
        raw_text=raw_text,
        patient_id=inputs.get("patient_id"),
        target_lang=target_language,
    )

    t0 = time.perf_counter()

    state = agents.parse_agent(state)
    state = agents.validation_agent(state)
    state = agents.summary_agent(state)
    state = agents.simplify_agent(state)
    state = agents.temporal_agent(state)
    state = agents.bayesian_agent(state)
    state = agents.translate_agent(state)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    result = agents.format_final_response(state)
    result["__pipeline_latency_ms"] = round(elapsed_ms, 2)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  EVALUATORS  –  one function per metric
# ═══════════════════════════════════════════════════════════════════════════════

# ── 3a. Parse quality ─────────────────────────────────────────────────────────

def eval_parse_has_lab_values(run: Run, example: Example) -> dict:
    """Checks that parsed_data contains at least one lab value."""
    output = run.outputs or {}
    parsed_str = output.get("parsed_data", "")
    try:
        parsed = json.loads(parsed_str)
        labs = parsed.get("lab_values", [])
        score = 1 if len(labs) >= 1 else 0
    except Exception:
        score = 0
    return {"key": "parse_has_lab_values", "score": score}


def eval_parse_lab_count(run: Run, example: Example) -> dict:
    """Score based on how many lab values were extracted (normalised 0–1)."""
    expected_min = (example.outputs or {}).get("min_lab_count", 1)
    output = run.outputs or {}
    parsed_str = output.get("parsed_data", "")
    try:
        parsed = json.loads(parsed_str)
        found = len(parsed.get("lab_values", []))
        score = min(1.0, found / max(expected_min, 1))
    except Exception:
        score = 0.0
    return {"key": "parse_lab_count_score", "score": score}


def eval_parse_patient_name(run: Run, example: Example) -> dict:
    """Checks that patient_name is extracted when the report contains one."""
    expected_has = (example.outputs or {}).get("has_patient_name", False)
    output = run.outputs or {}
    parsed_str = output.get("parsed_data", "")
    try:
        parsed = json.loads(parsed_str)
        found = bool(parsed.get("patient_name"))
    except Exception:
        found = False

    if not expected_has:
        # Not expected – pass if not found; partial credit if found anyway
        score = 1.0 if not found else 0.5
    else:
        score = 1.0 if found else 0.0
    return {"key": "parse_patient_name", "score": score}


# ── 3b. Validation ────────────────────────────────────────────────────────────

def eval_validation_passes(run: Run, example: Example) -> dict:
    """Pipeline should always produce a non-empty validation result."""
    output = run.outputs or {}
    val = output.get("validation", "")
    score = 1 if val and len(val.strip()) > 10 else 0
    return {"key": "validation_result_present", "score": score}


def eval_validation_flags_abnormal(run: Run, example: Example) -> dict:
    """If the report has abnormal labs, the validation should mention them."""
    expected_abnormal = (example.outputs or {}).get("has_abnormal_labs", False)
    output = run.outputs or {}
    val = output.get("validation", "").lower()
    flags = any(kw in val for kw in ["abnormal", "high", "low", "critical", "outside", "attention"])

    if not expected_abnormal:
        score = 1.0  # no abnormal labs – validation may or may not flag
    else:
        score = 1.0 if flags else 0.0
    return {"key": "validation_flags_abnormal", "score": score}


# ── 3c. Summary quality ───────────────────────────────────────────────────────

def eval_summary_present(run: Run, example: Example) -> dict:
    """Medical summary must be non-empty."""
    output = run.outputs or {}
    summary = output.get("medical_summary", "")
    score = 1 if summary and len(summary.strip()) > 50 else 0
    return {"key": "summary_present", "score": score}


def eval_summary_mentions_abnormals(run: Run, example: Example) -> dict:
    """If there are abnormal results the summary should reference them."""
    expected_abnormal = (example.outputs or {}).get("has_abnormal_labs", False)
    if not expected_abnormal:
        return {"key": "summary_mentions_abnormals", "score": 1.0}

    output = run.outputs or {}
    summary = output.get("medical_summary", "").lower()
    found = any(kw in summary for kw in ["abnormal", "high", "low", "critical", "attention", "elevated", "decreased"])
    return {"key": "summary_mentions_abnormals", "score": 1.0 if found else 0.0}


def eval_summary_length(run: Run, example: Example) -> dict:
    """Summary should be detailed (>= 200 chars) for reports with data."""
    output = run.outputs or {}
    summary = output.get("medical_summary", "")
    score = min(1.0, len(summary) / 200)
    return {"key": "summary_length_score", "score": round(score, 2)}


# ── 3d. Simplified explanation quality ───────────────────────────────────────

def eval_simplified_present(run: Run, example: Example) -> dict:
    """Patient-friendly explanation must be non-empty."""
    output = run.outputs or {}
    simp = output.get("simple_explanation", "")
    score = 1 if simp and len(simp.strip()) > 50 else 0
    return {"key": "simplified_present", "score": score}


def eval_simplified_plain_language(run: Run, example: Example) -> dict:
    """
    Heuristic: plain language avoids dense medical jargon.
    Score = 1 if the simplified text contains at least one of the
    expected lay-English signal words/phrases.
    """
    output = run.outputs or {}
    simp = output.get("simple_explanation", "").lower()
    plain_signals = [
        "means", "this is", "your", "body", "blood", "normal", "low", "high",
        "doctor", "recommend", "suggest", "eat", "drink", "rest", "exercise",
        "follow", "check", "attention needed", "good news",
    ]
    hits = sum(1 for s in plain_signals if s in simp)
    score = min(1.0, hits / 3)
    return {"key": "simplified_plain_language", "score": round(score, 2)}


def eval_simplified_length(run: Run, example: Example) -> dict:
    """Simplified explanation should be meaningful (>= 150 chars)."""
    output = run.outputs or {}
    simp = output.get("simple_explanation", "")
    score = min(1.0, len(simp) / 150)
    return {"key": "simplified_length_score", "score": round(score, 2)}


# ── 3e. Translation quality ───────────────────────────────────────────────────

def eval_translation_present(run: Run, example: Example) -> dict:
    """Translated explanation must be non-empty when a non-English language is requested."""
    output = run.outputs or {}
    lang = output.get("target_language", "Hindi")
    trans = output.get("translated_explanation", "")
    if lang.lower() == "english":
        return {"key": "translation_present", "score": 1.0}
    score = 1.0 if trans and len(trans.strip()) > 20 else 0.0
    return {"key": "translation_present", "score": score}


def eval_translation_differs_from_english(run: Run, example: Example) -> dict:
    """
    For non-English targets, the translated text should differ from the
    English simple explanation (a proxy for actual translation).
    """
    output = run.outputs or {}
    lang = output.get("target_language", "Hindi")
    if lang.lower() == "english":
        return {"key": "translation_differs", "score": 1.0}

    simp = output.get("simple_explanation", "")
    trans = output.get("translated_explanation", "")
    if not simp or not trans:
        return {"key": "translation_differs", "score": 0.0}

    # Normalised edit-distance proxy: identical → score 0
    overlap = sum(c in trans for c in simp[:100]) / max(len(simp[:100]), 1)
    score = round(1.0 - overlap, 2)
    return {"key": "translation_differs", "score": max(0.0, score)}


# ── 3f. Risk & Bayesian analysis ─────────────────────────────────────────────

def eval_risk_probability_range(run: Run, example: Example) -> dict:
    """risk_probability must be between 0 and 1."""
    output = run.outputs or {}
    risk = output.get("risk_probability", -1)
    try:
        risk = float(risk)
        score = 1.0 if 0.0 <= risk <= 1.0 else 0.0
    except (TypeError, ValueError):
        score = 0.0
    return {"key": "risk_probability_valid_range", "score": score}


def eval_risk_nonzero_for_abnormal(run: Run, example: Example) -> dict:
    """When abnormal labs are present, risk should be > 0."""
    expected_abnormal = (example.outputs or {}).get("has_abnormal_labs", False)
    if not expected_abnormal:
        return {"key": "risk_nonzero_for_abnormal", "score": 1.0}

    output = run.outputs or {}
    risk = output.get("risk_probability", 0)
    try:
        score = 1.0 if float(risk) > 0 else 0.0
    except (TypeError, ValueError):
        score = 0.0
    return {"key": "risk_nonzero_for_abnormal", "score": score}


def eval_causal_analysis_present(run: Run, example: Example) -> dict:
    """Bayesian / causal analysis output should exist."""
    output = run.outputs or {}
    causal = output.get("causal_analysis", "")
    score = 1 if causal and len(causal.strip()) > 20 else 0
    return {"key": "causal_analysis_present", "score": score}


# ── 3g. Suggestions quality ───────────────────────────────────────────────────

def eval_suggestions_present(run: Run, example: Example) -> dict:
    """suggestions list should be non-empty for reports with lab values."""
    output = run.outputs or {}
    suggs = output.get("suggestions", [])
    score = 1 if isinstance(suggs, list) and len(suggs) > 0 else 0
    return {"key": "suggestions_present", "score": score}


def eval_suggestions_are_strings(run: Run, example: Example) -> dict:
    """Each suggestion should be a non-empty string."""
    output = run.outputs or {}
    suggs = output.get("suggestions", [])
    if not suggs:
        return {"key": "suggestions_are_strings", "score": 0.0}
    valid = sum(1 for s in suggs if isinstance(s, str) and len(s.strip()) > 5)
    score = valid / len(suggs)
    return {"key": "suggestions_are_strings", "score": round(score, 2)}


# ── 3h. End-to-end pipeline health ───────────────────────────────────────────

def eval_no_error_keys(run: Run, example: Example) -> dict:
    """Output should not contain error/exception keys."""
    output = run.outputs or {}
    has_error = any(k in output for k in ("error", "exception", "traceback"))
    return {"key": "no_error_keys", "score": 0 if has_error else 1}


def eval_latency_under_30s(run: Run, example: Example) -> dict:
    """
    Pipeline should complete within 30 seconds.
    Score: 1.0 if < 10 s, degrades linearly to 0 at 30 s.
    """
    output = run.outputs or {}
    latency_ms = output.get("__pipeline_latency_ms", 0)
    latency_s = latency_ms / 1000
    if latency_s <= 10:
        score = 1.0
    elif latency_s >= 30:
        score = 0.0
    else:
        score = round(1.0 - (latency_s - 10) / 20, 2)
    return {"key": "latency_under_30s", "score": score}


def eval_all_required_keys_present(run: Run, example: Example) -> dict:
    """
    The final response dict must contain all required top-level keys.
    """
    required = {
        "status", "parsed_data", "validation", "medical_summary",
        "simple_explanation", "translated_explanation", "target_language",
        "risk_probability", "suggestions",
    }
    output = run.outputs or {}
    missing = required - set(output.keys())
    score = round(1 - len(missing) / len(required), 2)
    return {"key": "all_required_keys_present", "score": score}


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  REGISTER ALL EVALUATORS
# ═══════════════════════════════════════════════════════════════════════════════

ALL_EVALUATORS = [
    # Parse
    eval_parse_has_lab_values,
    eval_parse_lab_count,
    eval_parse_patient_name,
    # Validation
    eval_validation_passes,
    eval_validation_flags_abnormal,
    # Summary
    eval_summary_present,
    eval_summary_mentions_abnormals,
    eval_summary_length,
    # Simplified
    eval_simplified_present,
    eval_simplified_plain_language,
    eval_simplified_length,
    # Translation
    eval_translation_present,
    eval_translation_differs_from_english,
    # Risk / Bayesian
    eval_risk_probability_range,
    eval_risk_nonzero_for_abnormal,
    eval_causal_analysis_present,
    # Suggestions
    eval_suggestions_present,
    eval_suggestions_are_strings,
    # Pipeline health
    eval_no_error_keys,
    eval_latency_under_30s,
    eval_all_required_keys_present,
]


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  DATASET HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def create_or_get_dataset(client: Client) -> str:
    """
    Create the LangSmith dataset if it doesn't exist, and return its name.
    Each call is idempotent – existing examples are not duplicated.
    """
    existing_datasets = [d.name for d in client.list_datasets()]
    if DATASET_NAME not in existing_datasets:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Synthetic medical reports for evaluating the Medical Explanation pipeline",
        )
        print(f"Created dataset: {DATASET_NAME}")
    else:
        print(f"Using existing dataset: {DATASET_NAME}")

    # Check existing example IDs to avoid duplicates
    existing_ids = {
        e.metadata.get("case_id")
        for e in client.list_examples(dataset_name=DATASET_NAME)
        if e.metadata
    }

    for case in EVAL_CASES:
        if case["id"] in existing_ids:
            continue
        client.create_example(
            inputs={"raw_text": case["raw_text"], "target_language": case["target_language"]},
            outputs=case["expected"],
            dataset_name=DATASET_NAME,
            metadata={"case_id": case["id"]},
        )
        print(f"  Added example: {case['id']}")

    return DATASET_NAME


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  INDIVIDUAL-AGENT TRACING HELPERS (optional, for deep inspection)
# ═══════════════════════════════════════════════════════════════════════════════

def run_with_tracing(inputs: dict) -> dict:
    """
    Same as run_pipeline but wraps each agent in a child run so you can
    see per-agent timing in the LangSmith trace UI.
    """
    from langsmith import traceable

    @traceable(name="parse_agent", run_type="chain")
    def traced_parse(state):
        return agents.parse_agent(state)

    @traceable(name="validation_agent", run_type="chain")
    def traced_validation(state):
        return agents.validation_agent(state)

    @traceable(name="summary_agent", run_type="chain")
    def traced_summary(state):
        return agents.summary_agent(state)

    @traceable(name="simplify_agent", run_type="chain")
    def traced_simplify(state):
        return agents.simplify_agent(state)

    @traceable(name="temporal_agent", run_type="chain")
    def traced_temporal(state):
        return agents.temporal_agent(state)

    @traceable(name="bayesian_agent", run_type="chain")
    def traced_bayesian(state):
        return agents.bayesian_agent(state)

    @traceable(name="translate_agent", run_type="chain")
    def traced_translate(state):
        return agents.translate_agent(state)

    raw_text = inputs["raw_text"]
    target_language = inputs.get("target_language", "Hindi")

    state = agents.get_default_state(
        raw_text=raw_text,
        patient_id=inputs.get("patient_id"),
        target_lang=target_language,
    )

    t0 = time.perf_counter()
    state = traced_parse(state)
    state = traced_validation(state)
    state = traced_summary(state)
    state = traced_simplify(state)
    state = traced_temporal(state)
    state = traced_bayesian(state)
    state = traced_translate(state)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    result = agents.format_final_response(state)
    result["__pipeline_latency_ms"] = round(elapsed_ms, 2)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  QUICK LOCAL SMOKE-TEST (no LangSmith key needed)
# ═══════════════════════════════════════════════════════════════════════════════

def run_local_smoke_test() -> None:
    """
    Runs every evaluator against every case locally and prints a summary
    table.  Useful for CI or offline development.
    """
    print("\n" + "=" * 70)
    print("LOCAL SMOKE TEST – Medical Report Pipeline Evaluation")
    print("=" * 70)

    total_scores: dict[str, list[float]] = {}

    for case in EVAL_CASES:
        print(f"\n▶  Case: {case['id']}")
        output = run_pipeline({"raw_text": case["raw_text"], "target_language": case["target_language"]})

        # Build minimal Run / Example objects for the evaluators
        class _FakeRun:
            outputs = output

        class _FakeExample:
            outputs = case["expected"]

        fake_run = _FakeRun()
        fake_example = _FakeExample()

        for evaluator in ALL_EVALUATORS:
            result = evaluator(fake_run, fake_example)
            key = result["key"]
            score = result["score"]
            total_scores.setdefault(key, []).append(score)
            status = "✓" if score >= 0.8 else ("~" if score >= 0.5 else "✗")
            print(f"   {status} {key:<45} {score:.2f}")

    print("\n" + "-" * 70)
    print("AGGREGATE AVERAGES")
    print("-" * 70)
    for key, scores in sorted(total_scores.items()):
        avg = sum(scores) / len(scores)
        bar = "█" * int(avg * 20) + "░" * (20 - int(avg * 20))
        print(f"  {key:<45} {bar}  {avg:.2f}")
    print("=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 8.  LANGSMITH EVALUATION RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run_langsmith_evaluation(use_tracing: bool = False) -> None:
    """
    Pushes the dataset to LangSmith (if not already there) and runs the
    full evaluation suite.

    Args:
        use_tracing: If True, each agent call is wrapped in a traceable
                     span so you can inspect per-step timing in the UI.
    """
    api_key = os.environ.get("LANGSMITH_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "LANGSMITH_API_KEY is not set.\n"
            "Export it with:  export LANGSMITH_API_KEY=<your-key>"
        )

    project = os.environ.get("LANGSMITH_PROJECT", "medical-explanation")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", project)

    client = Client(api_key=api_key)
    dataset_name = create_or_get_dataset(client)

    pipeline_fn = run_with_tracing if use_tracing else run_pipeline

    experiment_prefix = f"medical-pipeline-eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"\nStarting LangSmith evaluation – experiment prefix: {experiment_prefix}")

    results = evaluate(
        pipeline_fn,
        data=dataset_name,
        evaluators=ALL_EVALUATORS,
        experiment_prefix=experiment_prefix,
        metadata={
            "pipeline_version": "1.0",
            "agents": [
                "parse_agent", "validation_agent", "summary_agent",
                "simplify_agent", "temporal_agent", "bayesian_agent", "translate_agent",
            ],
        },
        max_concurrency=2,
    )

    print(f"\nEvaluation complete → view results at https://smith.langchain.com")
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 9.  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    # --local flag → run offline smoke-test only
    if "--local" in sys.argv:
        run_local_smoke_test()
    else:
        # Default: run full LangSmith evaluation with per-agent tracing
        run_langsmith_evaluation(use_tracing=True)
