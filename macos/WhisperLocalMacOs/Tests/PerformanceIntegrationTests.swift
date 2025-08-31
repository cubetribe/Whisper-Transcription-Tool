import XCTest
import Foundation
import Combine
@testable import WhisperLocalMacOs

/// Performance regression and benchmarking integration tests
/// Tests performance characteristics against baseline requirements
@MainActor
class PerformanceIntegrationTests: XCTestCase {
    
    // MARK: - Test Infrastructure
    
    private var tempDirectory: URL!
    private var benchmarkDirectory: URL!
    private var pythonBridge: PythonBridge!
    private var modelManager: ModelManager!
    private var performanceBaselines: PerformanceBaselines!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        tempDirectory = FileManager.default.temporaryDirectory
            .appendingPathComponent("PerformanceTests_\(UUID().uuidString)")
        benchmarkDirectory = tempDirectory.appendingPathComponent("benchmarks")
        
        try FileManager.default.createDirectory(at: tempDirectory, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: benchmarkDirectory, withIntermediateDirectories: true)
        
        pythonBridge = PythonBridge.shared
        modelManager = ModelManager.shared
        performanceBaselines = PerformanceBaselines()
        
        // Create benchmark test files
        try createBenchmarkFiles()
        
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
    
    // MARK: - Startup Performance Tests
    
    func testApplicationStartup_ColdStart() async throws {
        // Measure cold start time from initialization to ready state
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Initialize all major components
        let dependencyManager = DependencyManager.shared
        let pythonBridge = PythonBridge.shared
        let modelManager = ModelManager.shared
        
        // Wait for initial validations
        let _ = await dependencyManager.validateDependencies()
        let _ = await pythonBridge.initializeBridge()
        let _ = await modelManager.loadAvailableModels()
        
        let startupTime = CFAbsoluteTimeGetCurrent() - startTime
        
        // Performance requirement: Startup should complete within 5 seconds
        XCTAssertLessThan(startupTime, 5.0, "Cold startup should complete within 5 seconds")
        
        // Log performance metrics
        print("Cold Startup Performance: \(String(format: "%.2f", startupTime))s")
        
        // Verify components are ready
        XCTAssertTrue(dependencyManager.dependencyStatus.isValid, "Dependencies should be valid after startup")
        XCTAssertTrue(pythonBridge.isReady, "Python bridge should be ready")
        XCTAssertFalse(modelManager.availableModels.isEmpty, "Should load available models")
    }
    
    func testApplicationStartup_WarmStart() async throws {
        // Pre-initialize components for warm start test
        _ = await DependencyManager.shared.validateDependencies()
        _ = await pythonBridge.initializeBridge()
        _ = await modelManager.loadAvailableModels()
        
        // Simulate app restart (warm start)
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Re-initialize with cached state
        _ = await DependencyManager.shared.validateDependencies()
        _ = await pythonBridge.initializeBridge()
        _ = await modelManager.loadAvailableModels()
        
        let warmStartupTime = CFAbsoluteTimeGetCurrent() - startTime
        
        // Warm start should be faster than cold start
        XCTAssertLessThan(warmStartupTime, 2.0, "Warm startup should complete within 2 seconds")
        
        print("Warm Startup Performance: \(String(format: "%.2f", warmStartupTime))s")
    }
    
    // MARK: - Transcription Performance Tests
    
    func testTranscriptionPerformance_SmallFiles() async throws {
        let testFiles = [
            benchmarkDirectory.appendingPathComponent("small_30s.wav"),
            benchmarkDirectory.appendingPathComponent("small_60s.wav")
        ]
        
        var results: [TranscriptionPerformanceResult] = []
        
        for testFile in testFiles {
            let result = try await measureTranscriptionPerformance(
                file: testFile,
                model: "base.en",
                format: [.txt]
            )
            results.append(result)
            
            // Small files should process quickly
            XCTAssertLessThan(result.processingTime, 30.0, "Small files should process within 30 seconds")
            XCTAssertGreaterThan(result.realTimeSpeedRatio, 0.5, "Should achieve at least 0.5x real-time speed")
            
            print("Small File Performance (\(testFile.lastPathComponent)): \(result.summary)")
        }
        
        // Verify consistent performance across small files
        let averageSpeedRatio = results.map { $0.realTimeSpeedRatio }.reduce(0, +) / Double(results.count)
        XCTAssertGreaterThan(averageSpeedRatio, 0.5, "Average speed should meet minimum threshold")
    }
    
