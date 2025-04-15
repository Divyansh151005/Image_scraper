import pandas as pd
import requests
import os
import time

# Google Custom Search API credentials
API_KEY = "AIzaSyBczIZ_-9tX4L4t0d4-i7HZFyrbiH43PU4"
CX = "c7c8db37722f84c4e"

# Folder to save images
image_folder = "medicine_images"
os.makedirs(image_folder, exist_ok=True)

# -------- Fetch medicine description, usage, and precautions -------- #
def get_medicine_info(medicine_name):
    search_url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={medicine_name}&search=1"
    try:
        response = requests.get(search_url)
        data = response.json()
        rxcui = data.get("idGroup", {}).get("rxnormId", [None])[0]

        if not rxcui:
            return "No description", "No precautions", "No usage", None, None, None

        # Get detailed medicine info
        desc_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json"
        desc_response = requests.get(desc_url)
        desc_data = desc_response.json()
        description = desc_data.get("properties", {}).get("name", "No description available")
        usage = desc_data.get("properties", {}).get("usage", "No usage info")

        # Precautions from MedlinePlus
        precautions = get_medicine_precautions(medicine_name)

        # Get multiple views
        front, back, side = download_medicine_images(medicine_name)

        return description, precautions, usage, front, back, side
    except Exception as e:
        print(f"Error fetching data for {medicine_name}: {e}")
        return "Error", "Error", "Error", None, None, None

# -------- Get precautions from MedlinePlus -------- #
def get_medicine_precautions(medicine_name):
    try:
        search_url = f"https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term={medicine_name}+precautions"
        response = requests.get(search_url)
        data = response.text
        if "<content>" in data:
            start = data.index("<content>") + len("<content>")
            end = data.index("</content>", start)
            return data[start:end].strip()
        return "No specific precautions found. Consult a doctor."
    except:
        return "Error fetching precautions"

# -------- Download multiple views of the medicine -------- #
def download_medicine_images(medicine_name):
    views = ["front", "back", "side"]
    image_paths = []

    for view in views:
        query = f"{medicine_name} {view} view medicine"
        search_url = (
            f"https://www.googleapis.com/customsearch/v1?q={query}"
            f"&cx={CX}&key={API_KEY}&searchType=image"
        )
        try:
            print ("WWWWWWWWWWW")
            response = requests.get(search_url)
            data = response.json()
            print(f"[{view.upper()} VIEW URL]: {image_url}")


            image_url = data["items"][0]["link"]
            print(f"[{medicine_name} - {view.upper()}]: {image_url}")

            image_path = os.path.join(image_folder, f"{medicine_name}_{view}.jpg")
            image_response = requests.get(image_url, stream=True)

            if image_response.status_code == 200:
                with open(image_path, "wb") as file:
                    for chunk in image_response.iter_content(1024):
                        file.write(chunk)
                print(f"✅ Saved {view} view to {image_path}")
                image_paths.append(image_path)
            else:
                print(f"❌ Failed to download {view} image. HTTP Status: {image_response.status_code}")
                image_paths.append("Download failed")
        except Exception as e:
            print(f"⚠️ Error downloading {view} image for {medicine_name}: {e}")
            image_paths.append("Not Found")

    return image_paths[0], image_paths[1], image_paths[2]


# -------- Read the medicine names from file -------- #
file_path = "/Users/divyanshbarodiya/Downloads/Tablets_name.xlsx"  # Update path if needed
df = pd.read_excel(file_path) if file_path.endswith(".xlsx") else pd.read_csv(file_path)
medicine_names = df.iloc[:, 0].tolist()

# -------- Process each medicine -------- #
medicine_data = []

for medicine in medicine_names:
    print(f"Processing: {medicine}")
    desc, prec, usage, front, back, side = get_medicine_info(medicine)
    medicine_data.append([medicine, desc, prec, usage, front, back, side])
    time.sleep(1)  # Prevent rate limiting

# -------- Save to CSV -------- #
output_df = pd.DataFrame(medicine_data, columns=[
    "Medicine Name", "Description", "Precautions", "Usage", "Front View", "Back View", "Side View"
])
output_df.to_csv("medicine_details.csv", index=False)

print("\n✅ Medicine details saved to `medicine_details.csv`")
print(f"✅ Images saved in `{image_folder}` folder")
