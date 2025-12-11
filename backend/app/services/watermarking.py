"""
Watermarking Service for Artwork Protection

Provides OPTIONAL invisible watermarking capabilities:
- Embed invisible watermarks in artwork
- Extract watermarks from suspected copies
- Robust against transformations (resize, compression, etc.)
- LSB (Least Significant Bit) steganography
- Frequency domain watermarking (DCT-based)

NOTE: Watermarking is OPTIONAL. Artists can choose to:
1. Upload without watermark (feature-only storage, max privacy)
2. Upload with watermark (track usage, detect copies)

Use Cases:
- Track artwork usage across the internet
- Prove ownership of disputed artwork
- Detect unauthorized reproductions
- Forensic analysis of leaked artwork
"""

import numpy as np
from PIL import Image
import hashlib
from typing import Tuple, Optional, Dict
import cv2


class WatermarkingService:
    """
    Invisible watermarking service using LSB steganography and DCT.

    Methods:
    - embed_lsb: Simple LSB embedding (less robust, very invisible)
    - embed_dct: DCT-based embedding (more robust, still invisible)
    - extract_lsb: Extract LSB watermark
    - extract_dct: Extract DCT watermark
    - verify_watermark: Verify extracted watermark matches expected
    """

    def __init__(self):
        self.watermark_version = "1.0"

    def embed_lsb(
        self,
        image: Image.Image,
        watermark_data: str,
        strength: int = 1
    ) -> Image.Image:
        """
        Embed watermark using LSB (Least Significant Bit) steganography.

        Args:
            image: PIL Image to watermark
            watermark_data: String data to embed (e.g., artist ID, timestamp)
            strength: Number of LSBs to use (1-3, higher = more robust but visible)

        Returns:
            Watermarked PIL Image
        """
        # Convert image to numpy array
        img_array = np.array(image)

        # Convert watermark to binary
        watermark_binary = self._string_to_binary(watermark_data)

        # Add length prefix (so we know how much to extract)
        length_binary = format(len(watermark_binary), '032b')
        full_binary = length_binary + watermark_binary

        # Check if image can hold watermark
        max_bits = img_array.size * strength
        if len(full_binary) > max_bits:
            raise ValueError(
                f"Image too small to hold watermark. "
                f"Need {len(full_binary)} bits, have {max_bits}"
            )

        # Flatten image for easier bit manipulation
        flat_array = img_array.flatten()

        # Embed watermark
        bit_index = 0
        for i in range(len(full_binary)):
            # Modify LSB of pixel
            pixel_value = flat_array[i]

            # Clear LSB
            pixel_value = pixel_value & ~((1 << strength) - 1)

            # Set new LSB from watermark
            if i < len(full_binary):
                bits_to_embed = int(full_binary[i:i+strength] or '0', 2) if full_binary[i:i+strength] else 0
                pixel_value = pixel_value | bits_to_embed

            flat_array[i] = pixel_value

        # Reshape and convert back to image
        watermarked_array = flat_array.reshape(img_array.shape)
        watermarked_image = Image.fromarray(watermarked_array.astype('uint8'))

        return watermarked_image

    def extract_lsb(
        self,
        image: Image.Image,
        strength: int = 1
    ) -> Optional[str]:
        """
        Extract LSB watermark from image.

        Args:
            image: PIL Image to extract from
            strength: Number of LSBs used in embedding

        Returns:
            Extracted watermark string, or None if extraction fails
        """
        # Convert to numpy array
        img_array = np.array(image)
        flat_array = img_array.flatten()

        # Extract length prefix (32 bits)
        length_bits = ""
        for i in range(32):
            pixel_value = flat_array[i]
            lsb = pixel_value & ((1 << strength) - 1)
            length_bits += format(lsb, '0' + str(strength) + 'b')[:1]  # Take only first bit if strength > 1

        try:
            watermark_length = int(length_bits, 2)
        except ValueError:
            return None

        # Sanity check
        if watermark_length > flat_array.size * 8 or watermark_length == 0:
            return None

        # Extract watermark bits
        watermark_bits = ""
        for i in range(32, 32 + watermark_length):
            if i >= len(flat_array):
                break
            pixel_value = flat_array[i]
            lsb = pixel_value & ((1 << strength) - 1)
            watermark_bits += format(lsb, '0' + str(strength) + 'b')[:1]

        # Convert binary to string
        watermark = self._binary_to_string(watermark_bits)

        return watermark

    def embed_dct(
        self,
        image: Image.Image,
        watermark_data: str,
        strength: float = 0.1
    ) -> Image.Image:
        """
        Embed watermark using DCT (Discrete Cosine Transform).

        More robust to transformations (compression, resize) but more complex.

        Args:
            image: PIL Image to watermark
            watermark_data: String data to embed
            strength: Embedding strength (0.01-1.0, higher = more robust but visible)

        Returns:
            Watermarked PIL Image
        """
        # Convert to numpy array and grayscale
        if image.mode != 'RGB':
            image = image.convert('RGB')

        img_array = np.array(image)

        # Convert to YCbCr (watermark in Y channel)
        img_ycbcr = cv2.cvtColor(img_array, cv2.COLOR_RGB2YCrCb)
        y_channel = img_ycbcr[:, :, 0].astype(np.float32)

        # Convert watermark to binary
        watermark_binary = self._string_to_binary(watermark_data)
        watermark_bits = [int(b) for b in watermark_binary]

        # Pad watermark to fit in 8x8 blocks
        block_size = 8
        num_blocks_needed = len(watermark_bits)

        # Apply DCT to 8x8 blocks and embed watermark
        h, w = y_channel.shape
        block_count = 0

        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                if block_count >= num_blocks_needed:
                    break

                # Extract block
                block = y_channel[i:i+block_size, j:j+block_size]

                # Apply DCT
                dct_block = cv2.dct(block)

                # Embed watermark bit in mid-frequency coefficient
                # (robust to compression, less visible than low freq)
                if block_count < len(watermark_bits):
                    bit = watermark_bits[block_count]

                    # Embed in specific DCT coefficient (4,4 is mid-frequency)
                    if bit == 1:
                        dct_block[4, 4] += strength * abs(dct_block[4, 4]) + 1
                    else:
                        dct_block[4, 4] -= strength * abs(dct_block[4, 4]) + 1

                # Apply inverse DCT
                y_channel[i:i+block_size, j:j+block_size] = cv2.idct(dct_block)

                block_count += 1

            if block_count >= num_blocks_needed:
                break

        # Clip values and convert back to uint8
        y_channel = np.clip(y_channel, 0, 255).astype(np.uint8)
        img_ycbcr[:, :, 0] = y_channel

        # Convert back to RGB
        watermarked_array = cv2.cvtColor(img_ycbcr, cv2.COLOR_YCrCb2RGB)
        watermarked_image = Image.fromarray(watermarked_array)

        return watermarked_image

    def extract_dct(
        self,
        image: Image.Image,
        watermark_length_bits: int
    ) -> Optional[str]:
        """
        Extract DCT watermark from image.

        Args:
            image: PIL Image to extract from
            watermark_length_bits: Expected watermark length in bits

        Returns:
            Extracted watermark string, or None if extraction fails
        """
        # Convert to YCbCr
        if image.mode != 'RGB':
            image = image.convert('RGB')

        img_array = np.array(image)
        img_ycbcr = cv2.cvtColor(img_array, cv2.COLOR_RGB2YCrCb)
        y_channel = img_ycbcr[:, :, 0].astype(np.float32)

        # Extract watermark bits
        block_size = 8
        h, w = y_channel.shape
        extracted_bits = []

        block_count = 0
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                if block_count >= watermark_length_bits:
                    break

                # Extract block
                block = y_channel[i:i+block_size, j:j+block_size]

                # Apply DCT
                dct_block = cv2.dct(block)

                # Extract bit from coefficient (4,4)
                coeff = dct_block[4, 4]

                # Positive = 1, Negative = 0 (simplified extraction)
                bit = 1 if coeff > 0 else 0
                extracted_bits.append(str(bit))

                block_count += 1

            if block_count >= watermark_length_bits:
                break

        # Convert bits to string
        watermark_binary = ''.join(extracted_bits)
        watermark = self._binary_to_string(watermark_binary)

        return watermark

    def generate_watermark_payload(
        self,
        artist_id: int,
        artwork_id: int,
        timestamp: str = None
    ) -> str:
        """
        Generate watermark payload string.

        Format: artist_id:artwork_id:timestamp:hash

        Args:
            artist_id: Artist ID
            artwork_id: Artwork ID
            timestamp: Timestamp (ISO format)

        Returns:
            Watermark payload string
        """
        from datetime import datetime

        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        payload = f"{artist_id}:{artwork_id}:{timestamp}"

        # Add hash for integrity
        payload_hash = hashlib.sha256(payload.encode()).hexdigest()[:8]
        full_payload = f"{payload}:{payload_hash}"

        return full_payload

    def verify_watermark(
        self,
        extracted_watermark: str,
        expected_artist_id: int,
        expected_artwork_id: int
    ) -> Tuple[bool, Dict]:
        """
        Verify extracted watermark matches expected values.

        Args:
            extracted_watermark: Watermark extracted from image
            expected_artist_id: Expected artist ID
            expected_artwork_id: Expected artwork ID

        Returns:
            Tuple of (is_valid, metadata_dict)
        """
        try:
            parts = extracted_watermark.split(':')

            if len(parts) != 4:
                return False, {"error": "Invalid watermark format"}

            artist_id = int(parts[0])
            artwork_id = int(parts[1])
            timestamp = parts[2]
            extracted_hash = parts[3]

            # Verify hash
            payload = f"{artist_id}:{artwork_id}:{timestamp}"
            expected_hash = hashlib.sha256(payload.encode()).hexdigest()[:8]

            if extracted_hash != expected_hash:
                return False, {"error": "Hash verification failed"}

            # Verify IDs
            if artist_id != expected_artist_id or artwork_id != expected_artwork_id:
                return False, {
                    "error": "ID mismatch",
                    "extracted_artist_id": artist_id,
                    "extracted_artwork_id": artwork_id
                }

            return True, {
                "artist_id": artist_id,
                "artwork_id": artwork_id,
                "timestamp": timestamp,
                "verified": True
            }

        except Exception as e:
            return False, {"error": str(e)}

    def _string_to_binary(self, text: str) -> str:
        """Convert string to binary representation."""
        binary = ''.join(format(ord(char), '08b') for char in text)
        return binary

    def _binary_to_string(self, binary: str) -> str:
        """Convert binary representation to string."""
        # Pad to multiple of 8
        padding = 8 - (len(binary) % 8)
        if padding != 8:
            binary += '0' * padding

        # Convert 8-bit chunks to characters
        chars = []
        for i in range(0, len(binary), 8):
            byte = binary[i:i+8]
            try:
                char = chr(int(byte, 2))
                # Only add printable characters
                if 32 <= ord(char) <= 126 or char in '\n\r\t':
                    chars.append(char)
            except ValueError:
                pass

        return ''.join(chars)


