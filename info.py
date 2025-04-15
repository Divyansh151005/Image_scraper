import openai
import pandas as pd

# Initialize OpenAI API key
openai.api_key = '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'
# Load the CSV file with the list of medicines
medicine_data = pd.read_csv('medicine_details.csv')

def get_medicine_details(medicine_name):
    # Formulate the prompt to generate details for the given medicine
    prompt = f"Provide a description, precautions, and usage information for the following medicine: {medicine_name}"
    
    # Use the OpenAI API to get the response (using a basic model like `text-davinci-003`)
    response = openai.Completion.create(
        model="text-davinci-003",  # Use a basic model such as text-davinci-003
        prompt=prompt,
        max_tokens=300
    )
    
    # Extract the response
    details = response['choices'][0]['text'].strip()
    
    return details

# Loop through the medicines in the CSV
for index, row in medicine_data.iterrows():
    medicine_name = row['Medicine Name']
    
    # Get details for the medicine from OpenAI
    details = get_medicine_details(medicine_name)
    
    # You can split the details into description, precautions, and usage based on how OpenAI responds.
    # For simplicity, we'll print them.
    print(f"Details for {medicine_name}:")
    print(details)
    print("-" * 50)