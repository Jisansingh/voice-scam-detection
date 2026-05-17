from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification
)

import torch

MODEL_PATH = "model/transformer_model"

# Load tokenizer and model
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)

model = DistilBertForSequenceClassification.from_pretrained(
    MODEL_PATH
)

model.eval()

def predict(text):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    )

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=1)

    scam_probability = probs[0][1].item()

    if scam_probability > 0.5:
        risk = "HIGH RISK"
    else:
        risk = "LOW RISK"

    return {
        "text": text,
        "scam_probability": round(scam_probability, 4),
        "risk": risk
    }

# Manual tests
if __name__ == "__main__":
    tests = [
        "Your account is blocked share OTP immediately",
        "Meeting tomorrow at 5 PM",
        "Congratulations you won lottery claim reward now"
    ]

    for t in tests:
        result = predict(t)
        print("\n===================")
        print(result)
