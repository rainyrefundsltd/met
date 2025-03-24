# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MET_OFFICE_API_KEY = os.getenv("MET_OFFICE_API_KEY")

if not MET_OFFICE_API_KEY:
    raise ValueError("Missing MET_OFFICE_API_KEY. Please set it in the .env file.")

AWS_ACCESS = os.getenv("AWS_ACCESS")

if not MET_OFFICE_API_KEY:
    raise ValueError("Missing AWS_ACCESS. Please set it in the .env file.")

AWS_SECRET = os.getenv("AWS_SECRET")

if not MET_OFFICE_API_KEY:
    raise ValueError("Missing AWS_SECRET. Please set it in the .env file.")

AWS_REGION = os.getenv("AWS_REGION")

if not MET_OFFICE_API_KEY:
    raise ValueError("Missing AWS_REGION. Please set it in the .env file.")