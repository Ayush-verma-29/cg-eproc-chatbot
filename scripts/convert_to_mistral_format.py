import json
import os

def convert_to_mistral_format():
    input_file = r"c:\cg-eproc-chatbot\data\qa_dataset.jsonl"
    output_file = r"c:\cg-eproc-chatbot\data\mistral_train_dataset.jsonl"
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        return False
        
    converted = 0
    with open(input_file, "r", encoding="utf-8") as fin, open(output_file, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            sample = json.loads(line)
            
            # Formulate system prompt
            system_prompt = (
                "You are an expert procurement assistant for the Chhattisgarh e-Procurement Portal. "
                "Provide accurate, precise, and verified answers with bracketed citations based strictly on the provided context. "
                "Always treat the Chhattisgarh Store Purchase Rules as the primary authority."
            )
            
            # Map Alpaca to Chat format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{sample['input']}\n\nQuestion: {sample['instruction']}"},
                {"role": "assistant", "content": sample["output"]}
            ]
            
            fout.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
            converted += 1
            
    print(f"Successfully converted {converted} samples to Mistral Chat format at: {output_file}")
    return True

if __name__ == "__main__":
    convert_to_mistral_format()
