"""
Medical Report Processing API
Uses local fallback agents for report parsing and processing.
"""

from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import shutil
from typing import Optional, List, Dict
from datetime import datetime
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

from ocr import extract_text
import agents
from db import MedicalDatabase

# Initialize database
db = MedicalDatabase()

# Job tracking
processing_jobs: Dict[str, Dict] = {}
job_lock = threading.Lock()

# Thread pool for background processing
executor = ThreadPoolExecutor(max_workers=4)


# ============== API Endpoints ==============
async def upload_report(request: Request):
    try:
        form = await request.form()
        file = form.get("file")
        if file is None:
            return JSONResponse({"detail": "Missing file"}, status_code=400)

        patient_id = form.get("patient_id")
        language = form.get("language", "Hindi")

        job_id = str(uuid.uuid4())
        temp_path = f"temp_{job_id}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with job_lock:
            processing_jobs[job_id] = {
                "status": "processing",
                "progress": 0,
                "message": "Starting OCR extraction...",
                "created_at": datetime.now().isoformat(),
                "temp_file": temp_path,
                "patient_id": patient_id,
                "language": language
            }

        background = BackgroundTask(process_report_async, job_id)

        return JSONResponse({
            "job_id": job_id,
            "status": "processing",
            "message": "Report processing started. Check status with GET /job/{job_id}",
            "estimated_time": "30-60 seconds"
        }, background=background)

    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


async def get_job_status(request: Request):
    job_id = request.path_params.get("job_id")
    with job_lock:
        if job_id not in processing_jobs:
            return JSONResponse({"detail": "Job not found"}, status_code=404)

        job = processing_jobs[job_id]

        if job["status"] == "completed":
            return JSONResponse({
                "job_id": job_id,
                "status": "completed",
                "progress": 100,
                "message": job.get("message", "Processing complete"),
                "result": job["result"],
                "completed_at": job["completed_at"]
            })

        if job["status"] == "failed":
            return JSONResponse({
                "job_id": job_id,
                "status": "failed",
                "progress": job.get("progress", 0),
                "message": job.get("message", job.get("error", "Processing failed")),
                "error": job.get("error"),
                "failed_at": job.get("failed_at")
            })

        return JSONResponse({
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "message": job["message"],
            "created_at": job["created_at"]
        })


