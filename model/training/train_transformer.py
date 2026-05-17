from datasets import Dataset
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)

# Simple starter dataset
import pandas as pd

# Load CSV dataset
df = pd.read_csv("datasets/scam_dataset.csv")

dataset = Dataset.from_pandas(df)

# Load tokenizer
tokenizer = DistilBertTokenizer.from_pretrained(
    "distilbert-base-uncased"
)

# Tokenization
def tokenize(example):
    return tokenizer(
        example["text"],
        padding="max_length",
        truncation=True,
        max_length=128
    )

dataset = dataset.map(tokenize)

# Load model
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=2
)

# Training config
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=5,
    per_device_train_batch_size=2,
    logging_steps=1,
    save_strategy="no"
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset
)

# Train
trainer.train()

# Save model
model.save_pretrained("model/transformer_model")
tokenizer.save_pretrained("model/transformer_model")

print("✅ Transformer model saved!")
