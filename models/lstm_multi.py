# app/models/lstm_multi.py

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout


def preprocess_data(records):
    """
    Convert incoming region/month score records into a normalized
    DataFrame suitable for multi-output LSTM training.
    """
    df = pd.DataFrame(records)
    df["date_created"] = pd.to_datetime(df["date_created"])
    df.set_index("date_created", inplace=True)

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(df.to_numpy())

    df_scaled = pd.DataFrame(scaled, index=df.index, columns=df.columns)
    return df_scaled, scaler


def single_step_sampler(df, window=1):
    """
    Create sequence windows (X) and labels (y).
    Predict all feature columns (multi-output regression).
    """
    X, y = [], []
    for i in range(len(df) - window):
        X.append(df.iloc[i:i+window].values)
        y.append(df.iloc[i+window].values)
    return np.array(X), np.array(y)


def build_lstm_model(input_shape):
    """
    Multi-output LSTM model:
    - Two LSTM layers
    - Dropout for regularization
    - Dense layer with output dimension equal to #features
    """
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        LSTM(50),
        Dropout(0.2),
        Dense(input_shape[1], activation="linear")
    ])
    model.compile(optimizer='adam', loss='mse')
    return model


def train_and_predict(records):
    """
    Train a multi-output LSTM on past region scores and predict
    next month's 5 KPIs:
        - meeting_score
        - participants_score
        - total_topics
        - transferred_topics
        - total_score
    """
    df_scaled, scaler = preprocess_data(records)
    X, y = single_step_sampler(df_scaled, window=1)

    model = build_lstm_model((1, X.shape[2]))
    model.fit(X, y, epochs=50)

    last_sequence = df_scaled.iloc[-1:].values.reshape(1, 1, -1)
    pred = model.predict(last_sequence)
    pred_real = scaler.inverse_transform(pred)[0]

    return {
        "meeting_score": float(pred_real[0]),
        "participants_score": float(pred_real[1]),
        "total_topics": int(pred_real[2]),
        "transferred_topics": int(pred_real[3]),
        "total_score": float(pred_real[4]),
    }