def process_report_async(job_id: str):
    """Background task to process the report"""
    try:
        with job_lock:
            job = processing_jobs[job_id]

        temp_path = job["temp_file"]
        patient_id = job["patient_id"]
        language = job["language"]

        def update_progress(progress: int, message: str):
            with job_lock:
                processing_jobs[job_id]["progress"] = progress
                processing_jobs[job_id]["message"] = message

        update_progress(10, "Extracting text from document...")

        raw_text = extract_text(temp_path)

        if not raw_text or len(raw_text.strip()) < 10:
            raise Exception("Could not extract text from image")

        update_progress(20, "Parsing medical data...")

        initial_state = agents.get_default_state(
            raw_text=raw_text,
            patient_id=patient_id,
            target_lang=language
        )

        update_progress(30, "Running parse agent...")
        parsed_state = agents.parse_agent(initial_state)

        update_progress(40, "Running validation agent...")
        validated_state = agents.validation_agent(parsed_state)

        update_progress(50, "Running summary agent...")
        summary_state = agents.summary_agent(validated_state)

        update_progress(60, "Running simplification agent...")
        simplified_state = agents.simplify_agent(summary_state)

        update_progress(70, "Running temporal analysis agent...")
        temporal_state = agents.temporal_agent(simplified_state)

        update_progress(75, "Running Bayesian analysis...")
        bayesian_state = agents.bayesian_agent(temporal_state)

        update_progress(85, "Running translation agent...")
        translated_state = agents.translate_agent(bayesian_state)

        result = translated_state

        update_progress(95, "Saving results...")

        if patient_id:
            db.save_report(
                patient_id=patient_id,
                report_date=result["report_date"],
                parsed_data=result["parsed_data"],
                summary=result["medical_summary"],
                simple_explanation=result["simplified_explanation"],
                translated=result["translated_explanation"],
                risk_probability=result["risk_probability"]
            )

        response = agents.format_final_response(result)

        try:
            import os
            os.remove(temp_path)
        except:
            pass

        with job_lock:
            processing_jobs[job_id]["status"] = "completed"
            processing_jobs[job_id]["progress"] = 100
            processing_jobs[job_id]["message"] = "Processing complete"
            processing_jobs[job_id]["result"] = response
            processing_jobs[job_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        with job_lock:
            processing_jobs[job_id]["status"] = "failed"
            processing_jobs[job_id]["progress"] = processing_jobs[job_id].get("progress", 0)
            processing_jobs[job_id]["message"] = f"Processing failed: {str(e)}"
            processing_jobs[job_id]["error"] = str(e)
            processing_jobs[job_id]["failed_at"] = datetime.now().isoformat()

        try:
            import os
            os.remove(processing_jobs[job_id]["temp_file"])
        except:
            pass


async def get_patient_history(request: Request):
    patient_id = request.path_params.get("patient_id")
    limit = int(request.query_params.get("limit", 10))
    try:
        reports = db.get_patient_reports(patient_id, limit)
        return JSONResponse({
            "patient_id": patient_id,
            "report_count": len(reports),
            "reports": reports
        })
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


async def get_temporal_analysis(request: Request):
    patient_id = request.path_params.get("patient_id")
    try:
        reports = db.get_patient_reports(patient_id, limit=50)

        if not reports:
            return JSONResponse({
                "patient_id": patient_id,
                "message": "No historical data available",
                "time_series": {},
                "trends": []
            })

        # Build time-series: {test_name: [{date, value, unit, ref_low, ref_high, status}]}
        import re as _re
        time_series = {}

        for report in sorted(reports, key=lambda r: r.get("report_date", "")):
            report_date = report.get("report_date", "")
            try:
                parsed = json.loads(report.get("parsed_data", "{}"))
            except Exception:
                continue

            for lab in parsed.get("lab_values", []):
                test_name = lab.get("test_name", "").strip()
                if not test_name:
                    continue
                try:
                    numeric_value = float(str(lab.get("value", "")).replace(",", ""))
                except Exception:
                    continue

                unit      = lab.get("unit", "")
                ref_range = lab.get("reference_range", "")
                status    = lab.get("status", "unknown")

                # Parse reference range
                ref_low = ref_high = None
                if ref_range:
                    m = _re.search(
                        r"([0-9]+(?:\.[0-9]+)?)\s*(?:–|-|to)\s*([0-9]+(?:\.[0-9]+)?)",
                        ref_range, _re.IGNORECASE
                    )
                    if m:
                        ref_low  = float(m.group(1))
                        ref_high = float(m.group(2))
                    else:
                        lt = _re.search(r"<\s*([0-9]+(?:\.[0-9]+)?)", ref_range)
                        gt = _re.search(r">\s*([0-9]+(?:\.[0-9]+)?)", ref_range)
                        if lt:
                            ref_low, ref_high = 0.0, float(lt.group(1))
                        elif gt:
                            ref_low = float(gt.group(1))

                if test_name not in time_series:
                    time_series[test_name] = []

                time_series[test_name].append({
                    "date":      report_date,
                    "value":     numeric_value,
                    "unit":      unit,
                    "ref_range": ref_range,
                    "ref_low":   ref_low,
                    "ref_high":  ref_high,
                    "status":    status,
                })

        # Only keep tests that appear in at least 1 report (show all for single report too)
        # Sort each test's data by date ascending
        for test in time_series:
            time_series[test].sort(key=lambda x: x["date"])

        # Detect trends across multiple reports
        trend_summary = []
        for test, points in time_series.items():
            if len(points) >= 2:
                first_val = points[0]["value"]
                last_val  = points[-1]["value"]
                change    = last_val - first_val
                pct_change = round((change / first_val) * 100, 1) if first_val != 0 else 0
                direction = "improving" if abs(last_val) < abs(first_val) else "worsening"
                statuses  = [p["status"] for p in points]
                if all(s in ("high", "critical") for s in statuses):
                    pattern = "persistently_high"
                elif all(s == "low" for s in statuses):
                    pattern = "persistently_low"
                elif statuses[-1] in ("high", "critical") and statuses[0] == "normal":
                    pattern = "newly_elevated"
                elif statuses[-1] == "normal" and statuses[0] in ("high", "low", "critical"):
                    pattern = "normalising"
                else:
                    pattern = "fluctuating"

                trend_summary.append({
                    "test":       test,
                    "pattern":    pattern,
                    "direction":  direction,
                    "pct_change": pct_change,
                    "first":      first_val,
                    "last":       last_val,
                    "unit":       points[-1]["unit"],
                    "count":      len(points),
                })

        return JSONResponse({
            "patient_id":   patient_id,
            "total_reports": len(reports),
            "time_series":  time_series,
            "trend_summary": trend_summary,
            "analysis_date": datetime.now().isoformat(),
        })

    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


def analyze_temporal_trends(reports: List[dict]) -> dict:
    trends = []
    alerts = []
    test_values = {}
    for report in reports:
        try:
            parsed = json.loads(report.get("parsed_data", "{}"))
            for lab in parsed.get("lab_values", []):
                test_name = lab.get("test_name", "")
                if test_name not in test_values:
                    test_values[test_name] = []
                test_values[test_name].append({
                    "value": lab.get("value"),
                    "status": lab.get("status"),
                    "date": report.get("report_date")
                })
        except Exception:
            continue

    for test, values in test_values.items():
        if len(values) >= 2:
            statuses = [v["status"] for v in values]
            if all(s == "low" for s in statuses):
                trends.append({
                    "test": test,
                    "pattern": "persistently_low",
                    "occurrences": len(values),
                    "recommendation": f"Consider further investigation for {test}"
                })
            elif all(s == "high" for s in statuses):
                trends.append({
                    "test": test,
                    "pattern": "persistently_high",
                    "occurrences": len(values),
                    "recommendation": f"Monitor {test} levels closely"
                })

    return {
        "patient_id": reports[0].get("patient_id") if reports else None,
        "total_reports": len(reports),
        "trends": trends,
        "alerts": alerts,
        "analysis_date": datetime.now().isoformat()
    }


async def process_text_report(request: Request):
    try:
        form = await request.form()
        text = form.get("text")
        patient_id = form.get("patient_id")
        language = form.get("language", "Hindi")

        if not text:
            return JSONResponse({"detail": "Missing text field"}, status_code=400)

        state = agents.get_default_state(
            raw_text=text,
            patient_id=patient_id,
            target_lang=language
        )

        state = agents.parse_agent(state)
        state = agents.validation_agent(state)
        state = agents.summary_agent(state)
        state = agents.simplify_agent(state)
        state = agents.temporal_agent(state)
        state = agents.bayesian_agent(state)
        state = agents.translate_agent(state)

        response = agents.format_final_response(state)

        return JSONResponse(content=response)

    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


async def retranslate_report(request: Request):
    """Retranslate an already-processed report into a new language without re-uploading."""
    try:
        body = await request.json()
        parsed_data     = body.get("parsed_data", "")
        language        = body.get("language", "Hindi")
        suggestions     = body.get("suggestions", [])
        medical_summary = body.get("medical_summary", "")
        simplified      = body.get("simplified_explanation", "")
        temporal        = body.get("temporal_analysis", "")
        bayesian        = body.get("causal_analysis", "")
        risk            = body.get("risk_probability", 0.0)
        patient_id      = body.get("patient_id")
        report_date     = body.get("report_date", datetime.now().isoformat())
        disease_en      = body.get("disease_explanation_en", "")
        solution_en     = body.get("solution_plan_en", "")

        state = agents.get_default_state("", patient_id=patient_id, target_lang=language)
        state["parsed_data"]            = parsed_data
        state["medical_summary"]        = medical_summary
        state["simplified_explanation"] = simplified
        state["temporal_analysis"]      = temporal
        state["bayesian_analysis"]      = bayesian
        state["risk_probability"]       = risk
        state["suggestions"]            = suggestions
        state["target_language"]        = language
        state["report_date"]            = report_date
        state["disease_explanation_en"] = disease_en
        state["solution_plan_en"]       = solution_en

        state = agents.translate_agent(state)
        response = agents.format_final_response(state)
        return JSONResponse(content=response)

    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


app = Starlette(debug=True, routes=[
    Route("/", lambda request: JSONResponse({
        "message": "Medical CDSS API - Clinical Decision Support System",
        "version": "2.0.0",
        "endpoints": {
            "upload": "/upload",
            "job_status": "/job/{job_id}",
            "patient_history": "/patient/{patient_id}/history",
            "temporal_analysis": "/patient/{patient_id}/temporal",
            "languages": "/languages",
            "health": "/health"
        }
    })),
    Route("/health", lambda request: JSONResponse({"status": "healthy", "timestamp": datetime.now().isoformat()})),
    Route("/languages", lambda request: JSONResponse({
        "languages": [
            {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
            {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
            {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
            {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
            {"code": "mr", "name": "Marathi", "native_name": "मराठी"},
            {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી"},
            {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
            {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം"},
            {"code": "pa", "name": "Punjabi", "native_name": "ਪੰਜਾਬੀ"},
            {"code": "or", "name": "Odia", "native_name": "ଓଡ଼ିଆ"},
            {"code": "as", "name": "Assamese", "native_name": "অসমীয়া"},
            {"code": "ur", "name": "Urdu", "native_name": "اردو"},
        ]
    })),
    Route("/upload", upload_report, methods=["POST"]),
    Route("/retranslate", retranslate_report, methods=["POST"]),
    Route("/job/{job_id}", get_job_status),
    Route("/patient/{patient_id}/history", get_patient_history),
    Route("/patient/{patient_id}/temporal", get_temporal_analysis),
    Route("/text/", process_text_report, methods=["POST"]),
])

import os as _os

# In production, set ALLOWED_ORIGINS=https://your-site.netlify.app
# Leave unset (or "*") for local development
_raw_origins = _os.getenv("ALLOWED_ORIGINS", "*")
_allow_origins = (
    [o.strip() for o in _raw_origins.split(",")]
    if _raw_origins != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=120)
