# -*- coding: utf-8 -*-
"""financial data analysis model

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1RcSx8J5ND9JvzOTTpJsy_2oJyEer71fE

# Installing dependencies
"""

!pip install pandas numpy scikit-learn pmdarima optuna tensorflow requests nasdaq-data-link schedule watchdog psutil

# Install ta-lib separately due to build issues
!apt-get install -y build-essential
!wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
!tar -xzf ta-lib-0.4.0-src.tar.gz
!cd ta-lib && ./configure --prefix=/usr && make && make install
!pip install TA-Lib

"""# importing libraries"""

import threading
import time
import logging
import os
import pandas as pd
import requests
import warnings
import numpy as np
import talib as ta
import queue
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tensorflow as tf
from tensorflow.keras import layers, models
import optuna
from pmdarima import auto_arima

"""# functions and class definition"""

# API keys
nasdaq_api_key = 'gd42t9zaiR57Y855njEs'
news_api_key = '7ed5a84c0d7049f3b04a78c6ebf86641'
rapid_api_key = 'a56214b22bmsh15b7f5740e33f0cp1d6885jsn60a3702961f7'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Placeholder for signals
signals = {}

# Shared signals queue
signals_queue = queue.Queue()

# Handle errors with retries
def handle_errors(retry_attempts=3, delay_seconds=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retry_attempts:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Network error in {func.__name__}: {e}")
                    attempts += 1
                    time.sleep(delay_seconds)
                except Exception as e:
                    logger.error(f"Exception in {func.__name__}: {e}")
                    attempts += 1
                    time.sleep(delay_seconds)
            logger.error(f"Max retry attempts reached in {func.__name__}")
            return None
        return wrapper
    return decorator

def add_technical_indicators(df):
    df['VWAP'] = ta.WMA(df['Close'], timeperiod=14)
    df['RSI'] = ta.RSI(df['Close'], timeperiod=14)
    macd, macd_signal, macd_hist = ta.MACD(df['Close'], fastperiod=50, slowperiod=100, signalperiod=20)
    df['MACD'] = macd
    df['MACD_Signal'] = macd_signal
    df['MACD_Hist'] = macd_hist
    stoch_k, stoch_d = ta.STOCH(df['High'], df['Low'], df['Close'], fastk_period=14, slowk_period=3, slowd_period=3)
    df['STOCH_K'] = stoch_k
    df['STOCH_D'] = stoch_d
    df['STOCH'] = (stoch_k + stoch_d) / 2  # Adding average of stoch_k and stoch_d as 'STOCH'
    df.fillna(0, inplace=True)  # Fill NaN values
    return df

# Generate test data with over 240 data points
num_points = 20000
df_test = pd.DataFrame({
    'Time': np.random.rand(num_points) * 100,
    'Open': np.random.rand(num_points) * 100,
    'High': np.random.rand(num_points) * 100 + 100,
    'Low': np.random.rand(num_points) * 100,
    'Close': np.random.rand(num_points) * 100,
    'Volume': np.random.randint(1000, 3000, num_points)
})
df_test = add_technical_indicators(df_test)
print(df_test.tail(10))

class FileMonitor(FileSystemEventHandler):
    def __init__(self, file_path, process_function):
        self.file_path = file_path
        self.process_function = process_function
        self.last_modified = os.path.getmtime(file_path)

    def on_modified(self, event):
        if event.src_path == self.file_path:
            current_modified = os.path.getmtime(self.file_path)
            if current_modified != self.last_modified:
                self.last_modified = current_modified
                logger.info(f"Detected change in {self.file_path}")
                self.process_function()

class DataCollector:
    def __init__(self, historical_file_path):
        self.historical_file_path = historical_file_path
        self.nasdaq_api_key = nasdaq_api_key
        self.news_api_key = news_api_key
        self.rapid_api_key = rapid_api_key
        nasdaqdatalink.ApiConfig.api_key = self.nasdaq_api_key
        self.economic_data_fetched = False
        self.news_data_fetched = False
        self.sentiment_data_fetched = False
        self.exchange_data_fetched = False

        if os.path.exists(self.historical_file_path):
            self.setup_file_monitor(self.historical_file_path, self.process_historical_data)
        else:
            logger.error(f"Historical file path does not exist: {self.historical_file_path}")

        self.start_background_tasks()

    def fetch_with_retry(self, url, headers=None, params=None, retries=3):
        for attempt in range(retries):
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning(f"Rate limit reached for {url}. Retrying in 60 seconds...")
                time.sleep(60)
            else:
                logger.error(f"Failed to fetch data from {url}: {response.status_code}")
                time.sleep(5)
        return None

    @handle_errors()
    def fetch_economic_data(self):
        logger.info("Fetching economic data")
        datasets = {
            'GDP': 'FRED/GDP',
            'CPI': 'FRED/CPIAUCSL',
            'PPI': 'FRED/PPIACO',
            'Unemployment': 'FRED/UNRATE',
            'Interest_Rates': 'FRED/DFF',
            'Housing': 'FRED/HOUST',
            'Manufacturing': 'FRED/INDPRO',
            'Retail_Sales': 'FRED/RSXFS'
        }
        results = {}
        for key, endpoint in datasets.items():
            url = f"https://data.nasdaq.com/api/v3/datasets/{endpoint}.json?api_key={self.nasdaq_api_key}"
            data = self.fetch_with_retry(url)
            if data:
                latest_data = data['dataset']['data'][0]
                latest_value = latest_data[1]
                results[key] = latest_value
                print(f"Fetched {key} data: {latest_value}")
            else:
                logger.error(f"Failed to fetch {key}")

        if not self.economic_data_fetched:
            logger.info(f"Economic data fetched: {results}")
            print(f"Economic data results: {results}")
            self.economic_data_fetched = True

    @handle_errors()
    def fetch_news_data(self):
        logger.info("Fetching news data")
        url = "https://real-time-finance-data.p.rapidapi.com/currency-news"
        querystring = {"from_symbol": "EUR", "language": "en", "to_symbol": "USD"}
        headers = {
            "x-rapidapi-key": self.rapid_api_key,
            "x-rapidapi-host": "real-time-finance-data.p.rapidapi.com"
        }
        data = self.fetch_with_retry(url, headers=headers, params=querystring)
        if data:
            articles = data.get('news', [])
            recent_articles = [article for article in articles if datetime.strptime(article['published_at'], '%Y-%m-%dT%H:%M:%SZ').year >= 2024]
            if not self.news_data_fetched:
                logger.info(f"News data fetched: {recent_articles[:10]}")
                print(f"News data results: {recent_articles[:10]}")
                self.news_data_fetched = True
        else:
            logger.error("Failed to fetch news data")

    @handle_errors()
    def fetch_sentiment_data(self):
        logger.info("Fetching sentiment data")
        url = "https://latest-stock-price.p.rapidapi.com/any"
        headers = {
            "x-rapidapi-key": self.rapid_api_key,
            "x-rapidapi-host": "latest-stock-price.p.rapidapi.com"
        }
        data = self.fetch_with_retry(url, headers=headers)
        if data:
            sentiment_data = data[:10]
            if not self.sentiment_data_fetched:
                logger.info(f"Sentiment data fetched: {sentiment_data}")
                print(f"Sentiment data results: {sentiment_data[:10]}")
                self.sentiment_data_fetched = True
        else:
            logger.error("Failed to fetch sentiment data")

    @handle_errors()
    def fetch_exchange_data(self):
        logger.info("Fetching exchange data")
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        data = self.fetch_with_retry(url)
        if data:
            exchange_data = {key: data['rates'][key] for key in ['EUR', 'JPY', 'GBP', 'AUD', 'CAD']}
            if not self.exchange_data_fetched:
                logger.info(f"Exchange data fetched: {exchange_data}")
                print(f"Exchange data results: {exchange_data}")
                self.exchange_data_fetched = True
        else:
            logger.error("Failed to fetch exchange data")

    def setup_file_monitor(self, file_path, process_function):
        event_handler = FileMonitor(file_path, process_function)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(file_path), recursive=False)
        observer.start()
        logger.info(f"Started monitoring {file_path}")

    def start_background_tasks(self):
        tasks = [
            (self.fetch_economic_data, "Fetching economic data"),
            (self.fetch_news_data, "Fetching news data"),
            (self.fetch_sentiment_data, "Fetching sentiment data"),
            (self.fetch_exchange_data, "Fetching exchange data")
        ]
        for task_func, task_name in tasks:
            thread = threading.Thread(target=self.run_task_periodically, args=(task_func, task_name))
            thread.start()

    def run_task_periodically(self, task_func, task_name, interval_minutes=5):
        while True:
            try:
                task_func()
            except Exception as e:
                logger.error(f"Exception in {task_name}: {e}")
            time.sleep(interval_minutes * 60)

    def process_historical_data(self):
        logger.info(f"Processing historical data from {self.historical_file_path}")
        # Your historical data processing logic here
        pass

