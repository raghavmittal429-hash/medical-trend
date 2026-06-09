"""
Enhanced Medical Report Processing Agents
Using fallback processing for medical report parsing and analysis
"""

from typing import TypedDict, List, Optional, Any
from datetime import datetime
import json
import re
import os


# ── Language code map ────────────────────────────────────────
_LANG_CODES = {
    "hindi":     "hi",
    "bengali":   "bn",
    "tamil":     "ta",
    "telugu":    "te",
    "marathi":   "mr",
    "gujarati":  "gu",
    "kannada":   "kn",
    "malayalam": "ml",
    "punjabi":   "pa",
    "odia":      "or",
    "assamese":  "as",
    "urdu":      "ur",
    "english":   "en",
}

def _lang_code(language: str) -> str:
    return _LANG_CODES.get(language.strip().lower(), language.strip().lower()[:2])


def _google_translate(text: str, target_lang_code: str) -> str:
    """
    Translate text using Google Translate's free unofficial endpoint.
    No API key required. Uses the same engine as translate.google.com.
    """
    import urllib.request
    import urllib.parse
    import json as _json

    if not text or not text.strip():
        return text

    # Split long text into chunks ≤ 4500 chars (Google limit)
    def chunks(s, size=4500):
        return [s[i:i+size] for i in range(0, len(s), size)]

    translated_parts = []
    for chunk in chunks(text):
        params = urllib.parse.urlencode({
            "client": "gtx",
            "sl":     "en",
            "tl":     target_lang_code,
            "dt":     "t",
            "q":      chunk,
        })
        url = f"https://translate.googleapis.com/translate_a/single?{params}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        # Response structure: [[[translated, original, ...], ...], ...]
        part = "".join(
            seg[0] for seg in data[0] if seg[0]
        )
        translated_parts.append(part)

    return "".join(translated_parts)


def translate_text(text: str, target_language: str) -> str:
    """
    Translate a single text string.
    Strategy:
      1. Try Claude API if ANTHROPIC_API_KEY is set (best quality for medical text)
      2. Fall back to Google Translate free (no key needed)
      3. Fall back to original text if both fail
    """
    if not text or not text.strip():
        return text
    if target_language.strip().lower() in ("english", "en"):
        return text

    lang_code = _lang_code(target_language)

    # ── Try Claude first if API key available ────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        try:
            import anthropic
            client  = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Translate the following medical text into {target_language}. "
                        "Keep medical terms accurate. Preserve all lists, numbering, "
                        "and paragraph structure. Return ONLY the translated text.\n\n"
                        f"{text}"
                    )
                }]
            )
            return message.content[0].text.strip()
        except Exception:
            pass  # fall through to Google Translate

    # ── Google Translate (free, no key) ──────────────────────
    try:
        return _google_translate(text, lang_code)
    except Exception:
        return text  # last resort: return original


def translate_all(fields: dict, target_language: str) -> dict:
    """
    Translate multiple text fields.
    Strategy:
      1. Claude API (single batch call) if ANTHROPIC_API_KEY set
      2. Google Translate (free) for each field — still fast enough
      3. Original values if everything fails
    Never raises — always returns something usable.
    """
    if not fields or target_language.strip().lower() in ("english", "en"):
        return fields

    lang_code = _lang_code(target_language)
    non_empty = {k: v for k, v in fields.items() if v and str(v).strip()}
    if not non_empty:
        return fields

    result = dict(fields)

    # ── Try Claude batch call first ───────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        try:
            import anthropic
            numbered = {}
            lines = [
                f"Translate ALL sections below into {target_language}.",
                "Keep medical terms accurate. Preserve lists and paragraph structure.",
                "Return ONLY the translated sections in the same numbered format.\n"
            ]
            for i, (key, text) in enumerate(non_empty.items(), 1):
                numbered[i] = key
                lines.append(f"[SECTION {i}]\n{text}\n")

            client  = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=8192,
                messages=[{"role": "user", "content": "\n".join(lines)}]
            )
            raw   = message.content[0].text.strip()
            parts = re.split(r'\[SECTION\s+(\d+)\]', raw)
            i = 1
            while i + 1 < len(parts):
                num  = int(parts[i].strip())
                text = parts[i + 1].strip()
                if num in numbered:
                    result[numbered[num]] = text
                i += 2
            return result
        except Exception:
            pass  # fall through to Google Translate

    # ── Google Translate per field (free, no key) ─────────────
    for key, text in non_empty.items():
        try:
            result[key] = _google_translate(str(text), lang_code)
        except Exception:
            pass  # keep original for this field

    return result


# Keep old names as aliases so nothing else breaks
def translate_with_claude(text: str, target_language: str) -> str:
    return translate_text(text, target_language)

def translate_all_with_claude(fields: dict, target_language: str) -> dict:
    return translate_all(fields, target_language)



# ============== State Definitions ==============
class MedicalReportState(TypedDict, total=False):
    """State for the medical report processing pipeline"""
    raw_text: str
    parsed_data: str
    validation_result: str
    is_valid: bool
    medical_summary: str
    simplified_explanation: str
    translated_explanation: str
    target_language: str
    temporal_analysis: str
    trend_data: str
    bayesian_analysis: str
    causal_explanation: str
    risk_probability: float
    suggestions: List[str]
    translated_suggestions: List[str]
    disease_explanation_en: str
    solution_plan_en: str
    disease_explanation_hi: str
    solution_plan_hi: str
    patient_id: Optional[str]
    report_date: str


class LabValue(TypedDict, total=False):
    test_name: str
    value: str
    unit: str
    reference_range: str
    status: str  # normal, high, low, critical


class ParsedReport(TypedDict, total=False):
    patient_name: Optional[str]
    report_date: Optional[str]
    lab_type: Optional[str]
    lab_values: List[LabValue]
    findings: List[str]
    diagnosis: List[str]


# ============== Agent Helpers ==============
def detect_status_from_line(line: str) -> Optional[str]:
    lowered = line.lower()
    if re.search(r"\b(critical|panic|dangerously abnormal)\b", lowered):
        return "critical"
    if re.search(r"\b(high|elevated|above normal|above range|abnormally high|flag[:\s-]*h)\b", lowered):
        return "high"
    if re.search(r"\b(low|decreased|below normal|below range|abnormally low|flag[:\s-]*l)\b", lowered):
        return "low"
    if re.search(r"(?:\s|\|)(h|hi|\+)\s*$", lowered):
        return "high"
    if re.search(r"(?:\s|\|)(l|lo|-)\s*$", lowered):
        return "low"
    if re.search(r"\b(abnormal|out of range)\b", lowered):
        return "high"
    if re.search(r"\b(normal|within range|within normal)\b", lowered):
        return "normal"
    return None


def parse_numeric_value(value: Any) -> Optional[float]:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def extract_reference_bounds(reference_range: str) -> tuple[Optional[float], Optional[float]]:
    reference = (reference_range or "").replace("–", "-").replace("—", "-")
    if not reference:
        return None, None

    if reference.strip().startswith("<"):
        limit = parse_numeric_value(reference)
        return None, limit
    if reference.strip().startswith(">"):
        limit = parse_numeric_value(reference)
        return limit, None

    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", reference)]
    if len(numbers) >= 2:
        return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])
    return None, None


def infer_status_from_reference(value: Optional[float], reference_range: str) -> Optional[str]:
    if value is None:
        return None
    low, high = extract_reference_bounds(reference_range)
    if low is not None and value < low:
        return "low"
    if high is not None and value > high:
        return "high"
    if low is not None or high is not None:
        return "normal"
    return None


def infer_common_lab_status(test_name: str, value: Optional[float], current_status: str) -> str:
    if value is None or current_status in ["high", "low", "critical"]:
        return current_status

    name = test_name.lower()
    if "a1c" in name or "hba1c" in name:
        if value >= 9:
            return "critical"
        if value >= 5.7:
            return "high"
    if "glucose" in name or "blood sugar" in name or "fbs" in name:
        if value >= 200 or value < 54:
            return "critical"
        if value >= 100:
            return "high"
        if value < 70:
            return "low"
    if "egfr" in name or "gfr" in name:
        if value < 30:
            return "critical"
        if value < 60:
            return "low"
        if value < 90:
            return "low"
    if "ldl" in name:
        if value >= 190:
            return "critical"
        if value >= 130:
            return "high"
    if "hdl" in name:
        if value < 40:
            return "low"
    if "triglyceride" in name:
        if value >= 500:
            return "critical"
        if value >= 150:
            return "high"
    if "cholesterol" in name and "hdl" not in name and "ldl" not in name:
        if value >= 240:
            return "high"
        if value >= 200:
            return "high"
    return current_status


def lab_severity_score(test_name: str, value: Optional[float], status: str, reference_range: str) -> tuple[float, str]:
    name = test_name.lower()
    reason = "flagged outside the expected range"

    if status == "critical":
        return 0.30, "marked as critical"

    low, high = extract_reference_bounds(reference_range)
    if value is not None:
        if high is not None and value > high:
            deviation = (value - high) / max(abs(high), 1)
            return min(0.12 + deviation * 0.35, 0.32), f"above reference range {reference_range}"
        if low is not None and value < low:
            deviation = (low - value) / max(abs(low), 1)
            return min(0.12 + deviation * 0.35, 0.32), f"below reference range {reference_range}"

        if "a1c" in name or "hba1c" in name:
            if value >= 9:
                return 0.30, "A1C is very high"
            if value >= 6.5:
                return 0.22, "A1C is in the diabetes range"
            if value >= 5.7:
                return 0.11, "A1C is in the prediabetes range"
        if "glucose" in name or "blood sugar" in name or "fbs" in name:
            if value >= 200:
                return 0.28, "glucose is very high"
            if value >= 126:
                return 0.20, "glucose is in a diabetes-level range if fasting"
            if value >= 100:
                return 0.10, "glucose is mildly high if fasting"
            if value < 54:
                return 0.30, "glucose is very low"
            if value < 70:
                return 0.16, "glucose is low"
        if "egfr" in name or "gfr" in name:
            if value < 15:
                return 0.36, "eGFR is in kidney failure range"
            if value < 30:
                return 0.30, "eGFR shows severe loss of kidney function"
            if value < 45:
                return 0.24, "eGFR shows moderate to severe kidney function loss"
            if value < 60:
                return 0.18, "eGFR is below 60"
            if value < 90:
                return 0.07, "eGFR is below the usual adult normal range"
        if "ldl" in name:
            if value >= 190:
                return 0.26, "LDL is very high"
            if value >= 160:
                return 0.18, "LDL is high"
            if value >= 130:
                return 0.11, "LDL is above optimal range"
        if "hdl" in name and value < 40:
            return 0.10, "HDL is low"
        if "triglyceride" in name:
            if value >= 500:
                return 0.30, "triglycerides are very high"
            if value >= 200:
                return 0.17, "triglycerides are high"
            if value >= 150:
                return 0.10, "triglycerides are borderline high"
        if "cholesterol" in name and "hdl" not in name and "ldl" not in name:
            if value >= 240:
                return 0.16, "total cholesterol is high"
            if value >= 200:
                return 0.08, "total cholesterol is borderline high"

    if status in ["high", "low"]:
        return 0.12, reason
    return 0.0, "within detected range"


def extract_lab_values(raw_text: str) -> List[LabValue]:
    lab_values: List[LabValue] = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Try to capture lab lines in several common formats, including colon-separated and parenthetical status.
        match = re.match(
            r"^(.+?)[\s:]+([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z%/μ]*)\s*(?:\(([^)]+)\))?\s*(.*)$",
            line,
        )
        if match:
            test_name = match.group(1).strip().rstrip(":")
            value = match.group(2).strip()
            numeric_value = parse_numeric_value(value)
            unit = match.group(3).strip() or ""
            status_hint = match.group(4).strip() if match.group(4) else ""
            reference_range = match.group(5).strip() or ""
            status = detect_status_from_line(line) or "normal"

            # Detect explicit status labels such as (High), (Low), (Critical), (Normal)
            if status_hint:
                lowered = status_hint.lower()
                if "critical" in lowered:
                    status = "critical"
                elif "high" in lowered or "elevated" in lowered or "abnormal" in lowered:
                    status = "high"
                elif "low" in lowered or "decreased" in lowered:
                    status = "low"
                elif "normal" in lowered:
                    status = "normal"
                elif re.search(r"\d", status_hint):
                    reference_range = status_hint

            # If we did not derive status explicitly, infer from reference range if available
            if status == "normal" and reference_range:
                try:
                    measurement = float(value)

                    # Handle range formats like "13-17", "70-100"
                    if "-" in reference_range or "–" in reference_range or "to" in reference_range.lower():
                        parts = re.split(r"\s*(?:-|–|to)\s*", reference_range, flags=re.IGNORECASE)
                        if len(parts) >= 2:
                            try:
                                low = float(re.sub(r"[^\d.]", "", parts[0].strip()))
                                high = float(re.sub(r"[^\d.]", "", parts[1].strip()))
                                if measurement < low:
                                    status = "low"
                                elif measurement > high:
                                    status = "high"
                            except ValueError:
                                pass
                    # Handle formats like "<200", ">50", "<=100"
                    elif reference_range.startswith("<"):
                        try:
                            limit = float(re.sub(r"[^\d.]", "", reference_range[1:].strip()))
                            if measurement >= limit:
                                status = "high"
                        except ValueError:
                            pass
                    elif reference_range.startswith(">"):
                        try:
                            limit = float(re.sub(r"[^\d.]", "", reference_range[1:].strip()))
                            if measurement <= limit:
                                status = "low"
                        except ValueError:
                            pass
                except ValueError:
                    status = "unknown"

            reference_status = infer_status_from_reference(numeric_value, reference_range)
            if reference_status and status in ["normal", "unknown"]:
                status = reference_status
            status = infer_common_lab_status(test_name, numeric_value, status)

            lab_values.append({
                "test_name": test_name,
                "value": value,
                "unit": unit,
                "reference_range": reference_range,
                "status": status
            })

    return lab_values


