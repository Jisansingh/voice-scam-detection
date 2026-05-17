"""
Demo-ready testing samples for voice scam detection
Use these for frontend demos and testing
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'model'))

from improved_inference import ScamDetector

# Initialize detector
detector = ScamDetector()

# Demo scam examples - realistic Indian scam patterns
SCAM_EXAMPLES = [
    {
        "text": "your account is blocked share otp to unblock immediately",
        "expected": "scam",
        "category": "otp_scam",
        "description": "OTP scam - account blocked trick"
    },
    {
        "text": "congratulations you won lottery prize claim money now",
        "expected": "scam",
        "category": "prize_lottery",
        "description": "Prize/lottery scam"
    },
    {
        "text": "sbi bank calling verify your aadhaar kyc update now",
        "expected": "scam",
        "category": "kyc_scam",
        "description": "Bank KYC scam"
    },
    {
        "text": "irs notice arrest warrant issued call immediately",
        "expected": "scam",
        "category": "irs_tax_scam",
        "description": "Tax/legal threat scam"
    },
    {
        "text": "your upi account blocked update kyc to continue",
        "expected": "scam",
        "category": "upi_scam",
        "description": "UPI KYC scam"
    },
    {
        "text": "this is bank security department confirm your cvv number",
        "expected": "scam",
        "category": "bank_fraud",
        "description": "Bank impersonation - CVV request"
    },
    {
        "text": "your son met with accident send money hospital now",
        "expected": "scam",
        "category": "emergency_scam",
        "description": "Emergency/accident scam"
    },
    {
        "text": "paytm wallet suspended update kyc immediately",
        "expected": "scam",
        "category": "upi_scam",
        "description": "Wallet KYC scam"
    },
    {
        "text": "electricity bill unpaid disconnection today pay now",
        "expected": "scam",
        "category": "utility_scam",
        "description": "Utility scam - electricity"
    },
    {
        "text": "amazon suspicious transaction verify your account now",
        "expected": "scam",
        "category": "tech_support",
        "description": "Tech support impersonation"
    }
]

# Demo legitimate examples - normal conversational patterns
LEGITIMATE_EXAMPLES = [
    {
        "text": "meeting scheduled tomorrow at 5 pm",
        "expected": "legit",
        "category": "general",
        "description": "Meeting reminder"
    },
    {
        "text": "your package has been delivered successfully",
        "expected": "legit",
        "category": "delivery",
        "description": "Delivery notification"
    },
    {
        "text": "thank you for your payment",
        "expected": "legit",
        "category": "confirmation",
        "description": "Payment confirmation"
    },
    {
        "text": "your appointment is confirmed for next week",
        "expected": "legit",
        "category": "confirmation",
        "description": "Appointment confirmation"
    },
    {
        "text": "please find attached the requested document",
        "expected": "legit",
        "category": "document",
        "description": "Document sharing"
    },
    {
        "text": "your order has been shipped",
        "expected": "legit",
        "category": "order",
        "description": "Order notification"
    },
    {
        "text": "the meeting has been rescheduled to friday",
        "expected": "legit",
        "category": "meeting",
        "description": "Meeting reschedule"
    },
    {
        "text": "your feedback has been recorded",
        "expected": "legit",
        "category": "feedback",
        "description": "Feedback acknowledgment"
    },
    {
        "text": "please verify your email address",
        "expected": "legit",
        "category": "verification",
        "description": "Email verification request"
    },
    {
        "text": "your request is being processed",
        "expected": "legit",
        "category": "status",
        "description": "Request status update"
    }
]


def run_demo_tests():
    """Run tests on demo samples"""
    print("="*70)
    print("DEMO-READY TESTING SAMPLES")
    print("="*70)

    print("\n📱 SCAM EXAMPLES (10 samples)")
    print("-"*70)

    scam_correct = 0
    for i, sample in enumerate(SCAM_EXAMPLES, 1):
        result = detector.analyze(sample["text"])
        pred_label = "scam" if result["is_scam"] else "legit"
        correct = pred_label == sample["expected"]
        if correct:
            scam_correct += 1

        status = "✅" if correct else "❌"
        print(f"{i}. {status} {sample['text'][:45]}...")
        print(f"   Pred: {result['risk_level']} ({result['scam_probability']:.2f}) | Cat: {result['scam_category']}")
        if result['warnings']:
            print(f"   Warning: {result['warnings'][0][:50]}...")

    print(f"\n📊 Scam Accuracy: {scam_correct}/{len(SCAM_EXAMPLES)}")

    print("\n✅ LEGITIMATE EXAMPLES (10 samples)")
    print("-"*70)

    legit_correct = 0
    for i, sample in enumerate(LEGITIMATE_EXAMPLES, 1):
        result = detector.analyze(sample["text"])
        pred_label = "scam" if result["is_scam"] else "legit"
        correct = pred_label == sample["expected"]
        if correct:
            legit_correct += 1

        status = "✅" if correct else "❌"
        print(f"{i}. {status} {sample['text'][:45]}...")
        print(f"   Pred: {result['risk_level']} ({result['scam_probability']:.2f}) | Cat: {result['scam_category']}")

    print(f"\n📊 Legit Accuracy: {legit_correct}/{len(LEGITIMATE_EXAMPLES)}")

    total_correct = scam_correct + legit_correct
    total = len(SCAM_EXAMPLES) + len(LEGITIMATE_EXAMPLES)

    print("\n" + "="*70)
    print(f"📈 TOTAL ACCURACY: {total_correct}/{total} ({total_correct/total*100:.0f}%)")
    print("="*70)

    return total_correct, total


def generate_json_output():
    """Generate JSON output for API testing"""
    import json

    results = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "model_version": "2.0",
        "scam_samples": [],
        "legit_samples": []
    }

    # Test scam samples
    for sample in SCAM_EXAMPLES:
        result = detector.analyze(sample["text"])
        results["scam_samples"].append({
            "text": sample["text"],
            "expected": sample["expected"],
            "predicted": "scam" if result["is_scam"] else "legit",
            "probability": result["scam_probability"],
            "risk_level": result["risk_level"],
            "category": result["scam_category"],
            "warnings": result["warnings"][:2] if result["warnings"] else []
        })

    # Test legit samples
    for sample in LEGITIMATE_EXAMPLES:
        result = detector.analyze(sample["text"])
        results["legit_samples"].append({
            "text": sample["text"],
            "expected": sample["expected"],
            "predicted": "scam" if result["is_scam"] else "legit",
            "probability": result["scam_probability"],
            "risk_level": result["risk_level"],
            "category": result["scam_category"]
        })

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'demo_results.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 JSON results saved to: {output_path}")
    return results


if __name__ == "__main__":
    run_demo_tests()
    generate_json_output()