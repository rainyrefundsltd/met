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

NIMROD_STATIONS = {
    "Clee Hill":           {"lat": 52.398056, "lon":  -2.596944},
    "Hameldon Hill":       {"lat": 53.754722, "lon":  -2.288611},
    "Chenies":             {"lat": 51.689167, "lon":  -0.530556},
    "Predannack":          {"lat": 50.003333, "lon":  -5.222500},
    "Ingham":              {"lat": 53.335000, "lon":  -0.559167},
    "Crug-y-Gorllwyn":     {"lat": 51.979722, "lon":  -4.444722},
    "Corse Hill":          {"lat": 55.691111, "lon":  -4.231389},
    "Hill of Dudwick":     {"lat": 57.430833, "lon":  -2.036111},
    "Drium-a-Starraig":    {"lat": 58.211111, "lon":  -6.183056},
    "Cobbacombe Cross":    {"lat": 50.963333, "lon":  -3.452778},
    "Thurnham":            {"lat": 51.294722, "lon":   0.604167},
    "Dean Hill":           {"lat": 51.030556, "lon":  -1.654444},
    "Castor Bay":          {"lat": 54.500000, "lon":  -6.340000},
    "Dublin Airport":      {"lat": 53.428889, "lon":  -6.258611},
    "Shannon Airport":     {"lat": 52.700278, "lon":  -8.923333},
}