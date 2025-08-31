import XCTest
import Foundation
@testable import WhisperLocalMacOs

class DataModelTests: XCTestCase {
    
    // MARK: - TranscriptionTask Tests
    
    func testTranscriptionTask_Initialization() {
        let inputURL = URL(fileURLWithPath: "/tmp/test.mp3")
        let outputDir = URL(fileURLWithPath: "/tmp/output")
        
        let task = TranscriptionTask(
            inputURL: inputURL,
            outputDirectory: outputDir,
            model: "base",
            formats: [.txt, .srt],
            language: "en"
        )
        
        XCTAssertEqual(task.inputURL, inputURL)
        XCTAssertEqual(task.outputDirectory, outputDir)
        XCTAssertEqual(task.model, "base")
        XCTAssertEqual(task.formats, [.txt, .srt])
        XCTAssertEqual(task.language, "en")
        XCTAssertEqual(task.status, .pending)
        XCTAssertEqual(task.progress, 0.0)
        XCTAssertNil(task.error)
        XCTAssertNil(task.startTime)
        XCTAssertNil(task.completionTime)
        XCTAssertTrue(task.outputFiles.isEmpty)
    }
    
    func testTranscriptionTask_DefaultValues() {
        let inputURL = URL(fileURLWithPath: "/tmp/test.mp3")
        let task = TranscriptionTask(inputURL: inputURL)
        
        XCTAssertEqual(task.outputDirectory, URL(fileURLWithPath: "transcriptions"))
        XCTAssertEqual(task.model, "tiny")
        XCTAssertEqual(task.formats, [.txt])
        XCTAssertEqual(task.language, "auto")
    }
    
    func testTranscriptionTask_ComputedProperties() {
        let inputURL = URL(fileURLWithPath: "/tmp/my_recording.mp3")
        let task = TranscriptionTask(inputURL: inputURL)
        
        XCTAssertEqual(task.inputFileName, "my_recording")
        XCTAssertEqual(task.inputFileExtension, "mp3")
        XCTAssertEqual(task.errorMessage, task.error)
    }
    
    func testTranscriptionTask_VideoDetection() {
        let videoURL = URL(fileURLWithPath: "/tmp/video.mp4")
        let audioURL = URL(fileURLWithPath: "/tmp/audio.mp3")
        
        let videoTask = TranscriptionTask(inputURL: videoURL)
        let audioTask = TranscriptionTask(inputURL: audioURL)
        
        XCTAssertTrue(videoTask.requiresAudioExtraction)
        XCTAssertFalse(audioTask.requiresAudioExtraction)
        
        // Test other video formats
        let movTask = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test.mov"))
        let aviTask = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test.avi"))
        let mkvTask = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test.mkv"))
        
        XCTAssertTrue(movTask.requiresAudioExtraction)
        XCTAssertTrue(aviTask.requiresAudioExtraction)
        XCTAssertTrue(mkvTask.requiresAudioExtraction)
    }
    
    func testTranscriptionTask_ProgressUpdates() {
        var task = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test.mp3"))
        
        // Test normal progress update
        task.updateProgress(0.5)
        XCTAssertEqual(task.progress, 0.5)
        
        // Test clamping to valid range
        task.updateProgress(-0.1)
        XCTAssertEqual(task.progress, 0.0)
        
        task.updateProgress(1.5)
        XCTAssertEqual(task.progress, 1.0)
    }
    
    func testTranscriptionTask_StateChanges() {
        var task = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test.mp3"))
        
        // Test mark started
        task.markStarted()
        XCTAssertEqual(task.status, .processing)
        XCTAssertNotNil(task.startTime)
        XCTAssertEqual(task.progress, 0.0)
        
        // Test mark completed with files
        let outputFiles = [URL(fileURLWithPath: "/tmp/output1.txt"), URL(fileURLWithPath: "/tmp/output2.srt")]
        task.markCompleted(outputFiles: outputFiles)
        XCTAssertEqual(task.status, .completed)
        XCTAssertNotNil(task.completionTime)
        XCTAssertEqual(task.progress, 1.0)
        XCTAssertEqual(task.outputFiles, outputFiles)
        XCTAssertNil(task.error)
        
        // Test reset
        task.reset()
        XCTAssertEqual(task.status, .pending)
        XCTAssertEqual(task.progress, 0.0)
        XCTAssertNil(task.error)
        XCTAssertNil(task.startTime)
        XCTAssertNil(task.completionTime)
        XCTAssertTrue(task.outputFiles.isEmpty)
        
        // Test mark failed
        task.markFailed(error: "Test error")
        XCTAssertEqual(task.status, .failed)
        XCTAssertNotNil(task.completionTime)
        XCTAssertEqual(task.error, "Test error")
        
        // Test mark cancelled
        task.markCancelled()
        XCTAssertEqual(task.status, .cancelled)
        XCTAssertNotNil(task.completionTime)
        XCTAssertEqual(task.error, "Cancelled by user")
    }
    
