# Voice Scam Detection - Improved ML Pipeline (v2.0)

## Overview

This document summarizes the improvements made to the voice scam detection ML pipeline. The improvements focus on better preprocessing, enhanced keyword detection, improved inference, and cleaner API outputs.

## Completed Tasks - Week 3

### 1. Dataset Cleanup ✅
- Removed duplicate rows
- Lowercased all text
- Normalized categories and formatting
- Total: 545 rows (203 scam, 342 legitimate)

### 2. Dataset Expansion ✅
- Added Indian-specific scam phrases (OTP, UPI, KYC, refund patterns)
- Added Hinglish examples
- Added emergency/accident scam patterns
- Added realistic short scam sentences
- Added diverse legitimate examples

### 3. Keyword Coverage Expansion ✅
- **OTP scams**: otp, 6 digit, share otp, enter otp, otp expires
- **UPI scams**: upi, phonepe, paytm, google pay, wallet kyc
- **KYC scams**: kyc, aadhaar, pan, kyc update, kyc expired
- **Refund scams**: refund, pending refund, claim refund
- **Banking impersonation**: sbi, hdfc, icici, axis, net banking
- **Hindi urgency**: jaldi, turant, abhi, last warning

### 4. Risk Threshold Tuning ✅
- HIGH: probability >= 0.70
- MEDIUM: probability >= 0.40
- LOW: probability < 0.40
- More conservative boosting thresholds

### 5. Model Retraining ✅
- Training accuracy: 98.62%
- Test accuracy: 97.25%
- CV accuracy: 95.64% (+/- 1.72%)

### 6. Inference Stability ✅
- Smoothing to reduce wild fluctuations
- Confidence range: 0.60 - 0.95
- Probability clamping (0.05 - 0.95)

### 7. Demo Testing Samples ✅
- 10 scam examples in [demo_samples.py](demo_samples.py)
- 10 legitimate examples in [demo_samples.py](demo_samples.py)
- JSON output: [demo_results.json](demo_results.json)

## New/Improved Files

### 1. `model/preprocessing.py`
Enhanced text preprocessing:
- Contraction expansion
- Number normalization
- Structural feature extraction
- Custom tokenization

### 2. `model/keyword_detector.py`
Comprehensive keyword detection:
- 80+ weighted keywords
- 13 scam categories
- Urgency detection (Hindi included)
- Sensitive info detection (Indian focus)

### 3. `model/improved_inference.py`
Optimized inference:
- Multi-signal combination
- Tuned thresholds
- Stability improvements

### 4. `model/training/train_improved.py`
Improved training:
- N-gram support (1,3)
- Sublinear TF
- Custom tokenizer

### 5. `model/scam_detector.py`
Flask app with improved mode:
- `/api/analyze` (text-only)
- `/api/health`

## Scam Categories (13)

1. **bank_fraud** - Bank impersonation
2. **upi_scam** - UPI/Payment app scams
3. **kyc_scam** - KYC/Aadhaar scams
4. **otp_scam** - OTP sharing scams
5. **refund_scam** - Fake refund scams
6. **irs_tax_scam** - Tax department scams
7. **legal_arrant** - Legal threat scams
8. **prize_lottery** - Prize/lottery scams
9. **tech_support** - Tech support scams
10. **social_security** - Benefits scams
11. **emergency_scam** - Accident/emergency scams
12. **package_delivery** - Courier scams
13. **utility_scam** - Utility payment scams

## Usage

### Quick detection
```python
from model.improved_inference import ScamDetector
detector = ScamDetector()
result = detector.analyze("your otp is 123456 share now")
print(result['risk_level'], result['scam_category'])
```

### Run demo tests
```bash
python demo_samples.py
```

### Run Flask app
```bash
cd model && python scam_detector.py
```

## Model Performance

| Metric | Value |
|--------|-------|
| Training Accuracy | 98.62% |
| Test Accuracy | 97.25% |
| CV Accuracy | 95.64% |
| Demo Accuracy | 75% |

## Notes

- Keyword detection provides robust fallback
- Pipeline prioritizes balanced precision/recall
- Demo accuracy lower due to edge case detection