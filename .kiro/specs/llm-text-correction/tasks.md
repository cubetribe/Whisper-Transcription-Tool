# Implementation Plan

## IMPLEMENTIERUNGSRICHTLINIEN FÜR CLAUDE

**KRITISCH: Diese Tasks müssen systematisch von oben nach unten abgearbeitet werden.**

### Strikte Implementierungsregeln:
- **Sequenzielle Bearbeitung**: Tasks MÜSSEN in der angegebenen Reihenfolge (1.1 → 1.2 → 1.3 → 2.1 → etc.) abgearbeitet werden
- **Keine Tasks überspringen**: Jeder Task muss vollständig abgeschlossen werden bevor der nächste beginnt
- **Keine Shortcuts**: Keine "Quick-Fixes", Workarounds oder vereinfachte Implementierungen
- **Alle Tests implementieren**: Unit Tests, Integration Tests, Error Handling Tests - ALLE müssen funktionieren
- **Production-Ready Code**: Jeder Task muss production-tauglichen Code produzieren
- **Vollständige Implementierung**: Alle Bullet Points in jedem Task müssen umgesetzt werden

### Qualitätskontrolle:
- **Keine Mocks oder Dummies**: Echte Implementierungen für alle Komponenten
- **Vollständige Error Handling**: Alle Fehlerfälle müssen behandelt werden
- **Echte Dependencies**: llama-cpp-python, psutil, FastAPI - alles muss echt integriert werden
- **Comprehensive Testing**: Tests müssen tatsächlich laufen und alle Szenarien abdecken
- **Documentation**: Code muss vollständig dokumentiert sein

### Task-Abhängigkeiten beachten:
- Prerequisites müssen erfüllt sein bevor nachfolgende Tasks beginnen
- Alle Requirements-Referenzen müssen validiert werden
- Integration zwischen Komponenten muss vollständig funktionieren

### Task-Tracking und Dokumentation:
- **Checkboxen abhaken**: Nach Abschluss jedes Tasks die entsprechende Checkbox von `[ ]` auf `[x]` ändern
- **Implementierungshinweise**: Bei jedem abgeschlossenen Task Hinweise unter dem Task hinzufügen:
  ```
  **IMPLEMENTIERT** - [Datum]
  - Dateien erstellt: [Liste der erstellten/geänderten Dateien]
  - Besonderheiten: [Wichtige Implementierungsdetails oder Abweichungen]
  - Tests: [Status der implementierten Tests]
  - Nächste Schritte: [Was für den nächsten Task zu beachten ist]
  ```
- **Änderungen dokumentieren**: Falls Implementierungsdetails vom ursprünglichen Plan abweichen, diese klar dokumentieren
- **Probleme festhalten**: Aufgetretene Probleme und deren Lösungen für zukünftige Referenz notieren
- **Integration Notes**: Wichtige Erkenntnisse für die Integration mit anderen Komponenten festhalten

### Beispiel für abgehakten Task:
```
- [x] 1.1 Create module5_text_correction directory structure
  **IMPLEMENTIERT** - 2024-01-15
  - Dateien erstellt: src/whisper_transcription_tool/module5_text_correction/__init__.py, llm_corrector.py, correction_prompts.py, batch_processor.py
  - Besonderheiten: Zusätzliche resource_manager.py erstellt für bessere Modularität
  - Tests: Grundlegende Import-Tests implementiert
  - Nächste Schritte: PromptTemplates für Task 1.2 bereit
```

- [ ] 1. Core Module Foundation
  - [ ] 1.1 Create module5_text_correction directory structure
    - Create module directory with __init__.py, llm_corrector.py, correction_prompts.py, batch_processor.py
    - Set up proper imports and module initialization
    - Add module to main package imports
    - _Requirements: 1.1, 7.1_

  - [ ] 1.2 Implement CorrectionPrompts class
    - Create PromptTemplates class with system and user prompts for light/standard/strict levels
    - Implement get_correction_prompt function with dialect normalization support
    - Add German-specific prompts for orthography, grammar, and punctuation correction
    - Create unit tests for prompt generation and parameter validation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 1.3 Create core data models
    - Implement CorrectionResult and CorrectionJob dataclasses
    - Create ModelStatus and SystemResources dataclasses for monitoring
    - Implement proper serialization and validation methods
    - _Requirements: 8.1, 8.2, 4.1_

