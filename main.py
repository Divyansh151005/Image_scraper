import google.generativeai as genai
import pandas as pd
import json
import time
import os
import argparse
from tqdm import tqdm
import random
import sys
from datetime import datetime

def setup_args():
    parser = argparse.ArgumentParser(description='Extract medicine information using Google Gemini API')
    parser.add_argument('--input', '-i', type=str, required=True, help='Path to text file with medicine names')
    parser.add_argument('--output', '-o', type=str, default='medicine_info.xlsx', help='Output Excel file path')
    parser.add_argument('--delay', '-d', type=float, default=5.0, help='Minimum delay between API calls in seconds')
    parser.add_argument('--max-retries', '-r', type=int, default=5, help='Maximum number of retries for quota errors')
    parser.add_argument('--checkpoint', '-c', type=str, default='checkpoint.json', help='Checkpoint file to resume from')
    return parser.parse_args()

def find_available_model():
    """Find an available Gemini model that works"""
    print("Searching for available Gemini models...")
    
    # List of model names to try in order of preference
    model_candidates = [
        "gemini-pro", 
        "gemini-1.0-pro",
        "gemini-1.5-pro", 
        "gemini-1.5-flash",
        "models/gemini-pro",
        "models/gemini-1.0-pro",
        "models/gemini-1.5-pro"
    ]
    
    # First try to list models
    try:
        available_models = []
        for m in genai.list_models():
            model_name = m.name
            print(f"- Found model: {model_name}")
            available_models.append(model_name)
            
            # Extract the short name if it's in the format "models/X"
            if "/" in model_name:
                short_name = model_name.split("/")[-1]
                if short_name not in model_candidates:
                    model_candidates.append(short_name)
                    
        print(f"Found {len(available_models)} available models")
        
        # If we found models that support text generation, try them first
        gemini_models = [m for m in available_models if "gemini" in m.lower()]
        if gemini_models:
            print(f"Will try these Gemini models first: {gemini_models}")
            model_candidates = gemini_models + [m for m in model_candidates if m not in gemini_models]
    except Exception as e:
        print(f"Could not list models: {str(e)}")
    
    # Try each model candidate
    for model_name in model_candidates:
        try:
            print(f"Trying model: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            # Test the model with a simple prompt
            test_response = model.generate_content("Hello, test message")
            print(f"✅ Successfully tested model: {model_name}")
            return model
        except Exception as e:
            print(f"❌ Model {model_name} failed: {str(e)}")
    
    raise ValueError("Could not find any working Gemini model. Please check your API key and available models.")

def get_medicine_info(model, medicine_name, max_retries=5):
    """Get structured medicine information from Gemini API with retry logic"""
    prompt = f"""
Provide detailed information about the medicine: {medicine_name}

Return ONLY a valid JSON object with this exact structure:
{{
  "type": "medicine",
  "generic_name": "",
  "brand_names": [],
  "drug_class": "",
  "uses": "",
  "dosage_forms": "",
  "side_effects": "",
  "warnings_precautions": "",
  "contraindications": "",
  "price_range_inr": ""
}}

Fill all fields with accurate information. If any information is unknown, use "Not available" as the value.
Return ONLY the JSON with no additional text or markdown formatting.
"""
    retry_count = 0
    while retry_count <= max_retries:
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            
            # Extract just the JSON part
            json_start = raw_text.find("{")
            json_end = raw_text.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No valid JSON found in response")
                
            clean_json = raw_text[json_start:json_end]
            parsed = json.loads(clean_json)
            
            # Add the original name as searched
            parsed["item_name"] = medicine_name
            return parsed
            
        except Exception as e:
            error_str = str(e)
            
            # Handle quota error specifically
            if "429" in error_str and "quota" in error_str:
                retry_count += 1
                if retry_count <= max_retries:
                    # Extract retry delay if present
                    retry_delay = 60  # Default delay
                    if "retry_delay" in error_str and "seconds:" in error_str:
                        try:
                            delay_start = error_str.find("seconds:") + 8
                            delay_end = error_str.find("}", delay_start)
                            retry_delay = int(error_str[delay_start:delay_end].strip())
                        except:
                            pass  # Use default if parsing fails
                    
                    # Add some jitter to avoid synchronized retries
                    retry_delay += random.uniform(1, 5)
                    
                    print(f"\n⚠️ Quota exceeded. Waiting {retry_delay:.1f} seconds before retry {retry_count}/{max_retries}...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return {
                        "item_name": medicine_name,
                        "error": "Quota exceeded after maximum retries",
                        "type": "quota_error"
                    }
            # Handle model not found error
            elif "404" in error_str and "not found" in error_str:
                return {
                    "item_name": medicine_name,
                    "error": "Model error: " + error_str,
                    "type": "model_error"
                }
            else:
                # For other errors, just return the error without retrying
                print(f"Error processing {medicine_name}: {error_str}")
                return {
                    "item_name": medicine_name,
                    "error": error_str,
                    "type": "error"
                }

def save_to_excel(data, output_path):
    """Save the medicine data to an Excel file"""
    if not data:
        print("No data to save")
        return
        
    df = pd.DataFrame(data)
    
    # Reorganize columns to put item_name first
    columns = ['item_name']
    for col in df.columns:
        if col not in ['item_name', 'error', 'type']:
            columns.append(col)
    if 'error' in df.columns:
        columns.append('error')
    if 'type' in df.columns:
        columns.append('type')
    
    # Only include columns that actually exist
    columns = [col for col in columns if col in df.columns]
    df = df[columns]
    df.to_excel(output_path, index=False)
    print(f"✅ Saved structured medicine data to '{output_path}'")

def save_checkpoint(data, processed_names, checkpoint_file):
    """Save progress to a checkpoint file"""
    checkpoint = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processed_data": data,
        "processed_names": processed_names
    }
    
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f)
    
    print(f"📝 Saved checkpoint to {checkpoint_file}")