def extract_field(raw_text: str, patterns: List[str]) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_list(raw_text: str, keywords: List[str]) -> List[str]:
    values: List[str] = []
    for keyword in keywords:
        pattern = rf"{keyword}[:\s]*(.+)"
        matches = re.findall(pattern, raw_text, re.IGNORECASE)
        for value in matches:
            text = value.strip()
            if text:
                values.append(text)
    return values


# ============== Agent 1: Parse Agent ==============
def parse_agent(state: MedicalReportState) -> MedicalReportState:
    raw_text = state.get("raw_text", "")
    parsed: ParsedReport = {
        "patient_name": extract_field(raw_text, [r"Patient Name[:\s]*(.+)", r"Name[:\s]*(.+)"])
        or None,
        "report_date": extract_field(raw_text, [r"Report Date[:\s]*(.+)", r"Date[:\s]*(.+)"])
        or None,
        "lab_type": extract_field(raw_text, [r"Lab Type[:\s]*(.+)", r"Test Type[:\s]*(.+)"])
        or None,
        "lab_values": extract_lab_values(raw_text),
        "findings": extract_list(raw_text, ["Findings", "Finding"]),
        "diagnosis": extract_list(raw_text, ["Diagnosis", "Diagnoses", "Impression"])
    }

    if not parsed["lab_values"]:
        parsed["lab_values"] = [{
            "test_name": "Unknown Test",
            "value": "N/A",
            "unit": "",
            "reference_range": "",
            "status": "unknown"
        }]

    return {
        **state,
        "parsed_data": json.dumps(parsed, indent=2),
        "is_valid": True
    }


# ============== Agent 2: Validation Agent ==============
def validation_agent(state: MedicalReportState) -> MedicalReportState:
    parsed_data = state.get("parsed_data", "")
    parsed_dict: Any = {}
    try:
        parsed_dict = json.loads(parsed_data)
    except Exception:
        parsed_dict = {}

    validation = {
        "is_valid": True,
        "validation_errors": [],
        "warnings": [],
        "confidence_score": 0.95,
        "needs_review": False,
        "review_notes": "Basic validation complete"
    }

    if not parsed_dict.get("lab_values"):
        validation["is_valid"] = False
        validation["validation_errors"].append("No lab values were found")
        validation["confidence_score"] = 0.65
        validation["needs_review"] = True

    return {
        **state,
        "validation_result": json.dumps(validation, indent=2),
        "is_valid": validation["is_valid"]
    }


# ============== Helper Functions ==============

def get_medical_interpretation(test_name: str, status: str, value: str, unit: str) -> str:
    """Provide medical interpretation for lab results"""
    interpretations = {
        # Blood Chemistry
        "glucose": {
            "high": "Elevated blood glucose may indicate diabetes, prediabetes, or stress response. Fasting glucose >126 mg/dL or random >200 mg/dL suggests diabetes.",
            "low": "Low blood glucose (hypoglycemia) can cause symptoms like shakiness, confusion, or loss of consciousness. May be due to diabetes treatment or other conditions.",
            "critical": "Critically abnormal glucose requires immediate medical attention."
        },
        "hemoglobin a1c": {
            "high": "Elevated HbA1c indicates poor long-term blood sugar control. Values >6.5% suggest diabetes. Target is usually <7% for diabetics.",
            "low": "Unusually low HbA1c may indicate frequent hypoglycemia or other conditions affecting red blood cells."
        },
        "creatinine": {
            "high": "Elevated creatinine suggests impaired kidney function. May indicate acute or chronic kidney disease, dehydration, or muscle breakdown.",
            "low": "Low creatinine is usually not concerning and may occur in malnutrition or muscle wasting."
        },
        "bun": {
            "high": "Elevated BUN may indicate kidney dysfunction, dehydration, high protein diet, or gastrointestinal bleeding.",
            "low": "Low BUN may occur in liver disease, malnutrition, or overhydration."
        },
        "egfr": {
            "low": "Low eGFR indicates reduced kidney function. Stage kidney disease based on value: Stage 3 (<60), Stage 4 (<30), Stage 5 (<15).",
            "high": "High eGFR may occur in pregnancy or certain kidney conditions."
        },

        # Lipids
        "total cholesterol": {
            "high": "High cholesterol increases cardiovascular risk. Target <200 mg/dL. May require lifestyle changes or medication.",
            "low": "Very low cholesterol may be due to malnutrition, liver disease, or hyperthyroidism."
        },
        "hdl": {
            "low": "Low HDL ('good' cholesterol) increases heart disease risk. Target >40 mg/dL for men, >50 mg/dL for women.",
            "high": "High HDL is protective against heart disease."
        },
        "ldl": {
            "high": "High LDL ('bad' cholesterol) increases atherosclerosis risk. Target <100 mg/dL for high risk, <130 mg/dL otherwise.",
            "low": "Very low LDL may occur with certain medications or rare genetic conditions."
        },
        "triglycerides": {
            "high": "High triglycerides increase heart disease and pancreatitis risk. May be due to diet, obesity, or metabolic syndrome.",
            "low": "Low triglycerides are generally not concerning."
        },

        # Liver Function
        "alt": {
            "high": "Elevated ALT indicates liver cell damage. May be due to hepatitis, fatty liver, medications, or other liver conditions.",
            "low": "Low ALT is usually not clinically significant."
        },
        "ast": {
            "high": "Elevated AST suggests liver or muscle damage. Often elevated with ALT in liver disease, but isolated elevation may indicate muscle injury.",
            "low": "Low AST is usually not concerning."
        },
        "bilirubin": {
            "high": "Elevated bilirubin may indicate liver disease, bile duct obstruction, or excessive red blood cell breakdown.",
            "low": "Low bilirubin is usually not concerning."
        },

        # Thyroid
        "tsh": {
            "high": "High TSH suggests hypothyroidism. May cause fatigue, weight gain, cold intolerance. Requires thyroid hormone replacement.",
            "low": "Low TSH suggests hyperthyroidism. May cause weight loss, heat intolerance, rapid heartbeat. Requires evaluation for cause."
        },
        "t3": {
            "high": "High T3 may indicate hyperthyroidism or thyroid hormone overdose.",
            "low": "Low T3 may occur in hypothyroidism or non-thyroidal illness."
        },
        "t4": {
            "high": "High T4 suggests hyperthyroidism or thyroid hormone overdose.",
            "low": "Low T4 indicates hypothyroidism or pituitary dysfunction."
        },

        # Blood Count
        "hemoglobin": {
            "high": "High hemoglobin may indicate dehydration, lung disease, or polycythemia. Can increase blood viscosity.",
            "low": "Low hemoglobin (anemia) causes fatigue, weakness. May be due to iron deficiency, blood loss, or chronic disease."
        },
        "hematocrit": {
            "high": "High hematocrit suggests dehydration or increased red blood cell production.",
            "low": "Low hematocrit indicates anemia or blood loss."
        },
        "wbc": {
            "high": "High white blood cell count (leukocytosis) suggests infection, inflammation, or leukemia.",
            "low": "Low white blood cell count (leukopenia) increases infection risk. May be due to medications, autoimmune disease, or bone marrow problems."
        },
        "platelets": {
            "high": "High platelet count (thrombocytosis) may increase clotting risk. Can be due to infection, inflammation, or myeloproliferative disorders.",
            "low": "Low platelet count (thrombocytopenia) increases bleeding risk. May be due to medications, autoimmune disease, or bone marrow problems."
        }
    }

    test_lower = test_name.lower()
    for key, interp in interpretations.items():
        if key in test_lower:
            return interp.get(status, f"Abnormal {test_name} result requires correlation with clinical symptoms and other tests.")

    # Generic interpretation for unknown tests
    if status in ["high", "low", "critical"]:
        return f"Abnormal {test_name} result. Clinical significance depends on your symptoms, medical history, and other test results."
    return ""


def generate_medical_recommendations(abnormal_labs: list, findings: list, diagnosis: list) -> list:
    """Generate comprehensive medical recommendations based on results"""
    recommendations = []

    # Recommendations based on abnormal labs
    if abnormal_labs:
        recommendations.append("Schedule follow-up appointment with your healthcare provider to discuss abnormal results")

        # Specific recommendations based on abnormal tests
        test_names = [lab.get("test_name", "").lower() for lab in abnormal_labs]

        if any("glucose" in name or "a1c" in name for name in test_names):
            recommendations.append("For abnormal glucose/HbA1c: Monitor blood sugar regularly, follow diabetic diet, exercise regularly")
            recommendations.append("Consult endocrinologist if diabetic or prediabetic")

        if any("creatinine" in name or "egfr" in name or "bun" in name for name in test_names):
            recommendations.append("For abnormal kidney function: Stay well-hydrated, avoid nephrotoxic medications, monitor blood pressure")
            recommendations.append("Consult nephrologist if kidney disease is suspected")

        if any("cholesterol" in name or "ldl" in name or "triglyceride" in name for name in test_names):
            recommendations.append("For abnormal lipids: Adopt heart-healthy diet (low saturated fat, high fiber), regular exercise, weight management")
            recommendations.append("Consider cardiology consultation for cardiovascular risk assessment")

        if any("alt" in name or "ast" in name or "bilirubin" in name for name in test_names):
            recommendations.append("For abnormal liver tests: Avoid alcohol, certain medications; eat balanced diet")
            recommendations.append("Further liver evaluation may be needed (ultrasound, additional blood tests)")

        if any("tsh" in name or "t3" in name or "t4" in name for name in test_names):
            recommendations.append("For abnormal thyroid tests: Monitor symptoms of hypo/hyperthyroidism, follow-up thyroid testing as recommended")
            recommendations.append("Consult endocrinologist for thyroid evaluation and treatment")

        if any("hemoglobin" in name or "hematocrit" in name for name in test_names):
            recommendations.append("For abnormal blood counts: Evaluate for anemia or polycythemia causes (iron studies, B12/folate levels)")
            recommendations.append("May need referral to hematologist")

    # Recommendations based on findings and diagnosis
    if findings or diagnosis:
        recommendations.append("Discuss clinical findings and diagnosis with your primary care physician")
        recommendations.append("Bring all previous medical records and current medications to your appointment")

    # General recommendations
    recommendations.append("Maintain healthy lifestyle: balanced diet, regular exercise, adequate sleep, stress management")
    recommendations.append("Keep track of your symptoms and any changes in your health status")
    recommendations.append("Stay up-to-date with recommended preventive screenings and vaccinations")

    return recommendations


