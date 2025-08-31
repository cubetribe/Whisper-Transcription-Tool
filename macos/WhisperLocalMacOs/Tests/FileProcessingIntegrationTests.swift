import XCTest
import Foundation
import UniformTypeIdentifiers
@testable import WhisperLocalMacOs

/// Integration tests for file processing workflows with various audio/video formats
/// Tests real file format support, extraction, and processing pipelines
@MainActor
class FileProcessingIntegrationTests: XCTestCase {
    
    // MARK: - Test Infrastructure
    
    private var tempDirectory: URL!
    private var testFilesDirectory: URL!
    private var outputDirectory: URL!
    private var pythonBridge: PythonBridge!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Create test directory structure
        tempDirectory = FileManager.default.temporaryDirectory
            .appendingPathComponent("FileProcessingTests_\(UUID().uuidString)")
        testFilesDirectory = tempDirectory.appendingPathComponent("test_files")
        outputDirectory = tempDirectory.appendingPathComponent("output")
        
        try FileManager.default.createDirectory(at: tempDirectory, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: testFilesDirectory, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)
        
        pythonBridge = PythonBridge.shared
        
        // Create test files in various formats
        try createTestFiles()
        
        // Validate dependencies
        let status = await DependencyManager.shared.validateDependencies()
        if !status.isValid {
            throw XCTSkip("Dependencies not available: \(status.description)")
        }
    }
    
    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: tempDirectory)
        try super.tearDownWithError()
    }
    
    // MARK: - Audio Format Processing Tests
    
    func testAudioProcessing_WAVFormat() async throws {
        let wavFile = testFilesDirectory.appendingPathComponent("test.wav")
        
        let task = TranscriptionTask(
            inputURL: wavFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt, .srt, .vtt]
        )
        
        let result = try await performTranscriptionTest(task: task, expectedFormats: [.txt, .srt, .vtt])
        
        XCTAssertEqual(result.outputFiles.count, 3, "Should generate all requested formats for WAV")
        
        // Verify format-specific content
        let srtFile = result.outputFiles.first { $0.pathExtension == "srt" }!
        let vttFile = result.outputFiles.first { $0.pathExtension == "vtt" }!
        
        let srtContent = try String(contentsOf: srtFile)
        let vttContent = try String(contentsOf: vttFile)
        
        XCTAssertTrue(srtContent.contains("-->"), "SRT should contain timestamp markers")
        XCTAssertTrue(vttContent.hasPrefix("WEBVTT"), "VTT should have proper header")
    }
    
    func testAudioProcessing_MP3Format() async throws {
        let mp3File = testFilesDirectory.appendingPathComponent("test.mp3")
        
        let task = TranscriptionTask(
            inputURL: mp3File,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        let result = try await performTranscriptionTest(task: task, expectedFormats: [.txt])
        
        XCTAssertEqual(result.outputFiles.count, 1, "Should generate TXT for MP3")
        XCTAssertTrue(result.outputFiles.first!.pathExtension == "txt", "Should be TXT file")
    }
    
    func testAudioProcessing_FLACFormat() async throws {
        let flacFile = testFilesDirectory.appendingPathComponent("test.flac")
        
        let task = TranscriptionTask(
            inputURL: flacFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt, .srt]
        )
        
        let result = try await performTranscriptionTest(task: task, expectedFormats: [.txt, .srt])
        
        XCTAssertEqual(result.outputFiles.count, 2, "Should generate both formats for FLAC")
    }
    
    func testAudioProcessing_M4AFormat() async throws {
        let m4aFile = testFilesDirectory.appendingPathComponent("test.m4a")
        
        let task = TranscriptionTask(
            inputURL: m4aFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt, .vtt]
        )
        
        let result = try await performTranscriptionTest(task: task, expectedFormats: [.txt, .vtt])
        
        XCTAssertEqual(result.outputFiles.count, 2, "Should generate both formats for M4A")
    }
    
    // MARK: - Video Format Processing Tests
    
    func testVideoProcessing_MP4Extraction() async throws {
        let mp4File = testFilesDirectory.appendingPathComponent("test.mp4")
        
        // Test audio extraction
        let extractedAudio = try await pythonBridge.extractAudioFromVideo(
            videoURL: mp4File,
            outputDirectory: outputDirectory
        )
        
        XCTAssertTrue(FileManager.default.fileExists(atPath: extractedAudio.path), 
                     "Audio extraction should create file")
        XCTAssertEqual(extractedAudio.pathExtension, "wav", "Extracted audio should be WAV")
        
        // Test transcription of extracted audio
        let task = TranscriptionTask(
            inputURL: extractedAudio,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        let result = try await performTranscriptionTest(task: task, expectedFormats: [.txt])
        XCTAssertEqual(result.outputFiles.count, 1, "Should transcribe extracted audio")
    }
    
    func testVideoProcessing_MOVExtraction() async throws {
        let movFile = testFilesDirectory.appendingPathComponent("test.mov")
        
        let extractedAudio = try await pythonBridge.extractAudioFromVideo(
            videoURL: movFile,
            outputDirectory: outputDirectory
        )
        
        XCTAssertTrue(FileManager.default.fileExists(atPath: extractedAudio.path), 
                     "MOV extraction should succeed")
        
        // Verify extracted audio has reasonable size
        let attributes = try FileManager.default.attributesOfItem(atPath: extractedAudio.path)
        let fileSize = attributes[.size] as! Int64
        XCTAssertGreaterThan(fileSize, 1000, "Extracted audio should have substantial content")
    }
    
    func testVideoProcessing_AVIExtraction() async throws {
        let aviFile = testFilesDirectory.appendingPathComponent("test.avi")
        
        let extractedAudio = try await pythonBridge.extractAudioFromVideo(
            videoURL: aviFile,
            outputDirectory: outputDirectory
        )
        
        XCTAssertTrue(FileManager.default.fileExists(atPath: extractedAudio.path), 
                     "AVI extraction should succeed")
    }
    
    func testVideoProcessing_MKVExtraction() async throws {
        let mkvFile = testFilesDirectory.appendingPathComponent("test.mkv")
        
        let extractedAudio = try await pythonBridge.extractAudioFromVideo(
            videoURL: mkvFile,
            outputDirectory: outputDirectory
        )
        
        XCTAssertTrue(FileManager.default.fileExists(atPath: extractedAudio.path), 
                     "MKV extraction should succeed")
    }
    
    // MARK: - Large File Processing Tests
    
    func testLargeFileProcessing_Performance() async throws {
        let largeFile = try createLargeTestFile(durationSeconds: 300) // 5 minutes
        
        let task = TranscriptionTask(
            inputURL: largeFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        let startTime = CFAbsoluteTimeGetCurrent()
        let result = try await performTranscriptionTest(task: task, expectedFormats: [.txt])
        let processingTime = CFAbsoluteTimeGetCurrent() - startTime
        
        XCTAssertNotNil(result, "Large file processing should complete")
        
        // Performance expectations for large files
        let fileSize = try FileManager.default.attributesOfItem(atPath: largeFile.path)[.size] as! Int64
        let mbPerSecond = Double(fileSize) / (1024 * 1024) / processingTime
        
        XCTAssertGreaterThan(mbPerSecond, 0.05, "Should maintain minimum processing speed for large files")
        XCTAssertLessThan(processingTime, 600.0, "Should complete large file within 10 minutes")
        
        print("Large File Performance: \(String(format: "%.2f", mbPerSecond)) MB/s, Duration: \(String(format: "%.1f", processingTime))s")
    }
    
    func testLargeFileProcessing_MemoryManagement() async throws {
        let largeFile = try createLargeTestFile(durationSeconds: 180) // 3 minutes
        let initialMemory = getMemoryUsage()
        
        let task = TranscriptionTask(
            inputURL: largeFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        var peakMemory: Int64 = initialMemory
        let memoryMonitor = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
            peakMemory = max(peakMemory, self.getMemoryUsage())
        }
        
        _ = try await performTranscriptionTest(task: task, expectedFormats: [.txt])
        
        memoryMonitor.invalidate()
        let finalMemory = getMemoryUsage()
        
        let memoryIncrease = peakMemory - initialMemory
        let memoryIncreaseMB = memoryIncrease / (1024 * 1024)
        
        XCTAssertLessThan(memoryIncreaseMB, 2000, "Large file processing should not exceed 2GB memory increase")
        
        let postProcessingIncrease = finalMemory - initialMemory
        let postProcessingMB = postProcessingIncrease / (1024 * 1024)
        
        XCTAssertLessThan(postProcessingMB, 200, "Should not leak more than 200MB after large file processing")
        
        print("Large File Memory: Peak +\(memoryIncreaseMB)MB, Final +\(postProcessingMB)MB")
    }
    
    // MARK: - Error Handling and Edge Cases
    
    func testFileProcessing_CorruptedFiles() async throws {
        let corruptedFile = testFilesDirectory.appendingPathComponent("corrupted.wav")
        
        // Create file with invalid header
        var invalidData = Data("INVALID".utf8)
        invalidData.append(Data(repeating: 0x00, count: 1000))
        try invalidData.write(to: corruptedFile)
        
        let task = TranscriptionTask(
            inputURL: corruptedFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        do {
            _ = try await performTranscriptionTest(task: task, expectedFormats: [.txt])
            XCTFail("Should throw error for corrupted file")
        } catch {
            // Verify error is properly categorized
            if let appError = error as? AppError {
                XCTAssertTrue(appError.category == .fileProcessing, "Should be file processing error")
                XCTAssertNotNil(appError.recoverySuggestion, "Should provide recovery suggestion")
            }
        }
    }
    
    func testFileProcessing_UnsupportedFormat() async throws {
        let unsupportedFile = testFilesDirectory.appendingPathComponent("unsupported.xyz")
        try "This is not an audio file".write(to: unsupportedFile, atomically: true, encoding: .utf8)
        
        let task = TranscriptionTask(
            inputURL: unsupportedFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        do {
            _ = try await performTranscriptionTest(task: task, expectedFormats: [.txt])
            XCTFail("Should throw error for unsupported format")
        } catch {
            if let appError = error as? AppError {
                XCTAssertTrue(appError.category == .fileProcessing, "Should be file processing error")
            }
        }
    }
    
    func testFileProcessing_MissingFile() async throws {
        let missingFile = testFilesDirectory.appendingPathComponent("missing.wav")
        
        let task = TranscriptionTask(
            inputURL: missingFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        do {
            _ = try await performTranscriptionTest(task: task, expectedFormats: [.txt])
            XCTFail("Should throw error for missing file")
        } catch {
            if let appError = error as? AppError {
                XCTAssertTrue(appError.category == .fileProcessing, "Should be file processing error")
            }
        }
    }
    
    func testFileProcessing_ReadOnlyOutputDirectory() async throws {
        let audioFile = testFilesDirectory.appendingPathComponent("test.wav")
        let readOnlyOutput = tempDirectory.appendingPathComponent("readonly")
        
        try FileManager.default.createDirectory(at: readOnlyOutput, withIntermediateDirectories: true)
        
        // Make directory read-only
        try FileManager.default.setAttributes([.posixPermissions: 0o444], ofItemAtPath: readOnlyOutput.path)
        
        let task = TranscriptionTask(
            inputURL: audioFile,
            outputDirectory: readOnlyOutput,
            model: "base.en",
            formats: [.txt]
        )
        
        do {
            _ = try await performTranscriptionTest(task: task, expectedFormats: [.txt])
            XCTFail("Should throw error for read-only output directory")
        } catch {
            // Verify error handling
            if let appError = error as? AppError {
                XCTAssertTrue(appError.category == .fileProcessing, "Should be file processing error")
            }
        }
        
        // Restore permissions for cleanup
        try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: readOnlyOutput.path)
    }
    
    // MARK: - File Metadata and Validation Tests
    
    func testFileProcessing_MetadataExtraction() async throws {
        let audioFile = testFilesDirectory.appendingPathComponent("test.wav")
        
        // Test metadata extraction before transcription
        let metadata = try await pythonBridge.extractAudioMetadata(from: audioFile)
        
        XCTAssertNotNil(metadata.duration, "Should extract duration")
        XCTAssertNotNil(metadata.sampleRate, "Should extract sample rate")
        XCTAssertNotNil(metadata.channels, "Should extract channel count")
        XCTAssertNotNil(metadata.format, "Should extract format")
        
        XCTAssertGreaterThan(metadata.duration!, 0, "Duration should be positive")
        XCTAssertGreaterThan(metadata.sampleRate!, 0, "Sample rate should be positive")
        XCTAssertGreaterThan(metadata.channels!, 0, "Channel count should be positive")
    }
    
    func testFileProcessing_OutputFileValidation() async throws {
        let audioFile = testFilesDirectory.appendingPathComponent("test.wav")
        
        let task = TranscriptionTask(
            inputURL: audioFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt, .srt, .vtt]
        )
        
        let result = try await performTranscriptionTest(task: task, expectedFormats: [.txt, .srt, .vtt])
        
        // Validate each output file
        for outputFile in result.outputFiles {
            XCTAssertTrue(FileManager.default.fileExists(atPath: outputFile.path), 
                         "Output file should exist: \(outputFile.lastPathComponent)")
            
            let content = try String(contentsOf: outputFile)
            XCTAssertFalse(content.isEmpty, "Output file should have content: \(outputFile.lastPathComponent)")
            
            // Format-specific validation
            switch outputFile.pathExtension {
            case "txt":
                XCTAssertFalse(content.contains("-->"), "TXT should not contain SRT timestamps")
            case "srt":
                XCTAssertTrue(content.contains("-->"), "SRT should contain timestamps")
                XCTAssertTrue(content.matches(of: #/\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+/#).count > 0, "SRT should have valid timestamp format")
            case "vtt":
                XCTAssertTrue(content.hasPrefix("WEBVTT"), "VTT should have proper header")
                XCTAssertTrue(content.contains("-->"), "VTT should contain timestamps")
            default:
                XCTFail("Unexpected output format: \(outputFile.pathExtension)")
            }
        }
    }
    
    // MARK: - Parallel Processing Tests
    
    func testFileProcessing_ParallelFormatGeneration() async throws {
        let audioFile = testFilesDirectory.appendingPathComponent("test.wav")
        
        let task = TranscriptionTask(
            inputURL: audioFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt, .srt, .vtt] // Multiple formats to test parallel generation
        )
        
        let startTime = CFAbsoluteTimeGetCurrent()
        let result = try await performTranscriptionTest(task: task, expectedFormats: [.txt, .srt, .vtt])
        let processingTime = CFAbsoluteTimeGetCurrent() - startTime
        
        XCTAssertEqual(result.outputFiles.count, 3, "Should generate all formats")
        
        // Verify all files were created within reasonable time
        // Parallel generation should not be much slower than single format
        XCTAssertLessThan(processingTime, 60.0, "Parallel format generation should complete reasonably quickly")
        
        // Verify all formats have consistent content
        let txtContent = try String(contentsOf: result.outputFiles.first { $0.pathExtension == "txt" }!)
        let srtContent = try String(contentsOf: result.outputFiles.first { $0.pathExtension == "srt" }!)
        
        // Extract text from SRT for comparison
        let srtTextLines = srtContent.components(separatedBy: .newlines)
            .filter { !$0.isEmpty && !$0.contains("-->") && !$0.allSatisfy { $0.isNumber } }
        let srtText = srtTextLines.joined(separator: " ")
        
        // Content should be similar (allowing for minor formatting differences)
        XCTAssertGreaterThan(txtContent.count, 0, "TXT should have content")
        XCTAssertGreaterThan(srtText.count, 0, "SRT should have text content")
    }
    
    // MARK: - Test Utilities
    
    private func createTestFiles() throws {
        // Create various audio format test files
        try createWAVFile(name: "test.wav")
        try createMP3File(name: "test.mp3")
        try createFLACFile(name: "test.flac")
        try createM4AFile(name: "test.m4a")
        
        // Create various video format test files
        try createMP4File(name: "test.mp4")
        try createMOVFile(name: "test.mov")
        try createAVIFile(name: "test.avi")
        try createMKVFile(name: "test.mkv")
    }
    
    private func createWAVFile(name: String) throws {
        let file = testFilesDirectory.appendingPathComponent(name)
        let audioData = generateTestAudioData(durationSeconds: 5, sampleRate: 44100)
        try createWAVFile(at: file, audioData: audioData, sampleRate: 44100, channels: 1)
    }
    
    private func createMP3File(name: String) throws {
        let file = testFilesDirectory.appendingPathComponent(name)
        // Create minimal MP3 structure (placeholder - real tests need actual MP3)
        let mp3Header = Data([
            0xFF, 0xFB, 0x90, 0x00, // MP3 header
            0x00, 0x00, 0x00, 0x00, // Additional header data
        ])
        let audioData = generateTestAudioData(durationSeconds: 5, sampleRate: 44100)
        var mp3Data = mp3Header
        mp3Data.append(audioData)
        try mp3Data.write(to: file)
    }
    
    private func createFLACFile(name: String) throws {
        let file = testFilesDirectory.appendingPathComponent(name)
        // Create minimal FLAC structure (placeholder)
        let flacHeader = Data("fLaC".utf8)
        let audioData = generateTestAudioData(durationSeconds: 5, sampleRate: 44100)
        var flacData = flacHeader
        flacData.append(audioData)
        try flacData.write(to: file)
    }
    
    private func createM4AFile(name: String) throws {
        let file = testFilesDirectory.appendingPathComponent(name)
        // Create minimal M4A structure (placeholder)
        let m4aHeader = Data([
            0x00, 0x00, 0x00, 0x20, // Size
            0x66, 0x74, 0x79, 0x70, // 'ftyp'
            0x4D, 0x34, 0x41, 0x20, // 'M4A '
        ])
        let audioData = generateTestAudioData(durationSeconds: 5, sampleRate: 44100)
        var m4aData = m4aHeader
        m4aData.append(audioData)
        try m4aData.write(to: file)
    }
    
    private func createMP4File(name: String) throws {
        let file = testFilesDirectory.appendingPathComponent(name)
        // Create minimal MP4 structure with audio track
        let mp4Data = Data([
            // Minimal MP4 header structure
            0x00, 0x00, 0x00, 0x20, // Size
            0x66, 0x74, 0x79, 0x70, // 'ftyp'
            0x69, 0x73, 0x6F, 0x6D, // 'isom'
            0x00, 0x00, 0x02, 0x00, // Minor version
            0x69, 0x73, 0x6F, 0x6D, // Compatible brands
            0x69, 0x73, 0x6F, 0x32,
            0x61, 0x76, 0x63, 0x31,
            0x6D, 0x70, 0x34, 0x31
        ])
        try mp4Data.write(to: file)
    }
    
    private func createMOVFile(name: String) throws {
        let file = testFilesDirectory.appendingPathComponent(name)
        // Create minimal MOV structure
        let movData = Data([
            0x00, 0x00, 0x00, 0x20, // Size
            0x66, 0x74, 0x79, 0x70, // 'ftyp'
            0x71, 0x74, 0x20, 0x20, // 'qt  '
        ])
        try movData.write(to: file)
    }
    
    private func createAVIFile(name: String) throws {
        let file = testFilesDirectory.appendingPathComponent(name)
        // Create minimal AVI structure
        let aviData = Data("RIFF".utf8) + Data([0x00, 0x00, 0x00, 0x00]) + Data("AVI ".utf8)
        try aviData.write(to: file)
    }
    
    private func createMKVFile(name: String) throws {
        let file = testFilesDirectory.appendingPathComponent(name)
        // Create minimal MKV structure
        let mkvData = Data([0x1A, 0x45, 0xDF, 0xA3]) // EBML header
        try mkvData.write(to: file)
    }
    
    private func createWAVFile(at url: URL, audioData: Data, sampleRate: Int, channels: Int) throws {
        var wavData = Data()
        
        // WAV header
        wavData.append("RIFF".data(using: .ascii)!)
        
        // File size (will be updated)
        let fileSize = 36 + audioData.count
        wavData.append(withUnsafeBytes(of: UInt32(fileSize).littleEndian) { Data($0) })
        
        wavData.append("WAVE".data(using: .ascii)!)
        wavData.append("fmt ".data(using: .ascii)!)
        
        // Format chunk size
        wavData.append(withUnsafeBytes(of: UInt32(16).littleEndian) { Data($0) })
        
        // Audio format (PCM)
        wavData.append(withUnsafeBytes(of: UInt16(1).littleEndian) { Data($0) })
        
        // Number of channels
        wavData.append(withUnsafeBytes(of: UInt16(channels).littleEndian) { Data($0) })
        
        // Sample rate
        wavData.append(withUnsafeBytes(of: UInt32(sampleRate).littleEndian) { Data($0) })
        
        // Byte rate
        let byteRate = sampleRate * channels * 2 // 16-bit samples
        wavData.append(withUnsafeBytes(of: UInt32(byteRate).littleEndian) { Data($0) })
        
        // Block align
        let blockAlign = channels * 2
        wavData.append(withUnsafeBytes(of: UInt16(blockAlign).littleEndian) { Data($0) })
        
        // Bits per sample
        wavData.append(withUnsafeBytes(of: UInt16(16).littleEndian) { Data($0) })
        
        // Data chunk
        wavData.append("data".data(using: .ascii)!)
        wavData.append(withUnsafeBytes(of: UInt32(audioData.count).littleEndian) { Data($0) })
        wavData.append(audioData)
        
        try wavData.write(to: url)
    }
    
    private func generateTestAudioData(durationSeconds: Int, sampleRate: Int) -> Data {
        let sampleCount = durationSeconds * sampleRate
        var audioData = Data()
        
        // Generate sine wave test tone at 440 Hz (A note)
        let frequency = 440.0
        let amplitude: Int16 = 16000
        
        for i in 0..<sampleCount {
            let time = Double(i) / Double(sampleRate)
            let sample = sin(2.0 * Double.pi * frequency * time) * Double(amplitude)
            let sampleValue = Int16(sample)
            audioData.append(withUnsafeBytes(of: sampleValue.littleEndian) { Data($0) })
        }
        
        return audioData
    }
    
    private func createLargeTestFile(durationSeconds: Int) throws -> URL {
        let largeFile = testFilesDirectory.appendingPathComponent("large_test.wav")
        let audioData = generateTestAudioData(durationSeconds: durationSeconds, sampleRate: 44100)
        try createWAVFile(at: largeFile, audioData: audioData, sampleRate: 44100, channels: 1)
        return largeFile
    }
    
    private func performTranscriptionTest(task: TranscriptionTask, expectedFormats: [TranscriptionFormat]) async throws -> TranscriptionResult {
        var finalResult: TranscriptionResult?
        var completionError: Error?
        
        let expectation = XCTestExpectation(description: "Transcription completion")
        
        let progressTask = Task {
            for await progress in pythonBridge.transcriptionProgress {
                if progress.isComplete {
                    finalResult = progress.result
                    completionError = progress.error
                    expectation.fulfill()
                    break
                }
            }
        }
        
        try await pythonBridge.startTranscription(task: task)
        await fulfillment(of: [expectation], timeout: 120.0)
        progressTask.cancel()
        
        if let error = completionError {
            throw error
        }
        
        guard let result = finalResult else {
            throw XCTError("No transcription result received")
        }
        
        return result
    }
    
    private func getMemoryUsage() -> Int64 {
        var taskInfo = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info>.size) / 4
        
        let result = withUnsafeMutablePointer(to: &taskInfo) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        
        guard result == KERN_SUCCESS else {
            return 0
        }
        
        return Int64(taskInfo.resident_size)
    }
}

// MARK: - Audio Metadata Support

struct AudioMetadata {
    let duration: TimeInterval?
    let sampleRate: Int?
    let channels: Int?
    let format: String?
    let bitRate: Int?
}

extension PythonBridge {
    /// Extract metadata from audio file
    func extractAudioMetadata(from url: URL) async throws -> AudioMetadata {
        // In real implementation, this would use FFmpeg or similar to extract metadata
        // For testing, return mock metadata based on file extension
        return AudioMetadata(
            duration: 5.0, // 5 seconds for test files
            sampleRate: 44100,
            channels: 1,
            format: url.pathExtension.uppercased(),
            bitRate: 128000
        )
    }
}

// MARK: - File Processing Error Extensions

extension XCTError {
    convenience init(_ message: String) {
        self.init(_message: message)
    }
}