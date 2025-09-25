#!/usr/bin/env python3
"""
BatchProcessor Usage Examples

This script demonstrates the various capabilities of the BatchProcessor
for intelligent text chunking and batch processing.
"""

import asyncio
import time
from typing import List

from .batch_processor import BatchProcessor, TextChunk, TokenizerStrategy


def mock_llm_correction(text: str) -> str:
    """
    Mock LLM correction function for demonstration.
    In a real implementation, this would call the actual LLM model.
    """
    # Simulate processing time
    time.sleep(0.1)

    # Simple mock corrections for demonstration
    corrections = {
        "das": "das",  # No change
        "ist": "ist",  # No change
        "ein": "ein",  # No change
        "tst": "Test",  # Spelling correction
        "functionieren": "funktionieren",  # Spelling correction
        "gud": "gut",  # Spelling correction
    }

    corrected = text
    for error, correction in corrections.items():
        corrected = corrected.replace(error, correction)

    return f"✓ {corrected}"


def progress_reporter(current: int, total: int, status: str):
    """Progress reporting callback"""
    percentage = (current / total) * 100
    print(f"[{percentage:5.1f}%] {current:2d}/{total:2d} - {status}")


def demonstrate_chunking_strategies():
    """Demonstrate different chunking strategies and tokenizers"""
    print("=" * 60)
    print("DEMONSTRATION: Chunking Strategies")
    print("=" * 60)

    # Sample German text with various sentence structures
    sample_text = """
    Dies ist ein Beispieltext für die Demonstration der intelligenten
    Textaufteilung. Der BatchProcessor kann verschiedene Tokenisierungsstrategien
    verwenden. Er respektiert Satzgrenzen und erstellt Überlappungen zwischen
    den Chunks. Das ist wichtig für die Kontexterhaltung bei der Textkorrektur.

    Dieser Text enthält mehrere Absätze und unterschiedliche Satzstrukturen.
    Manche Sätze sind kurz. Andere Sätze sind deutlich länger und enthalten
    mehr Informationen, die vom LLM-Modell verarbeitet werden müssen.

    Die Aufteilung sollte intelligent erfolgen und dabei sowohl die maximale
    Kontextlänge als auch die Satzgrenzen berücksichtigen. Überlappungen
    zwischen den Chunks sorgen für bessere Kohärenz.
    """

    strategies = [
        ("NLTK (Fallback)", "nltk"),
        ("Simple Regex", "simple"),
        ("SentencePiece", "sentencepiece")  # Will fallback if not available
    ]

    for strategy_name, strategy_key in strategies:
        print(f"\n--- {strategy_name} Strategy ---")

        try:
            processor = BatchProcessor(
                max_context_length=200,  # Small for demo
                overlap_sentences=1,
                tokenizer_strategy=strategy_key
            )

            chunks = processor.chunk_text(sample_text)

            print(f"Created {len(chunks)} chunks:")
            for i, chunk in enumerate(chunks):
                print(f"  Chunk {i}: {chunk.token_count} tokens, "
                      f"overlap: {chunk.overlap_start}/{chunk.overlap_end}")
                print(f"    Text: {chunk.text[:80]}...")

        except Exception as e:
            print(f"  Error with {strategy_name}: {e}")


def demonstrate_sync_processing():
    """Demonstrate synchronous batch processing"""
    print("\n" + "=" * 60)
    print("DEMONSTRATION: Synchronous Processing")
    print("=" * 60)

    processor = BatchProcessor(
        max_context_length=150,
        overlap_sentences=1
    )

    # Text with some intentional errors for correction demonstration
    text_with_errors = """
    Das ist ein tst für die Textkorrektur. Es soll gud functionieren.
    Der Prozess sollte alle Fehler finden und korrigieren. Manchmal
    gibt es auch komplexere Probleme in langen Sätzen, die mehrere
    Korrekturen benötigen könnten.
    """

    print("Original text:")
    print(f"  {text_with_errors.strip()}")

    try:
        chunks = processor.chunk_text(text_with_errors)
        print(f"\nProcessing {len(chunks)} chunks synchronously...")

        start_time = time.time()
        corrected_text = processor.process_chunks_sync(
            chunks,
            mock_llm_correction,
            progress_reporter
        )
        processing_time = time.time() - start_time

        print(f"\nCorrected text:")
        print(f"  {corrected_text}")
        print(f"\nProcessing time: {processing_time:.2f}s")

    except Exception as e:
        print(f"Sync processing failed: {e}")


