#!/usr/bin/env python3
"""
Test script to verify the Suggestions tab functionality
"""
import requests
import json

def test_suggestions_api():
    """Test the API endpoint to verify translated_suggestions are returned"""

    # Use the text endpoint for testing (easier than file upload)
    test_data = {
        "text": """Medical Report
Patient: John Doe
Date: 2024-01-15

Lab Results:
Glucose: 145 mg/dL (High)
Hemoglobin: 12.5 g/dL (Normal)
Creatinine: 1.8 mg/dL (High)
ALT: 85 U/L (High)

Diagnosis: Diabetes Mellitus, Kidney dysfunction
""",
        "language": "Hindi",
        "patient_id": "test_patient_123"
    }

    try:
        # Make request to the text processing endpoint
        response = requests.post(
            "http://localhost:8000/text/",
            data=test_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ API Response successful")
            print(f"Status: {result.get('status')}")

            # Debug: Check parsed data
            parsed_data = result.get('parsed_data', {})
            print(f"Parsed data type: {type(parsed_data)}")
            if isinstance(parsed_data, str):
                try:
                    parsed_data = json.loads(parsed_data)
                except:
                    print("Could not parse parsed_data JSON")
                    parsed_data = {}

            lab_values = parsed_data.get('lab_values', [])
            print(f"Number of lab values parsed: {len(lab_values)}")
            for lab in lab_values:
                print(f"  Lab: {lab.get('test_name')} = {lab.get('value')} ({lab.get('status')})")

            # Check if translated_suggestions field exists
            if 'translated_suggestions' in result:
                print("✅ translated_suggestions field found")
                suggestions = result.get('translated_suggestions', [])
                print(f"Number of translated suggestions: {len(suggestions)}")

                # Print first few suggestions
                for i, suggestion in enumerate(suggestions[:10]):
                    print(f"Suggestion {i+1}: {suggestion}")

                # Check if suggestions contain disease information
                full_suggestions = result.get('suggestions', [])
                print(f"Number of regular suggestions: {len(full_suggestions)}")
                has_disease_info = any("DISEASE INFORMATION" in str(s) for s in full_suggestions)
                print(f"✅ Disease information included: {has_disease_info}")

                # Print all suggestions to debug
                print("\n--- Regular Suggestions ---")
                for i, suggestion in enumerate(full_suggestions):
                    print(f"Suggestion {i+1}: {suggestion}")

                # Check for specific disease information
                has_diabetes_info = any("ELEVATED BLOOD GLUCOSE" in str(s) for s in full_suggestions)
                has_kidney_info = any("KIDNEY FUNCTION IMPAIRMENT" in str(s) for s in full_suggestions)
                has_liver_info = any("LIVER ENZYME ELEVATION" in str(s) for s in full_suggestions)

                print(f"✅ Diabetes information: {has_diabetes_info}")
                print(f"✅ Kidney information: {has_kidney_info}")
                print(f"✅ Liver information: {has_liver_info}")

                return True
            else:
                print("❌ translated_suggestions field missing")
                print("Available fields:", list(result.keys()))
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Make sure it's running on port 8001")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Suggestions Tab API...")
    success = test_suggestions_api()
    if success:
        print("\n🎉 All tests passed! Suggestions tab should work correctly.")
    else:
        print("\n❌ Tests failed. Please check the implementation.")