    func testTranscriptionTask_ProcessingTime() {
        var task = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test.mp3"))
        
        // No processing time when not started/completed
        XCTAssertEqual(task.processingTime, 0.0)
        
        // Set start time
        task.startTime = Date(timeIntervalSinceNow: -10) // 10 seconds ago
        XCTAssertEqual(task.processingTime, 0.0) // Still no completion time
        
        // Set completion time
        task.completionTime = Date() // Now
        XCTAssertGreaterThan(task.processingTime, 9.0) // Should be around 10 seconds
        XCTAssertLessThan(task.processingTime, 11.0)
    }
    
    func testTranscriptionTask_EstimatedTimeRemaining() {
        var task = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test.mp3"))
        
        // No estimate when not processing
        XCTAssertNil(task.estimatedTimeRemaining)
        
        // Set as processing with progress
        task.status = .processing
        task.startTime = Date(timeIntervalSinceNow: -5) // 5 seconds ago
        task.progress = 0.5 // 50% complete
        
        let estimated = task.estimatedTimeRemaining
        XCTAssertNotNil(estimated)
        XCTAssertGreaterThan(estimated!, 4.0) // Should be around 5 seconds remaining
        XCTAssertLessThan(estimated!, 6.0)
    }
    
    func testTranscriptionTask_Equality() {
        let inputURL = URL(fileURLWithPath: "/tmp/test.mp3")
        let task1 = TranscriptionTask(inputURL: inputURL, model: "base")
        let task2 = TranscriptionTask(inputURL: inputURL, model: "large")
        
        // Tasks should not be equal (different IDs)
        XCTAssertNotEqual(task1, task2)
        XCTAssertNotEqual(task1.id, task2.id)
        
        // Same task should be equal to itself
        XCTAssertEqual(task1, task1)
    }
    
    func testTranscriptionTask_Codable() throws {
        let inputURL = URL(fileURLWithPath: "/tmp/test.mp3")
        let outputDir = URL(fileURLWithPath: "/tmp/output")
        var task = TranscriptionTask(
            inputURL: inputURL,
            outputDirectory: outputDir,
            model: "base",
            formats: [.txt, .srt],
            language: "en"
        )
        
        task.markStarted()
        task.updateProgress(0.5)
        task.markCompleted()
        
        // Test encoding
        let encoder = JSONEncoder()
        let data = try encoder.encode(task)
        
        // Test decoding
        let decoder = JSONDecoder()
        let decodedTask = try decoder.decode(TranscriptionTask.self, from: data)
        
        XCTAssertEqual(decodedTask.id, task.id)
        XCTAssertEqual(decodedTask.inputURL, task.inputURL)
        XCTAssertEqual(decodedTask.outputDirectory, task.outputDirectory)
        XCTAssertEqual(decodedTask.model, task.model)
        XCTAssertEqual(decodedTask.formats, task.formats)
        XCTAssertEqual(decodedTask.language, task.language)
        XCTAssertEqual(decodedTask.status, task.status)
        XCTAssertEqual(decodedTask.progress, task.progress)
    }
    
    // MARK: - TranscriptionResult Tests
    
