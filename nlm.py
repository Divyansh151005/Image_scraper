import pandas as pd
import requests
import time
import os

# Google Custom Search API Credentials
API_KEY = ""
CX = ""

# Create folder for images
image_folder = "medicine_images"
os.makedirs(image_folder, exist_ok=True)

# Function to get description from RxNorm if available
def get_medicine_description(medicine_name):
    search_url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={medicine_name}&search=1"
    try:
        response = requests.get(search_url)
        data = response.json()
        rxcui = data.get("idGroup", {}).get("rxnormId", [None])[0]
        if not rxcui:
            return "No description available"
        desc_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json"
        desc_response = requests.get(desc_url)
        desc_data = desc_response.json()
        return desc_data.get("properties", {}).get("synonym", "No description available")
    except:
        return "Error fetching description"

# Function to get and download the image (works for all types)
def download_item_image(item_name):
    search_url = f"https://www.googleapis.com/customsearch/v1?q={item_name}&cx={CX}&key={API_KEY}&searchType=image"
    try:
        response = requests.get(search_url)
        data = response.json()
        if "items" not in data or not data["items"]:
            print(f"No image found for {item_name}")
            return None
        image_url = data["items"][0]["link"]
        image_response = requests.get(image_url, stream=True)
        image_path = os.path.join(image_folder, f"{item_name}.jpg")
        with open(image_path, "wb") as file:
            for chunk in image_response.iter_content(1024):
                file.write(chunk)
        return image_path
    except Exception as e:
        print(f"Error downloading image for {item_name}: {e}")
        return None

# Load items from text file
text_file_path = "/Users/divyanshbarodiya/Downloads/Medicine_images /medicine_list.txt"  # use the uploaded file path
with open(text_file_path, "r") as file:
    item_names = [line.strip() for line in file if line.strip()]

# Store extracted data
item_data = []

for item in item_names:
    print(f"Processing: {item}")
    description = get_medicine_description(item)
    image_path = download_item_image(item)
    item_data.append([item, description, image_path])
    time.sleep(1)  # Respect API rate limits

# Save results
output_df = pd.DataFrame(item_data, columns=["Item Name", "Description", "Image Path"])
output_df.to_csv("item_details.csv", index=False)

print("✅ Details saved to item_details.csv")
print(f"📁 Images saved in {image_folder}")


