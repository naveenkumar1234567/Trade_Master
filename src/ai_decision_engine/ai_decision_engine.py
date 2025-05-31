import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pandas as pd
from src.chart_generator.chart_generator import save_candlestick_chart
from ultralytics import YOLO
from src.ai_decision_engine.news_fetcher import get_latest_news
import random
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

class AIDecisionEngine:
    def __init__(self, model_name: str = "prosusai/finbert"):
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertForSequenceClassification.from_pretrained(model_name)
        self.model.eval()
        self.yolo_model = YOLO("yolov8n.pt")

        model_path = os.path.join(os.path.dirname(__file__), "ai_trade_model.pkl")
        if os.path.exists(model_path):
            self.trade_model = joblib.load(model_path)
        else:
            self.trade_model = None

    def predict_sentiment(self, text: str) -> float:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze()
        sentiment_score = probs[2] - probs[0]  # Positive - Negative
        return sentiment_score.item()

    def fetch_news_sentiment(self, ticker: str) -> float:
        print(f"[INFO] Fetching news sentiment for {ticker}")
        return round(random.uniform(-1, 1), 2)

    def make_trade_decision(self, df, sentiment_score: float, pattern: str) -> str:
        if self.trade_model is None:
            print("[WARN] No trained AI model found, using fallback logic.")
            return self._fallback_decision(sentiment_score, pattern)

        try:
            last_row = df.iloc[-1]
            features = np.array([
                last_row["open"], last_row["high"], last_row["low"], last_row["close"],
                sentiment_score,
                1 if pattern.lower().startswith("bullish") else -1 if pattern.lower().startswith("bearish") else 0
            ]).reshape(1, -1)
            pred = self.trade_model.predict(features)[0]
            return pred  # BUY, SELL, or HOLD
        except Exception as e:
            print(f"[ERROR] AI prediction failed: {e}")
            return "HOLD"

    def _fallback_decision(self, sentiment_score: float, pattern: str) -> str:
        if sentiment_score > 0.5 and "bullish" in pattern.lower():
            return "BUY"
        elif sentiment_score < -0.5 and "bearish" in pattern.lower():
            return "SELL"
        else:
            return "HOLD"

    def detect_pattern(self, df: pd.DataFrame, ticker: str) -> str:
        chart_path = save_candlestick_chart(df, ticker)
        results = self.yolo_model(chart_path)
        try:
            pattern = results[0].names[results[0].probs.top1]
            return pattern
        except Exception:
            return "unknown"

    def analyze(self, ticker: str, candles_dict: dict) -> str:
        news_text = get_latest_news(ticker)
        sentiment_score = self.predict_sentiment(news_text)

        recent_df = candles_dict.get("5m")
        if recent_df is None or recent_df.empty:
            return "HOLD"

        pattern = self.detect_pattern(recent_df, ticker)

        decision = self.make_trade_decision(recent_df, sentiment_score, pattern)
        print(f"[ANALYZE] {ticker}: News='{news_text}', SentimentScore={sentiment_score}, Pattern={pattern}, Decision={decision}")
        return decision