def get_simple_explanation(test_name: str, status: str) -> str:
    """Provide simple patient-friendly explanations for common lab tests"""
    explanations = {
        # Blood sugar
        "glucose": {
            "high": "Your blood sugar is higher than normal. This might mean diabetes or prediabetes. Your doctor may recommend diet changes, exercise, or medication.",
            "low": "Your blood sugar is lower than normal. This can cause shakiness or confusion. Make sure you eat regular meals.",
            "critical": "Your blood sugar needs immediate attention. Contact your doctor right away."
        },
        "hemoglobin a1c": {
            "high": "This shows your average blood sugar over the past 3 months is high. It helps diagnose and monitor diabetes.",
            "low": "This is unusually low and may need further evaluation."
        },

        # Kidney function
        "creatinine": {
            "high": "This suggests your kidneys may not be working as well as they should. Your doctor may want more tests.",
            "low": "This is usually not a concern unless very low."
        },
        "bun": {
            "high": "This may indicate kidney problems or dehydration. Your doctor will interpret this with other tests.",
            "low": "This can happen with liver disease or malnutrition."
        },
        "egfr": {
            "low": "This measures how well your kidneys filter waste from your blood. Lower numbers mean reduced kidney function."
        },

        # Cholesterol
        "total cholesterol": {
            "high": "High cholesterol can increase heart disease risk. Your doctor may recommend diet and exercise changes.",
            "low": "Very low cholesterol is usually not harmful."
        },
        "ldl": {
            "high": "This 'bad' cholesterol is high and can build up in your arteries. Lifestyle changes or medication may help.",
            "low": "This is usually protective for your heart."
        },
        "hdl": {
            "low": "This 'good' cholesterol is low. Higher HDL protects against heart disease.",
            "high": "This is good! High HDL helps protect your heart."
        },
        "triglycerides": {
            "high": "High triglycerides can increase heart disease risk. Diet changes and exercise can help lower them.",
            "low": "This is usually not a concern."
        },

        # Liver tests
        "alt": {
            "high": "This liver enzyme is elevated, which may mean liver inflammation or damage.",
            "low": "This is usually not concerning."
        },
        "ast": {
            "high": "This liver enzyme is high. It can be elevated in liver or muscle problems.",
            "low": "This is usually not concerning."
        },
        "bilirubin": {
            "high": "High bilirubin can cause jaundice (yellow skin/eyes) and may indicate liver or bile duct problems.",
            "low": "This is usually not concerning."
        },

        # Thyroid
        "tsh": {
            "high": "This suggests your thyroid may be underactive (hypothyroidism). You might feel tired or gain weight.",
            "low": "This suggests your thyroid may be overactive (hyperthyroidism). You might lose weight or feel anxious."
        },
        "t3": {
            "high": "Your thyroid hormone T3 is high. This can cause symptoms of hyperthyroidism.",
            "low": "Your thyroid hormone T3 is low. This can cause symptoms of hypothyroidism."
        },
        "t4": {
            "high": "Your thyroid hormone T4 is high. This can cause symptoms of hyperthyroidism.",
            "low": "Your thyroid hormone T4 is low. This can cause symptoms of hypothyroidism."
        },

        # Blood counts
        "hemoglobin": {
            "high": "Your red blood cells are carrying more oxygen than normal. This can happen with dehydration.",
            "low": "Your red blood cells are low (anemia). This can cause fatigue and weakness."
        },
        "hematocrit": {
            "high": "The proportion of red blood cells in your blood is high. This can happen with dehydration.",
            "low": "The proportion of red blood cells in your blood is low. This can cause anemia symptoms."
        },
        "wbc": {
            "high": "Your white blood cell count is high. This usually means your body is fighting an infection.",
            "low": "Your white blood cell count is low. This can increase your risk of infections."
        },
        "platelets": {
            "high": "Your platelet count is high. This can increase clotting risk but is often not serious.",
            "low": "Your platelet count is low. This can increase bleeding risk and needs medical attention."
        }
    }

    test_lower = test_name.lower()
    for key, interp in explanations.items():
        if key in test_lower:
            return interp.get(status, f"This test result is abnormal. Your doctor can explain what this means for your health.")

    # Generic explanation for unknown tests
    if status in ["high", "low", "critical"]:
        return "This test result is outside the normal range. Your doctor will explain what this means and if any action is needed."
    return ""


# ============== Agent 3: Summary Agent ==============
def summary_agent(state: MedicalReportState) -> MedicalReportState:
    parsed = state.get("parsed_data", "")
    summary = "Medical summary could not be generated."

    try:
        parsed_dict = json.loads(parsed)
        labs = parsed_dict.get("lab_values", [])
        findings = parsed_dict.get("findings", [])
        diagnosis = parsed_dict.get("diagnosis", [])
        patient_name = parsed_dict.get("patient_name")
        report_date = parsed_dict.get("report_date")

        # Build comprehensive medical summary
        summary_parts = []

        # Header with patient info
        if patient_name:
            summary_parts.append(f"PATIENT: {patient_name}")
        if report_date:
            summary_parts.append(f"REPORT DATE: {report_date}")
        summary_parts.append("=" * 60)

        # Overall assessment
        abnormal_labs = [lab for lab in labs if lab.get("status") in ["high", "low", "critical"]]
        normal_labs = [lab for lab in labs if lab.get("status") == "normal"]

        if abnormal_labs:
            summary_parts.append(f"OVERALL ASSESSMENT: {len(abnormal_labs)} abnormal result(s) requiring medical attention")
        else:
            summary_parts.append("OVERALL ASSESSMENT: All laboratory values within normal ranges")
        summary_parts.append("")

        # Detailed Lab Results Analysis
        if labs:
            summary_parts.append("DETAILED LABORATORY ANALYSIS:")
            summary_parts.append("-" * 40)

            # Process each lab result with medical context
            for lab in labs:
                test_name = lab.get("test_name", "Unknown Test")
                value = lab.get("value", "N/A")
                unit = lab.get("unit", "")
                ref_range = lab.get("reference_range", "")
                status = lab.get("status", "unknown")

                summary_parts.append(f"Test: {test_name}")
                summary_parts.append(f"Result: {value}{unit}")
                if ref_range:
                    summary_parts.append(f"Reference Range: {ref_range}")

                # Add medical interpretation based on test type and status
                interpretation = get_medical_interpretation(test_name, status, value, unit)
                if interpretation:
                    summary_parts.append(f"Interpretation: {interpretation}")

                summary_parts.append("")  # Empty line between tests

        # Clinical Findings Section
        if findings:
            summary_parts.append("CLINICAL FINDINGS:")
            summary_parts.append("-" * 40)
            for i, finding in enumerate(findings, 1):
                summary_parts.append(f"{i}. {finding}")
            summary_parts.append("")

        # Diagnosis and Impression
        if diagnosis:
            summary_parts.append("DIAGNOSIS/IMPRESSION:")
            summary_parts.append("-" * 40)
            for i, diag in enumerate(diagnosis, 1):
                summary_parts.append(f"{i}. {diag}")
            summary_parts.append("")

        # Comprehensive Recommendations
        summary_parts.append("MEDICAL RECOMMENDATIONS:")
        summary_parts.append("-" * 40)

        recommendations = generate_medical_recommendations(abnormal_labs, findings, diagnosis)
        for rec in recommendations:
            summary_parts.append(f"• {rec}")

        summary_parts.append("")
        summary_parts.append("IMPORTANT NOTES:")
        summary_parts.append("-" * 40)
        summary_parts.append("• This analysis is for informational purposes only")
        summary_parts.append("• Always consult with your healthcare provider for proper interpretation")
        summary_parts.append("• Results should be correlated with your clinical symptoms and history")
        summary_parts.append("• Follow-up testing may be required based on these results")

        summary = "\n".join(summary_parts)

    except Exception as e:
        summary = f"Unable to generate a structured summary from the parsed data. Error: {str(e)}"

    return {
        **state,
        "medical_summary": summary
    }


# ============== Agent 4: Simplification Agent ==============
def simplify_agent(state: MedicalReportState) -> MedicalReportState:
    parsed = state.get("parsed_data", "")
    medical_summary = state.get("medical_summary", "")

    try:
        parsed_dict = json.loads(parsed)
        labs = parsed_dict.get("lab_values", [])
        findings = parsed_dict.get("findings", [])
        diagnosis = parsed_dict.get("diagnosis", [])

        # Create comprehensive patient-friendly explanation
        simplified_parts = []

        # Overall health status
        abnormal_labs = [lab for lab in labs if lab.get("status") in ["high", "low", "critical"]]
        normal_labs = [lab for lab in labs if lab.get("status") == "normal"]

        simplified_parts.append("YOUR MEDICAL REPORT EXPLANATION")
        simplified_parts.append("=" * 50)

        if abnormal_labs:
            simplified_parts.append(f"⚠️  ATTENTION NEEDED: {len(abnormal_labs)} of your lab test(s) are outside normal ranges")
            simplified_parts.append("")
            simplified_parts.append("Abnormal Results Explained:")
            for lab in abnormal_labs:
                test_name = lab.get("test_name", "Unknown Test")
                status = lab.get("status", "abnormal")
                value = lab.get("value", "N/A")
                unit = lab.get("unit", "")

                simplified_parts.append(f"• {test_name}: {value}{unit} ({status})")

                # Add simple explanation for common tests
                simple_explanation = get_simple_explanation(test_name, status)
                if simple_explanation:
                    simplified_parts.append(f"  What this means: {simple_explanation}")
                simplified_parts.append("")
        else:
            simplified_parts.append("✅ GOOD NEWS: All your lab tests are within normal ranges")
            simplified_parts.append("This suggests your body systems are functioning normally.")
            simplified_parts.append("")

        # Explain what lab tests measure
        if labs:
            simplified_parts.append("UNDERSTANDING YOUR LAB TESTS:")
            simplified_parts.append("Lab tests help doctors understand how your body is working. They measure:")
            simplified_parts.append("• Blood sugar and diabetes risk")
            simplified_parts.append("• Kidney and liver function")
            simplified_parts.append("• Cholesterol and heart health")
            simplified_parts.append("• Blood cell counts and infection fighting ability")
            simplified_parts.append("• Thyroid hormone levels")
            simplified_parts.append("• And many other important body functions")
            simplified_parts.append("")

        # Clinical findings explanation
        if findings:
            simplified_parts.append("CLINICAL FINDINGS:")
            simplified_parts.append("Your report includes these observations from your healthcare provider:")
            for finding in findings:
                simplified_parts.append(f"• {finding}")
            simplified_parts.append("")
            simplified_parts.append("These findings help your doctor understand your current health status.")
            simplified_parts.append("")

        # Diagnosis explanation
        if diagnosis:
            simplified_parts.append("DIAGNOSIS/IMPRESSION:")
            simplified_parts.append("Your healthcare provider's assessment includes:")
            for diag in diagnosis:
                simplified_parts.append(f"• {diag}")
            simplified_parts.append("")
            simplified_parts.append("This section summarizes what your doctor thinks may be affecting your health.")
            simplified_parts.append("")

        # What to do next
        simplified_parts.append("WHAT SHOULD YOU DO NEXT?")
        simplified_parts.append("-" * 30)

        if abnormal_labs:
            simplified_parts.append("1. 📞 Contact your doctor soon to discuss these results")
            simplified_parts.append("2. 📝 Bring this report to your appointment")
            simplified_parts.append("3. ❓ Ask your doctor to explain what these results mean for you")
            simplified_parts.append("4. 📋 Follow any instructions for additional tests or treatments")
        else:
            simplified_parts.append("1. 🎉 Continue your healthy lifestyle habits")
            simplified_parts.append("2. 📅 Keep up with regular check-ups as recommended")
            simplified_parts.append("3. ⚡ Stay aware of any new symptoms and report them to your doctor")

        simplified_parts.append("")
        simplified_parts.append("WHY DOCTOR INTERPRETATION MATTERS:")
        simplified_parts.append("-" * 40)
        simplified_parts.append("• Lab results are only one piece of your health puzzle")
        simplified_parts.append("• Your symptoms, medical history, and physical exam are also important")
        simplified_parts.append("• Your doctor can explain how these results apply specifically to you")
        simplified_parts.append("• They can recommend the best next steps for your health")
        simplified_parts.append("")
        simplified_parts.append("REMEMBER: This is general information. Always consult your healthcare provider")
        simplified_parts.append("for personalized medical advice and treatment recommendations.")

        simplified = "\n".join(simplified_parts)

    except Exception:
        # Enhanced fallback explanation
        simplified = (
            "YOUR MEDICAL REPORT - GENERAL EXPLANATION\n"
            "=" * 50 + "\n\n"
            "This medical report contains important information about your health based on laboratory tests "
            "and clinical observations.\n\n"
            "WHAT LAB TESTS TELL US:\n"
            "• They measure how different parts of your body are working\n"
            "• Some results may be outside normal ranges, which could need attention\n"
            "• Normal ranges can vary by age, gender, and individual factors\n\n"
            "WHY SEE YOUR DOCTOR:\n"
            "• They can explain what these results mean for your specific situation\n"
            "• They consider your symptoms, medical history, and other factors\n"
            "• They can recommend any needed follow-up tests or treatments\n\n"
            "IMPORTANT: Always share this report with your healthcare provider for proper interpretation "
            "and personalized medical advice. They are best qualified to explain what these results mean for you."
        )

    return {
        **state,
        "simplified_explanation": simplified
    }


