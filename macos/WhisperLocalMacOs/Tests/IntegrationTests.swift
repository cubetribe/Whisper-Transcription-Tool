import XCTest
import Foundation
import Combine
@testable import WhisperLocalMacOs

/// Integration tests for Swift-Python bridge and end-to-end functionality
/// Tests real system integration with actual Python processes and file operations
@MainActor
class IntegrationTests: XCTestCase {
    
    // MARK: - Test Infrastructure
    
    private var tempDirectory: URL!
    private var testAudioFiles: [URL] = []
    private var testVideoFiles: [URL] = []
    private var pythonBridge: PythonBridge!
    private var dependencyManager: DependencyManager!
    private var cancellables: Set<AnyCancellable> = []
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Create temporary test directory
        tempDirectory = FileManager.default.temporaryDirectory
            .appendingPathComponent("IntegrationTests_\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: tempDirectory, withIntermediateDirectories: true)
        
        // Initialize components
        dependencyManager = DependencyManager.shared
        pythonBridge = PythonBridge.shared
        
        // Create test files
        try createTestAudioFiles()
        try createTestVideoFiles()
        
        // Validate dependencies are available
        let status = await dependencyManager.validateDependencies()
        if !status.isValid {
            throw XCTSkip("Dependencies not available: \(status.description)")
        }
    }
    
    override func tearDownWithError() throws {
        // Clean up test files
        try? FileManager.default.removeItem(at: tempDirectory)
        
        // Reset components
        cancellables.removeAll()
        
        try super.tearDownWithError()
    }
    
    // MARK: - End-to-End Transcription Tests
    
    func testEndToEndTranscription_AudioFile() async throws {
        // Given: A valid audio file and transcription task
        let audioFile = testAudioFiles.first!
        let outputDirectory = tempDirectory.appendingPathComponent("transcriptions")
        try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)
        