def load_checkpoint(checkpoint_file):
    """Load progress from a checkpoint file"""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        
        print(f"📋 Loaded checkpoint from {checkpoint_file} (saved: {checkpoint['timestamp']})")
        return checkpoint["processed_data"], checkpoint["processed_names"]
    
    return [], set()

def main():
    # Configure API key
    api_key = ""
    genai.configure(api_key=api_key)
    
    args = setup_args()
    
    try:
        # Find an available and working model
        model = find_available_model()

        # Load medicine names
        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Input file not found: {args.input}")
        
        with open(args.input, "r") as file:
            all_medicine_names = [line.strip() for line in file if line.strip()]
        
        print(f"Loaded {len(all_medicine_names)} medicine names from {args.input}")
        
        # Load checkpoint if exists
        all_data, processed_names = load_checkpoint(args.checkpoint)
        processed_names_set = set(processed_names)
        
        # Filter out already processed medicines
        medicine_names = [med for med in all_medicine_names if med not in processed_names_set]
        
        if len(medicine_names) == 0:
            print("✅ All medicines have been processed already!")
            save_to_excel(all_data, args.output)
            return
        
        print(f"Processing {len(medicine_names)} remaining medicines...")
        
        # Process each medicine with quota handling
        checkpoint_frequency = max(1, min(10, len(medicine_names) // 5))  # Save checkpoint every ~20% of medicines
        
        for i, med in enumerate(tqdm(medicine_names, desc="Processing medicines")):
            try:
                result = get_medicine_info(model, med, max_retries=args.max_retries)
                all_data.append(result)
                processed_names_set.add(med)
                
                # Add jitter to delay to avoid predictable patterns
                delay = args.delay + random.uniform(0.5, 2.0)
                time.sleep(delay)
                
                # Save checkpoint periodically
                if (i + 1) % checkpoint_frequency == 0:
                    save_checkpoint(all_data, list(processed_names_set), args.checkpoint)
                    
            except KeyboardInterrupt:
                print("\n🛑 Processing interrupted by user. Saving progress...")
                save_checkpoint(all_data, list(processed_names_set), args.checkpoint)
                save_to_excel(all_data, args.output)
                sys.exit(0)
                
            except Exception as e:
                print(f"\n⚠️ Unexpected error processing {med}: {str(e)}")
                all_data.append({
                    "item_name": med,
                    "error": str(e),
                    "type": "unexpected_error"
                })
        
        # Save final results
        save_to_excel(all_data, args.output)
        
        # Clean up checkpoint if everything completed successfully
        if len(processed_names_set) == len(all_medicine_names):
            if os.path.exists(args.checkpoint):
                os.remove(args.checkpoint)
                print(f"🧹 Removed checkpoint file as all processing completed")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()