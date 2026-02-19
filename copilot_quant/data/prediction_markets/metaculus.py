"""
Metaculus data fetcher.

Fetches forecast data from Metaculus using their public API.
API Documentation: https://www.metaculus.com/api/
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Union

import pandas as pd
import requests

from copilot_quant.data.prediction_markets.base import PredictionMarketProvider

logger = logging.getLogger(__name__)


class MetaculusProvider(PredictionMarketProvider):
    """Metaculus data provider."""

    def __init__(self):
        """Initialize Metaculus provider."""
        super().__init__("Metaculus")
        self.base_url = "https://www.metaculus.com/api2"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "copilot_quant/1.0.0", "Accept": "application/json"})

    def list_markets(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        List available questions on Metaculus.

        Args:
            limit: Maximum number of questions to return

        Returns:
            DataFrame with question information
        """
        try:
            url = f"{self.base_url}/questions/"
            params = {
                "status": "open",
                "order_by": "-activity",
                "limit": limit if limit else 100,
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            markets = []
            results = data.get("results", [])

            for question in results:
                markets.append(
                    {
                        "market_id": str(question.get("id", "")),
                        "title": question.get("title", ""),
                        "category": question.get("category", ""),
                        "close_time": question.get("close_time", ""),
                        "status": question.get("status", ""),
                        "volume": 0,  # Metaculus doesn't have volume (it's not a market)
                        "liquidity": 0,
                        "num_predictions": question.get("number_of_predictions", 0),
                        "community_prediction": question.get("community_prediction", {}).get("q2", None),
                    }
                )

            df = pd.DataFrame(markets)
            if not df.empty and "close_time" in df.columns:
                df["close_time"] = pd.to_datetime(df["close_time"], errors="coerce")

            logger.info(f"Retrieved {len(df)} questions from Metaculus")
            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Metaculus questions: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching Metaculus questions: {e}")
            return pd.DataFrame()

    def get_market_data(
        self,
        market_id: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """
        Get historical prediction data for a Metaculus question.

        Args:
            market_id: Question ID
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with historical community predictions
        """
        try:
            # Get prediction history
            url = f"{self.base_url}/questions/{market_id}/prediction_history/"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            predictions = []

            # Metaculus returns prediction history with timestamps
            for entry in data:
                timestamp = entry.get("t", "")
                distribution = entry.get("distribution", {})

                # For binary questions, use the probability
                # For continuous questions, use the median (q2)
                prediction_value = None
                if "x" in entry:  # Binary question
                    prediction_value = entry.get("x", None)
                elif "q2" in distribution:  # Continuous question median
                    prediction_value = distribution.get("q2", None)

                if prediction_value is not None:
                    predictions.append(
                        {
                            "timestamp": timestamp,
                            "prediction": float(prediction_value),
                            "q1": distribution.get("q1", None),  # 25th percentile
                            "q2": distribution.get("q2", None),  # 50th percentile (median)
                            "q3": distribution.get("q3", None),  # 75th percentile
                        }
                    )

            df = pd.DataFrame(predictions)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
                df = df.set_index("timestamp").sort_index()

                # Filter by date range if provided
                if start_date:
                    if isinstance(start_date, str):
                        start_date = pd.to_datetime(start_date)
                    df = df[df.index >= start_date]
                if end_date:
                    if isinstance(end_date, str):
                        end_date = pd.to_datetime(end_date)
                    df = df[df.index <= end_date]

            logger.info(f"Retrieved {len(df)} prediction points for question {market_id}")
            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Metaculus prediction data: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching Metaculus prediction data: {e}")
            return pd.DataFrame()

    def get_market_details(self, market_id: str) -> Dict:
        """
        Get detailed information about a Metaculus question.

        Args:
            market_id: Question ID

        Returns:
            Dictionary with question details
        """
        try:
            url = f"{self.base_url}/questions/{market_id}/"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            community_pred = data.get("community_prediction", {})

            return {
                "market_id": str(data.get("id", "")),
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "category": data.get("category", ""),
                "type": data.get("type", ""),  # 'binary', 'continuous', etc.
                "resolution_criteria": data.get("resolution_criteria", ""),
                "close_time": data.get("close_time", ""),
                "resolution_time": data.get("resolve_time", ""),
                "status": data.get("status", ""),
                "num_predictions": data.get("number_of_predictions", 0),
                "community_prediction": community_pred.get("q2", None),
                "prediction_range": {
                    "q1": community_pred.get("q1", None),
                    "q2": community_pred.get("q2", None),
                    "q3": community_pred.get("q3", None),
                },
                "outcomes": data.get("possibilities", {}).get("type", "unknown"),
            }

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Metaculus question details: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching Metaculus question details: {e}")
            return {}