    func testTranscriptionResult_SuccessfulInitialization() {
        let result = TranscriptionResult(
            inputFile: "/tmp/test.mp3",
            outputFiles: ["/tmp/test.txt", "/tmp/test.srt"],
            processingTime: 45.5,
            modelUsed: "base",
            language: "en"
        )
        
        XCTAssertEqual(result.inputFile, "/tmp/test.mp3")
        XCTAssertEqual(result.outputFiles, ["/tmp/test.txt", "/tmp/test.srt"])
        XCTAssertEqual(result.processingTime, 45.5)
        XCTAssertEqual(result.modelUsed, "base")
        XCTAssertEqual(result.language, "en")
        XCTAssertTrue(result.success)
        XCTAssertNil(result.error)
        XCTAssertNotNil(result.timestamp)
    }
    
    func testTranscriptionResult_FailedInitialization() {
        let result = TranscriptionResult(
            inputFile: "/tmp/test.mp3",
            error: "Transcription failed",
            processingTime: 10.0,
            modelUsed: "base"
        )
        
        XCTAssertEqual(result.inputFile, "/tmp/test.mp3")
        XCTAssertTrue(result.outputFiles.isEmpty)
        XCTAssertEqual(result.processingTime, 10.0)
        XCTAssertEqual(result.modelUsed, "base")
        XCTAssertNil(result.language)
        XCTAssertFalse(result.success)
        XCTAssertEqual(result.error, "Transcription failed")
        XCTAssertNotNil(result.timestamp)
    }
    
    func testTranscriptionResult_URLs() {
        let result = TranscriptionResult(
            inputFile: "/tmp/test.mp3",
            outputFiles: ["/tmp/test.txt", "/tmp/test.srt"],
            processingTime: 30.0,
            modelUsed: "base"
        )
        
        XCTAssertEqual(result.inputURL?.path, "/tmp/test.mp3")
        XCTAssertEqual(result.outputURLs.count, 2)
        XCTAssertEqual(result.outputURLs[0].path, "/tmp/test.txt")
        XCTAssertEqual(result.outputURLs[1].path, "/tmp/test.srt")
    }
    
    func testTranscriptionResult_ProcessingTimeFormatted() {
        let result = TranscriptionResult(
            inputFile: "/tmp/test.mp3",
            outputFiles: [],
            processingTime: 125.0, // 2 minutes 5 seconds
            modelUsed: "base"
        )
        
        let formatted = result.processingTimeFormatted
        XCTAssertTrue(formatted.contains("2"))
        XCTAssertTrue(formatted.contains("5"))
    }
    
    func testTranscriptionResult_Codable() throws {
        let metadata = TranscriptionMetadata(
            confidence: 0.85,
            segmentCount: 10,
            averageSegmentDuration: 5.0,
            audioDuration: 120.0,
            languageConfidence: 0.95,
            detectedLanguage: "en",
            vadUsed: true,
            peakMemoryUsage: 512000000,
            customProperties: ["key": "value"]
        )
        
        let result = TranscriptionResult(
            inputFile: "/tmp/test.mp3",
            outputFiles: ["/tmp/test.txt"],
            processingTime: 30.0,
            modelUsed: "base",
            language: "en",
            metadata: metadata
        )
        
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(result)
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let decodedResult = try decoder.decode(TranscriptionResult.self, from: data)
        
        XCTAssertEqual(decodedResult.inputFile, result.inputFile)
        XCTAssertEqual(decodedResult.outputFiles, result.outputFiles)
        XCTAssertEqual(decodedResult.processingTime, result.processingTime)
        XCTAssertEqual(decodedResult.modelUsed, result.modelUsed)
        XCTAssertEqual(decodedResult.language, result.language)
        XCTAssertEqual(decodedResult.success, result.success)
        XCTAssertEqual(decodedResult.metadata?.confidence, metadata.confidence)
    }
    
    // MARK: - TranscriptionMetadata Tests
    
