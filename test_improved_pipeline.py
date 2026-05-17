#!/usr/bin/env python3
"""
Quick test script for improved ML pipeline
Usage: python test_improved_pipeline.py
"""
import sys
import os

# Add model directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'model'))

from improved_inference import ScamDetector, create_api_response

def main():
    print("="*70)
    print("VOICE SCAM DETECTOR - IMPROVED PIPELINE TEST")
    print("="*70)

    # Initialize detector
    print("\n🔄 Initializing detector...")
    detector = ScamDetector()
    print(f"   ML Model: {'Loaded' if detector.model else 'Not available'}")
    print(f"   Vectorizer: {'Loaded' if detector.vectorizer else 'Not available'}")

    # Test cases
    test_cases = [
        # Scam examples
        ("Your account has been compromised share OTP immediately", True, "bank_fraud"),
        ("Congratulations you won a lottery claim your reward now", True, "prize_lottery"),
        ("IRS Notice: Arrest warrant issued - call immediately", True, "irs_tax_scam"),
        ("This is bank security please confirm your CVV number", True, "bank_fraud"),
        ("Your electricity will be disconnected pay bill now", True, "utility_scam"),

        # Legitimate examples
        ("Meeting scheduled tomorrow at 5 PM", False, None),
        ("Your package has been delivered successfully", False, None),
        ("Thank you for your payment", False, None),
        ("Project review meeting is postponed", False, None),
        ("Please find attached the requested document", False, None),
    ]

    print("\n" + "-"*70)
    print("TEST RESULTS")
    print("-"*70)

    correct = 0
    total = len(test_cases)

    for text, is_scam_expected, expected_category in test_cases:
        result = detector.analyze(text)
        is_scam_predicted = result['is_scam']
        category = result['scam_category']

        # Check correctness
        correct_prediction = is_scam_predicted == is_scam_expected

        # For scams, also check category (approximate)
        if is_scam_expected and expected_category:
            category_match = expected_category in category
        else:
            category_match = True

        status = "✅" if correct_prediction else "❌"

        if correct_prediction:
            correct += 1

        print(f"\n{status} {text[:50]}...")
        print(f"   Expected: {'SCAM' if is_scam_expected else 'LEGIT'} | Predicted: {result['risk_level']}")
        print(f"   Probability: {result['scam_probability']:.2f} | Category: {category}")

        if result['warnings']:
            print(f"   Warnings: {len(result['warnings'])}")
            for w in result['warnings'][:2]:
                print(f"      - {w}")

    print("\n" + "-"*70)
    print(f"ACCURACY: {correct}/{total} ({correct/total*100:.0f}%)")
    print("-"*70)

    # Test API format
    print("\n📋 API Response Format Test:")
    result = detector.analyze(test_cases[0][0])
    api_response = create_api_response(result)

    print(f"\n✓ success: {api_response['success']}")
    print(f"✓ timestamp: {api_response['timestamp']}")
    print(f"✓ result.scam_probability: {api_response['result']['scam_probability']}")
    print(f"✓ result.is_scam: {api_response['result']['is_scam']}")
    print(f"✓ result.risk_level: {api_response['result']['risk_level']}")
    print(f"✓ result.scam_category: {api_response['result']['scam_category']}")
    print(f"✓ result.recommendation: {api_response['result']['recommendation']}")
    print(f"✓ result.warnings: {len(api_response['result']['warnings'])} warnings")
    print(f"✓ details.analysis: {len(api_response['details']['analysis'])} components")

    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()