    func testTranscriptionPerformance_MediumFiles() async throws {
        let testFiles = [
            benchmarkDirectory.appendingPathComponent("medium_5min.wav"),
            benchmarkDirectory.appendingPathComponent("medium_10min.wav")
        ]
        
        var results: [TranscriptionPerformanceResult] = []
        
        for testFile in testFiles {
            let result = try await measureTranscriptionPerformance(
                file: testFile,
                model: "base.en",
                format: [.txt]
            )
            results.append(result)
            
            // Medium files should maintain good performance
            XCTAssertLessThan(result.processingTime, 600.0, "Medium files should process within 10 minutes")
            XCTAssertGreaterThan(result.realTimeSpeedRatio, 0.3, "Should achieve at least 0.3x real-time speed")
            
            print("Medium File Performance (\(testFile.lastPathComponent)): \(result.summary)")
        }
        
        // Performance should scale reasonably with file size
        let speedRatios = results.map { $0.realTimeSpeedRatio }
        let speedVariation = speedRatios.max()! - speedRatios.min()!
        XCTAssertLessThan(speedVariation, 0.5, "Speed variation should be reasonable across medium files")
    }
    
    func testTranscriptionPerformance_LargeFiles() async throws {
        let testFile = benchmarkDirectory.appendingPathComponent("large_30min.wav")
        
        let result = try await measureTranscriptionPerformance(
            file: testFile,
            model: "base.en",
            format: [.txt]
        )
        
        // Large files should complete within reasonable time
        XCTAssertLessThan(result.processingTime, 1800.0, "Large files should process within 30 minutes")
        XCTAssertGreaterThan(result.realTimeSpeedRatio, 0.1, "Should achieve at least 0.1x real-time speed")
        
        // Memory usage should remain bounded
        XCTAssertLessThan(result.peakMemoryMB, 2000, "Should not exceed 2GB memory usage")
        
        print("Large File Performance: \(result.summary)")
    }
    
    func testTranscriptionPerformance_ModelComparison() async throws {
        let testFile = benchmarkDirectory.appendingPathComponent("medium_5min.wav")
        let models = ["base.en", "small.en"] // Test different model sizes
        
        var modelResults: [String: TranscriptionPerformanceResult] = [:]
        
        for model in models {
            // Ensure model is available
            if !modelManager.isModelAvailable(model) {
                try await modelManager.downloadModel(model)
            }
            
            let result = try await measureTranscriptionPerformance(
                file: testFile,
                model: model,
                format: [.txt]
            )
            modelResults[model] = result
            
            print("Model Performance (\(model)): \(result.summary)")
        }
        
        // Verify different models have expected performance characteristics
        if let baseResult = modelResults["base.en"],
           let smallResult = modelResults["small.en"] {
            
            // Smaller model should be faster but potentially less accurate
            XCTAssertLessThan(smallResult.processingTime, baseResult.processingTime * 1.5, 
                             "Small model should not be significantly slower than expected")
            
            // Both should meet minimum performance requirements
            XCTAssertGreaterThan(baseResult.realTimeSpeedRatio, 0.1, "Base model should meet speed requirements")
            XCTAssertGreaterThan(smallResult.realTimeSpeedRatio, 0.1, "Small model should meet speed requirements")
        }
    }
    
    // MARK: - Batch Processing Performance Tests
    