    func testTranscriptionMetadata_QualityAssessment() {
        let excellentMetadata = TranscriptionMetadata(confidence: 0.95, segmentCount: nil, averageSegmentDuration: nil, audioDuration: nil, languageConfidence: nil, detectedLanguage: nil, vadUsed: nil, peakMemoryUsage: nil, customProperties: nil)
        XCTAssertEqual(excellentMetadata.qualityAssessment, .excellent)
        
        let goodMetadata = TranscriptionMetadata(confidence: 0.85, segmentCount: nil, averageSegmentDuration: nil, audioDuration: nil, languageConfidence: nil, detectedLanguage: nil, vadUsed: nil, peakMemoryUsage: nil, customProperties: nil)
        XCTAssertEqual(goodMetadata.qualityAssessment, .good)
        
        let fairMetadata = TranscriptionMetadata(confidence: 0.75, segmentCount: nil, averageSegmentDuration: nil, audioDuration: nil, languageConfidence: nil, detectedLanguage: nil, vadUsed: nil, peakMemoryUsage: nil, customProperties: nil)
        XCTAssertEqual(fairMetadata.qualityAssessment, .fair)
        
        let poorMetadata = TranscriptionMetadata(confidence: 0.65, segmentCount: nil, averageSegmentDuration: nil, audioDuration: nil, languageConfidence: nil, detectedLanguage: nil, vadUsed: nil, peakMemoryUsage: nil, customProperties: nil)
        XCTAssertEqual(poorMetadata.qualityAssessment, .poor)
        
        let veryPoorMetadata = TranscriptionMetadata(confidence: 0.5, segmentCount: nil, averageSegmentDuration: nil, audioDuration: nil, languageConfidence: nil, detectedLanguage: nil, vadUsed: nil, peakMemoryUsage: nil, customProperties: nil)
        XCTAssertEqual(veryPoorMetadata.qualityAssessment, .veryPoor)
        
        let unknownMetadata = TranscriptionMetadata(confidence: nil, segmentCount: nil, averageSegmentDuration: nil, audioDuration: nil, languageConfidence: nil, detectedLanguage: nil, vadUsed: nil, peakMemoryUsage: nil, customProperties: nil)
        XCTAssertEqual(unknownMetadata.qualityAssessment, .unknown)
    }
    
    // MARK: - WhisperModel Tests
    
    func testWhisperModel_Initialization() {
        let performance = ModelPerformance(speedMultiplier: 16.0, accuracy: "Good", memoryUsage: "Low", languages: 99)
        let model = WhisperModel(
            name: "base",
            sizeMB: 74.0,
            description: "Base model",
            performance: performance,
            downloadURL: "https://example.com/base.bin"
        )
        
        XCTAssertEqual(model.name, "base")
        XCTAssertEqual(model.id, "base") // id should match name
        XCTAssertEqual(model.sizeMB, 74.0)
        XCTAssertEqual(model.description, "Base model")
        XCTAssertEqual(model.performance.speedMultiplier, 16.0)
        XCTAssertEqual(model.downloadURL, "https://example.com/base.bin")
        XCTAssertFalse(model.isDownloaded)
        XCTAssertNil(model.localFilePath)
        XCTAssertEqual(model.downloadProgress, 0.0)
        XCTAssertFalse(model.isDownloading)
    }
    
    func testWhisperModel_ComputedProperties() {
        let performance = ModelPerformance(speedMultiplier: 16.0, accuracy: "Good", memoryUsage: "Low", languages: 99)
        let model = WhisperModel(
            name: "base.en",
            sizeMB: 74.0,
            description: "Base English model",
            performance: performance,
            downloadURL: "https://example.com/base.en.bin"
        )
        
        XCTAssertEqual(model.sizeBytes, 74 * 1024 * 1024)
        XCTAssertTrue(model.sizeFormatted.contains("74"))
        XCTAssertTrue(model.isEnglishOnly)
        XCTAssertEqual(model.baseName, "base")
        XCTAssertEqual(model.languages, ["English"])
        XCTAssertEqual(model.sizeCategory, .small)
    }
    
    func testWhisperModel_MultilingualModel() {
        let performance = ModelPerformance(speedMultiplier: 8.0, accuracy: "Excellent", memoryUsage: "High", languages: 99)
        let model = WhisperModel(
            name: "large-v3-turbo",
            sizeMB: 809.0,
            description: "Large model",
            performance: performance,
            downloadURL: "https://example.com/large-v3-turbo.bin"
        )
        
        XCTAssertFalse(model.isEnglishOnly)
        XCTAssertTrue(model.languages.count > 1)
        XCTAssertTrue(model.languages.contains("English"))
        XCTAssertTrue(model.languages.contains("Spanish"))
        XCTAssertEqual(model.sizeCategory, .large)
    }
    
