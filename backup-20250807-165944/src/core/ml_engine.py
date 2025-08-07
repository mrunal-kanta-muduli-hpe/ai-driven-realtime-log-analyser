"""
Machine Learning Engine Module

Provides machine learning capabilities for log analysis including:
- Error classification
- Anomaly detection  
- Pattern recognition
- Model training and evaluation
"""

import logging
import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import joblib

# ML libraries
try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.preprocessing import LabelEncoder
    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML libraries not available: {e}")
    ML_AVAILABLE = False

from ..utils.config import Config


class MLEngine:
    """Machine Learning engine for log analysis."""
    
    def __init__(self, config: Config):
        """Initialize ML engine with configuration."""
        self.config = config
        self.ml_config = config.get_ml_config()
        self.model_path = Path(self.ml_config.get("model_path", "data/models/"))
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.error_classifier = None
        self.anomaly_detector = None
        self.tfidf_vectorizer = None
        self.label_encoder = None
        
        # Model parameters
        self.feature_config = self.ml_config.get("feature_extraction", {})
        self.classifier_config = self.ml_config.get("models", {}).get("error_classifier", {})
        self.anomaly_config = self.ml_config.get("models", {}).get("anomaly_detector", {})
        
        # Load existing models if available
        self._load_models()
    
    def train_models(self, log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train ML models on log entries."""
        if not ML_AVAILABLE:
            logging.warning("ML libraries not available, skipping training")
            return {"status": "skipped", "reason": "ML libraries not available"}
        
        logging.info(f"Training ML models on {len(log_entries)} log entries")
        
        try:
            # Prepare training data
            features, labels = self._prepare_training_data(log_entries)
            
            if len(features) < 10:
                logging.warning("Insufficient training data, skipping ML training")
                return {"status": "skipped", "reason": "Insufficient training data"}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=0.2, random_state=42, stratify=labels
            )
            
            # Train error classifier
            classifier_results = self._train_error_classifier(X_train, X_test, y_train, y_test)
            
            # Train anomaly detector
            anomaly_results = self._train_anomaly_detector(features)
            
            # Save models
            self._save_models()
            
            results = {
                "status": "success",
                "training_samples": len(features),
                "classifier_results": classifier_results,
                "anomaly_results": anomaly_results,
                "model_path": str(self.model_path)
            }
            
            logging.info("ML model training completed successfully")
            return results
            
        except Exception as e:
            logging.error(f"ML training failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def classify_errors(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify errors in log entries."""
        if not ML_AVAILABLE or not self.error_classifier:
            return self._fallback_classification(log_entries)
        
        error_entries = [entry for entry in log_entries if entry.get("is_error", False)]
        
        if not error_entries:
            return []
        
        try:
            # Extract features
            features = self._extract_features([entry.get("message", "") for entry in error_entries])
            
            # Predict
            predictions = self.error_classifier.predict(features)
            probabilities = self.error_classifier.predict_proba(features)
            
            # Create results
            classifications = []
            for i, entry in enumerate(error_entries):
                pred_label = self.label_encoder.inverse_transform([predictions[i]])[0]
                confidence = np.max(probabilities[i])
                
                classification = {
                    "entry_id": entry.get("line_number", i),
                    "message": entry.get("message", ""),
                    "predicted_category": pred_label,
                    "confidence": float(confidence),
                    "component": entry.get("component"),
                    "timestamp": entry.get("timestamp")
                }
                classifications.append(classification)
            
            logging.info(f"Classified {len(classifications)} error entries")
            return classifications
            
        except Exception as e:
            logging.error(f"Error classification failed: {e}")
            return self._fallback_classification(error_entries)
    
    def detect_anomalies(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in log entries."""
        if not ML_AVAILABLE or not self.anomaly_detector:
            return self._fallback_anomaly_detection(log_entries)
        
        try:
            # Extract features for all entries
            features = self._extract_features([entry.get("message", "") for entry in log_entries])
            
            # Predict anomalies
            anomaly_scores = self.anomaly_detector.decision_function(features)
            predictions = self.anomaly_detector.predict(features)
            
            # Create results for anomalies (prediction = -1)
            anomalies = []
            for i, (entry, score, pred) in enumerate(zip(log_entries, anomaly_scores, predictions)):
                if pred == -1:  # Anomaly
                    anomaly = {
                        "entry_id": entry.get("line_number", i),
                        "message": entry.get("message", ""),
                        "anomaly_score": float(score),
                        "component": entry.get("component"),
                        "timestamp": entry.get("timestamp"),
                        "is_error": entry.get("is_error", False)
                    }
                    anomalies.append(anomaly)
            
            logging.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            logging.error(f"Anomaly detection failed: {e}")
            return self._fallback_anomaly_detection(log_entries)
    
    def _prepare_training_data(self, log_entries: List[Dict[str, Any]]) -> Tuple[Any, Any]:
        """Prepare training data from log entries."""
        error_entries = [entry for entry in log_entries if entry.get("is_error", False)]
        
        # Extract messages and create labels
        messages = []
        labels = []
        
        for entry in error_entries:
            message = entry.get("message", "")
            if not message:
                continue
                
            messages.append(message)
            
            # Create label based on error patterns
            label = self._categorize_error(entry)
            labels.append(label)
        
        # Extract features
        features = self._extract_features(messages)
        
        # Encode labels
        if not self.label_encoder:
            self.label_encoder = LabelEncoder()
        
        encoded_labels = self.label_encoder.fit_transform(labels)
        
        return features, encoded_labels
    
    def _categorize_error(self, entry: Dict[str, Any]) -> str:
        """Categorize error entry into predefined categories."""
        message = entry.get("message", "").lower()
        error_text = entry.get("error", "").lower()
        component = entry.get("component", "").lower()
        
        text_to_analyze = f"{message} {error_text} {component}"
        
        # Define error categories
        if any(keyword in text_to_analyze for keyword in ["connection", "refused", "timeout", "network"]):
            return "connection_error"
        elif any(keyword in text_to_analyze for keyword in ["database", "db", "sql", "postgres"]):
            return "database_error"
        elif any(keyword in text_to_analyze for keyword in ["auth", "authentication", "permission", "denied"]):
            return "authentication_error"
        elif any(keyword in text_to_analyze for keyword in ["memory", "oom", "out of memory"]):
            return "memory_error"
        elif any(keyword in text_to_analyze for keyword in ["config", "configuration", "setting"]):
            return "configuration_error"
        elif any(keyword in text_to_analyze for keyword in ["startup", "initialization", "start"]):
            return "startup_error"
        elif any(keyword in text_to_analyze for keyword in ["service", "unavailable", "down"]):
            return "service_error"
        else:
            return "general_error"
    
    def _extract_features(self, messages: List[str]) -> Any:
        """Extract features from log messages."""
        if not self.tfidf_vectorizer:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=self.feature_config.get("max_features", 5000),
                ngram_range=tuple(self.feature_config.get("ngram_range", [1, 2])),
                min_df=self.feature_config.get("min_df", 2),
                max_df=self.feature_config.get("max_df", 0.95),
                stop_words='english'
            )
            return self.tfidf_vectorizer.fit_transform(messages)
        else:
            return self.tfidf_vectorizer.transform(messages)
    
    def _train_error_classifier(self, X_train: Any, X_test: Any, y_train: Any, y_test: Any) -> Dict[str, Any]:
        """Train error classification model."""
        algorithm = self.classifier_config.get("algorithm", "random_forest")
        params = self.classifier_config.get("parameters", {})
        
        if algorithm == "random_forest":
            self.error_classifier = RandomForestClassifier(**params)
        else:
            # Default to RandomForest
            self.error_classifier = RandomForestClassifier(**params)
        
        # Train
        self.error_classifier.fit(X_train, y_train)
        
        # Evaluate
        predictions = self.error_classifier.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        
        results = {
            "algorithm": algorithm,
            "accuracy": accuracy,
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
        
        logging.info(f"Error classifier trained - Algorithm: {algorithm}, Accuracy: {accuracy:.3f}")
        return results
    
    def _train_anomaly_detector(self, features: Any) -> Dict[str, Any]:
        """Train anomaly detection model."""
        algorithm = self.anomaly_config.get("algorithm", "isolation_forest")
        params = self.anomaly_config.get("parameters", {})
        
        if algorithm == "isolation_forest":
            self.anomaly_detector = IsolationForest(**params)
        else:
            # Default to IsolationForest
            self.anomaly_detector = IsolationForest(**params)
        
        # Train
        self.anomaly_detector.fit(features)
        
        # Evaluate on training data
        predictions = self.anomaly_detector.predict(features)
        anomaly_count = np.sum(predictions == -1)
        anomaly_rate = anomaly_count / len(predictions) * 100
        
        results = {
            "algorithm": algorithm,
            "training_samples": len(features),
            "anomalies_detected": int(anomaly_count),
            "anomaly_rate": anomaly_rate
        }
        
        logging.info(f"Anomaly detector trained - Algorithm: {algorithm}, Anomaly rate: {anomaly_rate:.1f}%")
        return results
    
    def _save_models(self):
        """Save trained models to disk."""
        try:
            if self.error_classifier:
                joblib.dump(self.error_classifier, self.model_path / "error_classifier.pkl")
            
            if self.anomaly_detector:
                joblib.dump(self.anomaly_detector, self.model_path / "anomaly_detector.pkl")
            
            if self.tfidf_vectorizer:
                joblib.dump(self.tfidf_vectorizer, self.model_path / "tfidf_vectorizer.pkl")
            
            if self.label_encoder:
                joblib.dump(self.label_encoder, self.model_path / "label_encoder.pkl")
            
            logging.info(f"Models saved to {self.model_path}")
            
        except Exception as e:
            logging.error(f"Failed to save models: {e}")
    
    def _load_models(self):
        """Load existing models from disk."""
        try:
            classifier_path = self.model_path / "error_classifier.pkl"
            if classifier_path.exists():
                self.error_classifier = joblib.load(classifier_path)
                logging.info("Loaded error classifier model")
            
            anomaly_path = self.model_path / "anomaly_detector.pkl"
            if anomaly_path.exists():
                self.anomaly_detector = joblib.load(anomaly_path)
                logging.info("Loaded anomaly detector model")
            
            vectorizer_path = self.model_path / "tfidf_vectorizer.pkl"
            if vectorizer_path.exists():
                self.tfidf_vectorizer = joblib.load(vectorizer_path)
                logging.info("Loaded TF-IDF vectorizer")
            
            encoder_path = self.model_path / "label_encoder.pkl"
            if encoder_path.exists():
                self.label_encoder = joblib.load(encoder_path)
                logging.info("Loaded label encoder")
                
        except Exception as e:
            logging.warning(f"Failed to load models: {e}")
    
    def _fallback_classification(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback classification using rule-based approach."""
        classifications = []
        
        for i, entry in enumerate(log_entries):
            if not entry.get("is_error", False):
                continue
            
            category = self._categorize_error(entry)
            
            classification = {
                "entry_id": entry.get("line_number", i),
                "message": entry.get("message", ""),
                "predicted_category": category,
                "confidence": 0.7,  # Default confidence for rule-based
                "component": entry.get("component"),
                "timestamp": entry.get("timestamp"),
                "method": "rule_based"
            }
            classifications.append(classification)
        
        return classifications
    
    def _fallback_anomaly_detection(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback anomaly detection using simple heuristics."""
        anomalies = []
        
        # Simple heuristics for anomaly detection
        message_counts = {}
        for entry in log_entries:
            message = entry.get("message", "")[:100]  # First 100 chars
            message_counts[message] = message_counts.get(message, 0) + 1
        
        # Messages that appear only once could be anomalies
        rare_messages = {msg for msg, count in message_counts.items() if count == 1}
        
        for i, entry in enumerate(log_entries):
            message = entry.get("message", "")[:100]
            
            # Check if this is a rare message or has anomaly indicators
            is_anomaly = (
                message in rare_messages or
                len(message) > 500 or  # Very long messages
                any(keyword in message.lower() for keyword in ["panic", "fatal", "critical", "corruption"])
            )
            
            if is_anomaly:
                anomaly = {
                    "entry_id": entry.get("line_number", i),
                    "message": entry.get("message", ""),
                    "anomaly_score": -0.5,  # Default score for rule-based
                    "component": entry.get("component"),
                    "timestamp": entry.get("timestamp"),
                    "is_error": entry.get("is_error", False),
                    "method": "rule_based"
                }
                anomalies.append(anomaly)
        
        return anomalies
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        info = {
            "ml_available": ML_AVAILABLE,
            "models_loaded": {
                "error_classifier": self.error_classifier is not None,
                "anomaly_detector": self.anomaly_detector is not None,
                "tfidf_vectorizer": self.tfidf_vectorizer is not None,
                "label_encoder": self.label_encoder is not None
            },
            "model_path": str(self.model_path),
            "feature_config": self.feature_config
        }
        
        if self.label_encoder:
            try:
                info["error_categories"] = list(self.label_encoder.classes_)
            except:
                pass
        
        return info
