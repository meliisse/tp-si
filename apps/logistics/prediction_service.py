"""
AI/ML Prediction Service for delivery time estimation and route optimization
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error
from django.db import models
from django.utils import timezone
from apps.logistics.models import Expedition, Tournee, TrackingLog
from apps.core.models import Destination

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for AI/ML predictions in logistics"""

    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_training_data(self):
        """Prepare historical data for training the ML model"""
        # Get historical expedition data
        expeditions = Expedition.objects.filter(
            date_livraison__isnull=False,
            predicted_delivery_time__isnull=False
        ).select_related('client', 'type_service', 'destination')

        if not expeditions.exists():
            logger.warning("No historical data available for training")
            return None

        data = []
        for exp in expeditions:
            # Calculate actual delivery time in hours
            if exp.date_creation and exp.date_livraison:
                actual_hours = (exp.date_livraison - exp.date_creation).total_seconds() / 3600

                # Get distance (simplified - in real implementation, use actual distance calculation)
                distance = self._estimate_distance(exp.destination)

                data.append({
                    'weight': float(exp.poids),
                    'volume': float(exp.volume),
                    'distance': distance,
                    'service_type': exp.type_service.nom if exp.type_service else 'standard',
                    'destination': exp.destination.ville if exp.destination else 'unknown',
                    'actual_delivery_hours': actual_hours
                })

        if not data:
            return None

        df = pd.DataFrame(data)

        # Encode categorical variables
        categorical_cols = ['service_type', 'destination']
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
            df[col] = self.label_encoders[col].fit_transform(df[col])

        return df

    def train_model(self):
        """Train the ML model for delivery time prediction"""
        try:
            df = self.prepare_training_data()
            if df is None or len(df) < 10:
                logger.warning("Insufficient data for training")
                return False

            # Features and target
            feature_cols = ['weight', 'volume', 'distance', 'service_type', 'destination']
            X = df[feature_cols]
            y = df['actual_delivery_hours']

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )

            # Train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            self.model.fit(X_train, y_train)

            # Evaluate model
            y_pred = self.model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            logger.info(f"Model trained successfully. MAE: {mae:.2f} hours")

            self.is_trained = True
            return True

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False

    def predict_delivery_time(self, expedition):
        """Predict delivery time for an expedition"""
        if not self.is_trained or self.model is None:
            # Fallback to rule-based estimation
            return self._rule_based_prediction(expedition)

        try:
            # Prepare features
            distance = self._estimate_distance(expedition.destination)
            features = {
                'weight': float(expedition.poids),
                'volume': float(expedition.volume),
                'distance': distance,
                'service_type': expedition.type_service.nom if expedition.type_service else 'standard',
                'destination': expedition.destination.ville if expedition.destination else 'unknown'
            }

            # Encode categorical features
            for col in ['service_type', 'destination']:
                if col in self.label_encoders:
                    try:
                        features[col] = self.label_encoders[col].transform([features[col]])[0]
                    except:
                        # Unknown category, use most frequent
                        features[col] = 0
                else:
                    features[col] = 0

            # Create feature array
            feature_array = np.array([[features[col] for col in ['weight', 'volume', 'distance', 'service_type', 'destination']]])

            # Scale features
            feature_scaled = self.scaler.transform(feature_array)

            # Predict
            predicted_hours = self.model.predict(feature_scaled)[0]

            # Convert to datetime
            predicted_delivery = expedition.date_creation + timedelta(hours=predicted_hours)

            return predicted_delivery

        except Exception as e:
            logger.error(f"Error predicting delivery time: {e}")
            return self._rule_based_prediction(expedition)

    def _rule_based_prediction(self, expedition):
        """Fallback rule-based delivery time prediction"""
        base_hours = 24  # Base 1 day

        # Adjust based on weight
        if expedition.poids > 50:
            base_hours += 12
        elif expedition.poids > 20:
            base_hours += 6

        # Adjust based on volume
        if expedition.volume > 10:
            base_hours += 8
        elif expedition.volume > 5:
            base_hours += 4

        # Adjust based on service type
        if expedition.type_service and 'express' in expedition.type_service.nom.lower():
            base_hours = max(base_hours - 12, 6)

        return expedition.date_creation + timedelta(hours=base_hours)

    def _estimate_distance(self, destination):
        """Estimate distance to destination (simplified)"""
        # In a real implementation, this would use geocoding and distance calculation
        # For now, return a default distance based on destination
        if destination and hasattr(destination, 'ville'):
            # Simple distance estimation based on city (placeholder)
            city_distances = {
                'Paris': 50,
                'Lyon': 150,
                'Marseille': 250,
                'Toulouse': 200,
                'Nice': 300,
                'Nantes': 100,
                'Bordeaux': 120,
                'Lille': 80,
                'Strasbourg': 180,
                'Rennes': 90
            }
            return city_distances.get(destination.ville, 100)
        return 100  # Default distance in km

    def optimize_route(self, expeditions):
        """Optimize delivery route for multiple expeditions"""
        # Simplified route optimization
        # In a real implementation, this would use TSP algorithms or routing APIs

        if not expeditions:
            return []

        # Sort by destination priority (simplified)
        sorted_expeditions = sorted(expeditions, key=lambda x: self._estimate_distance(x.destination))

        # Group by destination area (simplified clustering)
        route_groups = {}
        for exp in sorted_expeditions:
            city = exp.destination.ville if exp.destination else 'unknown'
            if city not in route_groups:
                route_groups[city] = []
            route_groups[city].append(exp)

        # Create optimized route
        optimized_route = []
        for city_expeditions in route_groups.values():
            optimized_route.extend(city_expeditions)

        return optimized_route

    def predict_demand(self, destination, date_range):
        """Predict demand for a destination in a date range"""
        # Simplified demand prediction
        # In a real implementation, this would use time series forecasting

        historical_expeditions = Expedition.objects.filter(
            destination=destination,
            date_creation__range=date_range
        ).count()

        # Simple trend-based prediction
        predicted_demand = max(historical_expeditions * 1.1, 1)  # 10% growth assumption

        return int(predicted_demand)

    def update_predictions(self):
        """Update delivery time predictions for pending expeditions"""
        pending_expeditions = Expedition.objects.filter(
            statut__in=['en_transit', 'tri'],
            predicted_delivery_time__isnull=True
        )

        updated_count = 0
        for expedition in pending_expeditions:
            predicted_time = self.predict_delivery_time(expedition)
            if predicted_time:
                expedition.predicted_delivery_time = predicted_time
                expedition.save()
                updated_count += 1

        logger.info(f"Updated predictions for {updated_count} expeditions")
        return updated_count


# Global service instance
prediction_service = PredictionService()