    func testWhisperModel_SizeCategories() {
        let tinyModel = WhisperModel(name: "tiny", sizeMB: 39, description: "", performance: ModelPerformance(speedMultiplier: 32, accuracy: "Fair", memoryUsage: "Very Low", languages: 99), downloadURL: "")
        XCTAssertEqual(tinyModel.sizeCategory, .tiny)
        
        let smallModel = WhisperModel(name: "small", sizeMB: 244, description: "", performance: ModelPerformance(speedMultiplier: 6, accuracy: "Better", memoryUsage: "Medium", languages: 99), downloadURL: "")
        XCTAssertEqual(smallModel.sizeCategory, .medium)
        
        let largeModel = WhisperModel(name: "large", sizeMB: 1550, description: "", performance: ModelPerformance(speedMultiplier: 4, accuracy: "Excellent", memoryUsage: "Very High", languages: 99), downloadURL: "")
        XCTAssertEqual(largeModel.sizeCategory, .extraLarge)
    }
    
    func testWhisperModel_DownloadStateManagement() {
        var model = WhisperModel(name: "base", sizeMB: 74, description: "", performance: ModelPerformance(speedMultiplier: 16, accuracy: "Good", memoryUsage: "Low", languages: 99), downloadURL: "")
        
        XCTAssertFalse(model.isDownloaded)
        XCTAssertFalse(model.isDownloading)
        
        // Test download progress
        model.updateDownloadProgress(0.5)
        XCTAssertEqual(model.downloadProgress, 0.5)
        XCTAssertTrue(model.isDownloading)
        
        // Test completion
        let localPath = URL(fileURLWithPath: "/tmp/base.bin")
        model.markDownloaded(at: localPath)
        XCTAssertTrue(model.isDownloaded)
        XCTAssertEqual(model.localFilePath, localPath)
        XCTAssertEqual(model.downloadProgress, 1.0)
        XCTAssertFalse(model.isDownloading)
        
        // Test reset
        model.resetDownloadState()
        XCTAssertFalse(model.isDownloaded)
        XCTAssertNil(model.localFilePath)
        XCTAssertEqual(model.downloadProgress, 0.0)
        XCTAssertFalse(model.isDownloading)
    }
    
    func testWhisperModel_Comparison() {
        let tinyModel = WhisperModel(name: "tiny", sizeMB: 39, description: "", performance: ModelPerformance(speedMultiplier: 32, accuracy: "Fair", memoryUsage: "Very Low", languages: 99), downloadURL: "")
        let baseModel = WhisperModel(name: "base", sizeMB: 74, description: "", performance: ModelPerformance(speedMultiplier: 16, accuracy: "Good", memoryUsage: "Low", languages: 99), downloadURL: "")
        let largeModel = WhisperModel(name: "large", sizeMB: 1550, description: "", performance: ModelPerformance(speedMultiplier: 4, accuracy: "Excellent", memoryUsage: "Very High", languages: 99), downloadURL: "")
        
        XCTAssertTrue(tinyModel < baseModel)
        XCTAssertTrue(baseModel < largeModel)
        XCTAssertTrue(tinyModel < largeModel)
        
        let sortedModels = [largeModel, tinyModel, baseModel].sorted()
        XCTAssertEqual(sortedModels[0].name, "tiny")
        XCTAssertEqual(sortedModels[1].name, "base")
        XCTAssertEqual(sortedModels[2].name, "large")
    }
    
    func testWhisperModel_AvailableModels() {
        let availableModels = WhisperModel.availableModels
        XCTAssertFalse(availableModels.isEmpty)
        
        // Check that we have expected models
        let modelNames = availableModels.map { $0.name }
        XCTAssertTrue(modelNames.contains("tiny"))
        XCTAssertTrue(modelNames.contains("base"))
        XCTAssertTrue(modelNames.contains("large-v3-turbo"))
        
        // Check default model
        let defaultModel = WhisperModel.defaultModel
        XCTAssertEqual(defaultModel.name, "large-v3-turbo")
        
        // Check fastest model
        let fastestModel = WhisperModel.fastestModel
        XCTAssertEqual(fastestModel.name, "tiny")
    }
    
    // MARK: - ModelPerformance Tests
    
