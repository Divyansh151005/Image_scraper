import requests
import pandas as pd
import time
import os

class ProductImageScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        # Google Custom Search API credentials
        self.API_KEY = ""
        self.CX = ""

    def get_image_link(self, item_name):
        """Get image link for the item using Google Custom Search API."""
        search_url = f"https://www.googleapis.com/customsearch/v1?q={item_name}&cx={self.CX}&key={self.API_KEY}&searchType=image"
        try:
            response = requests.get(search_url)
            data = response.json()
            if "items" in data and data["items"]:
                return data["items"][0]["link"]
            else:
                return "No image found"
        except Exception as e:
            print(f"Error fetching image for {item_name}: {e}")
            return "Error fetching image"

    def process_items(self, file_path):
        """Read item names from file and return DataFrame with name and image link."""
        image_data = []

        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                name = line.strip()
                if not name:
                    continue
                print(f"Fetching image for: {name}")
                image_link = self.get_image_link(name)
                image_data.append({
                    "name": name,
                    "image_link": image_link
                })
                time.sleep(0.5)  # Avoid hitting API rate limits

        return pd.DataFrame(image_data)

def main():
    print("Product Image Scraper")
    print("---------------------")

    input_file = input("Enter the path to the text file containing product names: ")

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    scraper = ProductImageScraper()
    try:
        df = scraper.process_items(input_file)
        output_file = os.path.splitext(input_file)[0] + "_images.xlsx"
        df.to_excel(output_file, index=False)
        print(f"\nImage scraping complete! {len(df)} items processed.")
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
