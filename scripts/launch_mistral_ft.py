import requests
import os
import json
import time

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "kD2gfSxmPAPIJ5mvoqdAYX7ebfW6D827")
TRAIN_FILE_PATH = r"c:\cg-eproc-chatbot\data\mistral_train_dataset.jsonl"

def upload_file(api_key, file_path):
    print("Uploading training file to Mistral AI...")
    url = "https://api.mistral.ai/v1/files"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    with open(file_path, "rb") as f:
        files = {
            "file": (os.path.basename(file_path), f),
            "purpose": (None, "fine-tune")
        }
        r = requests.post(url, headers=headers, files=files)
        
    if r.status_code != 200:
        print(f"Error uploading file: {r.status_code} - {r.text}")
        return None
        
    file_info = r.json()
    file_id = file_info.get("id")
    print(f"[Success] Upload successful. File ID: {file_id}")
    return file_id

def launch_fine_tune(api_key, file_id, base_model="open-mistral-7b"):
    print(f"Initiating fine-tuning job on base model '{base_model}'...")
    url = "https://api.mistral.ai/v1/fine_tuning/jobs"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": base_model,
        "training_files": [file_id],
        "validation_files": [],
        "hyperparameters": {
            "training_steps": 300,  # ~3 epochs for 2000 samples with typical batch size
            "learning_rate": 0.00001
        }
    }
    
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print(f"Error launching job: {r.status_code} - {r.text}")
        return None
        
    job_info = r.json()
    job_id = job_info.get("id")
    print(f"[Started] Fine-tuning job successfully created! Job ID: {job_id}")
    print(f"Job Status: {job_info.get('status')}")
    return job_info

def main():
    if not MISTRAL_API_KEY:
        print("Error: Mistral API Key not configured.")
        return
        
    file_id = upload_file(MISTRAL_API_KEY, TRAIN_FILE_PATH)
    if not file_id:
        return
        
    # Wait for the file to be processed
    print("Waiting 10 seconds for Mistral to validate the file...")
    time.sleep(10)
    
    # Try with open-mistral-7b
    job = launch_fine_tune(MISTRAL_API_KEY, file_id, "open-mistral-7b")
    if not job:
        print("\nRetrying with alternative base model 'open-mistral-nemo'...")
        launch_fine_tune(MISTRAL_API_KEY, file_id, "open-mistral-nemo")

if __name__ == "__main__":
    main()
