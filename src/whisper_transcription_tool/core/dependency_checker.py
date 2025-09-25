"""
Dependency validation module for LLM text correction features.
Checks for required dependencies on startup and provides helpful error messages.
"""
import importlib
import logging
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DependencyInfo:
    """Information about a required dependency."""
    name: str
    import_name: str
    min_version: Optional[str] = None
    install_command: Optional[str] = None
    description: str = ""
    required_for: str = ""

class DependencyChecker:
    """Manages dependency validation for LLM features."""

    # Define LLM-specific dependencies
    LLM_DEPENDENCIES = {
        'llama_cpp': DependencyInfo(
            name='llama-cpp-python',
            import_name='llama_cpp',
            min_version='0.2.0',
            install_command='CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python',
            description='Python bindings for llama.cpp with Metal support',
            required_for='Local LLM inference'
        ),
        'sentencepiece': DependencyInfo(
            name='sentencepiece',
            import_name='sentencepiece',
            min_version='0.1.99',
            install_command='pip install sentencepiece>=0.1.99',
            description='SentencePiece tokenizer for LeoLM',
            required_for='LeoLM tokenization'
        ),
        'nltk': DependencyInfo(
            name='nltk',
            import_name='nltk',
            min_version='3.8',
            install_command='pip install nltk>=3.8',
            description='Natural Language Toolkit for fallback tokenization',
            required_for='Fallback tokenization'
        ),
        'transformers': DependencyInfo(
            name='transformers',
            import_name='transformers',
            min_version='4.21.0',
            install_command='pip install transformers>=4.21.0',
            description='Hugging Face transformers for model utilities',
            required_for='Model configuration and utilities'
        )
    }

    @classmethod
    def check_dependency(cls, dep_key: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a single dependency is available.

        Args:
            dep_key: Key from LLM_DEPENDENCIES

        Returns:
            Tuple of (is_available, error_message)
        """
        if dep_key not in cls.LLM_DEPENDENCIES:
            return False, f"Unknown dependency: {dep_key}"

        dep_info = cls.LLM_DEPENDENCIES[dep_key]

        try:
            module = importlib.import_module(dep_info.import_name)

            # Check version if specified
            if dep_info.min_version and hasattr(module, '__version__'):
                from packaging import version
                if version.parse(module.__version__) < version.parse(dep_info.min_version):
                    return False, (
                        f"{dep_info.name} version {module.__version__} is below "
                        f"minimum required {dep_info.min_version}"
                    )

            return True, None

        except ImportError as e:
            error_msg = (
                f"Missing dependency: {dep_info.name}\n"
                f"Required for: {dep_info.required_for}\n"
                f"Install with: {dep_info.install_command}\n"
                f"Error details: {str(e)}"
            )
            return False, error_msg

    @classmethod
    def check_all_llm_dependencies(cls, graceful: bool = True) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Check all LLM dependencies.

        Args:
            graceful: If True, collect all errors. If False, raise on first error.

        Returns:
            Dictionary mapping dependency keys to (is_available, error_message) tuples
        """
        results = {}

        for dep_key in cls.LLM_DEPENDENCIES:
            is_available, error_msg = cls.check_dependency(dep_key)
            results[dep_key] = (is_available, error_msg)

            if not graceful and not is_available:
                logger.error(f"Dependency check failed: {error_msg}")
                raise ImportError(error_msg)

        return results

    @classmethod
    def validate_llm_setup(cls, require_all: bool = False) -> bool:
        """
        Validate that LLM dependencies are properly set up.

        Args:
            require_all: If True, all dependencies must be available.
                        If False, allows graceful degradation.

        Returns:
            True if setup is valid (based on require_all parameter)
        """
        results = cls.check_all_llm_dependencies(graceful=True)

        missing_deps = []
        for dep_key, (is_available, error_msg) in results.items():
            if not is_available:
                missing_deps.append((dep_key, error_msg))
                logger.warning(f"LLM dependency issue: {error_msg}")

        if missing_deps:
            if require_all:
                logger.error("Missing required LLM dependencies. LLM features will be disabled.")
                cls._print_installation_guide(missing_deps)
                return False
            else:
                logger.info("Some LLM dependencies missing. Features will be limited.")
                cls._print_installation_guide(missing_deps)
        else:
            logger.info("All LLM dependencies are available.")

        return True

    @classmethod
    def _print_installation_guide(cls, missing_deps: List[Tuple[str, str]]) -> None:
        """Print installation guide for missing dependencies."""
        print("\n" + "="*80)
        print("LLM DEPENDENCY INSTALLATION GUIDE")
        print("="*80)

        for dep_key, error_msg in missing_deps:
            dep_info = cls.LLM_DEPENDENCIES[dep_key]
            print(f"\n❌ {dep_info.name}:")
            print(f"   Purpose: {dep_info.required_for}")
            print(f"   Install: {dep_info.install_command}")

            # Special instructions for macOS Metal support
            if dep_key == 'llama_cpp':
                print("   macOS Note: The CMAKE_ARGS ensure Metal GPU acceleration")
                print("   Alternative: pip install llama-cpp-python (CPU-only)")

        print(f"\n🔧 Quick setup for all LLM dependencies:")
        print("   pip install -e \".[llm]\"")
        print("   OR")
        print("   pip install -r requirements.txt")

        print(f"\n📋 After installation, initialize NLTK data:")
        print("   python -c \"import nltk; nltk.download('punkt')\"")

        print("="*80 + "\n")

    @classmethod
    def setup_nltk_data(cls) -> bool:
        """
        Setup NLTK data downloads if NLTK is available.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            import nltk

            # Download required NLTK data
            required_datasets = ['punkt', 'punkt_tab']

            for dataset in required_datasets:
                try:
                    nltk.download(dataset, quiet=True)
                    logger.info(f"NLTK dataset '{dataset}' ready")
                except Exception as e:
                    logger.warning(f"Failed to download NLTK dataset '{dataset}': {e}")

            return True

        except ImportError:
            logger.warning("NLTK not available, skipping data setup")
            return False

    @classmethod
    def get_dependency_status(cls) -> Dict[str, Dict[str, any]]:
        """
        Get detailed status of all LLM dependencies.

        Returns:
            Dictionary with detailed dependency information
        """
        status = {}
        results = cls.check_all_llm_dependencies(graceful=True)

        for dep_key, (is_available, error_msg) in results.items():
            dep_info = cls.LLM_DEPENDENCIES[dep_key]

            version_info = "Unknown"
            if is_available:
                try:
                    module = importlib.import_module(dep_info.import_name)
                    if hasattr(module, '__version__'):
                        version_info = module.__version__
                except:
                    pass

            status[dep_key] = {
                'name': dep_info.name,
                'available': is_available,
                'version': version_info,
                'min_version': dep_info.min_version,
                'description': dep_info.description,
                'required_for': dep_info.required_for,
                'install_command': dep_info.install_command,
                'error': error_msg if not is_available else None
            }

        return status


def validate_startup_dependencies(require_all: bool = False) -> bool:
    """
    Convenience function for validating dependencies at application startup.

    Args:
        require_all: Whether all LLM dependencies are required

    Returns:
        True if validation passes
    """
    checker = DependencyChecker()

    # Setup NLTK data if available
    checker.setup_nltk_data()

    # Validate LLM setup
    return checker.validate_llm_setup(require_all=require_all)


if __name__ == "__main__":
    # CLI for dependency checking
    import argparse

    parser = argparse.ArgumentParser(description="Check LLM dependencies")
    parser.add_argument("--require-all", action="store_true",
                       help="Require all dependencies (exit with error if missing)")
    parser.add_argument("--status", action="store_true",
                       help="Show detailed dependency status")

    args = parser.parse_args()

    if args.status:
        import json
        status = DependencyChecker.get_dependency_status()
        print(json.dumps(status, indent=2))
    else:
        success = validate_startup_dependencies(require_all=args.require_all)
        sys.exit(0 if success else 1)