    func testModelPerformance_AccuracyPercentage() {
        let fairPerformance = ModelPerformance(speedMultiplier: 32, accuracy: "Fair", memoryUsage: "Low", languages: 99)
        XCTAssertEqual(fairPerformance.accuracyPercentage, 70)
        
        let goodPerformance = ModelPerformance(speedMultiplier: 16, accuracy: "Good", memoryUsage: "Low", languages: 99)
        XCTAssertEqual(goodPerformance.accuracyPercentage, 80)
        
        let excellentPerformance = ModelPerformance(speedMultiplier: 4, accuracy: "Excellent", memoryUsage: "High", languages: 99)
        XCTAssertEqual(excellentPerformance.accuracyPercentage, 95)
        
        let unknownPerformance = ModelPerformance(speedMultiplier: 8, accuracy: "Unknown", memoryUsage: "Medium", languages: 99)
        XCTAssertEqual(unknownPerformance.accuracyPercentage, 75)
    }
    
    func testModelPerformance_MemoryCategory() {
        let veryLowMemory = ModelPerformance(speedMultiplier: 32, accuracy: "Fair", memoryUsage: "Very Low", languages: 99)
        XCTAssertEqual(veryLowMemory.memoryCategory, .veryLow)
        XCTAssertEqual(veryLowMemory.memoryCategory.estimatedRAMUsage, 0.5)
        XCTAssertEqual(veryLowMemory.memoryCategory.colorName, "systemGreen")
        
        let highMemory = ModelPerformance(speedMultiplier: 4, accuracy: "Excellent", memoryUsage: "High", languages: 99)
        XCTAssertEqual(highMemory.memoryCategory, .high)
        XCTAssertEqual(highMemory.memoryCategory.estimatedRAMUsage, 4.0)
        XCTAssertEqual(highMemory.memoryCategory.colorName, "systemRed")
        
        let mediumMemory = ModelPerformance(speedMultiplier: 8, accuracy: "Good", memoryUsage: "Medium", languages: 99)
        XCTAssertEqual(mediumMemory.memoryCategory, .medium)
        XCTAssertEqual(mediumMemory.memoryCategory.estimatedRAMUsage, 2.0)
        XCTAssertEqual(mediumMemory.memoryCategory.colorName, "systemOrange")
    }
    
    // MARK: - Collection Extensions Tests
    
    func testTranscriptionResults_CollectionExtensions() {
        let successResult1 = TranscriptionResult(inputFile: "test1.mp3", outputFiles: ["test1.txt"], processingTime: 30.0, modelUsed: "base")
        let successResult2 = TranscriptionResult(inputFile: "test2.mp3", outputFiles: ["test2.txt"], processingTime: 45.0, modelUsed: "large")
        let failedResult = TranscriptionResult(inputFile: "test3.mp3", error: "Failed", modelUsed: "base")
        
        let results = [successResult1, successResult2, failedResult]
        
        // Test successful results
        XCTAssertEqual(results.successful.count, 2)
        XCTAssertTrue(results.successful.contains(successResult1))
        XCTAssertTrue(results.successful.contains(successResult2))
        
        // Test failed results
        XCTAssertEqual(results.failed.count, 1)
        XCTAssertTrue(results.failed.contains(failedResult))
        
        // Test success rate
        XCTAssertEqual(results.successRate, 2.0/3.0, accuracy: 0.001)
        
        // Test total processing time
        XCTAssertEqual(results.totalProcessingTime, 75.0) // 30 + 45 + 0
        
        // Test average processing time
        XCTAssertEqual(results.averageProcessingTime, 25.0, accuracy: 0.001) // 75 / 3
        
        // Test most used model
        XCTAssertEqual(results.mostUsedModel, "base") // Used twice vs "large" used once
    }
}

// MARK: - Test Helper Extensions

extension TranscriptionTask {
    static func testTask(
        inputURL: URL = URL(fileURLWithPath: "/tmp/test.mp3"),
        outputDirectory: URL = URL(fileURLWithPath: "/tmp"),
        model: String = "base",
        formats: [OutputFormat] = [.txt]
    ) -> TranscriptionTask {
        return TranscriptionTask(
            inputURL: inputURL,
            outputDirectory: outputDirectory,
            model: model,
            formats: formats
        )
    }
}