"""
AI Attack Defense System

Protects against adversarial attacks on the copyright detection model:
- Adversarial perturbation detection
- Feature space anomaly detection
- Input validation and sanitization
- Query pattern analysis (evasion detection)
- Robust feature extraction

Adversarial attacks to defend against:
1. FGSM (Fast Gradient Sign Method)
2. PGD (Projected Gradient Descent)
3. DeepFool
4. Feature poisoning
5. Query-based black-box attacks
"""

import numpy as np
import torch
import torch.nn.functional as F
from typing import Dict, Tuple, Optional, List
from PIL import Image
import hashlib
from collections import defaultdict, deque
import time


class AdversarialDetector:
    """
    Detects adversarial perturbations in input images.

    Methods:
    - Statistical analysis of image properties
    - Feature space consistency checks
    - Perturbation magnitude detection
    - Frequency domain analysis
    """

    def __init__(self, device='cuda'):
        self.device = device

        # Track normal image statistics for baseline
        self.baseline_stats = {
            'mean_pixel': 127.5,
            'std_pixel': 50.0,
            'gradient_magnitude': 30.0,
            'frequency_energy': 0.5
        }

        # Detection thresholds
        self.thresholds = {
            'pixel_std': 3.0,  # Standard deviations from normal
            'gradient_magnitude': 100.0,  # Max gradient
            'high_frequency_ratio': 0.3,  # Max high-freq energy ratio
            'feature_variance': 5.0  # Feature space variance
        }

    def detect_adversarial(
        self,
        image: Image.Image,
        features: Optional[np.ndarray] = None
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Detect if image contains adversarial perturbations.

        Args:
            image: Input PIL Image
            features: Extracted features (optional, for feature space analysis)

        Returns:
            Tuple of (is_adversarial, analysis_scores)
        """
        scores = {}
        is_adversarial = False

        # Convert to numpy array
        img_array = np.array(image)

        # 1. Pixel statistics analysis
        pixel_score = self._analyze_pixel_statistics(img_array)
        scores['pixel_anomaly'] = pixel_score

        if pixel_score > 0.7:
            is_adversarial = True

        # 2. Gradient magnitude analysis
        gradient_score = self._analyze_gradients(img_array)
        scores['gradient_anomaly'] = gradient_score

        if gradient_score > 0.8:
            is_adversarial = True

        # 3. Frequency domain analysis
        freq_score = self._analyze_frequency_domain(img_array)
        scores['frequency_anomaly'] = freq_score

        if freq_score > 0.75:
            is_adversarial = True

        # 4. Feature space analysis (if features provided)
        if features is not None:
            feature_score = self._analyze_feature_space(features)
            scores['feature_anomaly'] = feature_score

            if feature_score > 0.8:
                is_adversarial = True

        # 5. Noise pattern analysis
        noise_score = self._analyze_noise_patterns(img_array)
        scores['noise_anomaly'] = noise_score

        if noise_score > 0.7:
            is_adversarial = True

        # Overall adversarial probability
        scores['overall_probability'] = np.mean(list(scores.values()))

        return is_adversarial, scores

    def _analyze_pixel_statistics(self, img_array: np.ndarray) -> float:
        """Analyze pixel value statistics for anomalies."""
        # Calculate statistics
        mean_val = np.mean(img_array)
        std_val = np.std(img_array)
        min_val = np.min(img_array)
        max_val = np.max(img_array)

        anomaly_score = 0.0

        # Check for unusual mean/std
        if abs(mean_val - self.baseline_stats['mean_pixel']) > 50:
            anomaly_score += 0.2

        if std_val > self.baseline_stats['std_pixel'] * 2:
            anomaly_score += 0.3

        # Check for clipping (sign of perturbations)
        clip_ratio = (np.sum(img_array == 0) + np.sum(img_array == 255)) / img_array.size
        if clip_ratio > 0.1:
            anomaly_score += 0.3

        return min(1.0, anomaly_score)

    def _analyze_gradients(self, img_array: np.ndarray) -> float:
        """Analyze image gradients for adversarial perturbations."""
        # Convert to grayscale if color
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array

        # Calculate gradients
        grad_x = np.diff(gray, axis=1)
        grad_y = np.diff(gray, axis=0)

        # Gradient magnitude
        # Pad to match dimensions
        grad_x_padded = np.pad(grad_x, ((0, 0), (0, 1)), mode='edge')
        grad_y_padded = np.pad(grad_y, ((0, 1), (0, 0)), mode='edge')

        grad_magnitude = np.sqrt(grad_x_padded**2 + grad_y_padded**2)
        mean_grad = np.mean(grad_magnitude)
        max_grad = np.max(grad_magnitude)

        anomaly_score = 0.0

        # High gradient magnitude indicates perturbations
        if mean_grad > self.thresholds['gradient_magnitude']:
            anomaly_score += 0.5

        # Very high max gradient (adversarial noise)
        if max_grad > 200:
            anomaly_score += 0.4

        return min(1.0, anomaly_score)

    def _analyze_frequency_domain(self, img_array: np.ndarray) -> float:
        """Analyze frequency domain for high-frequency perturbations."""
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array

        # Compute 2D FFT
        fft = np.fft.fft2(gray)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)

        # Calculate energy in high frequencies
        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2

        # Define high frequency region (outer 30% of spectrum)
        mask = np.ones((h, w), dtype=bool)
        y, x = np.ogrid[:h, :w]
        radius = min(h, w) * 0.35
        center_region = (x - center_w)**2 + (y - center_h)**2 <= radius**2
        mask[center_region] = False

        high_freq_energy = np.sum(magnitude[mask])
        total_energy = np.sum(magnitude)

        high_freq_ratio = high_freq_energy / (total_energy + 1e-8)

        anomaly_score = 0.0

        # Adversarial perturbations often have high-frequency components
        if high_freq_ratio > self.thresholds['high_frequency_ratio']:
            anomaly_score += 0.6

        # Very high ratio is strong indicator
        if high_freq_ratio > 0.5:
            anomaly_score += 0.3

        return min(1.0, anomaly_score)

    def _analyze_feature_space(self, features: np.ndarray) -> float:
        """Analyze feature space for anomalies."""
        # Calculate feature statistics
        mean_feature = np.mean(features)
        std_feature = np.std(features)
        min_feature = np.min(features)
        max_feature = np.max(features)

        anomaly_score = 0.0

        # Check for unusual feature magnitudes
        if std_feature > self.thresholds['feature_variance']:
            anomaly_score += 0.4

        # Check for extreme values
        if max_feature > 100 or min_feature < -100:
            anomaly_score += 0.4

        return min(1.0, anomaly_score)

    def _analyze_noise_patterns(self, img_array: np.ndarray) -> float:
        """Analyze for structured noise patterns (sign of adversarial attack)."""
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array

        # Calculate local variance
        from scipy.ndimage import uniform_filter

        local_mean = uniform_filter(gray, size=5)
        local_sq_mean = uniform_filter(gray**2, size=5)
        local_var = local_sq_mean - local_mean**2

        # High uniform variance suggests noise injection
        var_std = np.std(local_var)
        var_mean = np.mean(local_var)

        anomaly_score = 0.0

        if var_mean > 100:
            anomaly_score += 0.5

        if var_std > 50:
            anomaly_score += 0.3

        return min(1.0, anomaly_score)


class QueryPatternAnalyzer:
    """
    Analyzes query patterns to detect evasion attempts.

    Detects:
    - Systematic feature probing
    - Gradient estimation attacks
    - Query-based model stealing
    - Boundary exploration
    """

    def __init__(self):
        # Track queries per user/IP
        self.query_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Track feature similarities of queries
        self.feature_cache: Dict[str, List[np.ndarray]] = defaultdict(list)

    def analyze_query_pattern(
        self,
        identifier: str,
        features: np.ndarray,
        query_metadata: Dict
    ) -> Tuple[bool, Dict]:
        """
        Analyze query pattern for evasion attempts.

        Args:
            identifier: User/IP identifier
            features: Extracted features from query
            query_metadata: Additional query info

        Returns:
            Tuple of (is_suspicious, analysis)
        """
        is_suspicious = False
        analysis = {
            'patterns_detected': [],
            'risk_score': 0.0
        }

        # Record query
        self.query_history[identifier].append({
            'timestamp': time.time(),
            'features': features,
            'metadata': query_metadata
        })

        # Get recent queries
        recent_queries = list(self.query_history[identifier])[-20:]

        if len(recent_queries) < 5:
            return False, analysis

        # 1. Detect systematic feature probing
        if self._is_feature_probing(recent_queries):
            analysis['patterns_detected'].append('feature_probing')
            analysis['risk_score'] += 30
            is_suspicious = True

        # 2. Detect gradient estimation (queries with small perturbations)
        if self._is_gradient_estimation(recent_queries):
            analysis['patterns_detected'].append('gradient_estimation')
            analysis['risk_score'] += 40
            is_suspicious = True

        # 3. Detect high query frequency (model stealing)
        if self._is_high_frequency_queries(recent_queries):
            analysis['patterns_detected'].append('high_frequency_queries')
            analysis['risk_score'] += 20

        # 4. Detect boundary exploration
        if self._is_boundary_exploration(recent_queries):
            analysis['patterns_detected'].append('boundary_exploration')
            analysis['risk_score'] += 35
            is_suspicious = True

        return is_suspicious, analysis

    def _is_feature_probing(self, queries: List[Dict]) -> bool:
        """Detect systematic feature space exploration."""
        if len(queries) < 10:
            return False

        # Extract features from queries
        features_list = [q['features'] for q in queries]

        # Calculate pairwise similarities
        similarities = []
        for i in range(len(features_list) - 1):
            f1 = features_list[i]
            f2 = features_list[i + 1]
            sim = np.dot(f1, f2) / (np.linalg.norm(f1) * np.linalg.norm(f2) + 1e-8)
            similarities.append(sim)

        # If queries are systematically different (low correlation)
        # but in sequence, it suggests probing
        mean_sim = np.mean(similarities)
        if mean_sim < 0.5:  # Very different features
            return True

        return False

    def _is_gradient_estimation(self, queries: List[Dict]) -> bool:
        """Detect gradient estimation attacks (small perturbations)."""
        if len(queries) < 5:
            return False

        features_list = [q['features'] for q in queries[-5:]]

        # Check for very similar features (small perturbations)
        for i in range(len(features_list) - 1):
            f1 = features_list[i]
            f2 = features_list[i + 1]
            sim = np.dot(f1, f2) / (np.linalg.norm(f1) * np.linalg.norm(f2) + 1e-8)

            # Very high similarity suggests small perturbations
            if sim > 0.99:
                return True

        return False

    def _is_high_frequency_queries(self, queries: List[Dict]) -> bool:
        """Detect unusually high query frequency."""
        if len(queries) < 10:
            return False

        # Check queries in last minute
        now = time.time()
        recent = [q for q in queries if now - q['timestamp'] < 60]

        # More than 30 queries per minute is suspicious
        return len(recent) > 30

    def _is_boundary_exploration(self, queries: List[Dict]) -> bool:
        """Detect boundary exploration (finding decision boundaries)."""
        if len(queries) < 10:
            return False

        # This would require access to detection results
        # For now, use feature distribution as proxy

        features_list = [q['features'] for q in queries[-10:]]

        # Calculate feature variance across dimensions
        feature_matrix = np.stack(features_list)
        variances = np.var(feature_matrix, axis=0)

        # High variance in some dimensions, low in others suggests
        # systematic exploration
        high_var_dims = np.sum(variances > np.median(variances) * 3)
        low_var_dims = np.sum(variances < np.median(variances) * 0.3)

        if high_var_dims > 100 and low_var_dims > 100:
            return True

        return False


class RobustFeatureExtractor:
    """
    Robust feature extraction with defense mechanisms.

    Defenses:
    - Input normalization
    - Feature randomization
    - Ensemble predictions
    - Gradient masking
    """

    def __init__(self, base_extractor, device='cuda'):
        self.base_extractor = base_extractor
        self.device = device

        # Defense parameters
        self.noise_std = 0.01  # Small noise for randomization
        self.num_samples = 3   # Number of samples for ensemble

    def extract_robust_features(
        self,
        image: Image.Image,
        use_ensemble: bool = True
    ) -> np.ndarray:
        """
        Extract features with adversarial defenses.

        Args:
            image: Input PIL Image
            use_ensemble: Use ensemble averaging (more robust but slower)

        Returns:
            Robust feature vector
        """
        if not use_ensemble:
            # Single extraction with input normalization
            return self._extract_with_normalization(image)

        # Ensemble extraction
        features_list = []

        for _ in range(self.num_samples):
            # Add small random noise to input
            noisy_features = self._extract_with_randomization(image)
            features_list.append(noisy_features)

        # Average features
        robust_features = np.mean(features_list, axis=0)

        # Normalize to unit length
        robust_features = robust_features / (np.linalg.norm(robust_features) + 1e-8)

        return robust_features

    def _extract_with_normalization(self, image: Image.Image) -> np.ndarray:
        """Extract features with input normalization."""
        # Convert to tensor
        from torchvision import transforms

        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        img_tensor = transform(image).unsqueeze(0).to(self.device)

        # Extract features
        with torch.no_grad():
            features = self.base_extractor(img_tensor)

        return features.cpu().numpy()

    def _extract_with_randomization(self, image: Image.Image) -> np.ndarray:
        """Extract features with input randomization."""
        from torchvision import transforms

        # Add random transformations as defense
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.RandomCrop(224),  # Random instead of center
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        img_tensor = transform(image).unsqueeze(0).to(self.device)

        # Add small Gaussian noise
        noise = torch.randn_like(img_tensor) * self.noise_std
        img_tensor = img_tensor + noise
        img_tensor = torch.clamp(img_tensor, 0, 1)

        # Extract features
        with torch.no_grad():
            features = self.base_extractor(img_tensor)

        return features.cpu().numpy()


class InputValidator:
    """
    Validates and sanitizes input images before processing.

    Checks:
    - File format validation
    - Image size limits
    - Content validation
    - Metadata sanitization
    """

    def __init__(self):
        self.allowed_formats = {'JPEG', 'PNG', 'WEBP', 'BMP'}
        self.max_size = (4096, 4096)  # Max dimensions
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    def validate_image(self, image: Image.Image, file_size: int) -> Tuple[bool, str]:
        """
        Validate image for security and format requirements.

        Args:
            image: PIL Image to validate
            file_size: File size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # 1. Check file size
        if file_size > self.max_file_size:
            return False, f"File too large ({file_size} bytes, max {self.max_file_size})"

        # 2. Check format
        if image.format not in self.allowed_formats:
            return False, f"Invalid format '{image.format}'. Allowed: {self.allowed_formats}"

        # 3. Check dimensions
        width, height = image.size
        if width > self.max_size[0] or height > self.max_size[1]:
            return False, f"Image too large ({width}x{height}), max {self.max_size}"

        # 4. Check for minimum size (too small = suspicious)
        if width < 50 or height < 50:
            return False, "Image too small (min 50x50)"

        # 5. Verify image can be loaded properly
        try:
            image.verify()
        except Exception as e:
            return False, f"Corrupted image: {str(e)}"

        return True, "valid"

    def sanitize_image(self, image: Image.Image) -> Image.Image:
        """
        Sanitize image by removing metadata and re-encoding.

        Args:
            image: Input PIL Image

        Returns:
            Sanitized PIL Image
        """
        # Convert to RGB (removes alpha channel and normalizes)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Remove EXIF and other metadata
        data = list(image.getdata())
        clean_image = Image.new(image.mode, image.size)
        clean_image.putdata(data)

        return clean_image


# Global instances
adversarial_detector = AdversarialDetector()
query_analyzer = QueryPatternAnalyzer()
input_validator = InputValidator()
