# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MET_OFFICE_API_KEY = os.getenv("MET_OFFICE_API_KEY")
ASDI_USERNAME = os.getenv("ASDI_USERNAME")
ASDI_PASSWORD = os.getenv("ASDI_PASSWORD")

if not MET_OFFICE_API_KEY:
    raise ValueError("Missing MET_OFFICE_API_KEY. Please set it in the .env file.")

if not ASDI_USERNAME or not ASDI_PASSWORD:
    raise ValueError("Missing ASDI credentials. Please set ASDI_USERNAME and ASDI_PASSWORD in the .env file.")
