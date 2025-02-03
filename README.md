# MET Office API & ASDI Archive Data Fetcher

This repository contains a Python application that interacts with the MET Office API to fetch real-time and historical weather data. It also pulls archived data from the ASDI (Amazon Sustainable Data Initiative) for further analysis.

## Features
- Retrieve historical MET Office weather archives from the AWS ASDI
- Retrieve latest MET Office weather forecast published at specific time of the day (e.g. 8am)

## Requirements
- Python 3.8+
- Access credentials for MET OFFICE & AWS

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

## MET Office Forecast Configuration
1. Create an MetOffice DataHub account [MET Office DataHub - Getting Started](https://datahub.metoffice.gov.uk/docs/getting-started)
2. Choose the atmospheric data, UK deterministic 2km (Latitude-Longitude projection) model.
3. There a few different options for the MET Office data. For now, choose the 8am option with a range 0-24.
4. Obtain your MET Office API key and copy it into a new .env file. Use .env.example as a guide.

## ASDI Configuration
1. Create an AWS account [Create AWS Account](https://repost.aws/knowledge-center/create-and-activate-aws-account)
2. Create a user with an access key and secret access key. You can also look up your AWS region, if you are in the UK this will be 'eu-west-2'.Paste these into your private .env file.  
3. The AWS bucket that we use in 'fetch_asdi.py' is here [AWS MET Office Historical Forecast Bucket](https://met-office-atmospheric-model-data.s3.eu-west-2.amazonaws.com/index.html#uk-deterministic-2km/)

Your final .env file should look like this:
```ini
MET_OFFICE_API_KEY=your_met_office_api_key_here
AWS_ACCESS=your_aws_access_key
AWS_SECRET=your_aws_secret_access_key
AWS_REGION=your_aws_region
```

## Usage
### Fetch Current Weather Data
```bash
python fetch_met_office_forecast.py
```

### Retrieve ASDI Archive Data from Given Publication Date
```bash
python fetch_asdi.py --date 'YYYY-MM-DD HH:MM:SS'
```

## Output
By default, the fetched data will be saved in the `data/asdi` directory as netCDF file.

## Contributing
1. Fork the repo
2. Create a new branch (`feature-branch`)
3. Commit your changes
4. Open a pull request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For inquiries, open an issue or contact the repository maintainer at `alexander.hall@rainyrefunds.com`.
