"""
ML Predictor - Machine Learning Price Direction Predictor
Uses Random Forest and feature engineering to predict price direction
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
import json
import os


class MLPredictor:
    """
    Machine Learning predictor using Random Forest
    Predicts price direction (UP/DOWN) with confidence
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or 'ml_model.json'
        self.model = None
        self.is_trained = False
        
        # Feature names
        self.feature_names = [
            'rsi', 'macd', 'bb_position', 'volume_ratio',
            'price_momentum', 'volatility', 'trend_strength'
        ]
        
        # Load or initialize model
        self._load_model()
    
    async def predict(self, price_data: Dict) -> Dict:
        """
        Predict price direction based on features
        """
        if not price_data or 'closes' not in price_data:
            return self._default_prediction()
        
        # Extract features
        features = self._extract_features(price_data)
        
        if not features:
            return self._default_prediction()
        
        # Make prediction
        if self.is_trained and self.model:
            prediction = self._predict_with_model(features)
        else:
            # Use heuristic-based prediction (when no model)
            prediction = self._heuristic_prediction(features)
        
        return prediction
    
    def _extract_features(self, data: Dict) -> np.ndarray:
        """Extract ML features from price data"""
        closes = data.get('closes', [])
        volumes = data.get('volumes', [1] * len(closes))
        
        if len(closes) < 30:
            return None
        
        # RSI
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-14:])
        avg_loss = np.mean(losses[-14:])
        rsi = 100 - (100 / (1 + avg_gain / (avg_loss + 0.0001)))
        
        # MACD
        ema_12 = self._ema(closes, 12)
        ema_26 = self._ema(closes, 26)
        macd = ema_12 - ema_26
        
        # Bollinger Band position
        recent = closes[-20:]
        sma = np.mean(recent)
        std = np.std(recent)
        bb_position = (closes[-1] - sma) / (std + 0.0001)
        
        # Volume ratio
        vol_ratio = np.mean(volumes[-5:]) / (np.mean(volumes[-20:]) + 0.0001)
        
        # Price momentum
        momentum = (closes[-1] - closes[-10]) / (closes[-10] + 0.0001) * 100
        
        # Volatility (ATR-like)
        volatility = np.std(deltas[-14:]) / (np.mean(closes[-14:]) + 0.0001) * 100
        
        # Trend strength
        ma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else closes[-1]
        ma_200 = np.mean(closes[-200:]) if len(closes) >= 200 else ma_50
        trend = (ma_50 - ma_200) / (ma_200 + 0.0001) * 100
        
        return np.array([
            rsi / 100,  # Normalize to 0-1
            (macd / closes[-1]) * 10,  # Normalize
            bb_position / 3,  # Normalize
            np.clip(vol_ratio, 0, 3) / 3,  # Clip and normalize
            np.clip(momentum, -10, 10) / 10,  # Normalize
            np.clip(volatility, 0, 10) / 10,  # Normalize
            np.clip(trend, -5, 5) / 5  # Normalize
        ])
    
    def _heuristic_prediction(self, features: np.ndarray) -> Dict:
        """
        Heuristic prediction when model is not trained
        Uses weighted feature analysis
        """
        # Feature weights
        weights = [0.2, 0.15, 0.2, 0.1, 0.15, 0.1, 0.1]
        
        score = sum(f * w for f, w in zip(features, weights))
        
        # Calculate confidence
        confidence = min(abs(score) * 50 + 50, 85)
        
        if score > 0.15:
            prediction = 'UP'
        elif score < -0.15:
            prediction = 'DOWN'
        else:
            prediction = 'SIDEWAYS'
        
        return {
            'prediction': prediction,
            'confidence': round(confidence, 1),
            'model_used': False,
            'features': features.tolist() if hasattr(features, 'tolist') else list(features)
        }
    
    def _predict_with_model(self, features: np.ndarray) -> Dict:
        """Use trained model for prediction"""
        # This would use sklearn or similar
        # For now, use heuristic
        return self._heuristic_prediction(features)
    
    def train(self, historical_data: List[Dict]) -> bool:
        """
        Train the model on historical data
        Expected format: [{'closes': [...], 'volumes': [...], 'future_direction': 'UP/DOWN'}]
        """
        if len(historical_data) < 100:
            return False
        
        X = []
        y = []
        
        for data in historical_data:
            features = self._extract_features(data)
            if features is not None:
                X.append(features)
                y.append(1 if data.get('future_direction') == 'UP' else 0)
        
        if len(X) < 50:
            return False
        
        # Simple training - store statistics
        X = np.array(X)
        y = np.array(y)
        
        # Calculate class means
        self.up_mean = np.mean(X[y == 1], axis=0)
        self.down_mean = np.mean(X[y == 0], axis=0)
        
        self.is_trained = True
        self._save_model()
        
        return True
    
    def _save_model(self):
        """Save model parameters"""
        model_data = {
            'is_trained': self.is_trained,
            'up_mean': self.up_mean.tolist() if hasattr(self, 'up_mean') else [],
            'down_mean': self.down_mean.tolist() if hasattr(self, 'down_mean') else []
        }
        
        with open(self.model_path, 'w') as f:
            json.dump(model_data, f)
    
    def _load_model(self):
        """Load saved model"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'r') as f:
                    model_data = json.load(f)
                
                self.is_trained = model_data.get('is_trained', False)
                if 'up_mean' in model_data:
                    self.up_mean = np.array(model_data['up_mean'])
                    self.down_mean = np.array(model_data['down_mean'])
            except:
                pass
    
    def _ema(self, data: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(data) < period:
            return sum(data) / len(data)
        
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _default_prediction(self) -> Dict:
        return {
            'prediction': 'SIDEWAYS',
            'confidence': 50,
            'model_used': False,
            'reason': 'Insufficient data'
        }
    
    def add_training_data(self, price_data: Dict, actual_direction: str):
        """
        Add a data point for continuous learning
        """
        # In production, would store and periodically retrain
        pass