# ============== Hindi Translation Dictionary ==============
HINDI_TRANSLATIONS = {
    # Main headings
    "YOUR MEDICAL REPORT EXPLANATION": "आपकी चिकित्सा रिपोर्ट व्याख्या",
    "ATTENTION NEEDED": "ध्यान की आवश्यकता है",
    "of your lab test(s) are outside normal ranges": "आपके प्रयोगशाला परीक्षणों में से सामान्य सीमा से बाहर हैं",
    "Abnormal Results Explained": "असामान्य परिणाम समझाए गए",
    "What this means": "इसका मतलब है",
    "GOOD NEWS": "अच्छी खबर है",
    "All your lab tests are within normal ranges": "आपके सभी प्रयोगशाला परीक्षण सामान्य सीमा में हैं",
    "This suggests your body systems are functioning normally": "यह सुझाव देता है कि आपके शरीर की प्रणालियां सामान्य रूप से काम कर रही हैं",
    
    # Lab tests section
    "UNDERSTANDING YOUR LAB TESTS": "आपके प्रयोगशाला परीक्षणों को समझना",
    "Lab tests help doctors understand how your body is working": "प्रयोगशाला परीक्षण डॉक्टरों को यह समझने में मदद करते हैं कि आपका शरीर कैसे काम कर रहा है",
    "They measure": "वे मापते हैं",
    "Blood sugar and diabetes risk": "रक्त शर्करा और मधुमेह का जोखिम",
    "Kidney and liver function": "गुर्दे और यकृत कार्य",
    "Cholesterol and heart health": "कोलेस्ट्रॉल और हृदय स्वास्थ्य",
    "Blood cell counts and infection fighting ability": "रक्त कोशिका गणना और संक्रमण से लड़ने की क्षमता",
    "Thyroid hormone levels": "थायराइड हार्मोन के स्तर",
    "And many other important body functions": "और शरीर के कई अन्य महत्वपूर्ण कार्य",
    
    # Clinical sections
    "CLINICAL FINDINGS": "नैदानिक निष्कर्ष",
    "Your report includes these observations from your healthcare provider": "आपकी रिपोर्ट में आपके स्वास्थ्य सेवा प्रदाता के ये अवलोकन शामिल हैं",
    "These findings help your doctor understand your current health status": "ये निष्कर्ष आपके डॉक्टर को आपकी वर्तमान स्वास्थ्य स्थिति को समझने में मदद करते हैं",
    "DIAGNOSIS/IMPRESSION": "निदान/प्रभाव",
    "Your healthcare provider's assessment includes": "आपके स्वास्थ्य सेवा प्रदाता का आकलन शामिल है",
    "This section summarizes what your doctor thinks may be affecting your health": "यह खंड सारांशित करता है कि आपके डॉक्टर को क्या लगता है कि आपके स्वास्थ्य को प्रभावित कर सकता है",
    
    # Action items
    "WHAT SHOULD YOU DO NEXT": "अगला क्या करना चाहिए",
    "Contact your doctor soon to discuss these results": "इन परिणामों पर चर्चा करने के लिए जल्दी अपने डॉक्टर से संपर्क करें",
    "Bring this report to your appointment": "इस रिपोर्ट को अपनी नियुक्ति में लाएं",
    "Ask your doctor to explain what these results mean for you": "अपने डॉक्टर से पूछें कि ये परिणाम आपके लिए क्या मायने रखते हैं",
    "Follow any instructions for additional tests or treatments": "अतिरिक्त परीक्षण या उपचार के किसी भी निर्देश का पालन करें",
    "Continue your healthy lifestyle habits": "अपनी स्वस्थ जीवनशैली की आदतों को जारी रखें",
    "Keep up with regular check-ups as recommended": "अनुशंसित नियमित जांच के साथ तालमेल रखें",
    "Stay aware of any new symptoms and report them to your doctor": "किसी भी नए लक्षण के बारे में जागरूक रहें और उन्हें अपने डॉक्टर को रिपोर्ट करें",
    
    # Importance section
    "WHY DOCTOR INTERPRETATION MATTERS": "डॉक्टर की व्याख्या क्यों महत्वपूर्ण है",
    "Lab results are only one piece of your health puzzle": "प्रयोगशाला परिणाम आपके स्वास्थ्य पहेली का केवल एक हिस्सा हैं",
    "Your symptoms, medical history, and physical exam are also important": "आपके लक्षण, चिकित्सा इतिहास और शारीरिक परीक्षा भी महत्वपूर्ण हैं",
    "Your doctor can explain how these results apply specifically to you": "आपका डॉक्टर समझा सकता है कि ये परिणाम विशेष रूप से आपके लिए कैसे लागू होते हैं",
    "They can recommend the best next steps for your health": "वे आपके स्वास्थ्य के लिए अगले सर्वोत्तम कदमों की सिफारिश कर सकते हैं",
    
    # Final message
    "REMEMBER": "याद रखें",
    "This is general information": "यह सामान्य जानकारी है",
    "Always consult your healthcare provider for personalized medical advice and treatment recommendations": "व्यक्तिगत चिकित्सा सलाह और उपचार की सिफारिशों के लिए हमेशा अपने स्वास्थ्य सेवा प्रदाता से परामर्श लें",
    
    # Common medical terms
    "Glucose": "ग्लूकोज",
    "Hemoglobin": "हीमोग्लोबिन",
    "Cholesterol": "कोलेस्ट्रॉल",
    "Creatinine": "क्रिएटिनिन",
    "TSH": "टीएसएच",
    "Thyroid": "थायराइड",
    "Kidney": "गुर्दा",
    "Liver": "यकृत",
    "Diabetes": "मधुमेह",
    "Hypothyroidism": "हाइपोथायरायडिज्म",
    "Type 2 Diabetes": "टाइप 2 मधुमेह",
    "HIGH": "उच्च",
    "LOW": "निम्न",
    "normal": "सामान्य",
    "abnormal": "असामान्य",
    "elevated": "ऊंचा",
    "below normal": "सामान्य से कम",
    "critically abnormal": "गंभीर रूप से असामान्य",
}

# ============== Agent 5: Translation Agent ==============
LANGUAGE_PACKS = {
    "english": {
        "title": "YOUR MEDICAL REPORT EXPLANATION",
        "attention": "Attention needed",
        "normal": "All detected lab values appear within normal limits.",
        "abnormal": "Abnormal results found",
        "meaning": "What this means",
        "next": "What you should do next",
        "consult": "Discuss these results with your doctor and follow their advice.",
        "track": "Keep this report and compare it with future test results.",
        "urgent": "Seek urgent care for severe symptoms, fainting, chest pain, breathlessness, confusion, or very high/low sugar symptoms.",
        "disclaimer": "This is general information, not a diagnosis.",
        "high": "high",
        "low": "low",
        "critical": "critical",
        "normal_word": "normal",
    },
    "hindi": {
        "title": "आपकी मेडिकल रिपोर्ट की व्याख्या",
        "attention": "ध्यान देने की जरूरत है",
        "normal": "मिले हुए लैब परिणाम सामान्य सीमा में दिख रहे हैं।",
        "abnormal": "असामान्य परिणाम मिले",
        "meaning": "इसका मतलब",
        "next": "अब क्या करें",
        "consult": "इन परिणामों पर अपने डॉक्टर से चर्चा करें और उनकी सलाह मानें।",
        "track": "इस रिपोर्ट को संभालकर रखें और भविष्य की रिपोर्ट से तुलना करें।",
        "urgent": "सीने में दर्द, सांस फूलना, बेहोशी, भ्रम या बहुत ज्यादा/कम शुगर जैसे गंभीर लक्षण हों तो तुरंत चिकित्सा सहायता लें।",
        "disclaimer": "यह सामान्य जानकारी है, निदान नहीं।",
        "high": "उच्च",
        "low": "कम",
        "critical": "गंभीर",
        "normal_word": "सामान्य",
    },
    "bengali": {
        "title": "আপনার মেডিকেল রিপোর্টের ব্যাখ্যা",
        "attention": "মনোযোগ প্রয়োজন",
        "normal": "যে ল্যাব ফল পাওয়া গেছে সেগুলো সাধারণ সীমার মধ্যে দেখাচ্ছে।",
        "abnormal": "অস্বাভাবিক ফল পাওয়া গেছে",
        "meaning": "এর অর্থ",
        "next": "এরপর কী করবেন",
        "consult": "এই ফলাফলগুলো আপনার ডাক্তারের সঙ্গে আলোচনা করুন এবং তাঁর পরামর্শ মেনে চলুন।",
        "track": "রিপোর্টটি সংরক্ষণ করুন এবং ভবিষ্যতের রিপোর্টের সঙ্গে তুলনা করুন।",
        "urgent": "বুকে ব্যথা, শ্বাসকষ্ট, অজ্ঞান হওয়া, বিভ্রান্তি বা খুব বেশি/কম সুগারের লক্ষণ হলে জরুরি চিকিৎসা নিন।",
        "disclaimer": "এটি সাধারণ তথ্য, রোগ নির্ণয় নয়।",
        "high": "উচ্চ",
        "low": "কম",
        "critical": "গুরুতর",
        "normal_word": "স্বাভাবিক",
    },
    "tamil": {
        "title": "உங்கள் மருத்துவ அறிக்கை விளக்கம்",
        "attention": "கவனம் தேவை",
        "normal": "கண்டறியப்பட்ட ஆய்வு முடிவுகள் சாதாரண வரம்பில் உள்ளதாக தெரிகிறது.",
        "abnormal": "அசாதாரண முடிவுகள் கண்டறியப்பட்டன",
        "meaning": "இதன் பொருள்",
        "next": "அடுத்து என்ன செய்ய வேண்டும்",
        "consult": "இந்த முடிவுகளை உங்கள் மருத்துவருடன் பேசுங்கள்; அவர்களின் ஆலோசனையை பின்பற்றுங்கள்.",
        "track": "இந்த அறிக்கையை வைத்திருந்து அடுத்த பரிசோதனைகளுடன் ஒப்பிடுங்கள்.",
        "urgent": "மார்வலி, மூச்சுத்திணறல், மயக்கம், குழப்பம் அல்லது மிக அதிக/குறைந்த சர்க்கரை அறிகுறிகள் இருந்தால் உடனடி சிகிச்சை பெறுங்கள்.",
        "disclaimer": "இது பொதுவான தகவல்; நோய் கண்டறிதல் அல்ல.",
        "high": "அதிகம்",
        "low": "குறைவு",
        "critical": "கடுமை",
        "normal_word": "சாதாரணம்",
    },
    "telugu": {
        "title": "మీ మెడికల్ రిపోర్ట్ వివరణ",
        "attention": "శ్రద్ధ అవసరం",
        "normal": "గుర్తించిన ల్యాబ్ విలువలు సాధారణ పరిధిలో ఉన్నట్లు కనిపిస్తున్నాయి.",
        "abnormal": "అసాధారణ ఫలితాలు కనిపించాయి",
        "meaning": "దీని అర్థం",
        "next": "తర్వాత ఏమి చేయాలి",
        "consult": "ఈ ఫలితాల గురించి మీ డాక్టర్‌తో మాట్లాడి వారి సలహాను పాటించండి.",
        "track": "ఈ రిపోర్టును భద్రపరచి భవిష్యత్ పరీక్షలతో పోల్చండి.",
        "urgent": "ఛాతి నొప్పి, శ్వాస ఇబ్బంది, స్పృహ కోల్పోవడం, గందరగోళం లేదా చాలా ఎక్కువ/తక్కువ షుగర్ లక్షణాలు ఉంటే అత్యవసర చికిత్స తీసుకోండి.",
        "disclaimer": "ఇది సాధారణ సమాచారం మాత్రమే; నిర్ధారణ కాదు.",
        "high": "ఎక్కువ",
        "low": "తక్కువ",
        "critical": "తీవ్రం",
        "normal_word": "సాధారణం",
    },
    "marathi": {
        "title": "आपल्या वैद्यकीय अहवालाचे स्पष्टीकरण",
        "attention": "लक्ष देणे आवश्यक",
        "normal": "आढळलेले लॅब परिणाम सामान्य मर्यादेत दिसत आहेत.",
        "abnormal": "असामान्य परिणाम आढळले",
        "meaning": "याचा अर्थ",
        "next": "पुढे काय करावे",
        "consult": "हे परिणाम आपल्या डॉक्टरांशी चर्चा करा आणि त्यांचा सल्ला पाळा.",
        "track": "हा अहवाल जतन करा आणि पुढील चाचण्यांशी तुलना करा.",
        "urgent": "छातीत दुखणे, श्वास लागणे, बेशुद्ध होणे, गोंधळ किंवा खूप जास्त/कमी साखरेची लक्षणे असल्यास तातडीची मदत घ्या.",
        "disclaimer": "ही सामान्य माहिती आहे; निदान नाही.",
        "high": "जास्त",
        "low": "कमी",
        "critical": "गंभीर",
        "normal_word": "सामान्य",
    },
    "gujarati": {
        "title": "તમારી મેડિકલ રિપોર્ટની સમજ",
        "attention": "ધ્યાન જરૂરી છે",
        "normal": "મળેલા લેબ પરિણામો સામાન્ય મર્યાદામાં દેખાય છે.",
        "abnormal": "અસામાન્ય પરિણામો મળ્યા",
        "meaning": "આનો અર્થ",
        "next": "હવે શું કરવું",
        "consult": "આ પરિણામો વિશે તમારા ડૉક્ટર સાથે વાત કરો અને તેમની સલાહ અનુસરો.",
        "track": "આ રિપોર્ટ સાચવી રાખો અને ભવિષ્યની તપાસ સાથે સરખાવો.",
        "urgent": "છાતીમાં દુખાવો, શ્વાસમાં તકલીફ, બેભાન થવું, ગુંચવણ અથવા બહુ ઊંચી/નીચી શુગરના લક્ષણો હોય તો તાત્કાલિક સારવાર લો.",
        "disclaimer": "આ સામાન્ય માહિતી છે; નિદાન નથી.",
        "high": "ઊંચું",
        "low": "નીચું",
        "critical": "ગંભીર",
        "normal_word": "સામાન્ય",
    },
    "kannada": {
        "title": "ನಿಮ್ಮ ವೈದ್ಯಕೀಯ ವರದಿ ವಿವರಣೆ",
        "attention": "ಗಮನ ಅಗತ್ಯ",
        "normal": "ಪತ್ತೆಯಾದ ಲ್ಯಾಬ್ ಫಲಿತಾಂಶಗಳು ಸಾಮಾನ್ಯ ಮಿತಿಯಲ್ಲಿವೆ ಎಂದು ಕಾಣುತ್ತದೆ.",
        "abnormal": "ಅಸಾಮಾನ್ಯ ಫಲಿತಾಂಶಗಳು ಕಂಡುಬಂದಿವೆ",
        "meaning": "ಇದರ ಅರ್ಥ",
        "next": "ಮುಂದೆ ಏನು ಮಾಡಬೇಕು",
        "consult": "ಈ ಫಲಿತಾಂಶಗಳನ್ನು ನಿಮ್ಮ ವೈದ್ಯರೊಂದಿಗೆ ಚರ್ಚಿಸಿ ಮತ್ತು ಅವರ ಸಲಹೆ ಪಾಲಿಸಿ.",
        "track": "ಈ ವರದಿಯನ್ನು ಉಳಿಸಿ ಮುಂದಿನ ಪರೀಕ್ಷೆಗಳೊಂದಿಗೆ ಹೋಲಿಸಿ.",
        "urgent": "ಛಾತಿ ನೋವು, ಉಸಿರಾಟದ ತೊಂದರೆ, ಮೂರ್ಛೆ, ಗೊಂದಲ ಅಥವಾ ಬಹಳ ಹೆಚ್ಚು/ಕಡಿಮೆ ಶುಗರ್ ಲಕ್ಷಣಗಳಿದ್ದರೆ ತುರ್ತು ಚಿಕಿತ್ಸೆ ಪಡೆಯಿರಿ.",
        "disclaimer": "ಇದು ಸಾಮಾನ್ಯ ಮಾಹಿತಿ; ರೋಗನಿರ್ಣಯವಲ್ಲ.",
        "high": "ಹೆಚ್ಚು",
        "low": "ಕಡಿಮೆ",
        "critical": "ಗಂಭೀರ",
        "normal_word": "ಸಾಮಾನ್ಯ",
    },
    "malayalam": {
        "title": "നിങ്ങളുടെ മെഡിക്കൽ റിപ്പോർട്ട് വിശദീകരണം",
        "attention": "ശ്രദ്ധ ആവശ്യമാണ്",
        "normal": "കണ്ടെത്തിയ ലാബ് ഫലങ്ങൾ സാധാരണ പരിധിയിലാണെന്ന് തോന്നുന്നു.",
        "abnormal": "അസാധാരണ ഫലങ്ങൾ കണ്ടെത്തി",
        "meaning": "ഇതിന്റെ അർത്ഥം",
        "next": "അടുത്തതായി ചെയ്യേണ്ടത്",
        "consult": "ഈ ഫലങ്ങൾ നിങ്ങളുടെ ഡോക്ടറുമായി ചർച്ച ചെയ്യുകയും അവരുടെ ഉപദേശം പാലിക്കുകയും ചെയ്യുക.",
        "track": "ഈ റിപ്പോർട്ട് സൂക്ഷിച്ച് ഭാവിയിലുള്ള പരിശോധനകളുമായി താരതമ്യം ചെയ്യുക.",
        "urgent": "നെഞ്ചുവേദന, ശ്വാസതടസം, ബോധക്ഷയം, ആശയക്കുഴപ്പം, വളരെ ഉയർന്ന/കുറഞ്ഞ ഷുഗർ ലക്ഷണങ്ങൾ എന്നിവയുണ്ടെങ്കിൽ അടിയന്തര ചികിത്സ തേടുക.",
        "disclaimer": "ഇത് പൊതുവായ വിവരമാണ്; രോഗനിർണയം അല്ല.",
        "high": "ഉയർന്ന",
        "low": "കുറഞ്ഞ",
        "critical": "ഗുരുതരം",
        "normal_word": "സാധാരണം",
    },
}