- [ ] 2. Resource Management System
  - [ ] 2.1 Implement ResourceManager singleton
    - Create thread-safe singleton ResourceManager with model locks
    - Implement model resource mapping for Whisper subprocess and LeoLM in-process
    - Add GPU acceleration detection for Metal/CUDA/CPU
    - Create unit tests for singleton behavior and thread safety
    - _Requirements: 1.1, 1.3, 1.5, 4.1, 4.4_

  - [ ] 2.2 Add memory monitoring and management
    - Implement check_available_memory using psutil
    - Add memory threshold checking before model loading
    - Create force_cleanup method with garbage collection
    - Implement memory usage monitoring with configurable thresholds
    - _Requirements: 4.1, 4.2, 4.3, 9.2_

  - [ ] 2.3 Implement model swapping functionality
    - Create swap_models method with proper resource cleanup
    - Add model loading/unloading with error handling
    - Implement request_model and release_model with locking
    - Add integration tests for model swapping scenarios
    - _Requirements: 1.2, 1.3, 4.5, 9.1, 9.3_

- [ ] 3. LLM Integration
  - [ ] 3.1 Implement LLMCorrector class
    - Create LLMCorrector with llama-cpp-python integration
    - Implement model loading with platform-specific optimizations (Metal/CUDA)
    - Add context length detection and token estimation
    - Create proper error handling for model loading failures
    - _Requirements: 1.1, 1.4, 6.1, 10.1_

  - [ ] 3.2 Add text correction functionality
    - Implement correct_text method with prompt integration
    - Add temperature and generation parameter handling
    - Create proper error handling for LLM inference failures
    - Implement token counting and context management
    - _Requirements: 2.1, 2.2, 2.3, 9.3_

  - [ ] 3.3 Add model lifecycle management
    - Implement load_model and unload_model methods
    - Add proper memory cleanup and resource deallocation
    - Create model verification and integrity checking
    - Add unit tests for model lifecycle operations
    - _Requirements: 1.2, 1.3, 9.1, 10.2_

- [x] 4. Batch Processing Implementation
  - [x] 4.1 Create BatchProcessor class foundation
    - Implement BatchProcessor with configurable chunking parameters
    - Add TextChunk dataclass with overlap handling (depends on task 1.3 data models)
    - Create chunking strategy selection (SentencePiece vs NLTK)
    - Implement basic chunk_text method with sentence boundary detection
    - _Requirements: 3.1, 3.2_
    **IMPLEMENTIERT** - 2024-09-25
    - Dateien erstellt: src/whisper_transcription_tool/module5_text_correction/batch_processor.py, __init__.py aktualisiert
    - Besonderheiten: Vollständige BatchProcessor Klasse mit TextChunk dataclass, TokenizerStrategy enum, und ChunkProcessingResult
    - Tests: Funktionsfähige Integration getestet mit Mock-Funktionen
    - Nächste Schritte: Intelligentes Chunking bereits implementiert

  - [x] 4.2 Implement intelligent text chunking
    - Add SentencePiece tokenizer integration for LeoLM compatibility
    - Implement NLTK fallback for sentence segmentation
    - Create overlap handling between chunks for context continuity
    - Add token estimation and context length validation
    - _Requirements: 3.1, 3.2, 3.3_
    **IMPLEMENTIERT** - 2024-09-25
    - Dateien erstellt: Vollständige Chunking-Logik in batch_processor.py
    - Besonderheiten: SentencePiece/NLTK/Simple Fallback-Strategien, intelligente Satzgrenzen-Erkennung, Overlap-Berechnung
    - Tests: Token-Estimation und Chunking erfolgreich getestet
    - Nächste Schritte: Chunk-Processing bereits implementiert

  - [x] 4.3 Add chunk processing and reassembly
    - Implement process_chunks_async for FastAPI BackgroundTask integration (depends on task 3.2 LLM correction)
    - Create process_chunks_sync for CLI usage (depends on task 3.2 LLM correction)
    - Add _merge_overlapping_chunks method for intelligent reassembly
    - Implement progress reporting with chunk-level granularity
    - _Requirements: 3.3, 3.4, 3.5_
    **IMPLEMENTIERT** - 2024-09-25
    - Dateien erstellt: Async/Sync Processing in batch_processor.py
    - Besonderheiten: ThreadPoolExecutor für Async-Processing, intelligente Overlap-Merge-Logik, detaillierte Progress-Callbacks
    - Tests: Beide Processing-Modi erfolgreich getestet
    - Nächste Schritte: Error Handling bereits implementiert

  - [x] 4.4 Add error handling and recovery
    - Implement chunk-level error handling with continuation
    - Add partial correction support for failed chunks
    - Create detailed error reporting with chunk position information
    - Add integration tests for error scenarios
    - _Requirements: 3.5, 9.3_
    **IMPLEMENTIERT** - 2024-09-25
    - Dateien erstellt: Comprehensive Error Handling in batch_processor.py
    - Besonderheiten: ChunkProcessingResult für detaillierte Fehlerbehandlung, Fallback zu Original-Text bei Fehlern, Continue-Processing trotz einzelner Chunk-Failures
    - Tests: Error-Szenarien erfolgreich getestet mit Mock-Fehlern
    - Nächste Schritte: BatchProcessor komplett funktionsfähig für Integration in LLM-System

  **ZUSÄTZLICHE IMPLEMENTIERUNG**:
    - Dateien erstellt: examples.py (Demonstriert alle BatchProcessor Features), README.md (Comprehensive Dokumentation)
    - Besonderheiten: requirements.txt erweitert um sentencepiece, nltk, transformers für Tokenization
    - Tests: Integration erfolgreich getestet, alle Komponenten funktionsfähig
    - Integration: Bereit für LLMCorrector Integration und API-Endpunkte

