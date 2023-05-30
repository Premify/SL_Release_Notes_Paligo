import pandas as pd
import re
import streamlit as st
from collections import defaultdict
import base64
from datetime import datetime
from pytz import timezone

# Set the layout to wide
st.set_page_config(layout="wide")

# Define the mapping of categories to sections
mapping = {
    'New feature': 'New feature',
    'Improvement': 'Improvement',
    'API': 'Improvement',
    'Bug fix': 'Bug fix',
    'Removal': 'Removal',
}

# Define the order of categories
category_order = ['New feature', 'Improvement', 'Bug fix', 'Removal', 'MISSING CATEGORY']


# Function to load data from csv
@st.cache_data
def load_data(file):
    return pd.read_csv(file)


# Function to generate the notes text
def generate_notes_text(df, patch_version):
    # Initialize a dictionary to hold the notes
    notes = defaultdict(list)

    # Populate the dictionary with the notes
    for _, row in df.iterrows():
        # Check if the category exists and if not, assign it to a default category
        raw_category = row['Benutzerdefinierte Felder (Release Notes Category)']
        category = mapping.get(raw_category, 'MISSING CATEGORY')

        vorgangsschlussel = row['Vorgangsschlüssel']
        release_note = row['Benutzerdefinierte Felder (Release Notes)']
        release_note_approved = row['Benutzerdefinierte Felder (Release Notes approved)'] if 'Benutzerdefinierte Felder (Release Notes approved)' in df.columns else 'MISSING'
        notes[category].append((vorgangsschlussel, release_note, release_note_approved))

    # Get current date in Berlin timezone
    berlin_time = datetime.now(timezone('Europe/Berlin'))
    release_date = berlin_time.strftime('%d-%B-%Y')

    # Start writing the notes text
    notes_text = f'<h3>Patch version {patch_version}<br></h3>'
    notes_text += f'<p style="font-style: italic;">Release date: {release_date}<br></p>'

    # Loop through the categories in the desired order
    for category in category_order:
        # Check if the category exists in the notes
        if category in notes:
            # Adjust the category name to plural if there's more than one item
            if len(notes[category]) > 1:
                if category == "Bug fix":
                    category_display = "Bug fixes"
                else:
                    category_display = category + 's'
            else:
                category_display = category

            # Write the category heading
            notes_text += f'<h3 style="font-style: italic;">{category_display}<br></h3>'

            # Write each note under its respective category
            for vorgangsschlussel, release_note, release_note_approved in notes[category]:
                # Check for text pattern and replace 'MODULE' with it
                pattern = r'\[(.*?)\]'
                # Ensure release_note is a string or 'MISSING' if it's None or NaN
                release_note = str(release_note) if pd.notnull(release_note) else 'MISSING'

                match = re.search(pattern, release_note)
                if match:
                    module_name = match.group(1)
                    release_note = re.sub(pattern, '', release_note).strip()
                else:
                    module_name = 'MODULE'

                notes_text += f'<p><b>{module_name} ({vorgangsschlussel})</b><br>'
                notes_text += f'{release_note}</p>'
    return notes_text


# Streamlit code
st.title("CSV to Text")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    patch_version = df["Lösungsversionen"].iloc[0]  # This gets the patch version from the first row of the column "Lösungsversionen"
    notes_text = generate_notes_text(df, patch_version)

    # Display the generated text in a markdown component to support HTML formatting
    st.markdown(notes_text, unsafe_allow_html=True)