def language_pack(target_lang: str) -> dict:
    key = (target_lang or "English").strip().lower()
    return LANGUAGE_PACKS.get(key, LANGUAGE_PACKS["english"])


def build_translated_report(state: MedicalReportState, target_lang: str) -> tuple[str, list[str]]:
    pack = language_pack(target_lang)
    parsed = _parsed_report_from_state(state)
    labs = parsed.get("lab_values", [])
    abnormal_labs = [lab for lab in labs if str(lab.get("status", "")).lower() in ["high", "low", "critical"]]

    lines = [pack["title"], "=" * 42, ""]
    if abnormal_labs:
        lines.append(f"{pack['attention']}: {len(abnormal_labs)}")
        lines.append(pack["abnormal"] + ":")
        for lab in abnormal_labs[:12]:
            status = str(lab.get("status", "abnormal")).lower()
            translated_status = pack.get(status, status)
            test_name = lab.get("test_name", "Test")
            value = lab.get("value", "N/A")
            unit = lab.get("unit", "")
            lines.append(f"- {test_name}: {value}{unit} ({translated_status})")
            simple = get_simple_explanation(str(test_name), status) if pack is LANGUAGE_PACKS["english"] else pack["consult"]
            if simple:
                lines.append(f"  {pack['meaning']}: {simple}")
    else:
        lines.append(pack["normal"])

    suggestions = [
        pack["consult"],
        pack["track"],
        pack["urgent"],
        pack["disclaimer"],
    ]
    lines.append("")
    lines.append(pack["next"] + ":")
    for index, suggestion in enumerate(suggestions, 1):
        lines.append(f"{index}. {suggestion}")

    return "\n".join(lines), suggestions


def translate_agent(state: MedicalReportState) -> MedicalReportState:
    target_lang = state.get("target_language", "Hindi")
    is_english  = target_lang.strip().lower() in ("english", "en")

    simplified_en  = state.get("simplified_explanation", "")
    disease_en     = state.get("disease_explanation_en", "")
    solution_en    = state.get("solution_plan_en", "")
    suggestions_en = state.get("suggestions", [])

    # Normalise suggestions to a list of strings
    if isinstance(suggestions_en, list):
        suggestion_list = [str(s).strip() for s in suggestions_en if str(s).strip()]
    elif isinstance(suggestions_en, str):
        suggestion_list = [s.strip().lstrip("0123456789.-) ")
                           for s in suggestions_en.split("\n") if s.strip()]
    else:
        suggestion_list = []

    if is_english:
        return {
            **state,
            "translated_explanation": simplified_en,
            "translated_suggestions": suggestion_list,
            "target_language":        target_lang,
            "disease_explanation_hi": disease_en,
            "solution_plan_hi":       solution_en,
        }

    # ── Build one batch dict and translate everything in a single API call ──
    fields_to_translate = {
        "simplified_explanation": simplified_en,
        "disease_explanation":    disease_en,
        "solution_plan":          solution_en,
    }
    # Add each suggestion as its own keyed field
    for i, s in enumerate(suggestion_list):
        fields_to_translate[f"suggestion_{i}"] = s

    # RuntimeError from translate_all_with_claude propagates to retranslate endpoint
    translated = translate_all_with_claude(fields_to_translate, target_lang)

    translated_explanation = translated.get("simplified_explanation", simplified_en)
    disease_translated     = translated.get("disease_explanation",    disease_en)
    solution_translated    = translated.get("solution_plan",          solution_en)
    translated_suggestions = [
        translated.get(f"suggestion_{i}", suggestion_list[i])
        for i in range(len(suggestion_list))
    ]

    return {
        **state,
        "translated_explanation": translated_explanation,
        "translated_suggestions": translated_suggestions,
        "target_language":        target_lang,
        "disease_explanation_hi": disease_translated,
        "solution_plan_hi":       solution_translated,
    }


