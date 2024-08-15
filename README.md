### README.md

# Financial Data Analysis Model

This project is a comprehensive financial data analysis and forecasting model designed to analyze financial market data, extract key technical indicators, and predict future price movements using machine learning models, particularly neural networks with TensorFlow.

## Features

- **Technical Indicator Extraction**: This model extracts key technical indicators like VWAP, RSI, MACD, STOCH, SMA, etc., from historical financial data.
- **Data Collection**: The model fetches various types of financial data, including economic data, news, sentiment analysis, and exchange rates, using APIs.
- **File Monitoring**: A file monitoring system triggers data processing upon detecting changes in financial data files.
- **TensorFlow Model**: A neural network model built with TensorFlow is used to predict future price movements based on historical data.
- **Error Handling**: The model includes robust error handling and retry mechanisms to manage network-related issues.

## Installation

1. **Install Dependencies**:
    ```bash
    pip install pandas numpy scikit-learn pmdarima optuna tensorflow requests nasdaq-data-link schedule watchdog psutil
    ```

2. **Install TA-Lib**:
    ```bash
    apt-get install -y build-essential
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib && ./configure --prefix=/usr && make && make install
    pip install TA-Lib
    ```

## Usage

### Data Collection and Monitoring

- **Data Collection**: The `DataCollector` class fetches data from different sources like NASDAQ, news, sentiment analysis, and exchange rates.
- **File Monitoring**: The `FileMonitor` class monitors changes in specified files and triggers data processing.

### Model Training and Evaluation

1. **Load Data**: Load historical financial data in CSV format and preprocess it by extracting features such as technical indicators and datetime information.
2. **Model Training**: Train the TensorFlow model using KFold cross-validation.
3. **Model Evaluation**: Evaluate the model's performance on the validation data using Mean Squared Error (MSE).
4. **Model Saving**: Save the trained model and scalers for future predictions.

### Example

```python
# Initialize the Data Collector
data_collector = DataCollector('/path/to/historical_data.csv')

# Initialize the TensorFlow Model
model = TensorFlowModel(data=df, target_column='Close')

# Train the model
model.fit()

# Save the model
model.save_model('financial_model.h5', 'scaler.pkl')

# Evaluate the model
mse = model.evaluate(X_test, y_test)
print(f'Mean Squared Error: {mse}')
```

## Dependencies

- Python 3.7+
- Pandas
- NumPy
- Scikit-learn
- PMDARIMA
- Optuna
- TensorFlow
- Requests
- NASDAQ Data Link
- Schedule
- Watchdog
- Psutil
- TA-Lib

## API Keys

The code requires API keys to fetch data from various sources. Replace the placeholders with your actual API keys:

- `nasdaq_api_key = 'your_nasdaq_api_key'`
- `news_api_key = 'your_news_api_key'`
- `rapid_api_key = 'your_rapid_api_key'`

## License

This project is licensed under the MIT License - see the LICENSE file for details.



