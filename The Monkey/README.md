# Prediction/The Monkey

This directory contains scripts and tools for prediction modeling, trading algorithms, and data analysis.

## Features
- Trading algorithm implementation
- Data scraping and analysis
- Beta distribution modeling and backtesting

## Setup
1. **Install dependencies**
   ```bash
   pip install -r ../../requirements.txt
   ```
2. **Set environment variables**
   - `KALSHI_KEY_ID`: Your Kalshi API key ID
   - `KALSHI_PRIVATE_KEY_PATH`: Path to your Kalshi private key file (PEM format)
   
   Example (on Mac/Linux):
   ```bash
   export KALSHI_KEY_ID=your-key-id
   export KALSHI_PRIVATE_KEY_PATH=/path/to/your/private_key.pem
   ```

## Usage
- Run the trading algorithm:
  ```bash
  python "Trading Algorithm"
  ```
- Review individual script headers for specific instructions.

## Notes
- **Do not commit your private key or credentials to the repository.**
- This repo is for educational and research purposes only.

## License
This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details. 