# MET Office API & ASDI Archive Data Fetcher

This repository contains a Python application that interacts with the MET Office API to fetch real-time and historical weather data. It also pulls archived data from the ASDI (Amazon Sustainable Data Initiative) for further analysis.

## Features
- Fetch 24h forecast precipitation data from Met Office API
- Retrieve historical MET Office weather archives from the AWS ASDI
- Parse and store data in a structured format
- Support for JSON and CSV exports
- Simple command-line interface

## Requirements
- Python 3.8+
- Access credentials for ASDI (if applicable)

## Installation
```bash
# Clone the repository
git clone https://github.com/rainyrefundsltd/met.git
cd met

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

## Configuration
1. Obtain an API key from the [MET Office API portal](https://www.metoffice.gov.uk/services/data/datapoint)
2. If using ASDI, ensure you have the necessary credentials
3. Create a `.env` file in the project root and add:
```ini
MET_OFFICE_API_KEY=your_api_key
ASDI_USERNAME=your_username
ASDI_PASSWORD=your_password
```

## Usage
### Fetch Current Weather Data
```bash
python fetch_met_office_forecast.py --time_h 8 --latitude 50 --longitude 0
```

### Retrieve ASDI Archive Data
```bash
python fetch_asdi.py --date 2024-01-01 --format csv
```

## Output
By default, the fetched data will be saved in the `data/` directory as JSON or CSV files.

## Contributing
1. Fork the repo
2. Create a new branch (`feature-branch`)
3. Commit your changes
4. Open a pull request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For inquiries, open an issue or contact the repository maintainer at `alexander.hall@rainyrefunds.com`.