async def demonstrate_async_processing():
    """Demonstrate asynchronous batch processing"""
    print("\n" + "=" * 60)
    print("DEMONSTRATION: Asynchronous Processing")
    print("=" * 60)

    processor = BatchProcessor(
        max_context_length=100,  # Smaller chunks for more parallelism
        overlap_sentences=1
    )

    # Longer text to benefit from async processing
    long_text = """
    Dies ist ein längerer Beispieltext für die asynchrone Verarbeitung.
    Der BatchProcessor kann mehrere Chunks parallel verarbeiten, was
    die Gesamtverarbeitungszeit deutlich reduziert. Jeder Chunk wird
    in einem separaten Thread verarbeitet, während der Hauptthread
    frei bleibt für andere Aufgaben.

    Die asynchrone Verarbeitung ist besonders nützlich bei großen
    Transkriptionen oder wenn viele Dateien gleichzeitig verarbeitet
    werden sollen. Die Fortschrittsberichterstattung erfolgt in
    Echtzeit, sobald einzelne Chunks abgeschlossen sind.

    Das System ist darauf ausgelegt, auch bei Fehlern robust zu
    funktionieren und die Verarbeitung fortzusetzen, selbst wenn
    einzelne Chunks fehlschlagen sollten.
    """

    print("Processing long text asynchronously...")

    try:
        chunks = processor.chunk_text(long_text)
        print(f"Processing {len(chunks)} chunks asynchronously...")

        start_time = time.time()
        corrected_text = await processor.process_chunks_async(
            chunks,
            mock_llm_correction,
            progress_reporter
        )
        processing_time = time.time() - start_time

        print(f"\nAsync processing completed in {processing_time:.2f}s")
        print(f"Corrected text length: {len(corrected_text)} characters")
        print(f"First 200 chars: {corrected_text[:200]}...")

    except Exception as e:
        print(f"Async processing failed: {e}")


def demonstrate_error_handling():
    """Demonstrate error handling and recovery"""
    print("\n" + "=" * 60)
    print("DEMONSTRATION: Error Handling and Recovery")
    print("=" * 60)

    def failing_correction_fn(text: str) -> str:
        """Correction function that fails on certain chunks"""
        if "Fehler" in text:
            raise ValueError("Simulated processing error")
        return f"✓ {text}"

    processor = BatchProcessor(max_context_length=100)

    error_text = """
    Dieser Text sollte normalerweise funktionieren. Das ist kein Problem.
    Aber hier ist ein Fehler drin, der das System zum Absturz bringen könnte.
    Nach dem Fehler sollte die Verarbeitung trotzdem weitergehen.
    """

    try:
        chunks = processor.chunk_text(error_text)
        print(f"Processing {len(chunks)} chunks with simulated errors...")

        corrected_text = processor.process_chunks_sync(
            chunks,
            failing_correction_fn,
            progress_reporter
        )

        print(f"\nResult despite errors:")
        print(f"  {corrected_text}")
        print("\nNote: Failed chunks fall back to original text.")

    except Exception as e:
        print(f"Error handling demo failed: {e}")


def demonstrate_overlap_handling():
    """Demonstrate intelligent overlap handling"""
    print("\n" + "=" * 60)
    print("DEMONSTRATION: Overlap Handling")
    print("=" * 60)

    processor = BatchProcessor(
        max_context_length=50,  # Very small for clear overlap demo
        overlap_sentences=2  # More overlap for demonstration
    )

    overlap_text = """
    Satz eins ist kurz. Satz zwei ist etwas länger als der erste.
    Satz drei enthält noch mehr Informationen für die Demonstration.
    Satz vier zeigt die Überlappungen zwischen den verschiedenen Chunks.
    Satz fünf ist der letzte Satz in diesem Beispiel.
    """

    try:
        chunks = processor.chunk_text(overlap_text)

        print("Chunk details with overlaps:")
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i}:")
            print(f"  Text: {chunk.text}")
            print(f"  Positions: {chunk.start_pos}-{chunk.end_pos}")
            print(f"  Sentences: {chunk.sentence_start}-{chunk.sentence_end}")
            print(f"  Overlaps: start={chunk.overlap_start}, end={chunk.overlap_end}")

        # Process and show how overlaps are handled
        corrected_text = processor.process_chunks_sync(
            chunks,
            lambda t: f"[{t}]",  # Simple wrapper to show chunk boundaries
            None  # No progress callback for cleaner output
        )

        print(f"\nMerged result:")
        print(f"  {corrected_text}")

    except Exception as e:
        print(f"Overlap demo failed: {e}")


async def main():
    """Run all demonstrations"""
    print("BatchProcessor Capability Demonstrations")
    print("This script shows all major features of the BatchProcessor")

    # Run demonstrations
    demonstrate_chunking_strategies()
    demonstrate_sync_processing()
    await demonstrate_async_processing()
    demonstrate_error_handling()
    demonstrate_overlap_handling()

    print("\n" + "=" * 60)
    print("ALL DEMONSTRATIONS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())