class WatermarkingPolicy:
    """
    Manages watermarking policy and artist preferences.

    Artists can choose:
    1. No watermarking (maximum privacy)
    2. LSB watermarking (very invisible, less robust)
    3. DCT watermarking (more robust, still invisible)
    """

    def __init__(self):
        # Artist watermarking preferences: {artist_id: preference}
        self.preferences: Dict[int, Dict] = {}

    def set_preference(
        self,
        artist_id: int,
        enabled: bool,
        method: str = 'lsb',
        strength: float = 1.0
    ):
        """
        Set watermarking preference for artist.

        Args:
            artist_id: Artist ID
            enabled: Enable watermarking
            method: 'lsb' or 'dct'
            strength: Embedding strength
        """
        self.preferences[artist_id] = {
            'enabled': enabled,
            'method': method,
            'strength': strength
        }

    def get_preference(self, artist_id: int) -> Dict:
        """Get watermarking preference for artist."""
        return self.preferences.get(artist_id, {
            'enabled': False,
            'method': 'lsb',
            'strength': 1.0
        })

    def is_enabled(self, artist_id: int) -> bool:
        """Check if watermarking is enabled for artist."""
        pref = self.get_preference(artist_id)
        return pref.get('enabled', False)


# Global instances
watermarking_service = WatermarkingService()
watermarking_policy = WatermarkingPolicy()
