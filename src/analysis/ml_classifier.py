"""
Machine Learning classifier for AI Driven Realtime Log Analyser
"""

import logging
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import re

# Import ML libraries with fallback
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from core.models import LogEntry

logger = logging.getLogger(__name__)


class MLClassifier:
    """
    Machine Learning classifier for log analysis
    
    Uses scikit-learn to classify log entries and predict error types
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "models/log_classifier.pkl"
        self.model = None
        self.is_trained = False
        
        if not ML_AVAILABLE:
            logger.warning("⚠️ ML libraries not available. ML classification disabled.")
            return
        
        # Initialize model pipeline
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True
            )),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        # Try to load existing model
        self._load_model()

    async def train(self, messages: List[str], labels: List[str]) -> Dict:
        """
        Train the ML model
        
        Args:
            messages: List of log messages for training
            labels: List of corresponding labels (ERROR, WARN, etc.)
            
        Returns:
            Training results and metrics
        """
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available")
            return {"status": "skipped", "reason": "ML libraries not available"}
        
        if len(messages) < 10:
            logger.warning("Insufficient training data for ML model")
            return {"status": "skipped", "reason": "Insufficient training data"}
        
        logger.info(f"Training ML model with {len(messages)} samples...")
        
        try:
            # Preprocess messages
            processed_messages = [self._preprocess_message(msg) for msg in messages]
            
            # Split data for validation
            if len(messages) > 20:
                X_train, X_test, y_train, y_test = train_test_split(
                    processed_messages, labels, test_size=0.2, random_state=42
                )
            else:
                X_train, X_test, y_train, y_test = processed_messages, [], labels, []
            
            # Train model
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            # Evaluate on test set if available
            results = {"status": "success", "training_samples": len(X_train)}
            
            if X_test:
                y_pred = self.model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                results.update({
                    "test_samples": len(X_test),
                    "accuracy": accuracy,
                    "classification_report": classification_report(y_test, y_pred, output_dict=True)
                })
                logger.info(f"✅ Model trained with accuracy: {accuracy:.3f}")
            else:
                logger.info("✅ Model trained (no test set for validation)")
            
            # Save model
            await self._save_model()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def classify(self, messages: List[str]) -> List[Dict]:
        """
        Classify log messages
        
        Args:
            messages: List of messages to classify
            
        Returns:
            List of classification results
        """
        if not ML_AVAILABLE or not self.is_trained:
            return []
        
        try:
            processed_messages = [self._preprocess_message(msg) for msg in messages]
            
            # Get predictions and probabilities
            predictions = self.model.predict(processed_messages)
            probabilities = self.model.predict_proba(processed_messages)
            
            results = []
            for i, (message, prediction) in enumerate(zip(messages, predictions)):
                # Get confidence (max probability)
                confidence = max(probabilities[i])
                
                results.append({
                    "message": message,
                    "predicted_class": prediction,
                    "confidence": confidence,
                    "all_probabilities": dict(zip(self.model.classes_, probabilities[i]))
                })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Classification failed: {e}")
            return []

    async def classify_entries(self, entries: List[LogEntry]) -> List[LogEntry]:
        """
        Classify log entries and update them with predictions
        
        Args:
            entries: List of LogEntry objects
            
        Returns:
            Updated LogEntry objects with classification results
        """
        if not entries:
            return entries
        
        messages = [entry.message for entry in entries]
        classifications = await self.classify(messages)
        
        # Update entries with classification results
        for entry, classification in zip(entries, classifications):
            if classification:
                # Store classification in raw_data
                if not entry.raw_data:
                    entry.raw_data = {}
                entry.raw_data['ml_classification'] = classification
        
        return entries

    def _preprocess_message(self, message: str) -> str:
        """Preprocess log message for ML"""
        # Remove timestamps
        message = re.sub(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}', '', message)
        
        # Remove common log formatting
        message = re.sub(r'\[[^\]]+\]', '', message)  # Remove [brackets]
        message = re.sub(r'\d+', 'NUM', message)       # Replace numbers
        message = re.sub(r'[a-f0-9]{8,}', 'HASH', message)  # Replace hashes
        
        # Clean whitespace
        message = ' '.join(message.split())
        
        return message.lower()

    async def _save_model(self):
        """Save trained model to disk"""
        if not self.is_trained or not ML_AVAILABLE:
            return
        
        try:
            model_path = Path(self.model_path)
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            joblib.dump(self.model, model_path)
            logger.info(f"💾 Model saved to {model_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save model: {e}")

    def _load_model(self):
        """Load pre-trained model from disk"""
        if not ML_AVAILABLE:
            return
        
        try:
            model_path = Path(self.model_path)
            if model_path.exists():
                self.model = joblib.load(model_path)
                self.is_trained = True
                logger.info(f"📂 Loaded pre-trained model from {model_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load model: {e}")

    async def get_feature_importance(self) -> Optional[Dict]:
        """Get feature importance from the trained model"""
        if not self.is_trained or not ML_AVAILABLE:
            return None
        
        try:
            # Get feature names from TfidfVectorizer
            feature_names = self.model.named_steps['tfidf'].get_feature_names_out()
            
            # Get feature log probabilities from MultinomialNB
            feature_log_prob = self.model.named_steps['classifier'].feature_log_prob_
            
            # Create feature importance dictionary
            importance = {}
            for class_idx, class_name in enumerate(self.model.classes_):
                class_importance = {}
                for feature_idx, feature_name in enumerate(feature_names):
                    class_importance[feature_name] = feature_log_prob[class_idx][feature_idx]
                
                # Sort by importance and take top features
                sorted_features = sorted(
                    class_importance.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:20]
                
                importance[class_name] = dict(sorted_features)
            
            return importance
            
        except Exception as e:
            logger.error(f"❌ Failed to get feature importance: {e}")
            return None

    async def predict_severity(self, message: str) -> Dict:
        """
        Predict severity of a log message
        
        Args:
            message: Log message to analyze
            
        Returns:
            Severity prediction with confidence
        """
        if not self.is_trained or not ML_AVAILABLE:
            return {"severity": "UNKNOWN", "confidence": 0.0}
        
        # Simple rule-based severity prediction
        message_lower = message.lower()
        
        # High severity keywords
        high_severity_keywords = ['critical', 'fatal', 'crash', 'exception', 'panic']
        medium_severity_keywords = ['error', 'fail', 'timeout', 'reject']
        low_severity_keywords = ['warn', 'deprecated', 'slow']
        
        if any(keyword in message_lower for keyword in high_severity_keywords):
            return {"severity": "HIGH", "confidence": 0.9}
        elif any(keyword in message_lower for keyword in medium_severity_keywords):
            return {"severity": "MEDIUM", "confidence": 0.7}
        elif any(keyword in message_lower for keyword in low_severity_keywords):
            return {"severity": "LOW", "confidence": 0.6}
        else:
            return {"severity": "UNKNOWN", "confidence": 0.3}

    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        info = {
            "ml_available": ML_AVAILABLE,
            "is_trained": self.is_trained,
            "model_path": self.model_path
        }
        
        if self.is_trained and ML_AVAILABLE:
            info.update({
                "model_type": type(self.model.named_steps['classifier']).__name__,
                "vectorizer_type": type(self.model.named_steps['tfidf']).__name__,
                "classes": list(self.model.classes_) if hasattr(self.model, 'classes_') else []
            })
        
        return info