def translate_to_hindi(text: str) -> str:
    """Translate English text to Hindi using manual translation dictionary"""
    translated = text
    
    # Replace all known phrases (longer phrases first to avoid partial replacements)
    sorted_phrases = sorted(HINDI_TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for english, hindi in sorted_phrases:
        # Case-insensitive replacement
        import re
        translated = re.sub(re.escape(english), hindi, translated, flags=re.IGNORECASE)
    
    return translated


# ============== Agent 6: Temporal Analysis Agent ==============
def _extract_time_series_from_raw(raw_text: str) -> list:
    """
    Parse multi-column trend tables from raw PDF text.
    Looks for patterns like:
        HbA1c    8.9    8.1    7.4    %
        Haemoglobin  10.2   10.8   10.4   g/dL
    Returns list of:
        {parameter, unit, history: [{date, value}, ...], ref_low, ref_high}
    """
    lines = raw_text.splitlines()
    time_series = []

    # Step 1: Find date headers — lines containing multiple month/year patterns
    date_headers = []
    date_line_idx = -1
    month_pat = re.compile(
        r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
        r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        r'[\s\-./]*(\d{4}|\d{2})?\b',
        re.IGNORECASE
    )
    for i, line in enumerate(lines):
        dates_found = date_pat = re.findall(
            r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
            r'[\s\-./]*(\d{4}|\d{2})?',
            line, re.IGNORECASE
        )
        if len(dates_found) >= 2:
            date_headers = [f"{m[0]} {m[1]}".strip() for m in dates_found if m[0]]
            date_line_idx = i
            break

    if date_line_idx == -1 or len(date_headers) < 2:
        return []

    # Step 2: Scan subsequent lines for data rows
    # Pattern: parameter name  num  num  num  [unit]  [trend_word]
    num_re   = re.compile(r'[-–]|([0-9]+(?:\.[0-9]+)?)')
    unit_re  = re.compile(
        r'\b(g/dL|mg/dL|%|mEq/L|uIU/mL|ng/mL|pg/mL|U/L|mg/g|ug/dL|'
        r'mL/min(?:/1\.73m2)?|IU/mL|mmol/L|ratio|index|/uL|mill/uL)\b',
        re.IGNORECASE
    )
    skip_words = {'normal','improving','worsening','fluctuating','stable',
                  'new','finding','trend','unit','parameter','result'}

    for line in lines[date_line_idx + 1:]:
        line = line.strip()
        if not line or len(line) < 8:
            continue

        # Extract all numbers from the line
        nums = re.findall(r'[0-9]+(?:\.[0-9]+)?', line)
        if len(nums) < len(date_headers):
            continue

        # Detect unit
        unit_match = unit_re.search(line)
        unit = unit_match.group(0) if unit_match else ''

        # Extract parameter name — text before the first number
        first_num_pos = re.search(r'[0-9]', line)
        if not first_num_pos:
            continue
        param_raw = line[:first_num_pos.start()].strip()
        # Clean up parameter name
        param = re.sub(r'[^A-Za-z0-9\s\-/().]', '', param_raw).strip()
        param = re.sub(r'\s+', ' ', param)

        # Skip header/footer rows
        if not param or param.lower() in skip_words or len(param) < 3:
            continue
        if any(w in param.lower() for w in ('parameter','result','test','unit')):
            continue

        # Map numbers to dates (take first N numbers matching date count)
        history = []
        num_idx = 0
        for d in date_headers:
            if num_idx < len(nums):
                try:
                    history.append({"date": d, "value": float(nums[num_idx])})
                    num_idx += 1
                except ValueError:
                    pass

        if len(history) < 2:
            continue

        # Determine trend direction
        values = [h['value'] for h in history]
        if values[-1] > values[0]:
            trend = "increasing"
        elif values[-1] < values[0]:
            trend = "decreasing"
        else:
            trend = "stable"

        time_series.append({
            "parameter": param,
            "unit":      unit,
            "history":   history,
            "trend":     trend,
        })

    return time_series


def temporal_agent(state: MedicalReportState) -> MedicalReportState:
    raw_text    = state.get("raw_text", "")
    report_date = state.get("report_date", "")

    temporal = {
        "trends":          [],
        "time_series":     [],   # NEW: [{parameter, unit, history:[{date,value}], trend}]
        "comparisons":     "No historical comparison available",
        "alerts":          [],
        "pattern_detected":"No persistent pattern identified",
        "time_analysis":   "Current report has no temporal history"
    }

    try:
        parsed_dict = json.loads(state.get("parsed_data", "{}"))
        labs = parsed_dict.get("lab_values", [])

        # ── 1. Current-report single-value trends (for deviation chart) ──
        trends = []
        alerts = []

        for lab in labs:
            test_name = lab.get("test_name", "").strip()
            raw_value = lab.get("value", "")
            unit      = lab.get("unit", "")
            status    = lab.get("status", "normal").lower()
            ref_range = lab.get("reference_range", "")

            try:
                numeric_value = float(str(raw_value).replace(",", "").strip())
            except ValueError:
                continue

            ref_low = ref_high = None
            if ref_range:
                range_match = re.search(
                    r"([0-9]+(?:\.[0-9]+)?)\s*(?:–|-|to)\s*([0-9]+(?:\.[0-9]+)?)",
                    str(ref_range), re.IGNORECASE
                )
                if range_match:
                    ref_low  = float(range_match.group(1))
                    ref_high = float(range_match.group(2))
                else:
                    lt = re.search(r"<\s*([0-9]+(?:\.[0-9]+)?)", str(ref_range))
                    gt = re.search(r">\s*([0-9]+(?:\.[0-9]+)?)", str(ref_range))
                    if lt:
                        ref_low, ref_high = 0.0, float(lt.group(1))
                    elif gt:
                        ref_low  = float(gt.group(1))
                        ref_high = numeric_value * 2

            percent_of_normal = 100.0
            deviation_pct     = 0.0
            if ref_low is not None and ref_high is not None and ref_high > ref_low:
                midpoint  = (ref_low + ref_high) / 2.0
                half_span = (ref_high - ref_low) / 2.0
                if midpoint > 0:
                    percent_of_normal = round((numeric_value / midpoint) * 100, 1)
                    percent_of_normal = max(5.0, min(200.0, percent_of_normal))
                if half_span > 0:
                    deviation_pct = round(((numeric_value - midpoint) / half_span) * 100, 1)
                    deviation_pct = max(-300.0, min(300.0, deviation_pct))
            else:
                deviation_pct = round(percent_of_normal - 100.0, 1)

            trends.append({
                "parameter":         test_name,
                "value":             numeric_value,
                "unit":              unit,
                "status":            status,
                "reference_range":   ref_range,
                "ref_low":           ref_low,
                "ref_high":          ref_high,
                "percent_of_normal": percent_of_normal,
                "deviation_pct":     deviation_pct,
            })

            if status in ("high", "critical"):
                alerts.append(f"{test_name} is HIGH ({raw_value} {unit}) — above normal range {ref_range}.")
            elif status == "low":
                alerts.append(f"{test_name} is LOW ({raw_value} {unit}) — below normal range {ref_range}.")

        temporal["trends"] = trends
        temporal["alerts"] = alerts[:6]

        # ── 2. Time-series extraction (for time vs disease chart) ──
        time_series = _extract_time_series_from_raw(raw_text)
        temporal["time_series"] = time_series

        # ── 3. Summary messages ───────────────────────────────
        abnormal = [t for t in trends if t["status"] in ("high", "low", "critical")]
        normal   = [t for t in trends if t["status"] == "normal"]

        if time_series:
            date_labels = [h["date"] for h in time_series[0]["history"]]
            temporal["time_analysis"] = (
                f"Temporal data found across {len(date_labels)} time points "
                f"({', '.join(date_labels)}). "
                f"Tracking {len(time_series)} parameters over time."
            )
            improving  = [t["parameter"] for t in time_series if t["trend"] == "decreasing"]
            worsening  = [t["parameter"] for t in time_series if t["trend"] == "increasing"]
            temporal["comparisons"] = (
                f"Tracked {len(time_series)} parameters across {len(date_labels)} visits. "
                + (f"Improving: {', '.join(improving[:3])}. " if improving else "")
                + (f"Worsening: {', '.join(worsening[:3])}." if worsening else "")
            )
            if len(worsening) >= 2:
                temporal["pattern_detected"] = (
                    f"Worsening trend in {len(worsening)} parameters: "
                    f"{', '.join(worsening[:4])}. Clinical review recommended."
                )
        elif trends:
            temporal["time_analysis"] = (
                f"Analysed {len(trends)} lab parameters from this report. "
                f"{len(abnormal)} abnormal, {len(normal)} normal. "
                "Upload future reports to track trends over time."
            )
            temporal["comparisons"] = (
                f"Single report — {len(trends)} lab values analysed. "
                "No historical data available yet for time comparison."
            )

    except Exception as e:
        temporal["time_analysis"] = f"Could not parse report: {str(e)}"

    return {
        **state,
        "temporal_analysis": json.dumps(temporal, indent=2),
        "trend_data":        str(temporal.get("trends", []))
    }


def generate_ai_suggestions(state: MedicalReportState) -> list:
    """Generate detailed AI suggestions based on parsed report content."""
    suggestions = [
        "Review the report with a medical professional.",
        "Follow up on any abnormal lab results.",
        "Share this summary and explanation with your doctor during your next visit.",
        "Ask your healthcare provider to clarify any findings or diagnoses you do not understand.",
        "Track key symptoms and lifestyle changes to discuss at your next appointment.",
        "Keep a copy of this report and compare it against future test results to monitor trends.",
        "Consider asking your doctor whether additional tests or specialist referrals are needed."
    ]

    try:
        parsed = json.loads(state.get("parsed_data", "{}"))
        labs = parsed.get("lab_values", [])
        findings = parsed.get("findings", [])
        diagnosis = parsed.get("diagnosis", [])

        abnormal_labs = [lab for lab in labs if lab.get("status") in ["high", "low", "critical"]]
        if abnormal_labs:
            suggestions.append("Focus on the most concerning abnormal lab values first when you review this with your provider.")
            
            # Enhanced actionable suggestions based on specific abnormal labs
            for lab in abnormal_labs:
                test_name = lab.get("test_name", "").lower()
                status = lab.get("status", "")
                
                if "glucose" in test_name or "a1c" in test_name:
                    if status == "high":
                        suggestions.extend([
                            "Consider daily blood sugar monitoring if diabetic or prediabetic.",
                            "Adopt a low-glycemic diet: reduce refined sugars, eat whole grains, vegetables, and lean proteins.",
                            "Aim for 30 minutes of moderate exercise most days (walking, swimming, cycling).",
                            "Consider vitamin D supplementation and sunlight exposure (10-30 minutes daily) for better insulin sensitivity.",
                            "Further tests to consider: Oral glucose tolerance test, insulin levels, or continuous glucose monitoring."
                        ])
                    elif status == "low":
                        suggestions.extend([
                            "Keep glucose monitoring supplies available and learn to recognize hypoglycemia symptoms.",
                            "Eat regular, balanced meals with complex carbohydrates.",
                            "Further tests: Check for insulinoma or other endocrine disorders if hypoglycemia persists."
                        ])
                
                elif any(term in test_name for term in ["creatinine", "egfr", "bun"]):
                    if status in ["high", "critical"]:
                        suggestions.extend([
                            "Increase water intake to at least 8-10 glasses daily unless fluid restricted.",
                            "Follow a kidney-friendly diet: reduce sodium, phosphorus, and potassium-rich foods.",
                            "Avoid NSAIDs and certain medications that can harm kidneys.",
                            "Further tests to consider: Urinalysis, kidney ultrasound, or 24-hour urine protein measurement."
                        ])
                
                elif any(term in test_name for term in ["cholesterol", "ldl", "hdl", "triglycerides"]):
                    if status == "high":
                        suggestions.extend([
                            "Adopt Mediterranean diet: olive oil, fish, nuts, fruits, vegetables, whole grains.",
                            "Increase omega-3 intake through fatty fish (salmon, mackerel) or supplements.",
                            "Aim for 150 minutes of moderate aerobic activity weekly.",
                            "Further tests: Coronary calcium scan or carotid artery ultrasound if high cardiovascular risk."
                        ])
                    elif "hdl" in test_name and status == "low":
                        suggestions.extend([
                            "Increase physical activity, especially aerobic exercise.",
                            "Include healthy fats: avocados, nuts, olive oil in diet.",
                            "Consider moderate alcohol consumption if not contraindicated."
                        ])
                
                elif any(term in test_name for term in ["alt", "ast", "bilirubin"]):
                    if status == "high":
                        suggestions.extend([
                            "Avoid alcohol completely until liver function normalizes.",
                            "Follow liver-healthy diet: reduce fried foods, processed meats, and sugary drinks.",
                            "Stay hydrated and maintain healthy weight.",
                            "Further tests: Liver ultrasound, viral hepatitis panel, or liver biopsy if indicated."
                        ])
                
                elif any(term in test_name for term in ["tsh", "t3", "t4"]):
                    if status == "high":  # Hypothyroidism
                        suggestions.extend([
                            "Monitor for hypothyroidism symptoms: fatigue, weight gain, cold intolerance.",
                            "Consider iodine-rich foods: seaweed, iodized salt, fish.",
                            "Further tests: Free T4, thyroid antibodies (TPO, TgAb) to confirm autoimmune thyroiditis."
                        ])
                    elif status == "low":  # Hyperthyroidism
                        suggestions.extend([
                            "Monitor for hyperthyroidism symptoms: weight loss, rapid heartbeat, heat intolerance.",
                            "Limit iodine-rich foods if hyperthyroidism suspected.",
                            "Further tests: Free T4, thyroid antibodies, thyroid ultrasound."
                        ])
                
                elif any(term in test_name for term in ["hemoglobin", "hematocrit"]):
                    if status == "low":
                        suggestions.extend([
                            "Increase iron-rich foods: spinach, lentils, red meat, fortified cereals.",
                            "Pair iron-rich foods with vitamin C sources (citrus, bell peppers) for better absorption.",
                            "Consider vitamin B12 and folate-rich foods: eggs, dairy, leafy greens.",
                            "Further tests: Ferritin, vitamin B12, folate levels, stool for occult blood."
                        ])
                    elif status == "high":
                        suggestions.extend([
                            "Stay well-hydrated, especially in hot weather or high altitude.",
                            "Further tests: Evaluate for polycythemia vera or other blood disorders."
                        ])
                
                elif "wbc" in test_name:
                    if status == "high":
                        suggestions.extend([
                            "Monitor for infection signs: fever, chills, fatigue.",
                            "Practice good hygiene and food safety.",
                            "Further tests: Blood culture, CRP, ESR if infection suspected."
                        ])
                    elif status == "low":
                        suggestions.extend([
                            "Avoid crowded places and people with infections.",
                            "Practice meticulous hand hygiene.",
                            "Further tests: Bone marrow biopsy if persistent leukopenia."
                        ])
                
                elif "platelets" in test_name:
                    if status == "low":
                        suggestions.extend([
                            "Avoid activities with high fall risk or contact sports.",
                            "Use soft toothbrush, avoid constipation to prevent bleeding.",
                            "Further tests: Peripheral blood smear, platelet antibodies, bone marrow evaluation."
                        ])
                    elif status == "high":
                        suggestions.extend([
                            "Monitor for unusual bleeding or clotting symptoms.",
                            "Further tests: JAK2 mutation testing if myeloproliferative disorder suspected."
                        ])

        if findings:
            suggestions.append("Clarify each clinical finding with your healthcare provider to understand its importance and next steps.")

        if diagnosis:
            suggestions.append("Ask whether the diagnosis requires treatment changes, monitoring, or lifestyle modifications.")
            suggestions.append("Check whether any medications, diets, or preventive actions should be started or adjusted.")

        if not abnormal_labs and not findings and not diagnosis:
            suggestions.extend([
                "Continue routine health check-ups and preventive care.",
                "Consider vitamin D testing if limited sun exposure.",
                "Maintain healthy BMI through balanced diet and regular exercise."
            ])

    except Exception:
        suggestions.append("If you have questions, ask your medical provider for a clear explanation of your results.")

    return suggestions


def _parsed_report_from_state(state: MedicalReportState) -> ParsedReport:
    try:
        return json.loads(state.get("parsed_data", "{}"))
    except Exception:
        return {"lab_values": [], "findings": [], "diagnosis": []}


def generate_hindi_disease_education(state: MedicalReportState) -> tuple[str, str, list[str]]:
    """Create Hindi disease education and practical improvement steps from report clues."""
    parsed = _parsed_report_from_state(state)
    labs = parsed.get("lab_values", [])
    diagnosis = parsed.get("diagnosis", [])
    diagnosis_text = " ".join(str(item).lower() for item in diagnosis)
    abnormal_labs = [lab for lab in labs if lab.get("status") in ["high", "low", "critical"]]
    lab_names = " ".join(str(lab.get("test_name", "")).lower() for lab in abnormal_labs)

    disease_sections: list[str] = []
    solution_steps: list[str] = []

    def add_section(title: str, explanation: str, clues: list[str], actions: list[str]) -> None:
        section = [title, explanation]
        if clues:
            section.append("रिपोर्ट में संकेत: " + ", ".join(clues))
        disease_sections.append("\n".join(section))
        solution_steps.extend(actions)

    glucose_clues = [
        f"{lab.get('test_name')}: {lab.get('value')}{lab.get('unit', '')} ({lab.get('status')})"
        for lab in abnormal_labs
        if "glucose" in str(lab.get("test_name", "")).lower() or "a1c" in str(lab.get("test_name", "")).lower()
    ]
    if glucose_clues or "diabetes" in diagnosis_text or "mellitus" in diagnosis_text:
        add_section(
            "मधुमेह / हाई ब्लड शुगर",
            "इसमें खून में शुगर सामान्य से अधिक रहती है। लंबे समय तक शुगर अधिक रहने पर आंख, किडनी, नसों और दिल पर असर पड़ सकता है, इसलिए नियमित जांच और नियंत्रण जरूरी है।",
            glucose_clues,
            [
                "शुगर नियंत्रण के लिए मीठे पेय, चीनी और मैदा कम करें; साबुत अनाज, दाल, सब्जियां और प्रोटीन बढ़ाएं।",
                "डॉक्टर की सलाह से फास्टिंग शुगर, HbA1c और जरूरत हो तो दवाओं की समीक्षा कराएं।",
                "सप्ताह में कम से कम 150 मिनट तेज चाल से चलना या हल्का व्यायाम करें, अगर डॉक्टर ने मना न किया हो।",
            ],
        )

    kidney_clues = [
        f"{lab.get('test_name')}: {lab.get('value')}{lab.get('unit', '')} ({lab.get('status')})"
        for lab in abnormal_labs
        if any(term in str(lab.get("test_name", "")).lower() for term in ["creatinine", "egfr", "bun"])
    ]
    if kidney_clues or "kidney" in diagnosis_text or "renal" in diagnosis_text:
        add_section(
            "किडनी फंक्शन में बदलाव",
            "किडनी शरीर से अपशिष्ट पदार्थ और अतिरिक्त पानी निकालती है। क्रिएटिनिन, BUN या eGFR में बदलाव किडनी पर दबाव या कार्यक्षमता में कमी का संकेत हो सकता है।",
            kidney_clues,
            [
                "पानी पर्याप्त मात्रा में लें, लेकिन अगर डॉक्टर ने फ्लूइड लिमिट बताई है तो वही मानें।",
                "नमक कम करें और दर्द की NSAID दवाएं जैसे ibuprofen बिना डॉक्टर की सलाह के न लें।",
                "डॉक्टर से यूरिन टेस्ट, ब्लड प्रेशर मॉनिटरिंग और किडनी अल्ट्रासाउंड की जरूरत पूछें।",
            ],
        )

    lipid_clues = [
        f"{lab.get('test_name')}: {lab.get('value')}{lab.get('unit', '')} ({lab.get('status')})"
        for lab in abnormal_labs
        if any(term in str(lab.get("test_name", "")).lower() for term in ["cholesterol", "ldl", "hdl", "triglyceride"])
    ]
    if lipid_clues or "cholesterol" in diagnosis_text or "dyslipidemia" in diagnosis_text:
        add_section(
            "कोलेस्ट्रॉल / दिल का जोखिम",
            "LDL या ट्राइग्लिसराइड अधिक होने से धमनियों में चर्बी जमने का खतरा बढ़ सकता है। HDL कम होने पर दिल की सुरक्षा घट सकती है।",
            lipid_clues,
            [
                "तला हुआ भोजन, प्रोसेस्ड स्नैक्स और संतृप्त वसा कम करें; फल, सब्जियां, नट्स और फाइबर बढ़ाएं।",
                "डॉक्टर से कुल हृदय जोखिम और जरूरत होने पर लिपिड कम करने वाली दवा पर चर्चा करें।",
                "धूम्रपान बंद करें और वजन, कमर का माप तथा ब्लड प्रेशर पर नजर रखें।",
            ],
        )

    liver_clues = [
        f"{lab.get('test_name')}: {lab.get('value')}{lab.get('unit', '')} ({lab.get('status')})"
        for lab in abnormal_labs
        if any(term in str(lab.get("test_name", "")).lower() for term in ["alt", "ast", "bilirubin"])
    ]
    if liver_clues or "liver" in diagnosis_text or "hepatic" in diagnosis_text:
        add_section(
            "लिवर एंजाइम में बढ़ोतरी",
            "ALT, AST या bilirubin बढ़ना लिवर में सूजन, फैटी लिवर, दवा के असर, संक्रमण या पित्त की समस्या से जुड़ा हो सकता है।",
            liver_clues,
            [
                "शराब से बचें और बिना सलाह के सप्लीमेंट या दवाएं न लें।",
                "तेल, चीनी और प्रोसेस्ड भोजन कम करें; वजन अधिक हो तो धीरे-धीरे कम करें।",
                "डॉक्टर से लिवर अल्ट्रासाउंड और hepatitis profile जैसी आगे की जांचों की जरूरत पूछें।",
            ],
        )

    thyroid_clues = [
        f"{lab.get('test_name')}: {lab.get('value')}{lab.get('unit', '')} ({lab.get('status')})"
        for lab in abnormal_labs
        if any(term in str(lab.get("test_name", "")).lower() for term in ["tsh", "t3", "t4", "thyroid"])
    ]
    if thyroid_clues or "thyroid" in diagnosis_text:
        add_section(
            "थायरॉइड असंतुलन",
            "थायरॉइड हार्मोन शरीर की ऊर्जा, वजन, दिल की धड़कन और तापमान नियंत्रण में मदद करते हैं। TSH/T3/T4 में बदलाव hypo या hyperthyroid स्थिति दिखा सकता है।",
            thyroid_clues,
            [
                "थकान, वजन में बदलाव, धड़कन, ठंड/गर्मी सहन न होना जैसे लक्षण नोट करें।",
                "डॉक्टर से Free T4, TPO antibodies या repeat thyroid test की जरूरत पूछें।",
                "थायरॉइड दवा चल रही है तो उसे रोज एक ही समय पर लें और खुद से dose न बदलें।",
            ],
        )

    anemia_clues = [
        f"{lab.get('test_name')}: {lab.get('value')}{lab.get('unit', '')} ({lab.get('status')})"
        for lab in abnormal_labs
        if any(term in str(lab.get("test_name", "")).lower() for term in ["hemoglobin", "hematocrit", "rbc"])
    ]
    if anemia_clues or "anemia" in diagnosis_text:
        add_section(
            "एनीमिया / खून की कमी",
            "हीमोग्लोबिन या RBC कम होने पर शरीर में ऑक्सीजन पहुंचना कम हो सकता है। इससे थकान, कमजोरी, चक्कर या सांस फूलना हो सकता है।",
            anemia_clues,
            [
                "आयरन वाले भोजन जैसे हरी पत्तेदार सब्जियां, दाल, चना, गुड़ और डॉक्टर द्वारा सुझाए खाद्य पदार्थ लें।",
                "आयरन के साथ vitamin C लें; चाय/कॉफी तुरंत बाद न लें क्योंकि absorption कम हो सकता है।",
                "डॉक्टर से ferritin, vitamin B12, folate और blood loss की जांच की जरूरत पूछें।",
            ],
        )

    if not disease_sections:
        disease_sections.append(
            "रिपोर्ट में कोई स्पष्ट बीमारी संकेत नहीं मिला\n"
            "रिपोर्ट में उपलब्ध जानकारी के आधार पर कोई खास abnormal pattern साफ नहीं दिखा। फिर भी अंतिम अर्थ डॉक्टर आपके लक्षण, उम्र, दवाओं और पुरानी बीमारी के साथ जोड़कर बताएंगे।"
        )
        solution_steps.extend([
            "नियमित check-up जारी रखें और रिपोर्ट अपने डॉक्टर को दिखाएं।",
            "संतुलित भोजन, पर्याप्त नींद, व्यायाम और तनाव नियंत्रण पर ध्यान दें।",
            "नए लक्षण जैसे तेज दर्द, सांस फूलना, बेहोशी, लगातार बुखार या अत्यधिक कमजोरी हो तो तुरंत चिकित्सा सहायता लें।",
        ])

    solution_steps.append("यह सामान्य जानकारी है; व्यक्तिगत इलाज या दवा के लिए अपने डॉक्टर से सलाह लें।")

    return "\n\n".join(disease_sections), "\n".join(f"{index + 1}. {step}" for index, step in enumerate(dict.fromkeys(solution_steps))), list(dict.fromkeys(solution_steps))


def generate_english_disease_education(state: MedicalReportState) -> tuple[str, str]:
    """Create patient-friendly English disease education and improvement steps."""
    parsed = _parsed_report_from_state(state)
    labs = parsed.get("lab_values", [])
    diagnosis = parsed.get("diagnosis", [])
    raw_text = state.get("raw_text", "")
    diagnosis_text = " ".join(str(item).lower() for item in diagnosis)
    combined_text = f"{diagnosis_text} {raw_text.lower()}"
    abnormal_labs = [lab for lab in labs if lab.get("status") in ["high", "low", "critical"]]

    disease_sections: list[str] = []
    solution_steps: list[str] = []

    def clues_for(*terms: str) -> list[str]:
        return [
            f"{lab.get('test_name')}: {lab.get('value')}{lab.get('unit', '')} ({lab.get('status')})"
            for lab in abnormal_labs
            if any(term in str(lab.get("test_name", "")).lower() for term in terms)
        ]

    def add_section(title: str, explanation: str, clues: list[str], actions: list[str]) -> None:
        section = [title, explanation]
        if clues:
            section.append("Report clues: " + ", ".join(clues))
        disease_sections.append("\n".join(section))
        solution_steps.extend(actions)

    glucose_clues = clues_for("glucose", "a1c")
    if glucose_clues or "diabetes" in combined_text or "mellitus" in combined_text:
        add_section(
            "Diabetes / High Blood Sugar",
            "High blood sugar means glucose is staying in the blood instead of moving efficiently into body cells. If it remains high over time, it can affect the eyes, kidneys, nerves, heart, and wound healing.",
            glucose_clues,
            [
                "Reduce sugary drinks, sweets, refined flour, and large portions of rice or bread; choose vegetables, pulses, whole grains, and lean protein.",
                "Ask your doctor about fasting glucose, post-meal glucose, HbA1c, and whether medicine changes are needed.",
                "Do regular physical activity such as brisk walking for about 30 minutes on most days, if your doctor says it is safe.",
            ],
        )

    kidney_clues = clues_for("creatinine", "egfr", "bun")
    if kidney_clues or "kidney" in combined_text or "renal" in combined_text:
        add_section(
            "Kidney Function Changes",
            "The kidneys filter waste and extra fluid from the blood. Changes in creatinine, BUN, or eGFR may suggest dehydration, kidney stress, or reduced kidney filtering capacity.",
            kidney_clues,
            [
                "Drink enough water unless your doctor has restricted fluids.",
                "Reduce excess salt and avoid painkillers like ibuprofen or diclofenac unless prescribed.",
                "Ask your doctor if urine testing, blood pressure monitoring, kidney ultrasound, or repeat kidney function tests are needed.",
            ],
        )

    lipid_clues = clues_for("cholesterol", "ldl", "hdl", "triglyceride")
    if lipid_clues or "cholesterol" in combined_text or "dyslipidemia" in combined_text:
        add_section(
            "Cholesterol / Heart Risk",
            "High LDL, total cholesterol, or triglycerides can increase fatty deposits in blood vessels. Low HDL can reduce heart protection. Over time this may increase the risk of heart attack or stroke.",
            lipid_clues,
            [
                "Limit fried foods, processed snacks, butter/ghee-heavy foods, and sugary drinks.",
                "Increase fiber from oats, fruits, vegetables, beans, nuts, and whole grains.",
                "Discuss total heart risk with your doctor and ask whether lipid-lowering medicine is needed.",
            ],
        )

    liver_clues = clues_for("alt", "ast", "bilirubin")
    if liver_clues or "liver" in combined_text or "hepatic" in combined_text:
        add_section(
            "Liver Enzyme Elevation",
            "Raised ALT, AST, or bilirubin can happen with fatty liver, alcohol use, viral hepatitis, medicine effects, bile duct problems, or liver inflammation.",
            liver_clues,
            [
                "Avoid alcohol and do not take supplements or extra medicines without medical advice.",
                "Reduce fried foods, processed foods, and excess sugar; gradual weight loss can help fatty liver.",
                "Ask your doctor if liver ultrasound, hepatitis tests, or repeat liver function tests are required.",
            ],
        )

    thyroid_clues = clues_for("tsh", "t3", "t4", "thyroid")
    if thyroid_clues or "thyroid" in combined_text:
        add_section(
            "Thyroid Imbalance",
            "Thyroid hormones control energy, weight, temperature tolerance, heart rate, and metabolism. Abnormal TSH/T3/T4 may suggest underactive or overactive thyroid function.",
            thyroid_clues,
            [
                "Track symptoms such as fatigue, weight change, palpitations, constipation, anxiety, or heat/cold intolerance.",
                "Ask your doctor about Free T4, thyroid antibodies, repeat testing, or thyroid ultrasound if needed.",
                "If thyroid medicine is prescribed, take it consistently and do not change the dose yourself.",
            ],
        )

    anemia_clues = clues_for("hemoglobin", "hematocrit", "rbc")
    if anemia_clues or "anemia" in combined_text:
        add_section(
            "Anemia / Low Blood Count",
            "Low hemoglobin or red blood cell measures can reduce oxygen delivery to the body. This may cause tiredness, weakness, dizziness, pale skin, or shortness of breath.",
            anemia_clues,
            [
                "Eat iron-rich foods such as leafy greens, lentils, beans, fortified cereals, eggs, or doctor-approved meats.",
                "Take vitamin C with iron-rich foods and avoid tea/coffee immediately after meals because they can reduce iron absorption.",
                "Ask your doctor about ferritin, vitamin B12, folate, and evaluation for blood loss.",
            ],
        )

    if not disease_sections:
        disease_sections.append(
            "No Clear Disease Pattern Detected\n"
            "The extracted report did not show a clear disease pattern from the available values. A doctor should still interpret the result with your symptoms, age, medicines, and medical history."
        )
        solution_steps.extend([
            "Continue routine check-ups and share the report with your doctor.",
            "Maintain balanced food, sleep, exercise, hydration, and stress control.",
            "Seek urgent care for severe pain, breathlessness, fainting, persistent fever, confusion, or extreme weakness.",
        ])

    solution_steps.append("This is general information, not a diagnosis. Please follow your doctor for personal treatment and medicine decisions.")

    return "\n\n".join(disease_sections), "\n".join(f"{index + 1}. {step}" for index, step in enumerate(dict.fromkeys(solution_steps)))


def calculate_risk_assessment(state: MedicalReportState) -> dict:
    """
    Estimate clinical risk using Claude API for medical reasoning.
    Falls back to rule-based scoring if API key is unavailable.
    """
    parsed   = _parsed_report_from_state(state)
    labs     = parsed.get("lab_values", [])
    findings = parsed.get("findings", [])
    diagnosis = parsed.get("diagnosis", [])

    # ── No data at all ──────────────────────────────────────────
    if not labs and not findings and not diagnosis:
        return {
            "risk_probability": 0.2,
            "risk_level": "low",
            "causal_factors": [
                {"factor": "Limited report data",
                 "probability": 0.2,
                 "cause": "No measurable lab values were extracted from the PDF."}
            ],
            "causal_explanation": (
                "Risk could not be assessed accurately because no structured "
                "lab values were found in the report."
            ),
            "confidence": 0.40,
        }

    # ── Try Claude API ──────────────────────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        try:
            import anthropic

            # Build a compact but complete lab summary for the prompt
            lab_lines = []
            for lab in labs:
                name   = lab.get("test_name", "Unknown")
                value  = lab.get("value", "N/A")
                unit   = lab.get("unit", "")
                ref    = lab.get("reference_range", "")
                status = lab.get("status", "unknown")
                lab_lines.append(
                    f"- {name}: {value} {unit}  "
                    f"[ref: {ref if ref else 'not provided'}]  "
                    f"[status: {status}]"
                )

            diagnosis_text = ", ".join(str(d) for d in diagnosis) if diagnosis else "Not specified"
            findings_text  = ", ".join(str(f) for f in findings)  if findings  else "Not specified"
            labs_text      = "\n".join(lab_lines) if lab_lines else "No lab values extracted."

            prompt = f"""You are a senior clinical pathologist reviewing a patient's lab report.

Diagnoses mentioned: {diagnosis_text}
Clinical findings: {findings_text}

Lab Results:
{labs_text}

Based ONLY on the above data, provide a clinical risk assessment in the following JSON format.
Return ONLY valid JSON — no markdown, no explanation outside the JSON.

{{
  "risk_probability": <float 0.0 to 1.0, reflecting true clinical urgency>,
  "risk_level": "<low | medium | high>",
  "confidence": <float 0.0 to 1.0, how confident you are given the data>,
  "causal_explanation": "<2-3 sentence plain-English explanation of the overall risk and why>",
  "causal_factors": [
    {{
      "factor": "<specific test name or finding>",
      "probability": <float 0.0 to 1.0, individual contribution to risk>,
      "cause": "<brief clinical reason this value raises or lowers concern>"
    }}
  ]
}}

Guidelines for risk_probability:
- 0.0–0.25: All values normal or trivially mild deviations, no urgent action needed
- 0.26–0.50: Some abnormal values, needs follow-up at next routine visit
- 0.51–0.74: Multiple significant abnormalities, prompt clinical review needed
- 0.75–1.0: Critical values, organ dysfunction, or emergency-level findings

Include up to 8 causal_factors, ordered from most to least impactful.
Only include factors that genuinely appear in the data provided."""

            client  = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model      = "claude-haiku-4-5-20251001",
                max_tokens = 1024,
                messages   = [{"role": "user", "content": prompt}],
            )

            raw = message.content[0].text.strip()

            # Strip markdown fences if present
            raw = re.sub(r"^```(?:json)?", "", raw).strip()
            raw = re.sub(r"```$", "", raw).strip()

            result = json.loads(raw)

            # Validate and sanitise required fields
            risk_prob  = float(result.get("risk_probability", 0.3))
            risk_prob  = max(0.05, min(0.95, risk_prob))
            risk_level = result.get("risk_level", "medium").lower()
            if risk_level not in ("low", "medium", "high"):
                risk_level = "low" if risk_prob < 0.35 else ("high" if risk_prob >= 0.75 else "medium")

            confidence     = float(result.get("confidence", 0.80))
            explanation    = result.get("causal_explanation", "")
            causal_factors = result.get("causal_factors", [])

            # Ensure each factor has required keys
            clean_factors = []
            for f in causal_factors[:8]:
                if isinstance(f, dict) and "factor" in f:
                    clean_factors.append({
                        "factor":      str(f.get("factor", "")),
                        "probability": round(float(f.get("probability", risk_prob)), 2),
                        "cause":       str(f.get("cause", "")),
                    })

            return {
                "risk_probability": round(risk_prob, 2),
                "risk_level":       risk_level,
                "causal_factors":   clean_factors,
                "causal_explanation": explanation,
                "confidence":       round(confidence, 2),
                "assessed_by":      "claude-haiku-4-5",
            }

        except Exception as e:
            # Log and fall through to rule-based backup
            print(f"[RiskAssessment] Claude API failed: {e} — falling back to rule-based scoring.")

    # ── Rule-based fallback (used when no API key or Claude call fails) ─
    base_score      = 0.08
    severity_scores: list[float] = []
    diagnosis_boost = 0.0
    raw_text_boost  = 0.0
    causal_factors  = []
    abnormal_count  = 0
    critical_count  = 0
    normal_count    = 0
    raw_lower       = state.get("raw_text", "").lower()

    for lab in labs:
        test_name      = str(lab.get("test_name", "Unknown test"))
        test_lower     = test_name.lower()
        status         = str(lab.get("status", "unknown")).lower()
        value          = str(lab.get("value", "N/A"))
        unit           = str(lab.get("unit", ""))
        reference_range = str(lab.get("reference_range", ""))
        numeric_value  = parse_numeric_value(value)

        status = infer_common_lab_status(test_name, numeric_value, status)
        reference_status = infer_status_from_reference(numeric_value, reference_range)
        if reference_status and status in ["normal", "unknown"]:
            status = reference_status

        severity, severity_reason = lab_severity_score(test_name, numeric_value, status, reference_range)

        if severity > 0:
            abnormal_count += 1
            if status == "critical":
                critical_count += 1
            organ_boost = 0.03 if any(
                t in test_lower for t in
                ["creatinine", "egfr", "bun", "glucose", "a1c", "ldl",
                 "triglyceride", "alt", "ast", "bilirubin", "hemoglobin", "wbc", "platelet"]
            ) else 0.0
            total_severity = severity + organ_boost
            severity_scores.append(total_severity)
            causal_factors.append({
                "factor":      f"{test_name} is {status}",
                "probability": round(min(total_severity, 0.75), 2),
                "cause":       f"Value {value}{unit} — {severity_reason}",
            })
        elif status == "normal":
            normal_count += 1

    diagnosis_text = " ".join(str(d).lower() for d in diagnosis)
    finding_text   = " ".join(str(f).lower() for f in findings)
    combined_text  = f"{diagnosis_text} {finding_text} {raw_lower}"

    for term, weight in {
        "diabetes": 0.12, "kidney": 0.12, "renal": 0.12,
        "cardiac": 0.12,  "heart": 0.12,  "liver": 0.10,
        "hepatic": 0.10,  "infection": 0.08,
        "anemia": 0.07,   "thyroid": 0.06,
    }.items():
        if term in combined_text:
            diagnosis_boost = max(diagnosis_boost, weight)
            causal_factors.append({
                "factor":      f"{term.title()} condition mentioned",
                "probability": round(weight * 2, 2),
                "cause":       "Diagnosis or finding increases clinical follow-up priority.",
            })

    raw_hits = len(re.findall(
        r"\b(high|low|critical|abnormal|elevated|decreased|above normal|below normal|out of range)\b",
        raw_lower,
    ))
    if raw_hits and abnormal_count == 0:
        raw_text_boost = min(0.08 + raw_hits * 0.025, 0.18)
        causal_factors.append({
            "factor":      "Abnormal flags in report text",
            "probability": round(raw_text_boost, 2),
            "cause":       f"{raw_hits} abnormal keyword(s) detected in report text.",
        })

    top_severity       = max(severity_scores) if severity_scores else 0.0
    remaining_severity = max(sum(severity_scores) - top_severity, 0.0)
    severe_count       = sum(1 for s in severity_scores if s >= 0.25)
    abnormal_ratio     = abnormal_count / max(len(labs), 1)
    count_boost        = 0.0
    if abnormal_ratio >= 0.50 and abnormal_count >= 2: count_boost += 0.04
    if abnormal_count >= 3:  count_boost += 0.05
    if abnormal_count >= 5:  count_boost += 0.05
    if critical_count:       count_boost += 0.12

    score = (
        base_score
        + top_severity * 1.05
        + min(remaining_severity * 0.25, 0.16)
        + min(diagnosis_boost, 0.10)
        + raw_text_boost
        + count_boost
    )

    explicit_critical = bool(re.search(
        r"\b(critical|panic value|urgent|emergency|dangerously|immediate medical attention)\b",
        raw_lower,
    ))
    if abnormal_count == 0 and raw_hits == 0:
        score = min(score, 0.16 if normal_count else 0.22)
    if not explicit_critical:
        score = min(score, 0.42 if severe_count == 0 else (0.58 if severe_count == 1 else 0.68))
    elif severe_count <= 1:
        score = min(score, 0.72)

    risk_probability = max(0.05, min(score, 0.95))
    risk_level = "low" if risk_probability < 0.35 else ("high" if risk_probability >= 0.75 else "medium")

    if not causal_factors:
        causal_factors.append({
            "factor":      "No abnormal lab values detected",
            "probability": round(risk_probability, 2),
            "cause":       "All extracted results appear within normal ranges.",
        })

    return {
        "risk_probability":   round(risk_probability, 2),
        "risk_level":         risk_level,
        "causal_factors":     causal_factors[:8],
        "causal_explanation": (
            f"Risk is {risk_level}: {abnormal_count} abnormal and "
            f"{critical_count} critical value(s) identified. "
            "(Rule-based estimate — set ANTHROPIC_API_KEY for Claude-powered assessment.)"
        ),
        "confidence":     0.75 if labs else 0.55,
        "assessed_by":    "rule-based-fallback",
    }


