"""
LLM Model Management utilities for local model downloads and setup.
Handles LeoLM and other GGUF models with verification and progress tracking.
"""
import hashlib
import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Information about an available model."""
    name: str
    filename: str
    url: str
    sha256: Optional[str] = None
    size_mb: Optional[int] = None
    description: str = ""
    recommended: bool = False
    parameters: Optional[str] = None
    quantization: Optional[str] = None

class LLMModelManager:
    """Manages local LLM model downloads and verification."""

    # LeoLM model configurations
    AVAILABLE_MODELS = {
        'leolm-13b-chat-q4_0': ModelInfo(
            name='LeoLM 13B Chat Q4_0',
            filename='leolm-hesseianai-13b-chat-q4_0.gguf',
            url='https://huggingface.co/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/resolve/main/LeoLM-hesseianai-13b-chat.Q4_0.gguf',
            sha256='',  # To be filled when known
            size_mb=7500,
            description='LeoLM 13B Chat model with Q4_0 quantization - good balance of speed and quality',
            recommended=True,
            parameters='13B',
            quantization='Q4_0'
        ),
        'leolm-13b-chat-q5_k_m': ModelInfo(
            name='LeoLM 13B Chat Q5_K_M',
            filename='leolm-hesseianai-13b-chat-q5_k_m.gguf',
            url='https://huggingface.co/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/resolve/main/LeoLM-hesseianai-13b-chat.Q5_K_M.gguf',
            sha256='',  # To be filled when known
            size_mb=9200,
            description='LeoLM 13B Chat model with Q5_K_M quantization - higher quality, slower inference',
            recommended=False,
            parameters='13B',
            quantization='Q5_K_M'
        ),
        'leolm-13b-chat-q2_k': ModelInfo(
            name='LeoLM 13B Chat Q2_K',
            filename='leolm-hesseianai-13b-chat-q2_k.gguf',
            url='https://huggingface.co/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/resolve/main/LeoLM-hesseianai-13b-chat.Q2_K.gguf',
            sha256='',  # To be filled when known
            size_mb=5100,
            description='LeoLM 13B Chat model with Q2_K quantization - fastest, lower quality',
            recommended=False,
            parameters='13B',
            quantization='Q2_K'
        )
    }

    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialize the LLM model manager.

        Args:
            models_dir: Directory to store models. Defaults to project models directory.
        """
        if models_dir is None:
            # Default to project models directory
            project_root = Path(__file__).parent.parent.parent.parent.parent
            models_dir = project_root / "models" / "llm"

        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Model registry file
        self.registry_file = self.models_dir / "model_registry.json"

    def list_available_models(self) -> Dict[str, ModelInfo]:
        """Get list of available models for download."""
        return self.AVAILABLE_MODELS.copy()

    def list_downloaded_models(self) -> List[Dict[str, any]]:
        """Get list of already downloaded models."""
        downloaded = []

        for model_key, model_info in self.AVAILABLE_MODELS.items():
            model_path = self.models_dir / model_info.filename
            if model_path.exists():
                downloaded.append({
                    'key': model_key,
                    'name': model_info.name,
                    'filename': model_info.filename,
                    'path': str(model_path),
                    'size_bytes': model_path.stat().st_size,
                    'verified': self._verify_model(model_path, model_info.sha256) if model_info.sha256 else None
                })

        return downloaded

    def download_model(self,
                      model_key: str,
                      progress_callback: Optional[Callable[[int, int], None]] = None,
                      force: bool = False) -> Tuple[bool, str]:
        """
        Download a model by key.

        Args:
            model_key: Key from AVAILABLE_MODELS
            progress_callback: Optional callback for progress updates (downloaded, total)
            force: Force redownload even if file exists

        Returns:
            Tuple of (success, message)
        """
        if model_key not in self.AVAILABLE_MODELS:
            return False, f"Unknown model: {model_key}"

        model_info = self.AVAILABLE_MODELS[model_key]
        model_path = self.models_dir / model_info.filename

        # Check if already exists and verified
        if model_path.exists() and not force:
            if model_info.sha256:
                if self._verify_model(model_path, model_info.sha256):
                    return True, f"Model {model_info.name} already exists and is verified"
                else:
                    logger.warning(f"Model {model_info.name} exists but failed verification, redownloading...")
            else:
                return True, f"Model {model_info.name} already exists (verification not available)"

        logger.info(f"Downloading {model_info.name} from {model_info.url}")

        try:
            response = requests.get(model_info.url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            # Create temporary file
            temp_path = model_path.with_suffix('.tmp')

            with open(temp_path, 'wb') as f:
                downloaded = 0

                # Use tqdm for progress bar
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=model_info.name) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pbar.update(len(chunk))

                            if progress_callback:
                                progress_callback(downloaded, total_size)

            # Verify download if SHA256 provided
            if model_info.sha256:
                logger.info(f"Verifying {model_info.name}...")
                if not self._verify_model(temp_path, model_info.sha256):
                    temp_path.unlink()
                    return False, f"Model {model_info.name} failed SHA256 verification"

            # Move to final location
            temp_path.rename(model_path)

            # Update registry
            self._update_registry(model_key, model_info)

            return True, f"Successfully downloaded {model_info.name}"

        except Exception as e:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

            error_msg = f"Failed to download {model_info.name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_model_path(self, model_key: str) -> Optional[Path]:
        """
        Get path to downloaded model.

        Args:
            model_key: Key from AVAILABLE_MODELS

        Returns:
            Path to model file if it exists, None otherwise
        """
        if model_key not in self.AVAILABLE_MODELS:
            return None

        model_info = self.AVAILABLE_MODELS[model_key]
        model_path = self.models_dir / model_info.filename

        return model_path if model_path.exists() else None

    def _verify_model(self, model_path: Path, expected_sha256: str) -> bool:
        """
        Verify model file using SHA256 checksum.

        Args:
            model_path: Path to model file
            expected_sha256: Expected SHA256 hash

        Returns:
            True if verification passes
        """
        if not expected_sha256:
            logger.warning("No SHA256 provided for verification")
            return True

        try:
            sha256_hash = hashlib.sha256()
            with open(model_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)

            actual_sha256 = sha256_hash.hexdigest()
            matches = actual_sha256.lower() == expected_sha256.lower()

            if not matches:
                logger.error(f"SHA256 mismatch. Expected: {expected_sha256}, Got: {actual_sha256}")

            return matches

        except Exception as e:
            logger.error(f"Error verifying model: {e}")
            return False

    def _update_registry(self, model_key: str, model_info: ModelInfo) -> None:
        """Update the local model registry."""
        try:
            # Load existing registry
            registry = {}
            if self.registry_file.exists():
                with open(self.registry_file, 'r') as f:
                    registry = json.load(f)

            # Add model info
            registry[model_key] = {
                **asdict(model_info),
                'downloaded_at': None,  # Could add timestamp
                'path': str(self.models_dir / model_info.filename)
            }

            # Save registry
            with open(self.registry_file, 'w') as f:
                json.dump(registry, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to update model registry: {e}")

    def remove_model(self, model_key: str) -> Tuple[bool, str]:
        """
        Remove a downloaded model.

        Args:
            model_key: Key from AVAILABLE_MODELS

        Returns:
            Tuple of (success, message)
        """
        if model_key not in self.AVAILABLE_MODELS:
            return False, f"Unknown model: {model_key}"

        model_info = self.AVAILABLE_MODELS[model_key]
        model_path = self.models_dir / model_info.filename

        if not model_path.exists():
            return False, f"Model {model_info.name} is not downloaded"

        try:
            model_path.unlink()
            logger.info(f"Removed model {model_info.name}")
            return True, f"Successfully removed {model_info.name}"

        except Exception as e:
            error_msg = f"Failed to remove {model_info.name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_recommended_model(self) -> Optional[str]:
        """Get the key of the recommended model."""
        for model_key, model_info in self.AVAILABLE_MODELS.items():
            if model_info.recommended:
                return model_key
        return None

    def setup_leolm(self, model_key: Optional[str] = None) -> Tuple[bool, str, Optional[Path]]:
        """
        Setup LeoLM for text correction.

        Args:
            model_key: Specific model to setup. If None, uses recommended model.

        Returns:
            Tuple of (success, message, model_path)
        """
        if model_key is None:
            model_key = self.get_recommended_model()

        if model_key is None:
            return False, "No recommended model available", None

        # Check if already downloaded
        model_path = self.get_model_path(model_key)
        if model_path:
            return True, f"LeoLM model already available at {model_path}", model_path

        # Download the model
        logger.info(f"Setting up LeoLM model: {model_key}")
        success, message = self.download_model(model_key)

        if success:
            model_path = self.get_model_path(model_key)
            return True, f"LeoLM setup complete. Model at: {model_path}", model_path
        else:
            return False, f"Failed to setup LeoLM: {message}", None


def cli_model_manager():
    """CLI interface for model management."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Model Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List available models')
    list_parser.add_argument('--downloaded', action='store_true', help='Show only downloaded models')

    # Download command
    download_parser = subparsers.add_parser('download', help='Download a model')
    download_parser.add_argument('model_key', help='Model key to download')
    download_parser.add_argument('--force', action='store_true', help='Force redownload')

    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup LeoLM for text correction')
    setup_parser.add_argument('--model', help='Specific model key (optional)')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a downloaded model')
    remove_parser.add_argument('model_key', help='Model key to remove')

    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify downloaded models')
    verify_parser.add_argument('model_key', nargs='?', help='Model key to verify (optional)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = LLMModelManager()

    if args.command == 'list':
        if args.downloaded:
            models = manager.list_downloaded_models()
            print("\nDownloaded Models:")
            print("=" * 80)
            for model in models:
                size_gb = model['size_bytes'] / (1024**3)
                verified_status = "✓" if model['verified'] else "?" if model['verified'] is None else "✗"
                print(f"{verified_status} {model['name']}")
                print(f"   File: {model['filename']}")
                print(f"   Size: {size_gb:.1f} GB")
                print(f"   Path: {model['path']}")
                print()
        else:
            models = manager.list_available_models()
            print("\nAvailable Models:")
            print("=" * 80)
            for key, info in models.items():
                status = "⭐" if info.recommended else "  "
                size_info = f" ({info.size_mb}MB)" if info.size_mb else ""
                print(f"{status} {key}: {info.name}{size_info}")
                print(f"   {info.description}")
                print()

    elif args.command == 'download':
        print(f"Downloading model: {args.model_key}")
        success, message = manager.download_model(args.model_key, force=args.force)
        print(message)

    elif args.command == 'setup':
        print("Setting up LeoLM for text correction...")
        success, message, model_path = manager.setup_leolm(args.model)
        print(message)
        if model_path:
            print(f"Model path: {model_path}")

    elif args.command == 'remove':
        success, message = manager.remove_model(args.model_key)
        print(message)

    elif args.command == 'verify':
        if args.model_key:
            # Verify specific model
            model_path = manager.get_model_path(args.model_key)
            if not model_path:
                print(f"Model {args.model_key} not found")
                return

            model_info = manager.AVAILABLE_MODELS.get(args.model_key)
            if model_info and model_info.sha256:
                if manager._verify_model(model_path, model_info.sha256):
                    print(f"✓ {args.model_key} verification passed")
                else:
                    print(f"✗ {args.model_key} verification failed")
            else:
                print(f"? {args.model_key} no verification data available")
        else:
            # Verify all downloaded models
            models = manager.list_downloaded_models()
            print("\nModel Verification:")
            print("=" * 40)
            for model in models:
                if model['verified'] is True:
                    print(f"✓ {model['key']}")
                elif model['verified'] is False:
                    print(f"✗ {model['key']}")
                else:
                    print(f"? {model['key']} (no verification data)")


if __name__ == "__main__":
    cli_model_manager()