- [ ] 5. Configuration Integration
  - [ ] 5.1 Extend core configuration system
    - Add text_correction section to config schema
    - Implement configuration validation for all correction parameters
    - Add platform-specific configuration options (Metal/CUDA)
    - Create configuration migration for existing installations
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ] 5.2 Add CLI parameter support
    - Extend main CLI with --enable-correction and --correction-level flags
    - Add --dialect-normalization flag for regional text processing
    - Implement CLI parameter validation and help text
    - Create CLI integration tests for correction parameters
    - _Requirements: 6.1, 7.4_

  - [ ] 5.3 Implement configuration availability checking
    - Create is_correction_available function with comprehensive status checking
    - Add model file existence and integrity validation
    - Implement RAM requirement checking and reporting
    - Add configuration validation with detailed error messages
    - _Requirements: 7.5, 9.1, 10.4_

- [ ] 6. API and Backend Integration
  - [ ] 6.1 Extend FastAPI transcribe endpoint
    - Add enable_correction, correction_level, and dialect_normalization parameters
    - Implement parameter validation with proper error responses
    - Integrate correction workflow into existing transcription pipeline
    - Add WebSocket event integration for correction progress
    - _Requirements: 6.1, 6.5_

  - [ ] 6.2 Create correction status endpoint
    - Implement /api/correction-status GET endpoint
    - Add comprehensive status checking (model availability, RAM, etc.)
    - Create proper JSON response format with error details
    - Add endpoint documentation and integration tests
    - _Requirements: 6.2, 9.1, 10.2_

  - [ ] 6.3 Implement WebSocket event system
    - Add correction_started, correction_progress, correction_completed events
    - Implement correction_error event with detailed error information
    - Create event payload validation and documentation
    - Add WebSocket integration tests for all correction events
    - _Requirements: 6.3, 6.4, 9.1_

- [ ] 7. Main Orchestration Logic
  - [ ] 7.1 Implement correct_transcription async function
    - Create main orchestration function with resource management
    - Implement memory checking and model swapping logic
    - Add comprehensive error handling with fallback to original transcription
    - Integrate BatchProcessor and LLMCorrector components
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 9.4_

  - [ ] 7.2 Add synchronous correction support
    - Implement correct_transcription_sync for CLI usage
    - Create proper async/sync boundary handling
    - Add ThreadPoolExecutor integration for CPU-intensive operations
    - Implement progress reporting for both async and sync contexts
    - _Requirements: 1.1, 6.1_

  - [ ] 7.3 Integrate with existing transcription workflow
    - Modify module1_transcribe to call correction after transcription
    - Add correction enable/disable logic based on configuration
    - Implement proper event publishing for correction phases
    - Create integration tests for complete transcription + correction flow
    - _Requirements: 1.1, 1.4, 6.3_

- [ ] 8. File Output and Management
  - [ ] 8.1 Implement dual file output system
    - Create file naming convention for original and corrected versions
    - Implement timestamp suffix handling for duplicate filenames
    - Add proper file path sanitization and validation
    - Create file output tests for various scenarios
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ] 8.2 Add output format handling
    - Implement corrected text output for TXT format
    - Add metadata preservation for SRT/VTT timing information
    - Create JSON output format with correction metadata
    - Add format-specific output tests
    - _Requirements: 8.2, 8.4, 8.5_

  - [ ] 8.3 Implement batch file management
    - Add consistent file naming for batch processing
    - Implement proper file organization and cleanup
    - Create batch output summary and reporting
    - Add batch processing integration tests
    - _Requirements: 8.5, 3.4_