# TensorFlow Model
class TensorFlowModel:
    def __init__(self, data, target_column, n_splits=5):
        self.data = data
        self.target_column = target_column
        self.n_splits = n_splits
        self.scaler = StandardScaler()
        self.model = None

    def build_model(self, input_shape):
        model = models.Sequential()
        model.add(layers.Dense(64, activation='relu', input_shape=(input_shape,)))
        model.add(layers.Dense(64, activation='relu'))
        model.add(layers.Dense(1))
        model.compile(optimizer='adam', loss='mse')
        return model

    def fit(self):
        X = self.data.drop(columns=[self.target_column])
        y = self.data[self.target_column]
        X_scaled = self.scaler.fit_transform(X)
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=42)
        for train_index, val_index in kf.split(X_scaled):
            X_train, X_val = X_scaled[train_index], X_scaled[val_index]
            y_train, y_val = y.iloc[train_index], y.iloc[val_index]
            self.model = self.build_model(X_train.shape[1])
            self.model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_val, y_val))

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def evaluate(self, X, y):
        predictions = self.predict(X)
        mse = mean_squared_error(y, predictions)
        return mse

"""# running datacollector and tensorflow model"""

!pip install ta

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import ta  # for technical indicators
import tensorflow as tf
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
import os
import joblib  # for saving the scalers