    func testBatchProcessing_SmallBatch() async throws {
        let testFiles = [
            benchmarkDirectory.appendingPathComponent("small_30s.wav"),
            benchmarkDirectory.appendingPathComponent("small_60s.wav"),
            benchmarkDirectory.appendingPathComponent("small_90s.wav")
        ]
        
        let result = try await measureBatchProcessingPerformance(
            files: testFiles,
            model: "base.en",
            formats: [.txt]
        )
        
        // Small batch should complete efficiently
        XCTAssertLessThan(result.totalProcessingTime, 120.0, "Small batch should complete within 2 minutes")
        XCTAssertEqual(result.completedTasks, testFiles.count, "All tasks should complete")
        XCTAssertEqual(result.failedTasks, 0, "No tasks should fail")
        XCTAssertGreaterThan(result.averageSpeedRatio, 0.3, "Average speed should be reasonable")
        
        print("Small Batch Performance: \(result.summary)")
    }
    
    func testBatchProcessing_LargeBatch() async throws {
        let testFiles = (0..<10).map { i in
            benchmarkDirectory.appendingPathComponent("batch_\(i)_2min.wav")
        }
        
        let result = try await measureBatchProcessingPerformance(
            files: testFiles,
            model: "base.en",
            formats: [.txt]
        )
        
        // Large batch should complete within reasonable time
        XCTAssertLessThan(result.totalProcessingTime, 1200.0, "Large batch should complete within 20 minutes")
        XCTAssertEqual(result.completedTasks, testFiles.count, "All tasks should complete")
        XCTAssertLessThan(Double(result.failedTasks) / Double(testFiles.count), 0.1, "Failure rate should be <10%")
        
        // Should maintain reasonable throughput
        let throughputFilesPerMinute = Double(result.completedTasks) / (result.totalProcessingTime / 60.0)
        XCTAssertGreaterThan(throughputFilesPerMinute, 0.5, "Should process at least 0.5 files per minute")
        
        print("Large Batch Performance: \(result.summary)")
    }
    
    func testBatchProcessing_ConcurrencyScaling() async throws {
        let testFiles = (0..<6).map { i in
            benchmarkDirectory.appendingPathComponent("concurrent_\(i)_1min.wav")
        }
        
        // Test different concurrency levels
        let concurrencyLevels = [1, 2, 3]
        var scalingResults: [Int: BatchPerformanceResult] = [:]
        
        for concurrency in concurrencyLevels {
            let result = try await measureBatchProcessingPerformance(
                files: testFiles,
                model: "base.en",
                formats: [.txt],
                concurrency: concurrency
            )
            scalingResults[concurrency] = result
            
            print("Concurrency \(concurrency): \(result.summary)")
        }
        
        // Verify concurrency improves performance up to optimal level
        if let sequential = scalingResults[1],
           let concurrent2 = scalingResults[2],
           let concurrent3 = scalingResults[3] {
            
            // 2-way concurrency should be faster than sequential
            XCTAssertLessThan(concurrent2.totalProcessingTime, sequential.totalProcessingTime * 0.8, 
                             "2-way concurrency should provide speedup")
            
            // 3-way may or may not be faster (depends on system resources)
            // But should not be significantly worse
            XCTAssertLessThan(concurrent3.totalProcessingTime, sequential.totalProcessingTime * 1.2, 
                             "High concurrency should not degrade performance significantly")
        }
    }
    
    // MARK: - Memory Performance Tests
    
    func testMemoryPerformance_SteadyState() async throws {
        let initialMemory = getMemoryUsage()
        var memoryMeasurements: [Int64] = [initialMemory]
        
        // Perform multiple transcriptions to test memory stability
        let testFiles = [
            benchmarkDirectory.appendingPathComponent("small_30s.wav"),
            benchmarkDirectory.appendingPathComponent("small_60s.wav"),
            benchmarkDirectory.appendingPathComponent("small_30s.wav"), // Repeat to test cleanup
            benchmarkDirectory.appendingPathComponent("small_60s.wav")
        ]
        
        for (index, testFile) in testFiles.enumerated() {
            _ = try await measureTranscriptionPerformance(
                file: testFile,
                model: "base.en",
                format: [.txt]
            )
            
            // Measure memory after each transcription
            let currentMemory = getMemoryUsage()
            memoryMeasurements.append(currentMemory)
            
            print("Memory after transcription \(index + 1): \(currentMemory / (1024 * 1024))MB")
        }
        
        let finalMemory = memoryMeasurements.last!
        let memoryIncrease = finalMemory - initialMemory
        let memoryIncreaseMB = memoryIncrease / (1024 * 1024)
        
        // Memory should not continuously grow
        XCTAssertLessThan(memoryIncreaseMB, 200, "Memory increase should be bounded (<200MB)")
        
        // Memory should stabilize (no consistent growth pattern)
        let lastThreeMeasurements = Array(memoryMeasurements.suffix(3))
        let memoryGrowthRate = (lastThreeMeasurements.last! - lastThreeMeasurements.first!) / (1024 * 1024)
        XCTAssertLessThan(memoryGrowthRate, 50, "Memory should stabilize (growth <50MB over last 3 operations)")
        
        print("Memory Performance: Initial \(initialMemory / (1024 * 1024))MB, Final \(finalMemory / (1024 * 1024))MB, Growth \(memoryIncreaseMB)MB")
    }
    
