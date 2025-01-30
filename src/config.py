# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MET_OFFICE_API_KEY = os.getenv("MET_OFFICE_API_KEY")

if not MET_OFFICE_API_KEY:
    raise ValueError("Missing MET_OFFICE_API_KEY. Please set it in the .env file.")
