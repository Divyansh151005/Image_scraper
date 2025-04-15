import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import os
import json

class EnhancedMedicineScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Dictionary of known medicine types based on common suffixes
        self.medicine_forms = {
            'TAB': 'tablet',
            'TABLET': 'tablet',
            'CAP': 'capsule',
            'CAPS': 'capsule',
            'CAPSULE': 'capsule',
            'INJ': 'injection',
            'INJECTION': 'injection',
            'SYP': 'syrup',
            'SYRUP': 'syrup',
            'SPRAY': 'spray',
            'GEL': 'gel',
            'CREAM': 'cream',
            'OINTMENT': 'ointment',
            'LOTION': 'lotion',
            'DROPS': 'drops',
            'SUSP': 'suspension',
            'SUSPENSION': 'suspension'
        }
        
        # Terms indicating non-medicine products
        self.non_medicine_terms = [
            'PERFUME', 'PERFUEM', 'FACE WASH', 'CONDITIONER', 'SOAP', 'SHAMPOO', 
            'DEODORANT', 'COSMETIC', 'BEAUTY', 'WILD STONE'
        ]
        
        # Google Custom Search API Credentials
        self.API_KEY = "AIzaSyBczIZ_-9tX4L4t0d4-i7HZFyrbiH43PU4"
        self.CX = "c7c8db37722f84c4e"
        
        # External medicine information database file path
        self.db_file = "medicine_info_database.json"
        
        # Create or load medicine database
        self._initialize_medicine_database()

    def _initialize_medicine_database(self):
        """Initialize database or create a template database file if not exists"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.medicine_db = json.load(f)
                print(f"Loaded medicine database with {len(self.medicine_db)} entries")
            else:
                # Create a template database file
                self.medicine_db = self._create_template_database()
                with open(self.db_file, 'w', encoding='utf-8') as f:
                    json.dump(self.medicine_db, f, indent=4)
                print(f"Created new medicine database template file: {self.db_file}")
        except Exception as e:
            print(f"Error initializing database: {e}")
            self.medicine_db = {}

    def _create_template_database(self):
        """Create a template database with common medicine categories"""
        return {
            "antifungal_medicine": {
                "type": "medicine",
                "uses": "Used to treat fungal infections including infections of the skin, hair, nails, and internal infections.",
                "precautions": "Inform your doctor if you have liver disease, kidney disease, or allergies to similar medications. May interact with other drugs. Use with caution during pregnancy.",
                "side_effects": "Common side effects include headache, nausea, stomach pain, diarrhea, dizziness, and skin reactions. Severe allergic reactions are rare but possible.",
                "form": "tablet",
                "price_inr": "200-300",
                "description": "An antifungal medication that fights infections caused by fungus."
            },
            "pain_relief_product": {
                "type": "medicine",
                "uses": "Used for temporary relief of minor aches and pains of muscles and joints associated with arthritis, backache, strains, and sprains.",
                "precautions": "For external use only. Avoid contact with eyes or mucous membranes. Do not apply to wounds or damaged skin. Not recommended for children under 12 unless advised by doctor.",
                "side_effects": "May cause skin irritation, redness, or burning sensation at application site. Rarely may cause allergic reactions.",
                "form": "spray",
                "price_inr": "150-200",
                "description": "Contains natural and medicinal ingredients that provide relief from muscle and joint pain."
            },
            "perfume_product": {
                "type": "non-medicine",
                "uses": "For personal fragrance and to provide a pleasant scent to the user.",
                "precautions": "For external use only. Do not spray on irritated or broken skin. Keep away from flame and heat. Avoid spraying in eyes.",
                "side_effects": "May cause skin irritation or allergic reactions in sensitive individuals. May stain clothing.",
                "form": "perfume spray",
                "price_inr": "200-500",
                "description": "A personal fragrance product with various scent notes."
            },
            "antibiotic_medicine": {
                "type": "medicine",
                "uses": "Used to treat various bacterial infections including respiratory tract infections, urinary tract infections, skin infections, and gastrointestinal infections.",
                "precautions": "Take as prescribed by your doctor. Complete the full course of treatment even if you feel better. Take with food to reduce stomach upset. Inform your doctor about kidney problems or allergies to antibiotics.",
                "side_effects": "Common side effects include nausea, vomiting, diarrhea, stomach pain, headache, and allergic reactions. Prolonged use may lead to secondary infections.",
                "form": "capsule",
                "price_inr": "150-250",
                "description": "An antibiotic medication used to treat bacterial infections."
            },
            "vitamin_supplement": {
                "type": "medicine",
                "uses": "Used as a dietary supplement to provide essential vitamins and minerals that may be missing from the diet. Helps support overall health, immune function, and normal growth and development.",
                "precautions": "Do not exceed recommended dose. Not a substitute for a balanced diet. Inform your doctor if you have any chronic health conditions or are taking other medications. Some formulations may contain sugar.",
                "side_effects": "Generally well tolerated. Excess intake may cause nausea, headache, or digestive discomfort. Some people may experience allergic reactions.",
                "form": "syrup",
                "price_inr": "100-200",
                "description": "A supplement containing multiple vitamins and minerals essential for overall health."
            },
            "probiotic_supplement": {
                "type": "medicine",
                "uses": "Used to improve gut health, support digestive function, enhance immune function, and restore normal gut flora after antibiotic treatment.",
                "precautions": "Consult your doctor before use if you have a compromised immune system or serious underlying health conditions. Store according to package instructions to maintain potency.",
                "side_effects": "Generally well tolerated. Some people may experience temporary bloating, gas, or digestive discomfort when first starting.",
                "form": "capsule",
                "price_inr": "300-500",
                "description": "Contains beneficial bacteria that support digestive health and immune function."
            },
            "medical_tape": {
                "type": "medical_supply",
                "uses": "Used for securing dressings, bandages, and medical devices to the skin. Provides support for wounds and injuries.",
                "precautions": "Do not apply too tightly as it may restrict blood circulation. Do not use on open wounds, burns, or damaged skin unless directed by healthcare professional.",
                "side_effects": "May cause skin irritation, redness, or allergic reactions in sensitive individuals. Improper removal may damage skin.",
                "form": "tape",
                "price_inr": "50-100",
                "description": "A medical adhesive tape used for wound care and medical applications."
            },
            "skin_care_product": {
                "type": "non-medicine",
                "uses": "Used for cleansing, moisturizing, and improving the appearance of facial skin.",
                "precautions": "For external use only. Avoid contact with eyes. Discontinue use if irritation occurs.",
                "side_effects": "May cause irritation, redness, or allergic reactions in sensitive individuals.",
                "form": "face wash",
                "price_inr": "100-200",
                "description": "A skincare product designed for facial cleansing and care."
            },
            "hair_care_product": {
                "type": "non-medicine",
                "uses": "Used for conditioning hair, reducing tangles, adding shine, and improving hair manageability.",
                "precautions": "For external use only. Avoid contact with eyes. Rinse thoroughly after application.",
                "side_effects": "May cause scalp irritation or allergic reactions in sensitive individuals. May cause build-up if not rinsed properly.",
                "form": "conditioner",
                "price_inr": "150-300",
                "description": "A hair care product designed to improve hair condition and manageability."
            },
            "antiseptic_product": {
                "type": "medicine",
                "uses": "Used to prevent infection by killing or inhibiting growth of microorganisms on external body surfaces.",
                "precautions": "For external use only. Avoid contact with eyes. Do not use on deep wounds, puncture wounds, or serious burns. Consult doctor for persistent symptoms.",
                "side_effects": "May cause skin irritation, burning sensation, or allergic reactions in sensitive individuals.",
                "form": "solution",
                "price_inr": "80-150",
                "description": "An antiseptic solution used for cleaning wounds and preventing infections."
            },
            "digestive_medicine": {
                "type": "medicine",
                "uses": "Used to relieve digestive problems such as acidity, heartburn, indigestion, and gas.",
                "precautions": "Do not exceed recommended dose. Not recommended for long-term use without medical supervision. Consult doctor if you have kidney disease or are on a sodium-restricted diet.",
                "side_effects": "Generally well tolerated. May cause constipation, diarrhea, or flatulence in some individuals.",
                "form": "tablet",
                "price_inr": "100-150",
                "description": "A medication that neutralizes stomach acid and provides relief from digestive discomfort."
            },
            "analgesic_medicine": {
                "type": "medicine",
                "uses": "Used for relieving pain, fever, and inflammation associated with various conditions including headache, toothache, menstrual pain, arthritis, and cold/flu symptoms.",
                "precautions": "Do not exceed recommended dose. Not recommended for those with stomach ulcers, asthma, or certain bleeding disorders. Take with food to reduce stomach irritation.",
                "side_effects": "May cause stomach irritation, nausea, heartburn, and in rare cases, allergic reactions or stomach bleeding.",
                "form": "tablet",
                "price_inr": "30-100",
                "description": "A pain-relieving medication that reduces pain signals and inflammation in the body."
            }
        }

    def search_medicine_data(self, medicine_name):
        """
        Search for medicine data using database, pattern matching and online sources.
        Returns a dictionary containing all the required information.
        """
        print(f"Searching data for: {medicine_name}")
        
        # Initialize default data
        data = {
            "name": medicine_name.strip(),
            "type": "",
            "uses": "",
            "precautions": "",
            "side_effects": "",
            "form": "",
            "price_inr": "",
            "description": "",
            "image_link": ""
        }
        
        # First, determine if this is a medicine or non-medicine product
        data["type"] = self._determine_product_type(medicine_name)
        
        # Extract form from name if present
        data["form"] = self._extract_form_from_name(medicine_name)
        
        # Try to get medicine data using pattern matching against our database
        try:
            # Use pattern matching to find the best category
            matched_category = self._match_medicine_to_category(medicine_name)
            if matched_category and matched_category in self.medicine_db:
                category_data = self.medicine_db[matched_category]
                data.update({k: v for k, v in category_data.items() if v and k != "description"})
            
            # If still missing data, try online sources
            if not all([data["uses"], data["precautions"], data["side_effects"]]):
                online_data = self._search_online_sources(medicine_name)
                if online_data:
                    # Only update fields that are still empty
                    data.update({k: v for k, v in online_data.items() if v and not data[k]})
                    
            # Get description from RxNorm or other sources
            data["description"] = self.get_medicine_description(medicine_name)
            
            # Get image link using Google Custom Search API
            data["image_link"] = self.get_item_image_link(medicine_name)
        
        except Exception as e:
            print(f"Error searching for {medicine_name}: {str(e)}")
        
        # Clean up data
        for key in data:
            if isinstance(data[key], str):
                data[key] = data[key].strip()
                
        return data

    def _determine_product_type(self, name):
        """Determine if the product is medicine or non-medicine based on name."""
        name_upper = name.upper()
        
        # Check for non-medicine indicators
        if any(term in name_upper for term in self.non_medicine_terms):
            return "non-medicine"
            
        # Check for medicine indicators - dosage pattern (e.g., 250MG)
        if re.search(r'\d+\s*(?:MG|ML|MCG)', name_upper):
            return "medicine"
            
        # Check if name contains medicine form
        if any(form in name_upper for form in self.medicine_forms.keys()):
            return "medicine"
            
        # Default to medicine if uncertain (since most items in pharmacy lists are medicines)
        return "medicine"
    
    def _extract_form_from_name(self, name):
        """Extract the form (tablet, syrup, etc.) from the medicine name if present."""
        name_upper = name.upper()
        
        for form_indicator, form_name in self.medicine_forms.items():
            if form_indicator in name_upper:
                return form_name
                
        return ""

    def _match_medicine_to_category(self, medicine_name):
        """Match medicine name to a category in our database using pattern matching"""
        name_upper = medicine_name.upper()
        
        # Check for antifungal medicines
        if any(term in name_upper for term in ["CONAZOLE", "FUNGAL", "ANTIFUNGAL"]) or \
           (any(term in name_upper for term in ["250MG", "TAB"]) and not any(term in name_upper for term in ["VITAMIN", "MULTI"])):
            return "antifungal_medicine"
            
        # Check for pain relief products
        if any(term in name_upper for term in ["PAIN", "RELIEF", "ANALGESIC"]) or \
           "SPRAY" in name_upper and any(term in name_upper for term in ["ORTHO", "PAIN", "MUSCLE"]):
            return "pain_relief_product"
            
        # Check for perfumes
        if any(term in name_upper for term in ["PERFUME", "PERFUEM", "STONE", "FRAGRANCE", "DEODORANT"]):
            return "perfume_product"
            
        # Check for antibiotics
        if any(term in name_upper for term in ["ANTIBIOTIC", "MYCIN", "CILLIN", "FLOXACIN"]) or \
           (any(term in name_upper for term in ["50 MG", "INJECTION"]) and not any(term in name_upper for term in ["INSULIN", "VACCINE"])):
            return "antibiotic_medicine"
            
        # Check for vitamins
        if any(term in name_upper for term in ["MULTIVITAMIN", "VITAMIN", "MINERAL", "TONIC"]) or \
           (any(term in name_upper for term in ["SYP", "SYRUP", "200ML"]) and not any(term in name_upper for term in ["COUGH", "COLD"])):
            return "vitamin_supplement"
            
        # Check for probiotics
        if any(term in name_upper for term in ["PROBIOTIC", "GUT", "FLORA", "GUARDIAN", "BRIYO", "LACTOBACILLUS"]):
            return "probiotic_supplement"
            
        # Check for medical supplies
        if any(term in name_upper for term in ["TAPE", "BANDAGE", "GAUGE", "DRESSING", "SURGICAL"]):
            return "medical_tape"
            
        # Check for face care products
        if any(term in name_upper for term in ["FACE WASH", "FACE PACK", "FACIAL", "CLEANSER"]):
            return "skin_care_product"
            
        # Check for hair care products
        if any(term in name_upper for term in ["CONDITIONER", "SHAMPOO", "HAIR"]):
            return "hair_care_product"
            
        # Check for antiseptic products
        if any(term in name_upper for term in ["ANTISEPTIC", "DISINFECTANT", "DETTOL", "BETADINE"]):
            return "antiseptic_product"
            
        # Check for digestive medicines
        if any(term in name_upper for term in ["ANTACID", "DIGESTIVE", "GAS", "ACIDITY"]):
            return "digestive_medicine"
            
        # Check for pain relievers (analgesics)
        if any(term in name_upper for term in ["PARACETAMOL", "ACETAMINOPHEN", "IBUPROFEN", "ASPIRIN", "PAIN"]):
            return "analgesic_medicine"
            
        # Default to generic medicine if no match
        if self._determine_product_type(medicine_name) == "medicine":
            return "antibiotic_medicine"  # Default to common type
        else:
            return "skin_care_product"  # Default non-medicine
    
    def _search_online_sources(self, medicine_name):
        """Aggregate data from multiple online pharmaceutical reference sites"""
        try:
            # Try several sources, starting with more reliable ones
            data = self._try_medline_plus(medicine_name)
            
            # If we didn't get complete data, try another source
            if not all([data.get("uses"), data.get("precautions"), data.get("side_effects")]):
                drugs_data = self._try_drugs_com(medicine_name)
                # Update only empty fields
                for key in ["uses", "precautions", "side_effects"]:
                    if not data.get(key) and drugs_data.get(key):
                        data[key] = drugs_data.get(key)
            
            # Try a third source if needed
            if not all([data.get("uses"), data.get("precautions"), data.get("side_effects")]):
                mayo_data = self._try_mayo_clinic(medicine_name)
                # Update only empty fields
                for key in ["uses", "precautions", "side_effects"]:
                    if not data.get(key) and mayo_data.get(key):
                        data[key] = mayo_data.get(key)
                        
            # Try a fourth source if still missing data
            if not all([data.get("uses"), data.get("precautions"), data.get("side_effects")]):
                nih_data = self._try_nih_database(medicine_name)
                # Update only empty fields
                for key in ["uses", "precautions", "side_effects"]:
                    if not data.get(key) and nih_data.get(key):
                        data[key] = nih_data.get(key)
            
            return data
        except Exception as e:
            print(f"Error searching online for {medicine_name}: {e}")
            return {}

    def _try_medline_plus(self, medicine_name):
        """Extract medicine information from MedlinePlus"""
        data = {"uses": "", "precautions": "", "side_effects": ""}
        try:
            # Clean the medicine name to extract the base generic name
            clean_name = re.sub(r'\d+\s*(?:MG|ML|MCG)', '', medicine_name)
            clean_name = re.sub(r'(?:TAB|CAP|INJ|SYP|SYRUP|TABLET|CAPSULE|INJECTION)', '', clean_name)
            clean_name = clean_name.strip().lower()
            
            # Generate a search URL
            search_url = f"https://medlineplus.gov/druginfo/meds/a{clean_name.replace(' ', '')}.html"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract uses
                uses_section = soup.find('h2', string=re.compile('Why is this medication prescribed', re.I))
                if uses_section and uses_section.find_next('p'):
                    data["uses"] = uses_section.find_next('p').text.strip()
                
                # Extract precautions
                precautions_section = soup.find('h2', string=re.compile('What special precautions', re.I))
                if precautions_section and precautions_section.find_next('p'):
                    data["precautions"] = precautions_section.find_next('p').text.strip()
                
                # Extract side effects
                side_effects_section = soup.find('h2', string=re.compile('What side effects', re.I))
                if side_effects_section and side_effects_section.find_next('p'):
                    data["side_effects"] = side_effects_section.find_next('p').text.strip()
            
            return data
        except Exception as e:
            print(f"Error extracting from MedlinePlus for {medicine_name}: {e}")
            return data

    def _try_drugs_com(self, medicine_name):
        """Extract medicine information from Drugs.com"""
        data = {"uses": "", "precautions": "", "side_effects": ""}
        try:
            # Clean the medicine name
            clean_name = re.sub(r'\d+\s*(?:MG|ML|MCG)', '', medicine_name)
            clean_name = re.sub(r'(?:TAB|CAP|INJ|SYP|SYRUP|TABLET|CAPSULE|INJECTION)', '', clean_name)
            clean_name = clean_name.strip().lower().replace(' ', '-')
            
            # Generate search URL
            search_url = f"https://www.drugs.com/{clean_name}.html"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract uses
                uses_section = soup.find(['h2', 'h3'], string=re.compile(r'What is|Uses of|What is .* used for', re.I))
                if uses_section and uses_section.find_next('p'):
                    data["uses"] = uses_section.find_next('p').text.strip()
                
                # Extract precautions
                precautions_section = soup.find(['h2', 'h3'], string=re.compile(r'Before taking|Precautions|Warnings', re.I))
                if precautions_section and precautions_section.find_next('p'):
                    data["precautions"] = precautions_section.find_next('p').text.strip()
                
                # Extract side effects
                side_effects_section = soup.find(['h2', 'h3'], string=re.compile(r'Side effects|Adverse effects', re.I))
                if side_effects_section and side_effects_section.find_next('p'):
                    data["side_effects"] = side_effects_section.find_next('p').text.strip()
            
            return data
        except Exception as e:
            print(f"Error extracting from Drugs.com for {medicine_name}: {e}")
            return data

    def _try_mayo_clinic(self, medicine_name):
        """Extract medicine information from Mayo Clinic"""
        data = {"uses": "", "precautions": "", "side_effects": ""}
        try:
            # Clean the medicine name
            clean_name = re.sub(r'\d+\s*(?:MG|ML|MCG)', '', medicine_name)
            clean_name = re.sub(r'(?:TAB|CAP|INJ|SYP|SYRUP|TABLET|CAPSULE|INJECTION)', '', clean_name)
            clean_name = clean_name.strip().lower().replace(' ', '-')
            
            # Generate search URL
            search_url = f"https://www.mayoclinic.org/drugs-supplements/{clean_name}/in-depth/drg-20"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract uses
                uses_section = soup.find(['h2', 'h3'], string=re.compile(r'Why it\'s done|Description|Uses', re.I))
                if uses_section and uses_section.find_next('p'):
                    data["uses"] = uses_section.find_next('p').text.strip()
                
                # Extract precautions
                precautions_section = soup.find(['h2', 'h3'], string=re.compile(r'Before|Precautions|Warnings', re.I))
                if precautions_section and precautions_section.find_next('p'):
                    data["precautions"] = precautions_section.find_next('p').text.strip()
                
                # Extract side effects
                side_effects_section = soup.find(['h2', 'h3'], string=re.compile(r'Side effects|Risks', re.I))
                if side_effects_section and side_effects_section.find_next('p'):
                    data["side_effects"] = side_effects_section.find_next('p').text.strip()
            
            return data
        except Exception as e:
            print(f"Error extracting from Mayo Clinic for {medicine_name}: {e}")
            return data

    def _try_nih_database(self, medicine_name):
        """Extract medicine information from NIH DailyMed database"""
        data = {"uses": "", "precautions": "", "side_effects": ""}
        try:
            # Clean the medicine name
            clean_name = re.sub(r'\d+\s*(?:MG|ML|MCG)', '', medicine_name)
            clean_name = re.sub(r'(?:TAB|CAP|INJ|SYP|SYRUP|TABLET|CAPSULE|INJECTION)', '', clean_name)
            clean_name = clean_name.strip().lower().replace(' ', '+')
            
            # First, search for the drug to get its ID
            search_url = f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query={clean_name}&searchbutton=Search"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Find the first result link
                result_link = soup.select_one('a.search-result-link')
                
                if result_link and 'href' in result_link.attrs:
                    # Get the detail page URL
                    detail_url = "https://dailymed.nlm.nih.gov" + result_link['href']
                    detail_response = requests.get(detail_url, headers=self.headers, timeout=10)
                    
                    if detail_response.status_code == 200:
                        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                        
                        # Extract uses/indications
                        uses_section = detail_soup.find('h1', id=re.compile('indications-and-usage', re.I))
                        if uses_section and uses_section.find_next('div', class_='contentBox'):
                            data["uses"] = uses_section.find_next('div', class_='contentBox').get_text().strip()
                            # Limit text length
                            if len(data["uses"]) > 500:
                                data["uses"] = data["uses"][:497] + "..."
                        
                        # Extract precautions
                        precautions_section = detail_soup.find('h1', id=re.compile('precautions|warnings', re.I))
                        if precautions_section and precautions_section.find_next('div', class_='contentBox'):
                            data["precautions"] = precautions_section.find_next('div', class_='contentBox').get_text().strip()
                            # Limit text length
                            if len(data["precautions"]) > 500:
                                data["precautions"] = data["precautions"][:497] + "..."
                        
                        # Extract side effects
                        side_effects_section = detail_soup.find('h1', id=re.compile('adverse-reactions|side-effects', re.I))
                        if side_effects_section and side_effects_section.find_next('div', class_='contentBox'):
                            data["side_effects"] = side_effects_section.find_next('div', class_='contentBox').get_text().strip()
                            # Limit text length
                            if len(data["side_effects"]) > 500:
                                data["side_effects"] = data["side_effects"][:497] + "..."
            
            return data
        except Exception as e:
            print(f"Error extracting from NIH DailyMed for {medicine_name}: {e}")
            return data
            
    def get_medicine_description(self, medicine_name):
        """Get medicine description from RxNorm if available, otherwise generate one."""
        search_url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={medicine_name}&search=1"
        try:
            response = requests.get(search_url, timeout=10)
            data = response.json()
            rxcui = data.get("idGroup", {}).get("rxnormId", [None])[0]
            
            if not rxcui:
                # If no RxNorm data, generate a generic description
                return self._generate_generic_description(medicine_name)
                
            desc_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json"
            desc_response = requests.get(desc_url, timeout=10)
            desc_data = desc_response.json()
            description = desc_data.get("properties", {}).get("synonym", "") or desc_data.get("properties", {}).get("name", "")
            
            # If we got a description from RxNorm, append some additional context
            if description:
                medicine_type = self._determine_product_type(medicine_name)
                matched_category = self._match_medicine_to_category(medicine_name)
                
                if medicine_type == "medicine" and matched_category in self.medicine_db:
                    category_data = self.medicine_db[matched_category]
                    return f"{description}. {category_data.get('description', '')}"
                return description
            
            # Fallback to generated description
            return self._generate_generic_description(medicine_name)
        except Exception as e:
            print(f"Error fetching description for {medicine_name}: {e}")
            return self._generate_generic_description(medicine_name)

    def _generate_generic_description(self, medicine_name):
        """Generate a generic description based on product name and type"""
        product_type = self._determine_product_type(medicine_name)
        form = self._extract_form_from_name(medicine_name)
        name_upper = medicine_name.upper()
        
        if product_type == "medicine":
            # For antifungal medicines
            if any(term in name_upper for term in ["CONAZOLE", "FUNGAL", "ANTIFUNGAL"]) or \
               "250MG" in name_upper and "TAB" in name_upper:
                return "An antifungal medication used to treat fungal infections of the skin, nails, and other parts of the body."
            
            # For antibiotics
            elif any(term in name_upper for term in ["ANTIBIOTIC", "MYCIN", "CILLIN", "FLOXACIN"]) or \
                 "50 MG" in name_upper and "INJECTION" in name_upper:
                return "An antibiotic medication used to treat bacterial infections."
            
            # For vitamins and supplements
            elif any(term in name_upper for term in ["MULTIVITAMIN", "VITAMIN", "SYP", "SYRUP", "200ML"]):
                return "A vitamin supplement that provides essential nutrients for overall health and wellbeing."
            
            # For probiotics
            elif any(term in name_upper for term in ["PROBIOTIC", "GUT", "GUARDIAN", "FLORA", "BRIYO"]):
                return "A probiotic supplement that supports digestive health and immune function."
            
            # For pain relief products
            elif any(term in name_upper for term in ["PAIN", "RELIEF", "ORTHO", "SPRAY"]):
                return "A topical pain relief product used for muscle and joint pain."
            
            # For antiseptics
            elif any(term in name_upper for term in ["ANTISEPTIC", "DISINFECTANT"]):
                return "An antiseptic solution used for cleaning wounds and preventing infections."
            
            # For digestive medicines
            elif any(term in name_upper for term in ["ANTACID", "DIGESTIVE", "GAS", "ACIDITY"]):
                return "A medication used to relieve digestive problems such as acidity and heartburn."
            
            # For analgesics (pain relievers)
            elif any(term in name_upper for term in ["PARACETAMOL", "ACETAMINOPHEN", "IBUPROFEN", "ASPIRIN", "PAIN"]):
                return "A pain-relieving medication used to reduce pain, fever, and inflammation."
            
            # Generic description based on form
            else:
                if form:
                    return f"A pharmaceutical product in {form} form used for various health conditions."
                else:
                    return "A pharmaceutical product used for various health conditions."
        else:
            # For non-medicine products
            if "PERFUME" in name_upper or "PERFUEM" in name_upper:
                return "A fragrance product for personal use."
            elif "FACE WASH" in name_upper:
                return "A facial cleansing product for skin care."
            elif "CONDITIONER" in name_upper or "SHAMPOO" in name_upper:
                return "A hair care product that improves hair texture and manageability."
            elif "TAPE" in name_upper or "BANDAGE" in name_upper:
                return "An adhesive medical tape used for wound care and dressing."
            else:
                return "A personal care or hygiene product."

    def get_item_image_link(self, item_name):
        """Get image link for the item using Google Custom Search API."""
        search_url = f"https://www.googleapis.com/customsearch/v1?q={item_name}&cx={self.CX}&key={self.API_KEY}&searchType=image"
        try:
            response = requests.get(search_url, timeout=10)
            data = response.json()
            if "items" not in data or not data["items"]:
                print(f"No image found for {item_name}")
                return "No image available"
            image_url = data["items"][0]["link"]
            return image_url
        except Exception as e:
            print(f"Error getting image link for {item_name}: {e}")
            return "Error fetching image link"
        
    def process_medicine_list(self, file_path):
        """
        Process a file containing a list of medicine names.
        Returns a pandas DataFrame with medicine information.
        """
        medicines_data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Count the total number of lines for progress reporting
                total_lines = sum(1 for _ in file if _.strip())
                file.seek(0)  # Reset file pointer to beginning
                
                print(f"Found {total_lines} items to process")
                processed = 0
                
                for line in file:
                    if line.strip():  # Skip empty lines
                        try:
                            medicine_name = line.strip()
                            medicine_data = self.search_medicine_data(medicine_name)
                            medicines_data.append(medicine_data)
                            
                            # Progress reporting
                            processed += 1
                            if processed % 5 == 0 or processed == total_lines:
                                print(f"Processed {processed}/{total_lines} items ({(processed/total_lines)*100:.1f}%)")
                            
                            # Add a small variable delay to avoid overloading APIs
                            delay = random.uniform(0.3, 0.7)
                            time.sleep(delay)
                        except Exception as e:
                            print(f"Error processing item '{line.strip()}': {str(e)}")
                            # Add partial data for failed item
                            medicines_data.append({
                                "name": line.strip(),
                                "type": self._determine_product_type(line.strip()),
                                "form": self._extract_form_from_name(line.strip()),
                                "uses": "Information not available",
                                "precautions": "Information not available",
                                "side_effects": "Information not available",
                                "price_inr": "",
                                "description": self._generate_generic_description(line.strip()),
                                "image_link": "No image available"
                            })
            
            return pd.DataFrame(medicines_data)
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return pd.DataFrame(medicines_data) if medicines_data else pd.DataFrame()

    def enrich_medicine_database(self, new_data_df):
        """
        Update the medicine_info_database.json with new medicine information
        to improve future categorization and data retrieval.
        """
        try:
            updated = False
            
            # Process each medicine in the dataframe
            for _, row in new_data_df.iterrows():
                medicine_name = row['name']
                matched_category = self._match_medicine_to_category(medicine_name)
                
                # Check if we have useful information from this medicine
                if all([row.get('uses'), row.get('precautions'), row.get('side_effects')]) and \
                   not all(x.startswith('Information not available') for x in [row.get('uses'), row.get('precautions'), row.get('side_effects')]):
                    
                    # Only update if the category exists and data is more complete than what we have
                    if matched_category in self.medicine_db:
                        category_data = self.medicine_db[matched_category]
                        # Check if we should update (if our data is incomplete or generic)
                        if not all([category_data.get('uses'), category_data.get('precautions'), category_data.get('side_effects')]) or \
                           len(category_data.get('uses', '')) < 50:
                            # Update with new, more complete information
                            self.medicine_db[matched_category].update({
                                'uses': row.get('uses') if len(row.get('uses', '')) > len(category_data.get('uses', '')) else category_data.get('uses', ''),
                                'precautions': row.get('precautions') if len(row.get('precautions', '')) > len(category_data.get('precautions', '')) else category_data.get('precautions', ''),
                                'side_effects': row.get('side_effects') if len(row.get('side_effects', '')) > len(category_data.get('side_effects', '')) else category_data.get('side_effects', ''),
                            })
                            updated = True
            
            # Save updated database if changes were made
            if updated:
                with open(self.db_file, 'w', encoding='utf-8') as f:
                    json.dump(self.medicine_db, f, indent=4)
                print(f"Updated medicine database file: {self.db_file}")
            else:
                print("No updates were needed for the medicine database")
                
        except Exception as e:
            print(f"Error updating medicine database: {e}")


def main():
    print("Enhanced Medicine Data & Image Scraper")
    print("--------------------------------------")
    
    # Get input file path
    input_file = input("Enter the path to the text file containing medicine names: ")
    
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return
        
    # Create scraper and process file
    scraper = EnhancedMedicineScraper()
    
    try:
        # Process the medicine list
        print(f"Processing file: {input_file}")
        medicine_df = scraper.process_medicine_list(input_file)
        
        # Define output file paths
        base_name = os.path.splitext(input_file)[0]
        excel_output = f"{base_name}_complete_data.xlsx"
        csv_output = f"{base_name}_complete_data.csv"
        
        # Export to Excel and CSV
        medicine_df.to_excel(excel_output, index=False)
        medicine_df.to_csv(csv_output, index=False)
        
        print(f"\nData extraction complete! Processed {len(medicine_df)} items.")
        print(f"Data exported to Excel: {excel_output}")
        print(f"Data exported to CSV: {csv_output}")
        
        # Update medicine database with new information
        print("\nUpdating medicine database with new information...")
        scraper.enrich_medicine_database(medicine_df)
        
        print("\nAll tasks completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()