    func testMemoryPerformance_LargeFileHandling() async throws {
        let largeFile = benchmarkDirectory.appendingPathComponent("large_30min.wav")
        let initialMemory = getMemoryUsage()
        
        var peakMemory = initialMemory
        let memoryMonitor = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
            peakMemory = max(peakMemory, self.getMemoryUsage())
        }
        
        // Process large file
        _ = try await measureTranscriptionPerformance(
            file: largeFile,
            model: "base.en",
            format: [.txt]
        )
        
        memoryMonitor.invalidate()
        
        let finalMemory = getMemoryUsage()
        let peakIncrease = (peakMemory - initialMemory) / (1024 * 1024)
        let finalIncrease = (finalMemory - initialMemory) / (1024 * 1024)
        
        // Peak memory should be reasonable for large files
        XCTAssertLessThan(peakIncrease, 3000, "Peak memory increase should be <3GB for large files")
        
        // Memory should return to reasonable level after processing
        XCTAssertLessThan(finalIncrease, 300, "Final memory increase should be <300MB after processing")
        
        print("Large File Memory: Peak +\(peakIncrease)MB, Final +\(finalIncrease)MB")
    }
    
    // MARK: - Regression Tests Against Web Version
    
    func testPerformanceRegression_WebVersionComparison() async throws {
        // Benchmark against known web version performance characteristics
        let testFile = benchmarkDirectory.appendingPathComponent("benchmark_5min.wav")
        
        let result = try await measureTranscriptionPerformance(
            file: testFile,
            model: "base.en",
            format: [.txt]
        )
        
        // Compare against web version baselines (these would be established from actual measurements)
        let webVersionBaseline = performanceBaselines.webVersionBaseline
        
        // macOS version should be competitive with web version
        let speedRatioDifference = abs(result.realTimeSpeedRatio - webVersionBaseline.realTimeSpeedRatio)
        XCTAssertLessThan(speedRatioDifference, 0.3, "Speed should be within 0.3x of web version")
        
        // Memory usage should be reasonable
        XCTAssertLessThan(result.peakMemoryMB, webVersionBaseline.peakMemoryMB * 1.5, 
                         "Memory usage should not exceed 1.5x web version")
        
        // Quality should be maintained
        XCTAssertNotNil(result.outputContent, "Should produce transcription output")
        XCTAssertGreaterThan(result.outputContent!.count, 100, "Should produce substantial output")
        
        print("Web Version Comparison: macOS \(result.realTimeSpeedRatio)x vs Web \(webVersionBaseline.realTimeSpeedRatio)x")
    }
    
    // MARK: - Stress Tests
    
    func testStressTest_ContinuousOperation() async throws {
        let testFile = benchmarkDirectory.appendingPathComponent("small_60s.wav")
        let operationCount = 10
        var results: [TranscriptionPerformanceResult] = []
        
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Perform continuous operations
        for i in 0..<operationCount {
            let result = try await measureTranscriptionPerformance(
                file: testFile,
                model: "base.en",
                format: [.txt]
            )
            results.append(result)
            
            print("Stress test operation \(i + 1)/\(operationCount): \(String(format: "%.2f", result.realTimeSpeedRatio))x speed")
        }
        
        let totalTime = CFAbsoluteTimeGetCurrent() - startTime
        
        // Verify performance doesn't degrade over time
        let firstHalfAvg = results.prefix(operationCount / 2).map { $0.realTimeSpeedRatio }.reduce(0, +) / Double(operationCount / 2)
        let secondHalfAvg = results.suffix(operationCount / 2).map { $0.realTimeSpeedRatio }.reduce(0, +) / Double(operationCount / 2)
        
        let performanceDegradation = abs(firstHalfAvg - secondHalfAvg) / firstHalfAvg
        XCTAssertLessThan(performanceDegradation, 0.2, "Performance should not degrade more than 20% over time")
        
        // Overall throughput should be maintained
        let overallThroughput = Double(operationCount) / totalTime * 60.0 // operations per minute
        XCTAssertGreaterThan(overallThroughput, 1.0, "Should maintain at least 1 operation per minute")
        
        print("Stress Test: \(operationCount) operations in \(String(format: "%.1f", totalTime))s, throughput \(String(format: "%.2f", overallThroughput))/min")
    }
    
    // MARK: - Test Utilities
    
    private func createBenchmarkFiles() throws {
        // Create benchmark files of various sizes
        try createBenchmarkWAVFile(name: "small_30s.wav", durationSeconds: 30)
        try createBenchmarkWAVFile(name: "small_60s.wav", durationSeconds: 60)
        try createBenchmarkWAVFile(name: "small_90s.wav", durationSeconds: 90)
        try createBenchmarkWAVFile(name: "medium_5min.wav", durationSeconds: 300)
        try createBenchmarkWAVFile(name: "medium_10min.wav", durationSeconds: 600)
        try createBenchmarkWAVFile(name: "large_30min.wav", durationSeconds: 1800)
        try createBenchmarkWAVFile(name: "benchmark_5min.wav", durationSeconds: 300)
        
        // Create batch test files
        for i in 0..<10 {
            try createBenchmarkWAVFile(name: "batch_\(i)_2min.wav", durationSeconds: 120)
        }
        
        // Create concurrency test files
        for i in 0..<6 {
            try createBenchmarkWAVFile(name: "concurrent_\(i)_1min.wav", durationSeconds: 60)
        }
    }
    
    private func createBenchmarkWAVFile(name: String, durationSeconds: Int) throws {
        let file = benchmarkDirectory.appendingPathComponent(name)
        let audioData = generateBenchmarkAudio(durationSeconds: durationSeconds)
        try createWAVFile(at: file, audioData: audioData, sampleRate: 44100, channels: 1)
    }
    
    private func generateBenchmarkAudio(durationSeconds: Int) -> Data {
        let sampleRate = 44100
        let sampleCount = durationSeconds * sampleRate
        var audioData = Data()
        
        // Generate more complex test audio with speech-like characteristics
        let amplitude: Int16 = 16000
        let frequencies = [220.0, 440.0, 880.0, 1760.0] // Multiple harmonics
        
        for i in 0..<sampleCount {
            let time = Double(i) / Double(sampleRate)
            var sample: Double = 0
            
            // Create complex waveform with multiple frequencies
            for (index, frequency) in frequencies.enumerated() {
                let weight = 1.0 / Double(index + 1) // Decreasing amplitude for harmonics
                sample += sin(2.0 * Double.pi * frequency * time) * weight
            }
            
            // Add some noise to simulate real audio
            let noise = Double.random(in: -0.1...0.1)
            sample = (sample + noise) * Double(amplitude) / Double(frequencies.count)
            
            let sampleValue = Int16(max(-32768, min(32767, sample)))
            audioData.append(withUnsafeBytes(of: sampleValue.littleEndian) { Data($0) })
        }
        
        return audioData
    }
    
    private func createWAVFile(at url: URL, audioData: Data, sampleRate: Int, channels: Int) throws {
        var wavData = Data()
        
        // WAV header
        wavData.append("RIFF".data(using: .ascii)!)
        let fileSize = 36 + audioData.count
        wavData.append(withUnsafeBytes(of: UInt32(fileSize).littleEndian) { Data($0) })
        wavData.append("WAVE".data(using: .ascii)!)
        wavData.append("fmt ".data(using: .ascii)!)
        wavData.append(withUnsafeBytes(of: UInt32(16).littleEndian) { Data($0) })
        wavData.append(withUnsafeBytes(of: UInt16(1).littleEndian) { Data($0) })
        wavData.append(withUnsafeBytes(of: UInt16(channels).littleEndian) { Data($0) })
        wavData.append(withUnsafeBytes(of: UInt32(sampleRate).littleEndian) { Data($0) })
        let byteRate = sampleRate * channels * 2
        wavData.append(withUnsafeBytes(of: UInt32(byteRate).littleEndian) { Data($0) })
        let blockAlign = channels * 2
        wavData.append(withUnsafeBytes(of: UInt16(blockAlign).littleEndian) { Data($0) })
        wavData.append(withUnsafeBytes(of: UInt16(16).littleEndian) { Data($0) })
        wavData.append("data".data(using: .ascii)!)
        wavData.append(withUnsafeBytes(of: UInt32(audioData.count).littleEndian) { Data($0) })
        wavData.append(audioData)
        
        try wavData.write(to: url)
    }
    
    private func measureTranscriptionPerformance(
        file: URL,
        model: String,
        format: [TranscriptionFormat]
    ) async throws -> TranscriptionPerformanceResult {
        
        let task = TranscriptionTask(
            inputURL: file,
            outputDirectory: tempDirectory,
            model: model,
            formats: format
        )
        
        let initialMemory = getMemoryUsage()
        var peakMemory = initialMemory
        
        let memoryMonitor = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            peakMemory = max(peakMemory, self.getMemoryUsage())
        }
        
        let startTime = CFAbsoluteTimeGetCurrent()
        
        var finalResult: TranscriptionResult?
        let expectation = XCTestExpectation(description: "Performance test completion")
        
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
        await fulfillment(of: [expectation], timeout: 1800.0) // 30 minutes max
        progressTask.cancel()
        memoryMonitor.invalidate()
        
        let processingTime = CFAbsoluteTimeGetCurrent() - startTime
        
        guard let result = finalResult else {
            throw XCTError("No transcription result received")
        }
        
        // Calculate performance metrics
        let fileDuration = getAudioDuration(file: file)
        let realTimeSpeedRatio = fileDuration / processingTime
        let peakMemoryMB = (peakMemory - initialMemory) / (1024 * 1024)
        
        // Read output content for quality assessment
        let outputContent = try? String(contentsOf: result.outputFiles.first!)
        
        return TranscriptionPerformanceResult(
            fileName: file.lastPathComponent,
            model: model,
            processingTime: processingTime,
            realTimeSpeedRatio: realTimeSpeedRatio,
            peakMemoryMB: peakMemoryMB,
            outputContent: outputContent
        )
    }
    
    private func measureBatchProcessingPerformance(
        files: [URL],
        model: String,
        formats: [TranscriptionFormat],
        concurrency: Int = 1
    ) async throws -> BatchPerformanceResult {
        
        let tasks = files.map { file in
            TranscriptionTask(
                inputURL: file,
                outputDirectory: tempDirectory.appendingPathComponent("batch_\(UUID().uuidString)"),
                model: model,
                formats: formats
            )
        }
        
        // Create output directories
        for task in tasks {
            try FileManager.default.createDirectory(at: task.outputDirectory, withIntermediateDirectories: true)
        }
        
        let startTime = CFAbsoluteTimeGetCurrent()
        var completedTasks = 0
        var failedTasks = 0
        var speedRatios: [Double] = []
        
        // Process with specified concurrency
        if concurrency == 1 {
            // Sequential processing
            for task in tasks {
                do {
                    let result = try await measureTranscriptionPerformance(
                        file: task.inputURL,
                        model: model,
                        format: formats
                    )
                    completedTasks += 1
                    speedRatios.append(result.realTimeSpeedRatio)
                } catch {
                    failedTasks += 1
                }
            }
        } else {
            // Concurrent processing
            await withTaskGroup(of: Void.self) { group in
                let semaphore = AsyncSemaphore(value: concurrency)
                
                for task in tasks {
                    group.addTask {
                        await semaphore.wait()
                        defer { semaphore.signal() }
                        
                        do {
                            let result = try await self.measureTranscriptionPerformance(
                                file: task.inputURL,
                                model: model,
                                format: formats
                            )
                            completedTasks += 1
                            speedRatios.append(result.realTimeSpeedRatio)
                        } catch {
                            failedTasks += 1
                        }
                    }
                }
            }
        }
        
        let totalProcessingTime = CFAbsoluteTimeGetCurrent() - startTime
        let averageSpeedRatio = speedRatios.isEmpty ? 0 : speedRatios.reduce(0, +) / Double(speedRatios.count)
        
        return BatchPerformanceResult(
            totalProcessingTime: totalProcessingTime,
            completedTasks: completedTasks,
            failedTasks: failedTasks,
            averageSpeedRatio: averageSpeedRatio,
            concurrency: concurrency
        )
    }
    
    private func getAudioDuration(file: URL) -> TimeInterval {
        // Simplified duration calculation based on file name
        // In real implementation, would use audio metadata
        if file.lastPathComponent.contains("30s") { return 30.0 }
        if file.lastPathComponent.contains("60s") || file.lastPathComponent.contains("1min") { return 60.0 }
        if file.lastPathComponent.contains("90s") { return 90.0 }
        if file.lastPathComponent.contains("2min") { return 120.0 }
        if file.lastPathComponent.contains("5min") { return 300.0 }
        if file.lastPathComponent.contains("10min") { return 600.0 }
        if file.lastPathComponent.contains("30min") { return 1800.0 }
        return 60.0 // Default
    }
    
    private func getMemoryUsage() -> Int64 {
        var taskInfo = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info>.size) / 4
        
        let result = withUnsafeMutablePointer(to: &taskInfo) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        
        guard result == KERN_SUCCESS else { return 0 }
        return Int64(taskInfo.resident_size)
    }
}

