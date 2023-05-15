import pandas as pd
import re
import streamlit as st
from collections import defaultdict
import base64
import pyperclip
from datetime import datetime
from pytz import timezone

# Set the layout to wide
st.set_page_config(layout="wide")

# Define the mapping of categories to sections
mapping = {
    'New feature': 'New features',
    'Improvement': 'Improvements',
    'API': 'Improvements',
    'Bug fix': 'Bug fixes',
    'Removal': 'Removals',
}

# Define the order of categories
category_order = ['New features', 'Improvements', 'Bug fixes', 'Removals']

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
        category = mapping[row['Benutzerdefinierte Felder (Release Notes Category)']]
        vorgangsschlussel = row['Vorgangsschlüssel']
        release_note = row['Benutzerdefinierte Felder (Release Notes)']
        release_note_approved = row['Benutzerdefinierte Felder (Release Notes approved)']
        notes[category].append((vorgangsschlussel, release_note, release_note_approved))

    # Get current date in Berlin timezone
    berlin_time = datetime.now(timezone('Europe/Berlin'))
    release_date = berlin_time.strftime('%d-%B-%Y')

    # Start writing the notes text
    notes_text = f'\nPatch Version {patch_version}\nRelease date: {release_date}\n\n'
    # Loop through the categories in the desired order
    for category in category_order:
        # Check if the category exists in the notes
        if category in notes:
            # Write the category heading
            notes_text += f'\n{category}\n\n'

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

                notes_text += f"{module_name} ({vorgangsschlussel})\n"
                notes_text += f"{release_note}\n\n"
    return notes_text

# Function to download the text file
def get_text_file_download_link(text, filename='data.txt', title='Download text file'):
    """Generates a link to download the text file"""
    b64 = base64.b64encode(text.encode()).decode()  # some strings <-> bytes conversions necessary here
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}">{title}</a>'

# Streamlit code
st.title("CSV to Text")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    patch_version = st.text_input('\n\nEnter the Patch Version', '23.0.')
    df = load_data(uploaded_file)
    notes_text = generate_notes_text(df,    patch_version)
    # Create a dictionary to hold the status of each button
    button_status_dict = {}

    lines = notes_text.split('\n')
    for i, line in enumerate(lines):
        if line.strip() != '':
            # Create a unique key for each button using the index
            button_key = f"button_{i}"
            button_status = button_status_dict.get(button_key, False)
            if st.button(f"{line}", key=button_key):
                pyperclip.copy(line)
                button_status_dict[button_key] = True
                button_status = True
            if button_status:
                st.markdown("<span style='color:green'>Copied!<br /><br /></span>", unsafe_allow_html=True)

    st.markdown(get_text_file_download_link(notes_text), unsafe_allow_html=True)