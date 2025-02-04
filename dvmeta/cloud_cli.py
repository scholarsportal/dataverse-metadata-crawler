"""Module for handling .env file creation in Jupyter notebooks.

This module provides functions to securely collect user input for BASE_URL and API_KEY
using IPython widgets and save them into a .env file.
"""

from pathlib import Path

import ipywidgets as widgets
from IPython.display import display


def create_env_widgets() -> tuple:
    """Creates input widgets for BASE_URL and API_KEY and returns them."""
    base_url_widget = widgets.Text(
        description='BASE_URL:',
        placeholder='Enter the Base URL'
    )

    api_key_widget = widgets.Password(
        description='API_KEY:',
        placeholder='Enter your API Key'
    )

    return base_url_widget, api_key_widget


def save_env_file(base_url: str, api_key: str) -> None:
    """Saves the provided BASE_URL and API_KEY to a .env file."""
    with Path('.env').open('w', encoding='utf-8') as file:
        if base_url.strip():  # Only write BASE_URL if it's not empty
            file.write(f'BASE_URL = "{base_url}"\n')
        if api_key.strip():  # Only write API_KEY if it's not empty
            file.write(f'API_KEY = "{api_key}"\n')
            print('✅ Successfully created the .env file with API_KEY defined!')
        else:
            print('✅ Successfully created the .env file without API_KEY defined!')


def display_env_input() -> None:
    """Displays widgets for BASE_URL and API_KEY input and provides a save button."""
    base_url_widget, api_key_widget = create_env_widgets()
    display(base_url_widget, api_key_widget)

    def on_save(_) -> None:
        save_env_file(base_url_widget.value, api_key_widget.value)

    save_button = widgets.Button(description='Save .env')
    save_button.on_click(on_save)
    display(save_button)
