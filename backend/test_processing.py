#!/usr/bin/env python3
"""
Test script to run the medical report processing pipeline locally
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Mock the LLM to avoid Ollama dependency
class MockLLM:
    def invoke(self, prompt):
        if "parse" in prompt.lower():
            return '{"patient_info": {"name": "John Doe", "age": 35}, "lab_values": [{"test_name": "Vitamin D", "value": 15, "unit": "ng/mL", "status": "low"}]}'
        elif "validate" in prompt.lower():
            return '{"is_valid": true, "issues": [], "confidence": 0.9}'
        elif "summary" in prompt.lower():
            return "Patient has Vitamin D deficiency with low levels at 15 ng/mL."
        elif "simplify" in prompt.lower():
            return "Your Vitamin D is too low. You need more sun or supplements."
        elif "translate" in prompt.lower():
            return "आपका विटामिन डी बहुत कम है। आपको अधिक धूप या सप्लीमेंट की आवश्यकता है।"
        elif "temporal" in prompt.lower():
            return '{"trends": [{"test": "Vitamin D", "status": "persistently_low"}], "pattern_detected": "Low Vitamin D levels"}'
        elif "bayesian" in prompt.lower():
            return '{"risk_probability": 0.7, "causal_factors": [{"factor": "Vitamin D deficiency", "probability": 0.8}], "risk_level": "high"}'
        else:
            return "Mock response"

# Monkey patch before importing agents
sys.modules['langchain_ollama'] = type('MockModule', (), {'OllamaLLM': lambda **kwargs: MockLLM()})()

import agents

def test_processing():
    # Sample text for testing
    sample_text = """
    Patient Name: John Doe
    Age: 35
    Gender: Male

    Lab Results:
    - Vitamin D: 15 ng/mL (Normal: 30-100 ng/mL) - Low
    - Calcium: 9.2 mg/dL (Normal: 8.5-10.5 mg/dL) - Normal
    - Phosphorus: 3.5 mg/dL (Normal: 2.5-4.5 mg/dL) - Normal
    - TSH: 2.5 mIU/L (Normal: 0.4-4.0 mIU/L) - Normal

    Diagnosis: Vitamin D deficiency
    """

    print("Testing medical report processing pipeline...")
    print("=" * 50)

    # Create initial state
    initial_state = agents.get_default_state(
        raw_text=sample_text,
        patient_id="test_patient",
        target_lang="Hindi"
    )

    print("1. Parsing data...")
    parsed_state = agents.parse_agent(initial_state)
    print(f"   Parsed data: {parsed_state['parsed_data'][:200]}...")

    print("2. Validating data...")
    validated_state = agents.validation_agent(parsed_state)
    print(f"   Validation result: {validated_state['validation_result']}")

    print("3. Summarizing...")
    summary_state = agents.summary_agent(validated_state)
    print(f"   Medical summary: {summary_state['medical_summary'][:200]}...")

    print("4. Simplifying explanation...")
    simplified_state = agents.simplify_agent(summary_state)
    print(f"   Simple explanation: {simplified_state['simplified_explanation'][:200]}...")

    print("5. Translating...")
    translated_state = agents.translate_agent(simplified_state)
    print(f"   Translated explanation: {translated_state['translated_explanation'][:200]}...")

    print("6. Temporal analysis...")
    temporal_state = agents.temporal_agent(translated_state)
    print(f"   Temporal analysis: {temporal_state['temporal_analysis'][:200]}...")

    print("7. Bayesian analysis...")
    result = agents.bayesian_agent(temporal_state)
    print(f"   Risk probability: {result['risk_probability']}")

    # Format final response
    response = agents.format_final_response(result)
    print("\nFinal Response:")
    print("=" * 50)
    print(f"Status: {response['status']}")
    print(f"Patient ID: {response['patient_id']}")
    print(f"Risk Probability: {response['risk_probability']}")
    print(f"Suggestions: {response['suggestions']}")

    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_processing()