# ============== Agent 7: Bayesian/Causal Agent ==============
def bayesian_agent(state: MedicalReportState) -> MedicalReportState:
    assessment = calculate_risk_assessment(state)
    bayesian = {
        "risk_probability": assessment["risk_probability"],
        "causal_factors": assessment["causal_factors"],
        "causal_explanation": assessment["causal_explanation"],
        "risk_level": assessment["risk_level"],
        "reasoning_chain": "Rule-based inference from abnormal lab count, severity, organ-system markers, findings, and diagnosis terms",
        "confidence": assessment["confidence"]
    }

    suggestions = generate_ai_suggestions(state)
    disease_explanation_en, solution_plan_en = generate_english_disease_education(state)

    return {
        **state,
        "bayesian_analysis": json.dumps(bayesian, indent=2),
        "causal_explanation": bayesian.get("causal_explanation", ""),
        "risk_probability": bayesian.get("risk_probability", 0.2),
        "suggestions": suggestions,
        "disease_explanation_en": disease_explanation_en,
        "solution_plan_en": solution_plan_en,
        # disease_explanation_hi and solution_plan_hi are set by translate_agent
        "disease_explanation_hi": "",
        "solution_plan_hi": "",
    }


# ============== Helper Functions ==============
def get_default_state(raw_text: str, patient_id: str = None, target_lang: str = "Hindi") -> MedicalReportState:
    """Create default state for processing"""
    return {
        "raw_text": raw_text,
        "parsed_data": "",
        "validation_result": "",
        "is_valid": False,
        "medical_summary": "",
        "simplified_explanation": "",
        "translated_explanation": "",
        "target_language": target_lang,
        "temporal_analysis": "",
        "trend_data": "",
        "bayesian_analysis": "",
        "causal_explanation": "",
        "risk_probability": 0.0,
        "suggestions": [],
        "translated_suggestions": [],
        "disease_explanation_en": "",
        "solution_plan_en": "",
        "disease_explanation_hi": "",
        "solution_plan_hi": "",
        "patient_id": patient_id,
        "report_date": datetime.now().isoformat()
    }


def format_final_response(state: MedicalReportState) -> dict:
    """Format the final response for the API"""
    return {
        "status": "success",
        "patient_id": state.get("patient_id"),
        "report_date": state["report_date"],
        "parsed_data": state["parsed_data"],
        "validation": state["validation_result"],
        "medical_summary": state["medical_summary"],
        "simple_explanation": state["simplified_explanation"],
        "translated_explanation": state["translated_explanation"],
        "target_language": state["target_language"],
        "temporal_analysis": state["temporal_analysis"],
        "causal_analysis": state["bayesian_analysis"],
        "risk_probability": state["risk_probability"],
        "suggestions": state["suggestions"],
        "translated_suggestions": state.get("translated_suggestions", []),
        "disease_explanation_en": state.get("disease_explanation_en", ""),
        "solution_plan_en": state.get("solution_plan_en", ""),
        "disease_explanation_hi": state.get("disease_explanation_hi", ""),
        "solution_plan_hi": state.get("solution_plan_hi", "")
    }
