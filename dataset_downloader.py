# dataset_downloader.py
import os
from datasets import load_dataset
import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi

def download_common_voice_hf():
    """Download Common Voice from HuggingFace (Recommended Method)"""
    print("Downloading Common Voice dataset from HuggingFace...")
    
    # Download English dataset with streaming to save space
    cv_dataset = load_dataset(
        "mozilla-foundation/common_voice_12_0", 
        "en", 
        split="train",
        streaming=True  # Use streaming for large dataset
    )
    
    print("Dataset loaded successfully!")
    return cv_dataset

def download_common_voice_kaggle():
    """Alternative: Download from Kaggle"""
    print("Downloading Common Voice from Kaggle...")
    
    # Authenticate Kaggle API
    api = KaggleApi()
    api.authenticate()
    
    # Download dataset
    api.dataset_download_files(
        'mozillaorg/common-voice',
        path='./downloaded_datasets',
        unzip=True
    )
    
    print("Dataset downloaded to ./downloaded_datasets")

if __name__ == "__main__":
    # Use HuggingFace method (recommended)
    dataset = download_common_voice_hf()
    
    # Or use Kaggle method
    # download_common_voice_kaggle()
