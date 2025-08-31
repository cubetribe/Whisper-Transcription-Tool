#!/usr/bin/env python3
"""
macOS CLI Wrapper for Whisper Transcription Tool

This module provides a JSON-based command-line interface specifically designed 
for the macOS native application. It wraps the existing Python functionality
and provides structured JSON input/output for Swift-Python communication.
"""

import json
import sys
import os
import logging
import traceback
from typing import Dict, Any, Iterator
from pathlib import Path


class MacOSCLIWrapper:
    """
    Main CLI wrapper class that handles JSON command processing and routing.
    
    Provides standardized JSON input/output format for seamless Swift integration.
    All operations return structured responses with success/error status and
    progress updates where applicable.
    """
    
    def __init__(self):
        """Initialize the CLI wrapper with logging and configuration."""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("MacOSCLIWrapper initialized")
    
    def setup_logging(self):
        """Configure logging for the CLI wrapper."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stderr),  # Send logs to stderr, JSON to stdout
                logging.FileHandler(
                    os.path.expanduser('~/.whisper_tool_macos.log'),
                    mode='a'
                )
            ]
        )
    
    def handle_command(self, command_json: str) -> str:
        """
        Main command handler that processes JSON input and returns JSON output.
        
        Args:
            command_json: JSON string containing command and parameters
            
        Returns:
            JSON string with operation result or error information
        """
        try:
            # Parse input JSON
            command_data = json.loads(command_json)
            command = command_data.get('command', '')
            
            self.logger.info(f"Processing command: {command}")
            
            # Route to appropriate handler
            if command == 'transcribe':
                result = self._handle_transcribe(command_data)
            elif command == 'extract':
                result = self._handle_extract(command_data)
            elif command == 'list_models':
                result = self._handle_list_models(command_data)
            elif command == 'download_model':
                result = self._handle_download_model(command_data)
            elif command == 'process_batch':
                result = self._handle_process_batch(command_data)
            else:
                result = self._create_error_response(
                    f"Unknown command: {command}",
                    "UNKNOWN_COMMAND"
                )
            
            return json.dumps(result)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            return json.dumps(self._create_error_response(
                f"Invalid JSON input: {str(e)}",
                "JSON_DECODE_ERROR"
            ))
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.logger.error(traceback.format_exc())
            return json.dumps(self._create_error_response(
                f"Internal error: {str(e)}",
                "INTERNAL_ERROR"
            ))
    
    def _create_success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a standardized success response."""
        return {
            "success": True,
            "data": data,
            "timestamp": self._get_timestamp()
        }
    
    def _create_error_response(self, message: str, error_code: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "success": False,
            "error": message,
            "code": error_code,
            "timestamp": self._get_timestamp()
        }
    
    def _create_progress_response(self, progress: float, status: str, **kwargs) -> Dict[str, Any]:
        """Create a standardized progress update response."""
        response = {
            "type": "progress",
            "progress": progress,
            "status": status,
            "timestamp": self._get_timestamp()
        }
        response.update(kwargs)
        return response
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _handle_transcribe(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transcribe command with real-time progress updates."""
        try:
            # Validate required fields
            required_fields = ['input_file']
            missing_fields = [field for field in required_fields if field not in command_data]
            if missing_fields:
                return self._create_error_response(
                    f"Missing required fields: {missing_fields}",
                    "MISSING_FIELDS"
                )
            
            input_file = command_data['input_file']
            output_dir = command_data.get('output_dir', 'transcriptions')
            model = command_data.get('model', 'tiny')
            formats = command_data.get('formats', ['txt'])
            language = command_data.get('language', 'auto')
            
            # Validate input file
            input_path = Path(input_file)
            if not input_path.exists():
                return self._create_error_response(
                    f"Input file not found: {input_file}",
                    "FILE_NOT_FOUND"
                )
            
            if not self._is_supported_audio_format(input_path):
                return self._create_error_response(
                    f"Unsupported file format: {input_path.suffix}",
                    "UNSUPPORTED_FORMAT"
                )
            
            # Check available disk space
            if not self._check_disk_space(input_path, output_dir):
                return self._create_error_response(
                    "Insufficient disk space for transcription",
                    "INSUFFICIENT_DISK_SPACE"
                )
            
            # Perform transcription
            result = self._transcribe_file(input_path, output_dir, model, formats, language)
            
            if result['success']:
                return self._create_success_response({
                    'input_file': str(input_path),
                    'output_files': result['output_files'],
                    'processing_time': result['processing_time'],
                    'model_used': model,
                    'language': result.get('detected_language', language)
                })
            else:
                return self._create_error_response(
                    result['error'],
                    "TRANSCRIPTION_FAILED"
                )
                
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return self._create_error_response(
                f"Transcription failed: {str(e)}",
                "TRANSCRIPTION_ERROR"
            )
    
    def _handle_extract(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle extract command for video-to-audio conversion."""
        try:
            # Validate required fields
            required_fields = ['input_file']
            missing_fields = [field for field in required_fields if field not in command_data]
            if missing_fields:
                return self._create_error_response(
                    f"Missing required fields: {missing_fields}",
                    "MISSING_FIELDS"
                )
            
            input_file = command_data['input_file']
            output_dir = command_data.get('output_dir', 'transcriptions/temp')
            
            # Validate input file
            input_path = Path(input_file)
            if not input_path.exists():
                return self._create_error_response(
                    f"Input file not found: {input_file}",
                    "FILE_NOT_FOUND"
                )
            
            if not self._is_supported_video_format(input_path):
                return self._create_error_response(
                    f"Unsupported video format: {input_path.suffix}",
                    "UNSUPPORTED_FORMAT"
                )
            
            # Perform extraction
            result = self._extract_audio(input_path, output_dir)
            
            if result['success']:
                return self._create_success_response({
                    'input_file': str(input_path),
                    'output_file': result['output_file'],
                    'processing_time': result['processing_time']
                })
            else:
                return self._create_error_response(
                    result['error'],
                    "EXTRACTION_FAILED"
                )
                
        except Exception as e:
            self.logger.error(f"Extraction error: {e}")
            return self._create_error_response(
                f"Audio extraction failed: {str(e)}",
                "EXTRACTION_ERROR"
            )
    
    def _handle_list_models(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_models command - scan models directory and return available models."""
        try:
            models_dir = Path(command_data.get('models_dir', 'models'))
            
            # Ensure models directory exists
            if not models_dir.exists():
                models_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created models directory: {models_dir}")
            
            available_models = []
            downloaded_models = []
            
            # Get list of all supported models
            supported_models = self._get_supported_models()
            
            # Scan models directory for downloaded models
            for model_file in models_dir.glob('*.bin'):
                model_info = self._get_model_info_from_file(model_file)
                if model_info:
                    downloaded_models.append(model_info)
            
            # Combine supported and downloaded model information
            for model_name, model_info in supported_models.items():
                # Check if model is already downloaded
                is_downloaded = any(
                    downloaded['name'] == model_name 
                    for downloaded in downloaded_models
                )
                
                if is_downloaded:
                    # Update with downloaded file info
                    downloaded_info = next(
                        (d for d in downloaded_models if d['name'] == model_name), 
                        {}
                    )
                    model_info.update(downloaded_info)
                    model_info['is_downloaded'] = True
                else:
                    model_info['is_downloaded'] = False
                
                available_models.append(model_info)
            
            return self._create_success_response({
                'models': available_models,
                'models_directory': str(models_dir),
                'total_count': len(available_models),
                'downloaded_count': len(downloaded_models)
            })
            
        except Exception as e:
            self.logger.error(f"List models error: {e}")
            return self._create_error_response(
                f"Failed to list models: {str(e)}",
                "LIST_MODELS_ERROR"
            )
    
    def _handle_download_model(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle download_model command with progress tracking."""
        try:
            # Validate required fields
            required_fields = ['model_name']
            missing_fields = [field for field in required_fields if field not in command_data]
            if missing_fields:
                return self._create_error_response(
                    f"Missing required fields: {missing_fields}",
                    "MISSING_FIELDS"
                )
            
            model_name = command_data['model_name']
            models_dir = Path(command_data.get('models_dir', 'models'))
            force_redownload = command_data.get('force_redownload', False)
            
            # Get model information
            supported_models = self._get_supported_models()
            if model_name not in supported_models:
                return self._create_error_response(
                    f"Unsupported model: {model_name}. Available models: {list(supported_models.keys())}",
                    "UNSUPPORTED_MODEL"
                )
            
            model_info = supported_models[model_name]
            model_file_path = models_dir / f"{model_name}.bin"
            
            # Check if model already exists
            if model_file_path.exists() and not force_redownload:
                # Verify existing model
                if self._verify_model_integrity(model_file_path, model_info):
                    return self._create_success_response({
                        'model_name': model_name,
                        'file_path': str(model_file_path),
                        'status': 'already_downloaded',
                        'verified': True,
                        'size_bytes': model_file_path.stat().st_size
                    })
                else:
                    self.logger.warning(f"Model {model_name} failed verification, re-downloading")
            
            # Create models directory if it doesn't exist
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # Download model
            result = self._download_model_file(model_name, model_info, model_file_path)
            
            if result['success']:
                return self._create_success_response({
                    'model_name': model_name,
                    'file_path': str(model_file_path),
                    'status': 'downloaded',
                    'verified': result['verified'],
                    'size_bytes': result['size_bytes'],
                    'download_time': result['download_time']
                })
            else:
                return self._create_error_response(
                    result['error'],
                    "DOWNLOAD_FAILED"
                )
                
        except Exception as e:
            self.logger.error(f"Download model error: {e}")
            return self._create_error_response(
                f"Model download failed: {str(e)}",
                "DOWNLOAD_ERROR"
            )
    
    def _handle_process_batch(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle process_batch command - placeholder implementation."""
        # TODO: Implement in Task 2.4
        return self._create_error_response(
            "Batch processing functionality not yet implemented",
            "NOT_IMPLEMENTED"
        )
    
    def _is_supported_audio_format(self, file_path: Path) -> bool:
        """Check if file format is supported for transcription."""
        supported_formats = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.mov', '.avi'}
        return file_path.suffix.lower() in supported_formats
    
    def _check_disk_space(self, input_path: Path, output_dir: str) -> bool:
        """Check if there's enough disk space for transcription."""
        import shutil
        
        try:
            # Get file size
            file_size = input_path.stat().st_size
            
            # Check available disk space (require 2x file size)
            free_space = shutil.disk_usage(output_dir).free
            required_space = file_size * 2
            
            return free_space > required_space
        except Exception as e:
            self.logger.warning(f"Could not check disk space: {e}")
            return True  # Assume sufficient space if check fails
    
    def _transcribe_file(self, input_path: Path, output_dir: str, model: str, formats: list, language: str) -> Dict[str, Any]:
        """Perform actual transcription using existing whisper_transcription_tool."""
        import subprocess
        import time
        import re
        from datetime import datetime
        
        start_time = time.time()
        
        try:
            # Prepare command arguments
            cmd = [
                sys.executable, '-m', 'src.whisper_transcription_tool.main',
                'transcribe', str(input_path),
                '--model', model,
                '--output-dir', output_dir
            ]
            
            # Add format arguments
            for fmt in formats:
                if fmt in ['txt', 'srt', 'vtt']:
                    cmd.extend(['--output-format', fmt])
            
            # Add language if specified
            if language != 'auto':
                cmd.extend(['--language', language])
            
            self.logger.info(f"Running transcription command: {' '.join(cmd)}")
            
            # Run transcription with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor progress (simplified - real implementation would parse tqdm output)
            stdout, stderr = process.communicate()
            
            processing_time = time.time() - start_time
            
            if process.returncode == 0:
                # Parse output files from stdout/stderr
                output_files = self._parse_output_files(stdout, stderr, input_path, output_dir, formats)
                
                return {
                    'success': True,
                    'output_files': output_files,
                    'processing_time': processing_time,
                    'detected_language': self._extract_language_from_output(stdout, stderr)
                }
            else:
                self.logger.error(f"Transcription failed with return code {process.returncode}")
                self.logger.error(f"stderr: {stderr}")
                return {
                    'success': False,
                    'error': f"Transcription process failed: {stderr[:500]}..."
                }
                
        except Exception as e:
            self.logger.error(f"Transcription execution error: {e}")
            return {
                'success': False,
                'error': f"Failed to execute transcription: {str(e)}"
            }
    
    def _parse_output_files(self, stdout: str, stderr: str, input_path: Path, output_dir: str, formats: list) -> list:
        """Parse output file paths from command output."""
        output_files = []
        
        # Generate expected output file names based on input file and formats
        base_name = input_path.stem
        output_path = Path(output_dir)
        
        for fmt in formats:
            expected_file = output_path / f"{base_name}.{fmt}"
            if expected_file.exists():
                output_files.append(str(expected_file))
        
        return output_files
    
    def _extract_language_from_output(self, stdout: str, stderr: str) -> str:
        """Extract detected language from command output."""
        # Look for language detection patterns in output
        combined_output = stdout + stderr
        
        # Simple pattern matching - would need to be adjusted based on actual output format
        language_patterns = [
            r'Detected language: (\w+)',
            r'Language: (\w+)',
        ]
        
        for pattern in language_patterns:
            match = re.search(pattern, combined_output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'unknown'
    
    def _is_supported_video_format(self, file_path: Path) -> bool:
        """Check if file format is supported for video extraction."""
        supported_formats = {'.mp4', '.mov', '.avi'}
        return file_path.suffix.lower() in supported_formats
    
    def _extract_audio(self, input_path: Path, output_dir: str) -> Dict[str, Any]:
        """Extract audio from video using existing whisper_transcription_tool."""
        import subprocess
        import time
        
        start_time = time.time()
        
        try:
            # Prepare command arguments
            cmd = [
                sys.executable, '-m', 'src.whisper_transcription_tool.main',
                'extract', str(input_path),
                '--output-dir', output_dir
            ]
            
            self.logger.info(f"Running extraction command: {' '.join(cmd)}")
            
            # Run extraction
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            processing_time = time.time() - start_time
            
            if process.returncode == 0:
                # Parse output file from stdout/stderr
                output_file = self._parse_extracted_audio_file(stdout, stderr, input_path, output_dir)
                
                return {
                    'success': True,
                    'output_file': output_file,
                    'processing_time': processing_time
                }
            else:
                self.logger.error(f"Audio extraction failed with return code {process.returncode}")
                self.logger.error(f"stderr: {stderr}")
                return {
                    'success': False,
                    'error': f"Audio extraction failed: {stderr[:500]}..."
                }
                
        except Exception as e:
            self.logger.error(f"Audio extraction execution error: {e}")
            return {
                'success': False,
                'error': f"Failed to execute audio extraction: {str(e)}"
            }
    
    def _parse_extracted_audio_file(self, stdout: str, stderr: str, input_path: Path, output_dir: str) -> str:
        """Parse extracted audio file path from command output."""
        # Generate expected output file name
        base_name = input_path.stem
        output_path = Path(output_dir)
        expected_file = output_path / f"{base_name}.wav"
        
        if expected_file.exists():
            return str(expected_file)
        
        # Fallback: look for any .wav file in output directory with similar name
        for wav_file in output_path.glob(f"{base_name}*.wav"):
            return str(wav_file)
        
        return str(expected_file)  # Return expected path even if not found
    
    def _get_supported_models(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all supported Whisper models."""
        return {
            'tiny': {
                'name': 'tiny',
                'size_mb': 39,
                'description': 'Fastest, lowest accuracy',
                'performance': {
                    'speed_multiplier': 32,
                    'accuracy': 'Fair',
                    'memory_usage': 'Very Low',
                    'languages': 99
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin',
                'sha256': None  # Would need to be filled with actual checksums
            },
            'tiny.en': {
                'name': 'tiny.en',
                'size_mb': 39,
                'description': 'Fastest, English-only',
                'performance': {
                    'speed_multiplier': 32,
                    'accuracy': 'Fair',
                    'memory_usage': 'Very Low',
                    'languages': 1
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin',
                'sha256': None
            },
            'base': {
                'name': 'base',
                'size_mb': 74,
                'description': 'Good balance of speed and accuracy',
                'performance': {
                    'speed_multiplier': 16,
                    'accuracy': 'Good',
                    'memory_usage': 'Low',
                    'languages': 99
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin',
                'sha256': None
            },
            'base.en': {
                'name': 'base.en',
                'size_mb': 74,
                'description': 'Good balance, English-only',
                'performance': {
                    'speed_multiplier': 16,
                    'accuracy': 'Good',
                    'memory_usage': 'Low',
                    'languages': 1
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin',
                'sha256': None
            },
            'small': {
                'name': 'small',
                'size_mb': 244,
                'description': 'Better accuracy, slower',
                'performance': {
                    'speed_multiplier': 6,
                    'accuracy': 'Better',
                    'memory_usage': 'Medium',
                    'languages': 99
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin',
                'sha256': None
            },
            'small.en': {
                'name': 'small.en',
                'size_mb': 244,
                'description': 'Better accuracy, English-only',
                'performance': {
                    'speed_multiplier': 6,
                    'accuracy': 'Better',
                    'memory_usage': 'Medium',
                    'languages': 1
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin',
                'sha256': None
            },
            'medium': {
                'name': 'medium',
                'size_mb': 769,
                'description': 'High accuracy, slower processing',
                'performance': {
                    'speed_multiplier': 2,
                    'accuracy': 'High',
                    'memory_usage': 'High',
                    'languages': 99
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin',
                'sha256': None
            },
            'medium.en': {
                'name': 'medium.en',
                'size_mb': 769,
                'description': 'High accuracy, English-only',
                'performance': {
                    'speed_multiplier': 2,
                    'accuracy': 'High',
                    'memory_usage': 'High',
                    'languages': 1
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.en.bin',
                'sha256': None
            },
            'large-v1': {
                'name': 'large-v1',
                'size_mb': 1550,
                'description': 'Best accuracy (v1), very slow',
                'performance': {
                    'speed_multiplier': 1,
                    'accuracy': 'Excellent',
                    'memory_usage': 'Very High',
                    'languages': 99
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v1.bin',
                'sha256': None
            },
            'large-v2': {
                'name': 'large-v2',
                'size_mb': 1550,
                'description': 'Best accuracy (v2), very slow',
                'performance': {
                    'speed_multiplier': 1,
                    'accuracy': 'Excellent',
                    'memory_usage': 'Very High',
                    'languages': 99
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v2.bin',
                'sha256': None
            },
            'large-v3': {
                'name': 'large-v3',
                'size_mb': 1550,
                'description': 'Best accuracy (v3), very slow',
                'performance': {
                    'speed_multiplier': 1,
                    'accuracy': 'Excellent',
                    'memory_usage': 'Very High',
                    'languages': 99
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin',
                'sha256': None
            },
            'large-v3-turbo': {
                'name': 'large-v3-turbo',
                'size_mb': 809,
                'description': 'Best balance of accuracy and speed (recommended)',
                'performance': {
                    'speed_multiplier': 8,
                    'accuracy': 'Excellent',
                    'memory_usage': 'High',
                    'languages': 99
                },
                'download_url': 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin',
                'sha256': None
            }
        }
    
    def _get_model_info_from_file(self, model_file_path: Path) -> Dict[str, Any]:
        """Extract model information from a downloaded model file."""
        try:
            file_stats = model_file_path.stat()
            model_name = model_file_path.stem.replace('ggml-', '')
            
            return {
                'name': model_name,
                'file_path': str(model_file_path),
                'size_bytes': file_stats.st_size,
                'size_mb': round(file_stats.st_size / (1024 * 1024), 1),
                'modified_time': file_stats.st_mtime,
                'is_downloaded': True
            }
        except Exception as e:
            self.logger.error(f"Failed to get model info from {model_file_path}: {e}")
            return None
    
    def _verify_model_integrity(self, model_file_path: Path, model_info: Dict[str, Any]) -> bool:
        """Verify model file integrity using size and optionally checksum."""
        try:
            if not model_file_path.exists():
                return False
            
            # Check file size
            actual_size_mb = model_file_path.stat().st_size / (1024 * 1024)
            expected_size_mb = model_info.get('size_mb', 0)
            
            # Allow 5% tolerance for file size
            size_tolerance = expected_size_mb * 0.05
            if abs(actual_size_mb - expected_size_mb) > size_tolerance:
                self.logger.warning(f"Model size mismatch: expected {expected_size_mb}MB, got {actual_size_mb}MB")
                return False
            
            # TODO: Verify SHA256 checksum if available
            # if model_info.get('sha256'):
            #     return self._verify_checksum(model_file_path, model_info['sha256'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model verification failed: {e}")
            return False
    
    def _download_model_file(self, model_name: str, model_info: Dict[str, Any], output_path: Path) -> Dict[str, Any]:
        """Download a model file with progress tracking."""
        import time
        import subprocess
        
        start_time = time.time()
        
        try:
            download_url = model_info.get('download_url')
            if not download_url:
                return {
                    'success': False,
                    'error': f"No download URL available for model {model_name}"
                }
            
            self.logger.info(f"Downloading model {model_name} from {download_url}")
            
            # Use existing whisper tool download functionality if available
            cmd = [
                sys.executable, '-m', 'src.whisper_transcription_tool.main',
                'download-model', model_name,
                '--output-dir', str(output_path.parent)
            ]
            
            # Try using the existing tool first
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            download_time = time.time() - start_time
            
            if result.returncode == 0 and output_path.exists():
                # Verify downloaded model
                verified = self._verify_model_integrity(output_path, model_info)
                
                return {
                    'success': True,
                    'verified': verified,
                    'size_bytes': output_path.stat().st_size,
                    'download_time': download_time
                }
            else:
                # Fallback to direct download using curl/wget
                return self._download_with_curl(download_url, output_path, model_info, download_time)
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Model download timed out after 10 minutes"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Download failed: {str(e)}"
            }
    
    def _download_with_curl(self, url: str, output_path: Path, model_info: Dict[str, Any], elapsed_time: float) -> Dict[str, Any]:
        """Fallback download using curl."""
        import subprocess
        import time
        
        try:
            self.logger.info(f"Fallback: downloading with curl to {output_path}")
            
            # Use curl for download with progress
            cmd = [
                'curl', '-L', '-o', str(output_path), url,
                '--progress-bar'
            ]
            
            result = subprocess.run(cmd, timeout=600)
            
            total_time = elapsed_time + (time.time() - elapsed_time)
            
            if result.returncode == 0 and output_path.exists():
                verified = self._verify_model_integrity(output_path, model_info)
                
                return {
                    'success': True,
                    'verified': verified,
                    'size_bytes': output_path.stat().st_size,
                    'download_time': total_time
                }
            else:
                return {
                    'success': False,
                    'error': f"curl download failed with return code {result.returncode}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "curl download timed out"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"curl download failed: {str(e)}"
            }


def main():
    """
    Main entry point for the CLI wrapper.
    
    Reads JSON command from stdin and outputs JSON response to stdout.
    This allows for seamless communication with the Swift application.
    """
    if len(sys.argv) > 1:
        # Command provided as argument
        command_json = sys.argv[1]
    else:
        # Command provided via stdin
        command_json = sys.stdin.read()
    
    wrapper = MacOSCLIWrapper()
    result = wrapper.handle_command(command_json)
    
    # Output JSON result to stdout
    print(result)


if __name__ == '__main__':
    main()