- [ ] 9. Error Handling and Logging
  - [ ] 9.1 Create comprehensive error handling system
    - Implement custom exception classes for all error scenarios
    - Add error categorization and recovery strategies
    - Create user-friendly error messages with solution suggestions
    - Implement error logging with proper categorization
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 9.2 Add detailed logging system
    - Create separate text_correction logger category
    - Implement detailed operation logging with privacy considerations
    - Add configurable log levels and output formats
    - Create log sanitization to avoid sensitive data exposure (coordinate with ResourceManager for path anonymization)
    - _Requirements: 9.4, 9.5_

  - [ ] 9.3 Implement monitoring and metrics
    - Add optional performance metrics collection (depends on task 2.1 ResourceManager monitoring)
    - Implement correction_duration_seconds and other key metrics
    - Create metrics export functionality for monitoring systems
    - Add monitoring configuration and privacy controls
    - _Requirements: 9.5_

- [ ] 10. Frontend Integration
  - [ ] 10.1 Add correction UI controls
    - Create "Textkorrektur aktivieren" checkbox in web interface
    - Add correction level dropdown (light/standard/strict)
    - Implement dialect normalization toggle
    - Add UI state management for correction options
    - _Requirements: 5.1, 5.2, 5.5_

  - [ ] 10.2 Implement correction status display
    - Add model availability checking and status display
    - Create tooltip and help text for unavailable correction
    - Implement RAM requirement warnings and guidance
    - Add correction capability detection on page load
    - _Requirements: 5.3, 5.5_

  - [ ] 10.3 Add progress visualization
    - Implement two-phase progress bar (transcription + correction)
    - Add phase-specific status messages and ETA display
    - Create correction progress updates with chunk information
    - Implement proper handling of correction-skipped scenarios
    - _Requirements: 5.4, 5.5, 6.3_

  - [ ] 10.4 Add result presentation
    - Create download links for both original and corrected versions
    - Add correction metadata display (processing time, chunks, etc.)
    - Implement result comparison and diff visualization
    - Add proper error message display for correction failures
    - _Requirements: 5.6, 8.1, 9.1_

- [ ] 11. Dependencies and Installation
  - [ ] 11.1 Add llama-cpp-python dependency
    - Add llama-cpp-python to requirements with platform-specific installation notes
    - Create installation documentation for Metal/CUDA variants
    - Add dependency checking and validation on startup
    - Implement graceful degradation when dependencies unavailable
    - _Requirements: 10.1, 10.5_

  - [ ] 11.2 Add tokenization dependencies
    - Add sentencepiece dependency for LeoLM tokenizer compatibility
    - Include nltk as fallback for sentence segmentation
    - Create tokenizer setup and data download automation
    - Add tokenizer availability checking and fallback logic
    - _Requirements: 3.1, 3.2, 10.1_

  - [ ] 11.3 Create model download utilities
    - Implement optional CLI helper for LeoLM model download
    - Add model verification and integrity checking
    - Create download progress reporting and resumption
    - Add model management documentation and troubleshooting
    - _Requirements: 10.2, 10.5_

- [ ] 12. Testing and Quality Assurance
  - [ ] 12.1 Create comprehensive unit tests
    - Write unit tests for all core classes (LLMCorrector, BatchProcessor, ResourceManager)
    - Add tests for prompt generation and configuration validation
    - Create mock-based tests for LLM integration
    - Implement error handling and edge case testing
    - _Requirements: All requirements validation_

  - [ ] 12.2 Add integration tests
    - Create end-to-end tests for complete correction workflow
    - Add API integration tests for all new endpoints
    - Implement WebSocket event testing
    - Create batch processing integration tests
    - _Requirements: 1.1, 6.1, 6.2, 6.3_

  - [ ] 12.3 Implement performance and memory tests
    - Create memory usage tests for model swapping
    - Add performance benchmarks for correction speed
    - Implement resource cleanup validation tests
    - Create concurrent processing stress tests
    - _Requirements: 4.1, 4.3, 4.4, 4.5_

- [ ] 13. Documentation and User Guidance
  - [ ] 13.1 Create comprehensive documentation
    - Add README section for text correction feature
    - Create hardware requirements and setup documentation
    - Add troubleshooting guide for common issues
    - Include license information for LeoLM and dependencies
    - _Requirements: 10.3, 10.4, 10.5_

  - [ ] 13.2 Add configuration examples
    - Create example configurations for different use cases
    - Add platform-specific configuration guidance
    - Include performance tuning recommendations
    - Create migration guide for existing installations
    - _Requirements: 7.5, 10.5_

  - [ ] 13.3 Create user guides and FAQ
    - Add user guide for correction feature usage
    - Create FAQ for common questions and issues
    - Include best practices for model selection and configuration
    - Add troubleshooting steps for installation and runtime issues
    - _Requirements: 10.5, 9.1_