// MARK: - Performance Result Types

struct TranscriptionPerformanceResult {
    let fileName: String
    let model: String
    let processingTime: TimeInterval
    let realTimeSpeedRatio: Double
    let peakMemoryMB: Int64
    let outputContent: String?
    
    var summary: String {
        return "\(String(format: "%.2f", realTimeSpeedRatio))x speed, \(String(format: "%.1f", processingTime))s time, \(peakMemoryMB)MB peak"
    }
}

struct BatchPerformanceResult {
    let totalProcessingTime: TimeInterval
    let completedTasks: Int
    let failedTasks: Int
    let averageSpeedRatio: Double
    let concurrency: Int
    
    var summary: String {
        return "\(completedTasks)/\(completedTasks + failedTasks) completed, \(String(format: "%.2f", averageSpeedRatio))x avg speed, \(String(format: "%.1f", totalProcessingTime))s total"
    }
}

// MARK: - Performance Baselines

struct PerformanceBaselines {
    let webVersionBaseline: TranscriptionPerformanceResult
    
    init() {
        // These would be established from actual web version measurements
        self.webVersionBaseline = TranscriptionPerformanceResult(
            fileName: "benchmark_5min.wav",
            model: "base.en",
            processingTime: 150.0, // 2.5 minutes for 5 minute file
            realTimeSpeedRatio: 2.0, // 2x real-time speed
            peakMemoryMB: 800, // 800MB peak memory
            outputContent: nil
        )
    }
}

// MARK: - Async Utilities

actor AsyncSemaphore {
    private var count: Int
    private var waiters: [CheckedContinuation<Void, Never>] = []
    
    init(value: Int) {
        self.count = value
    }
    
    func wait() async {
        if count > 0 {
            count -= 1
        } else {
            await withCheckedContinuation { continuation in
                waiters.append(continuation)
            }
        }
    }
    
    func signal() {
        if waiters.isEmpty {
            count += 1
        } else {
            let waiter = waiters.removeFirst()
            waiter.resume()
        }
    }
}