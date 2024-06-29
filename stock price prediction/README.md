# Financial Data Analysis Model

This repository contains a financial data analysis model for predicting stock prices using technical indicators and a TensorFlow neural network model. The model includes functionality for fetching economic, news, sentiment, and exchange data, and it monitors a historical data file for changes.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Technical Indicators](#technical-indicators)
- [Model Training and Evaluation](#model-training-and-evaluation)
- [License](#license)

## Installation

To install the necessary dependencies for this project, you can use the provided package installation commands.

1. **Install Python packages:**

   ```bash
   pip install pandas numpy scikit-learn pmdarima optuna tensorflow requests nasdaq-data-link schedule watchdog psutil

**Install TA-Lib:**
apt-get install -y build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib && ./configure --prefix=/usr && make && make install
pip install TA-Lib


**Usage**
git clone https://github.com/sebukpor/financial-data-analysis-model.git
cd financial-data-analysis-model

**Run the model script:**
python financial_data_analysis_model.py


Project Structure
financial_data_analysis_model.py: Main script containing the model and data fetching logic.
README.md: This README file.
Additional data files or scripts as needed.
Dependencies
The project requires the following dependencies:

pandas
numpy
scikit-learn
pmdarima
optuna
tensorflow
requests
nasdaq-data-link
schedule
watchdog
psutil
TA-Lib
Technical Indicators
The following technical indicators are used in this model:

Volume Weighted Average Price (VWAP)
Relative Strength Index (RSI)
Moving Average Convergence Divergence (MACD)
Stochastic Oscillator (STOCH)
Simple Moving Average (SMA)
These indicators are added to the financial data for better analysis and predictions.

Model Training and Evaluation
The TensorFlow model is trained using historical financial data with the following steps:

Data Preprocessing: Adding technical indicators and scaling features.
Model Building: A neural network with dense layers.
Cross-Validation: Using KFold cross-validation for model training and validation.
Evaluation: Mean Squared Error (MSE) is used as the evaluation metric.
To train and evaluate the model, the script will:

Load the historical data.
Add technical indicators.
Train the model using KFold cross-validation.
Save the trained model and scaler.
Make predictions and evaluate the model's performance.
License
This project is licensed under the MIT License. See the LICENSE file for details.





