# Library Extract

A utility for web scraping/extracting library data from the National Library of Australia site. 

## Features

- Extracts library metadata including listed address. 
- Reverse Geocodes the address to provide lat/long details as well as the address record found. 
- Outputs data in CSV format. 

## Getting Started

### Prerequisites
- [Python 3](https://www.python.org/)

All dependencies are pre-installed in the dev container.

### Installation

Clone the repository:

```bash
git clone https://github.com/your-username/library-extract.git
cd library-extract
```

Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

You will need to sign up on maps.co geocoding and create a .env file with the following:
API_KEY= //Your API KEY 

### Usage

#### Python

```bash
python3 scrape_data.py
python3 geocode_data.py

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

This project is licensed under the MIT License.