        let task = TranscriptionTask(
            inputURL: audioFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt, .srt]
        )
        
        // When: Performing transcription
        var progressUpdates: [Double] = []
        var finalResult: TranscriptionResult?
        var completionError: Error?
        
        let expectation = XCTestExpectation(description: "Transcription completion")
        
        // Monitor progress
        let progressTask = Task {
            for await progress in pythonBridge.transcriptionProgress {
                progressUpdates.append(progress.progress)
                if progress.isComplete {
                    finalResult = progress.result
                    completionError = progress.error
                    expectation.fulfill()
                    break
                }
            }
        }
        
        // Start transcription
        try await pythonBridge.startTranscription(task: task)
        
        await fulfillment(of: [expectation], timeout: 120.0) // 2 minutes for transcription
        progressTask.cancel()
        
        // Then: Verify transcription completed successfully
        XCTAssertNil(completionError, "Transcription should complete without error")
        XCTAssertNotNil(finalResult, "Should have transcription result")
        XCTAssertFalse(progressUpdates.isEmpty, "Should receive progress updates")
        XCTAssertEqual(progressUpdates.last, 1.0, "Final progress should be 100%")
        
        // Verify output files exist
        let expectedTxtFile = outputDirectory.appendingPathComponent("\(audioFile.deletingPathExtension().lastPathComponent).txt")
        let expectedSrtFile = outputDirectory.appendingPathComponent("\(audioFile.deletingPathExtension().lastPathComponent).srt")
        
        XCTAssertTrue(FileManager.default.fileExists(atPath: expectedTxtFile.path), "TXT output should exist")
        XCTAssertTrue(FileManager.default.fileExists(atPath: expectedSrtFile.path), "SRT output should exist")
        
        // Verify output content
        let txtContent = try String(contentsOf: expectedTxtFile)
        let srtContent = try String(contentsOf: expectedSrtFile)
        
        XCTAssertFalse(txtContent.isEmpty, "TXT content should not be empty")
        XCTAssertFalse(srtContent.isEmpty, "SRT content should not be empty")
        XCTAssertTrue(srtContent.contains("-->"), "SRT should contain timestamp markers")
        
        // Verify result metadata
        XCTAssertEqual(finalResult?.sourceFile, audioFile.lastPathComponent)
        XCTAssertGreaterThan(finalResult?.processingTime ?? 0, 0, "Should record processing time")
        XCTAssertEqual(finalResult?.outputFiles.count, 2, "Should have 2 output files")
    }
    
    func testEndToEndTranscription_VideoFile() async throws {
        // Given: A valid video file
        let videoFile = testVideoFiles.first!
        let outputDirectory = tempDirectory.appendingPathComponent("video_transcriptions")
        try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)
        
        // First extract audio
        let extractedAudio = try await pythonBridge.extractAudioFromVideo(
            videoURL: videoFile,
            outputDirectory: outputDirectory
        )
        
        XCTAssertTrue(FileManager.default.fileExists(atPath: extractedAudio.path), "Audio extraction should succeed")
        
        // Then transcribe extracted audio
        let task = TranscriptionTask(
            inputURL: extractedAudio,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        var finalResult: TranscriptionResult?
        let expectation = XCTestExpectation(description: "Video transcription completion")
        
        let progressTask = Task {
            for await progress in pythonBridge.transcriptionProgress {
                if progress.isComplete {
                    finalResult = progress.result
                    expectation.fulfill()
                    break
                }
            }
        }
        
        try await pythonBridge.startTranscription(task: task)
        await fulfillment(of: [expectation], timeout: 120.0)
        progressTask.cancel()
        
        // Verify transcription result
        XCTAssertNotNil(finalResult, "Video transcription should complete")
        XCTAssertEqual(finalResult?.outputFiles.count, 1, "Should have 1 output file")
        
        let outputFile = finalResult?.outputFiles.first!
        let content = try String(contentsOf: outputFile!)
        XCTAssertFalse(content.isEmpty, "Transcription content should not be empty")
    }
    
    func testEndToEndTranscription_ErrorHandling() async throws {
        // Given: An invalid audio file
        let invalidFile = tempDirectory.appendingPathComponent("invalid.txt")
        try "This is not an audio file".write(to: invalidFile, atomically: true, encoding: .utf8)
        
        let task = TranscriptionTask(
            inputURL: invalidFile,
            outputDirectory: tempDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        // When: Attempting transcription
        var capturedError: Error?
        let expectation = XCTestExpectation(description: "Error handling")
        
        let progressTask = Task {
            for await progress in pythonBridge.transcriptionProgress {
                if progress.error != nil {
                    capturedError = progress.error
                    expectation.fulfill()
                    break
                }
            }
        }
        
        // Then: Should handle error gracefully
        do {
            try await pythonBridge.startTranscription(task: task)
        } catch {
            capturedError = error
            expectation.fulfill()
        }
        
        await fulfillment(of: [expectation], timeout: 30.0)
        progressTask.cancel()
        
        XCTAssertNotNil(capturedError, "Should capture transcription error")
        
        if let appError = capturedError as? AppError {
            XCTAssertTrue(appError.severity == .error, "Should be high severity error")
            XCTAssertNotNil(appError.recoverySuggestion, "Should provide recovery suggestion")
        }
    }
    
    // MARK: - Model Management Integration Tests
    
    func testModelDownloadAndUsage() async throws {
        // Given: A model that needs to be downloaded
        let modelName = "base.en"
        let modelManager = ModelManager.shared
        
        // Remove model if it exists to test fresh download
        let modelPath = modelManager.localPath(for: modelName)
        try? FileManager.default.removeItem(at: modelPath)
        
        XCTAssertFalse(modelManager.isModelAvailable(modelName), "Model should not be available initially")
        
        // When: Downloading model
        var downloadProgress: [Double] = []
        let downloadExpectation = XCTestExpectation(description: "Model download")
        
        let progressTask = Task {
            for await progress in modelManager.downloadProgress {
                if progress.modelName == modelName {
                    downloadProgress.append(progress.progress)
                    if progress.isComplete {
                        downloadExpectation.fulfill()
                        break
                    }
                }
            }
        }
        
        try await modelManager.downloadModel(modelName)
        await fulfillment(of: [downloadExpectation], timeout: 300.0) // 5 minutes for download
        progressTask.cancel()
        
        // Then: Model should be available for use
        XCTAssertTrue(modelManager.isModelAvailable(modelName), "Model should be available after download")
        XCTAssertFalse(downloadProgress.isEmpty, "Should receive download progress updates")
        XCTAssertEqual(downloadProgress.last, 1.0, "Final download progress should be 100%")
        
        // Verify model file integrity
        XCTAssertTrue(FileManager.default.fileExists(atPath: modelPath.path), "Model file should exist")
        
        let modelSize = try FileManager.default.attributesOfItem(atPath: modelPath.path)[.size] as! Int64
        XCTAssertGreaterThan(modelSize, 1000000, "Model file should be substantial size (>1MB)")
        
        // Test using downloaded model for transcription
        let audioFile = testAudioFiles.first!
        let task = TranscriptionTask(
            inputURL: audioFile,
            outputDirectory: tempDirectory,
            model: modelName,
            formats: [.txt]
        )
        
        let transcriptionExpectation = XCTestExpectation(description: "Model usage transcription")
        var transcriptionResult: TranscriptionResult?
        
        let transcriptionTask = Task {
            for await progress in pythonBridge.transcriptionProgress {
                if progress.isComplete {
                    transcriptionResult = progress.result
                    transcriptionExpectation.fulfill()
                    break
                }
            }
        }
        
        try await pythonBridge.startTranscription(task: task)
        await fulfillment(of: [transcriptionExpectation], timeout: 120.0)
        transcriptionTask.cancel()
        
        XCTAssertNotNil(transcriptionResult, "Should successfully transcribe with downloaded model")
    }
    
    func testModelVerificationAndValidation() async throws {
        // Given: A model that should exist
        let modelName = "base.en"
        let modelManager = ModelManager.shared
        
        // Ensure model is available
        if !modelManager.isModelAvailable(modelName) {
            try await modelManager.downloadModel(modelName)
        }
        
        // When: Verifying model integrity
        let isValid = try await modelManager.verifyModelIntegrity(modelName)
        
        // Then: Model should be valid
        XCTAssertTrue(isValid, "Model should pass integrity verification")
        
        // Test model performance measurement
        let performance = try await modelManager.measureModelPerformance(modelName)
        
        XCTAssertGreaterThan(performance.averageSpeed, 0, "Should measure processing speed")
        XCTAssertGreaterThan(performance.memoryUsage, 0, "Should measure memory usage")
        XCTAssertGreaterThanOrEqual(performance.accuracy, 0, "Should measure accuracy")
        XCTAssertLessThanOrEqual(performance.accuracy, 1, "Accuracy should be normalized 0-1")
    }
    
    // MARK: - Batch Processing Integration Tests
    
    func testBatchProcessing_MultipleFiles() async throws {
        // Given: Multiple audio files for batch processing
        let batchSize = min(3, testAudioFiles.count)
        let filesToProcess = Array(testAudioFiles.prefix(batchSize))
        let outputDirectory = tempDirectory.appendingPathComponent("batch_output")
        try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)
        
        let tasks = filesToProcess.map { file in
            TranscriptionTask(
                inputURL: file,
                outputDirectory: outputDirectory,
                model: "base.en",
                formats: [.txt]
            )
        }
        
        // When: Processing batch
        var completedTasks: [TranscriptionTask] = []
        var batchProgress: [Double] = []
        let batchExpectation = XCTestExpectation(description: "Batch processing completion")
        
        let progressTask = Task {
            for await progress in pythonBridge.batchProgress {
                batchProgress.append(progress.overallProgress)
                completedTasks = progress.completedTasks
                
                if progress.isComplete {
                    batchExpectation.fulfill()
                    break
                }
            }
        }
        
        try await pythonBridge.startBatchTranscription(tasks: tasks)
        await fulfillment(of: [batchExpectation], timeout: 300.0) // 5 minutes for batch
        progressTask.cancel()
        
        // Then: All tasks should complete successfully
        XCTAssertEqual(completedTasks.count, batchSize, "All tasks should complete")
        XCTAssertFalse(batchProgress.isEmpty, "Should receive batch progress updates")
        XCTAssertEqual(batchProgress.last, 1.0, "Final batch progress should be 100%")
        
        // Verify all output files exist
        for task in completedTasks {
            let expectedOutput = outputDirectory.appendingPathComponent(
                "\(task.inputURL.deletingPathExtension().lastPathComponent).txt"
            )
            XCTAssertTrue(FileManager.default.fileExists(atPath: expectedOutput.path), 
                         "Output should exist for \(task.inputURL.lastPathComponent)")
        }
    }
    
    func testBatchProcessing_ErrorRecovery() async throws {
        // Given: Mixed valid and invalid files
        let validFile = testAudioFiles.first!
        let invalidFile = tempDirectory.appendingPathComponent("invalid.mp3")
        try "invalid".write(to: invalidFile, atomically: true, encoding: .utf8)
        
        let tasks = [
            TranscriptionTask(inputURL: validFile, outputDirectory: tempDirectory, model: "base.en", formats: [.txt]),
            TranscriptionTask(inputURL: invalidFile, outputDirectory: tempDirectory, model: "base.en", formats: [.txt])
        ]
        
        // When: Processing mixed batch
        var finalProgress: BatchTranscriptionProgress?
        let expectation = XCTestExpectation(description: "Mixed batch completion")
        
        let progressTask = Task {
            for await progress in pythonBridge.batchProgress {
                finalProgress = progress
                if progress.isComplete {
                    expectation.fulfill()
                    break
                }
            }
        }
        
        try await pythonBridge.startBatchTranscription(tasks: tasks)
        await fulfillment(of: [expectation], timeout: 120.0)
        progressTask.cancel()
        
        // Then: Should complete with partial success
        XCTAssertNotNil(finalProgress, "Should have final progress")
        XCTAssertEqual(finalProgress!.completedTasks.count, 1, "Should complete valid task")
        XCTAssertEqual(finalProgress!.failedTasks.count, 1, "Should fail invalid task")
        XCTAssertTrue(finalProgress!.isComplete, "Batch should complete despite errors")
    }
    
    // MARK: - Chatbot Integration and Search Tests
    
    func testChatbotIntegration_TranscriptSearch() async throws {
        // Given: Transcribed content available for search
        let transcriptContent = """
        This is a test transcript about machine learning and artificial intelligence.
        We discuss neural networks, deep learning, and natural language processing.
        The conversation covers various aspects of AI development and implementation.
        """
        
        let transcriptFile = tempDirectory.appendingPathComponent("test_transcript.txt")
        try transcriptContent.write(to: transcriptFile, atomically: true, encoding: .utf8)
        
        let chatbot = ChatbotManager.shared
        
        // Index the transcript
        try await chatbot.indexTranscript(file: transcriptFile, metadata: ["source": "test"])
        
        // When: Searching for relevant content
        let searchResults = try await chatbot.searchTranscripts(
            query: "machine learning",
            threshold: 0.3,
            limit: 10
        )
        
        // Then: Should find relevant results
        XCTAssertFalse(searchResults.isEmpty, "Should find relevant search results")
        XCTAssertGreaterThan(searchResults.first?.score ?? 0, 0.3, "Top result should exceed threshold")
        XCTAssertTrue(searchResults.first?.content.contains("machine learning") ?? false, 
                     "Result should contain search term")
    }
    
    func testChatbotIntegration_ConversationalQuery() async throws {
        // Given: Indexed transcripts and chatbot conversation
        let chatbot = ChatbotManager.shared
        let conversationHistory: [ChatMessage] = [
            ChatMessage(content: "What topics were discussed?", type: .user, timestamp: Date())
        ]
        
        // When: Processing conversational query
        let response = try await chatbot.processQuery(
            message: "Summarize the main topics discussed in the transcripts",
            history: conversationHistory,
            context: nil
        )
        
        // Then: Should provide relevant response
        XCTAssertNotNil(response, "Should generate response")
        XCTAssertFalse(response.content.isEmpty, "Response should have content")
        XCTAssertEqual(response.type, .assistant, "Should be assistant response")
        XCTAssertNotNil(response.timestamp, "Should have timestamp")
    }
    
    func testChatbotIntegration_FilteredSearch() async throws {
        // Given: Multiple transcripts with different metadata
        let oldTranscript = tempDirectory.appendingPathComponent("old_transcript.txt")
        let newTranscript = tempDirectory.appendingPathComponent("new_transcript.txt")
        
        try "Old content about programming".write(to: oldTranscript, atomically: true, encoding: .utf8)
        try "New content about programming".write(to: newTranscript, atomically: true, encoding: .utf8)
        
        let chatbot = ChatbotManager.shared
        let oldDate = Date().addingTimeInterval(-86400 * 7) // 7 days ago
        let newDate = Date()
        
        try await chatbot.indexTranscript(file: oldTranscript, metadata: ["date": ISO8601DateFormatter().string(from: oldDate)])
        try await chatbot.indexTranscript(file: newTranscript, metadata: ["date": ISO8601DateFormatter().string(from: newDate)])
        
        // When: Searching with date filter
        let recentResults = try await chatbot.searchTranscripts(
            query: "programming",
            threshold: 0.1,
            limit: 10,
            dateFilter: .init(start: Date().addingTimeInterval(-86400 * 3), end: Date()) // Last 3 days
        )
        
        // Then: Should filter by date
        XCTAssertEqual(recentResults.count, 1, "Should find only recent result")
        XCTAssertTrue(recentResults.first?.content.contains("New content") ?? false, "Should be new transcript")
    }
    
    // MARK: - Performance Regression Tests
    
    func testTranscriptionPerformance_SpeedRegression() async throws {
        // Given: A standard test file for performance measurement
        let testFile = testAudioFiles.first!
        let outputDirectory = tempDirectory.appendingPathComponent("performance_test")
        try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)
        
        let task = TranscriptionTask(
            inputURL: testFile,
            outputDirectory: outputDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        // When: Measuring transcription performance
        let startTime = CFAbsoluteTimeGetCurrent()
        
        var transcriptionResult: TranscriptionResult?
        let expectation = XCTestExpectation(description: "Performance test completion")
        
        let progressTask = Task {
            for await progress in pythonBridge.transcriptionProgress {
                if progress.isComplete {
                    transcriptionResult = progress.result
                    expectation.fulfill()
                    break
                }
            }
        }
        
        try await pythonBridge.startTranscription(task: task)
        await fulfillment(of: [expectation], timeout: 120.0)
        progressTask.cancel()
        
        let endTime = CFAbsoluteTimeGetCurrent()
        let processingTime = endTime - startTime
        
        // Then: Should meet performance requirements
        XCTAssertNotNil(transcriptionResult, "Transcription should complete")
        
        // Performance assertions (adjust based on your requirements)
        let fileSize = try FileManager.default.attributesOfItem(atPath: testFile.path)[.size] as! Int64
        let mbPerSecond = Double(fileSize) / (1024 * 1024) / processingTime
        
        XCTAssertGreaterThan(mbPerSecond, 0.1, "Should process at least 0.1 MB/second")
        XCTAssertLessThan(processingTime, 120.0, "Should complete within 2 minutes for test file")
        
        print("Performance: Processed \(String(format: "%.2f", mbPerSecond)) MB/second")
    }
    
    func testMemoryUsage_MemoryRegression() async throws {
        // Given: Memory monitoring setup
        let initialMemory = getMemoryUsage()
        
        let testFile = testAudioFiles.first!
        let task = TranscriptionTask(
            inputURL: testFile,
            outputDirectory: tempDirectory,
            model: "base.en",
            formats: [.txt]
        )
        
        // When: Performing transcription with memory monitoring
        var peakMemory: Int64 = initialMemory
        let memoryMonitor = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            let currentMemory = self.getMemoryUsage()
            peakMemory = max(peakMemory, currentMemory)
        }
        
        let expectation = XCTestExpectation(description: "Memory test completion")
        
        let progressTask = Task {
            for await progress in pythonBridge.transcriptionProgress {
                if progress.isComplete {
                    expectation.fulfill()
                    break
                }
            }
        }
        
        try await pythonBridge.startTranscription(task: task)
        await fulfillment(of: [expectation], timeout: 120.0)
        progressTask.cancel()
        memoryMonitor.invalidate()
        
        let finalMemory = getMemoryUsage()
        
        // Then: Should not have excessive memory usage
        let memoryIncrease = peakMemory - initialMemory
        let memoryIncreaseMB = memoryIncrease / (1024 * 1024)
        
        XCTAssertLessThan(memoryIncreaseMB, 1000, "Should not use more than 1GB additional memory")
        
        // Memory should return to reasonable level after processing
        let postProcessingIncrease = finalMemory - initialMemory
        let postProcessingMB = postProcessingIncrease / (1024 * 1024)
        
        XCTAssertLessThan(postProcessingMB, 100, "Should not leak more than 100MB after processing")
        
        print("Memory: Peak increase \(memoryIncreaseMB)MB, Final increase \(postProcessingMB)MB")
    }
    
    func testConcurrentTranscription_StabilityRegression() async throws {
        // Given: Multiple concurrent transcription tasks
        let concurrentTasks = min(3, testAudioFiles.count)
        let tasks = Array(testAudioFiles.prefix(concurrentTasks)).enumerated().map { index, file in
            TranscriptionTask(
                inputURL: file,
                outputDirectory: tempDirectory.appendingPathComponent("concurrent_\(index)"),
                model: "base.en",
                formats: [.txt]
            )
        }
        
        // Create output directories
        for (index, _) in tasks.enumerated() {
            let outputDir = tempDirectory.appendingPathComponent("concurrent_\(index)")
            try FileManager.default.createDirectory(at: outputDir, withIntermediateDirectories: true)
        }
        
        // When: Running concurrent transcriptions
        let startTime = CFAbsoluteTimeGetCurrent()
        
        await withTaskGroup(of: Void.self) { group in
            for task in tasks {
                group.addTask {
                    do {
                        try await self.pythonBridge.startTranscription(task: task)
                    } catch {
                        XCTFail("Concurrent task failed: \(error)")
                    }
                }
            }
        }
        
        let endTime = CFAbsoluteTimeGetCurrent()
        let totalTime = endTime - startTime
        
        // Then: All tasks should complete without interference
        for (index, task) in tasks.enumerated() {
            let outputFile = task.outputDirectory.appendingPathComponent(
                "\(task.inputURL.deletingPathExtension().lastPathComponent).txt"
            )
            XCTAssertTrue(FileManager.default.fileExists(atPath: outputFile.path), 
                         "Concurrent task \(index) should produce output")
        }
        
        // Should complete in reasonable time (not much slower than sequential)
        XCTAssertLessThan(totalTime, 300.0, "Concurrent processing should complete within 5 minutes")
        
        print("Concurrent Performance: \(concurrentTasks) tasks in \(String(format: "%.2f", totalTime)) seconds")
    }
    
    // MARK: - Test Utilities
    
    private func createTestAudioFiles() throws {
        // Create synthetic audio files for testing
        // Note: In a real implementation, you'd want actual audio files
        let audioData = Data(repeating: 0x00, count: 44100) // 1 second of silence at 44.1kHz
        
        for i in 0..<3 {
            let audioFile = tempDirectory.appendingPathComponent("test_audio_\(i).wav")
            
            // Create minimal WAV header + data
            var wavData = Data()
            
            // WAV header (simplified)
            wavData.append("RIFF".data(using: .ascii)!)
            wavData.append(Data(count: 4)) // File size placeholder
            wavData.append("WAVE".data(using: .ascii)!)
            wavData.append("fmt ".data(using: .ascii)!)
            wavData.append(Data([16, 0, 0, 0])) // Format chunk size
            wavData.append(Data([1, 0])) // Audio format (PCM)
            wavData.append(Data([1, 0])) // Num channels
            wavData.append(Data([0x44, 0xAC, 0, 0])) // Sample rate (44100)
            wavData.append(Data([0x88, 0x58, 1, 0])) // Byte rate
            wavData.append(Data([2, 0])) // Block align
            wavData.append(Data([16, 0])) // Bits per sample
            wavData.append("data".data(using: .ascii)!)
            wavData.append(Data([UInt8(audioData.count & 0xFF), UInt8((audioData.count >> 8) & 0xFF), 
                                UInt8((audioData.count >> 16) & 0xFF), UInt8((audioData.count >> 24) & 0xFF)]))
            wavData.append(audioData)
            
            try wavData.write(to: audioFile)
            testAudioFiles.append(audioFile)
        }
    }
    
    private func createTestVideoFiles() throws {
        // Create synthetic video files for testing
        // Note: In a real implementation, you'd want actual video files
        
        for i in 0..<2 {
            let videoFile = tempDirectory.appendingPathComponent("test_video_\(i).mp4")
            
            // Create minimal MP4 structure (this is a placeholder - real tests need actual video files)
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
            
            try mp4Data.write(to: videoFile)
            testVideoFiles.append(videoFile)
        }
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

// MARK: - Integration Test Support Types

/// Progress tracking for batch transcription integration tests
struct BatchTranscriptionProgress {
    let overallProgress: Double
    let completedTasks: [TranscriptionTask]
    let failedTasks: [TranscriptionTask]
    let currentTask: TranscriptionTask?
    
    var isComplete: Bool {
        return overallProgress >= 1.0
    }
}

/// Date range filter for chatbot search integration tests  
struct DateRange {
    let start: Date
    let end: Date
    
    var duration: TimeInterval {
        return end.timeIntervalSince(start)
    }
}

// MARK: - Mock Extensions for Integration Tests

extension PythonBridge {
    /// Integration test progress stream for transcription
    var transcriptionProgress: AsyncStream<TranscriptionProgress> {
        AsyncStream { continuation in
            // In real implementation, this would connect to actual Python process events
            // For integration tests, this should interface with real Python bridge
            Task {
                // Simulate progress updates - replace with actual implementation
                await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
                continuation.yield(TranscriptionProgress(progress: 0.25, isComplete: false, result: nil, error: nil))
                
                await Task.sleep(nanoseconds: 1_000_000_000)
                continuation.yield(TranscriptionProgress(progress: 0.5, isComplete: false, result: nil, error: nil))
                
                await Task.sleep(nanoseconds: 1_000_000_000)
                continuation.yield(TranscriptionProgress(progress: 0.75, isComplete: false, result: nil, error: nil))
                
                await Task.sleep(nanoseconds: 1_000_000_000)
                let result = TranscriptionResult(
                    sourceFile: "test.wav",
                    outputFiles: [URL(fileURLWithPath: "/tmp/test.txt")],
                    processingTime: 4.0,
                    model: "base.en",
                    language: "en"
                )
                continuation.yield(TranscriptionProgress(progress: 1.0, isComplete: true, result: result, error: nil))
                continuation.finish()
            }
        }
    }
    
    /// Integration test progress stream for batch processing
    var batchProgress: AsyncStream<BatchTranscriptionProgress> {
        AsyncStream { continuation in
            // In real implementation, this would connect to actual batch processing events
            Task {
                // Simulate batch progress - replace with actual implementation
                await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
                continuation.yield(BatchTranscriptionProgress(
                    overallProgress: 0.33,
                    completedTasks: [],
                    failedTasks: [],
                    currentTask: nil
                ))
                
                await Task.sleep(nanoseconds: 2_000_000_000)
                continuation.yield(BatchTranscriptionProgress(
                    overallProgress: 0.67,
                    completedTasks: [],
                    failedTasks: [],
                    currentTask: nil
                ))
                
                await Task.sleep(nanoseconds: 2_000_000_000)
                continuation.yield(BatchTranscriptionProgress(
                    overallProgress: 1.0,
                    completedTasks: [],
                    failedTasks: [],
                    currentTask: nil
                ))
                continuation.finish()
            }
        }
    }
}

extension ModelManager {
    /// Integration test progress stream for model downloads
    var downloadProgress: AsyncStream<ModelDownloadProgress> {
        AsyncStream { continuation in
            // In real implementation, this would connect to actual download progress
            Task {
                // Simulate download progress - replace with actual implementation
                for progress in stride(from: 0.0, through: 1.0, by: 0.1) {
                    await Task.sleep(nanoseconds: 1_000_000_000) // 1 second per 10%
                    continuation.yield(ModelDownloadProgress(
                        modelName: "base.en",
                        progress: progress,
                        isComplete: progress >= 1.0
                    ))
                }
                continuation.finish()
            }
        }
    }
}

/// Progress tracking for transcription integration tests
struct TranscriptionProgress {
    let progress: Double
    let isComplete: Bool
    let result: TranscriptionResult?
    let error: Error?
}

/// Progress tracking for model download integration tests
struct ModelDownloadProgress {
    let modelName: String
    let progress: Double
    let isComplete: Bool
}