import requests
import pandas as pd
import time
import os
from duckduckgo_search import ddg_images

class DuckDuckGoImageScraper:
    def __init__(self, delay=0.5):
        self.delay = delay

    def get_image_link(self, query):
        try:
            results = ddg_images(query, max_results=1)
            if results:
                return results[0]['image']
            else:
                return "No image found"
        except Exception as e:
            print(f"Error fetching image for '{query}': {e}")
            return "Error fetching image"

    def process_items(self, input_file):
        image_data = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                name = line.strip()
                if not name:
                    continue
                print(f"🔍 Searching: {name}")
                image_link = self.get_image_link(name)
                image_data.append({"Product Name": name, "Image Link": image_link})
                time.sleep(self.delay)  # To avoid hammering the service
        return pd.DataFrame(image_data)


def main():
    print("🦆 DuckDuckGo Image Scraper")
    input_path = input("📄 Enter path to text file with product names: ").strip()

    if not os.path.exists(input_path):
        print("❌ File not found.")
        return

    scraper = DuckDuckGoImageScraper()
    df = scraper.process_items(input_path)

    output_file = os.path.splitext(input_path)[0] + "_duckduckgo_images.xlsx"
    df.to_excel(output_file, index=False)
    print(f"\n✅ Done! Saved results to: {output_file} ({len(df)} items)")

if __name__ == "__main__":
    main()