import pandas as pd
import requests
import os
import time

# Google Custom Search API Credentials
API_KEY = "AIzaSyBczIZ_-9tX4L4t0d4-i7HZFyrbiH43PU4"
CX = "c7c8db37722f84c4e"

# Create a folder to store images
image_folder = "medicine_images"
os.makedirs(image_folder, exist_ok=True)

# Function to fetch medicine info from RxNorm
def get_medicine_info(medicine_name):
    search_url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={medicine_name}&search=1"
    
    try:
        response = requests.get(search_url)
        data = response.json()

        # Get RxCUI ID from the response
        rxcui = data.get("idGroup", {}).get("rxnormId", [None])[0]

        if not rxcui:
            return "No description available", "No precautions available", "No usage information available", {"front view": None, "back view": None, "side view": None}

        # Get detailed medicine info from RxNorm
        desc_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json"
        desc_response = requests.get(desc_url)
        desc_data = desc_response.json()

        description = desc_data.get("properties", {}).get("name", "No description available")
        usage = desc_data.get("properties", {}).get("usage", "No usage information available")

        # Get precautions from MedlinePlus
        precautions = get_medicine_precautions(medicine_name)

        # Download multiple view images of the medicine
        image_paths = download_medicine_images(medicine_name)

        return description, precautions, usage, image_paths
    except Exception as e:
        print(f"Error fetching data for {medicine_name}: {e}")
        return "Error fetching data", "Error fetching data", "Error fetching data", {"front view": None, "back view": None, "side view": None}

# Function to fetch precautions from MedlinePlus
def get_medicine_precautions(medicine_name):
    try:
        search_url = f"https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term={medicine_name}+precautions"
        response = requests.get(search_url)
        data = response.text  # XML response

        # Extract precaution content from the XML
        if "<content>" in data:
            start = data.index("<content>") + len("<content>")
            end = data.index("</content>", start)
            precautions = data[start:end].strip()
        else:
            precautions = "No specific precautions found. Consult a doctor before use."

        return precautions
    except Exception as e:
        return "Error fetching data"

# Function to fetch and download multiple views of a medicine
def download_medicine_images(medicine_name):
    views = ["front view", "back view", "side view"]
    image_paths = {}

    for view in views:
        query = f"{medicine_name} {view} medicine"
        search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={CX}&key={API_KEY}&searchType=image"

        try:
            response = requests.get(search_url)
            data = response.json()

            image_url = data["items"][0]["link"]  # Get first image result

            # Download the image
            image_response = requests.get(image_url, stream=True)
            filename = f"{medicine_name.replace(' ', '_')}_{view.replace(' ', '_')}.jpg"
            image_path = os.path.join(image_folder, filename)

            with open(image_path, "wb") as file:
                for chunk in image_response.iter_content(1024):
                    file.write(chunk)

            image_paths[view] = image_path
        except Exception as e:
            print(f"Error fetching {view} image for {medicine_name}: {e}")
            image_paths[view] = None

    return image_paths

# Read the sheet containing the medicine names
file_path = "/Users/divyanshbarodiya/Downloads/Medicine_name1.xlsx"  # Change this to your file path
df = pd.read_excel(file_path) if file_path.endswith(".xlsx") else pd.read_csv(file_path)

# Assuming the first column contains the medicine names
medicine_names = df.iloc[:, 0].tolist()

# List to hold extracted data for each medicine
medicine_data = []

# Loop through each medicine and fetch details
for medicine in medicine_names:
    description, precautions, usage, image_paths = get_medicine_info(medicine)
    medicine_data.append([
        medicine,
        description,
        precautions,
        usage,
        image_paths.get("front view"),
        image_paths.get("back view"),
        image_paths.get("side view")
    ])
    time.sleep(1)  # Prevent API rate limiting

# Save the data to a new CSV file
output_df = pd.DataFrame(medicine_data, columns=[
    "Medicine Name", "Description", "Precautions", "Usage",
    "Front View Image Path", "Back View Image Path", "Side View Image Path"
])
output_df.to_csv("medicine_details.csv", index=False)

print(f"Medicine details saved to medicine_details.csv")
print(f"Images saved in '{image_folder}' folder")