# Load the data with specified column names
column_names = ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
file_path = '/content/sample_data/my data/EURUSD30.csv'
df = pd.read_csv(file_path, names=column_names)

# Function to add technical indicators
def add_technical_indicators(df):
    df['SMA'] = ta.trend.sma_indicator(df['Close'], window=14)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    df['MACD'] = ta.trend.macd(df['Close'])
    df = df.fillna(0)
    return df

df = add_technical_indicators(df)

# Extract features from 'Date' and 'Time'
df['Date'] = pd.to_datetime(df['Date'])
df['DayOfWeek'] = df['Date'].dt.dayofweek
df['Hour'] = pd.to_datetime(df['Time']).dt.hour

# Drop original 'Date' and 'Time' columns
df = df.drop(columns=['Date', 'Time'])

X = df.drop(columns=['Close'])
y = df['Close']

# Convert column names to strings
X.columns = X.columns.astype(str)

# TensorFlow Model class
class TensorFlowModel:
    def __init__(self, data, target_column, n_splits=5):
        self.data = data
        self.target_column = target_column
        self.n_splits = n_splits
        self.scaler = StandardScaler()
        self.model = None

    def build_model(self, input_shape):
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(64, activation='relu', input_shape=(input_shape,)))
        model.add(tf.keras.layers.Dense(64, activation='relu'))
        model.add(tf.keras.layers.Dense(1))
        model.compile(optimizer='adam', loss='mse')
        return model

    def fit(self):
        X = self.data.drop(columns=[self.target_column])
        y = self.data[self.target_column]
        X_scaled = self.scaler.fit_transform(X)
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=42)
        for train_index, val_index in kf.split(X_scaled):
            X_train, X_val = X_scaled[train_index], X_scaled[val_index]
            y_train, y_val = y.iloc[train_index], y.iloc[val_index]
            self.model = self.build_model(X_train.shape[1])
            self.model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_val, y_val))

    def save_model(self, model_path, scaler_path):
        self.model.save(model_path)
        joblib.dump(self.scaler, scaler_path)

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def evaluate(self, X, y):
        predictions = self.predict(X)
        mse = mean_squared_error(y, predictions)
        return mse

# Initialize the TensorFlow model
tf_model = TensorFlowModel(data=df, target_column='Close')
tf_model.fit()

# Save the model and scaler
tf_model.save_model('/content/sample_data/tf_model.h5', '/content/sample_data/scaler.pkl')

# Make predictions (for verification, can be removed later)
predictions = tf_model.predict(X)
df['Predictions'] = predictions

# Evaluate the model
mse = tf_model.evaluate(X, y)
print(f"Mean Squared Error: {mse}")
print(df.tail(5))

import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import ta  # for technical indicators
import joblib  # for loading the scaler

# Load the model and scaler
model = tf.keras.models.load_model('/content/sample_data/tf_model.h5')
scaler = joblib.load('/content/sample_data/scaler.pkl')

# Function to add technical indicators
def add_technical_indicators(df):
    df['SMA'] = ta.trend.sma_indicator(df['Close'], window=14)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    df['MACD'] = ta.trend.macd(df['Close'])
    df = df.fillna(0)
    return df

# Function to make a prediction with user input
def predict_user_input(data):
    # Convert the input data to a DataFrame
    df = pd.DataFrame([data])

    # Add technical indicators
    df = add_technical_indicators(df)

    # Extract features from 'Date' and 'Time'
    df['Date'] = pd.to_datetime(df['Date'])
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    df['Hour'] = pd.to_datetime(df['Time']).dt.hour

    # Drop original 'Date' and 'Time' columns
    df = df.drop(columns=['Date', 'Time'])

    # Convert column names to strings
    df.columns = df.columns.astype(str)

    # Drop the 'Close' column as it's the target
    X = df.drop(columns=['Close'])

    # Scale the features
    X_scaled = scaler.transform(X)

    # Make a prediction
    prediction = model.predict(X_scaled)
    return prediction[0][0]

"""# Testing model with user input for prediction"""

# User input data
user_data = {
    'Date': '2023-01-01',  # Replace with actual date
    'Time': '8:00:00 am',  # Replace with actual time
    'Open': 1.12345,
    'High': 1.12400,
    'Low': 1.12200,
    'Close': 1.12380,
    'Volume': 1000
}

# Make prediction
prediction = predict_user_input(user_data)
print(f"Prediction for the user input data: {prediction}")