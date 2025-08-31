import XCTest
import Foundation
@testable import WhisperLocalMacOs

@MainActor
class ViewModelTests: XCTestCase {
    
    // MARK: - TranscriptionViewModel Tests
    
    func testTranscriptionViewModel_InitialState() {
        let viewModel = TranscriptionViewModel()
        
        XCTAssertNil(viewModel.selectedFile)
        XCTAssertNil(viewModel.outputDirectory)
        XCTAssertEqual(viewModel.selectedModel, "large-v3-turbo")
        XCTAssertEqual(viewModel.selectedFormats, [.txt, .srt])
        XCTAssertEqual(viewModel.selectedLanguage, "auto")
        XCTAssertFalse(viewModel.isTranscribing)
        XCTAssertEqual(viewModel.transcriptionProgress, 0.0)
        XCTAssertTrue(viewModel.progressMessage.isEmpty)
        XCTAssertNil(viewModel.currentTask)
        XCTAssertNil(viewModel.lastResult)
        XCTAssertNil(viewModel.currentError)
        XCTAssertFalse(viewModel.showingError)
        XCTAssertTrue(viewModel.transcriptionQueue.isEmpty)
        XCTAssertFalse(viewModel.isProcessing)
        XCTAssertFalse(viewModel.isPaused)
        XCTAssertEqual(viewModel.batchProgress, 0.0)
        XCTAssertTrue(viewModel.batchMessage.isEmpty)
    }
    
    func testTranscriptionViewModel_CanStartTranscription() {
        let viewModel = TranscriptionViewModel()
        
        // Initially should not be able to start
        XCTAssertFalse(viewModel.canStartTranscription)
        
        // Set selected file
        let tempFile = URL(fileURLWithPath: "/tmp/test.mp3")
        viewModel.selectedFile = tempFile
        XCTAssertFalse(viewModel.canStartTranscription) // Still missing output directory
        
        // Set output directory
        let tempDir = URL(fileURLWithPath: "/tmp")
        viewModel.outputDirectory = tempDir
        XCTAssertTrue(viewModel.canStartTranscription) // Should now be able to start
        
        // Test when transcribing
        viewModel.isTranscribing = true
        XCTAssertFalse(viewModel.canStartTranscription)
        viewModel.isTranscribing = false
        
        // Test with empty formats
        viewModel.selectedFormats = []
        XCTAssertFalse(viewModel.canStartTranscription)
    }
    
    func testTranscriptionViewModel_RemoveSelectedFile() {
        let viewModel = TranscriptionViewModel()
        let tempFile = URL(fileURLWithPath: "/tmp/test.mp3")
        
        viewModel.selectedFile = tempFile
        viewModel.currentTask = TranscriptionTask(
            inputURL: tempFile,
            outputDirectory: URL(fileURLWithPath: "/tmp"),
            model: "large-v3-turbo",
            formats: [.txt]
        )
        viewModel.transcriptionProgress = 0.5
        viewModel.progressMessage = "Test message"
        
        viewModel.removeSelectedFile()
        
        XCTAssertNil(viewModel.selectedFile)
        XCTAssertNil(viewModel.currentTask)
        XCTAssertNil(viewModel.lastResult)
        XCTAssertEqual(viewModel.transcriptionProgress, 0.0)
        XCTAssertTrue(viewModel.progressMessage.isEmpty)
    }
    
    func testTranscriptionViewModel_BatchProcessing() {
        let viewModel = TranscriptionViewModel()
        let tempDir = URL(fileURLWithPath: "/tmp")
        viewModel.outputDirectory = tempDir
        
        // Initially should not be able to start batch
        XCTAssertFalse(viewModel.canStartBatch)
        XCTAssertEqual(viewModel.completedTasksCount, 0)
        XCTAssertEqual(viewModel.failedTasksCount, 0)
        XCTAssertFalse(viewModel.hasCompletedTasks)
        
        // Add some tasks
        let task1 = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test1.mp3"), outputDirectory: tempDir, model: "base", formats: [.txt])
        let task2 = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test2.mp3"), outputDirectory: tempDir, model: "base", formats: [.txt])
        
        viewModel.transcriptionQueue = [task1, task2]
        XCTAssertTrue(viewModel.canStartBatch)
        
        // Test batch controls
        XCTAssertFalse(viewModel.canPauseBatch) // Not processing yet
        
        viewModel.isProcessing = true
        XCTAssertTrue(viewModel.canPauseBatch)
        
        viewModel.isPaused = true
        XCTAssertFalse(viewModel.canPauseBatch) // Already paused
    }
    
    func testTranscriptionViewModel_TaskManagement() {
        let viewModel = TranscriptionViewModel()
        let tempDir = URL(fileURLWithPath: "/tmp")
        viewModel.outputDirectory = tempDir
        
        let task1 = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test1.mp3"), outputDirectory: tempDir, model: "base", formats: [.txt])
        let task2 = TranscriptionTask(inputURL: URL(fileURLWithPath: "/tmp/test2.mp3"), outputDirectory: tempDir, model: "base", formats: [.txt])
        
        viewModel.transcriptionQueue = [task1, task2]
        XCTAssertEqual(viewModel.transcriptionQueue.count, 2)
        
        // Test removing task
        viewModel.removeTask(task1)
        XCTAssertEqual(viewModel.transcriptionQueue.count, 1)
        XCTAssertEqual(viewModel.transcriptionQueue.first?.id, task2.id)
        
        // Test retry task
        viewModel.transcriptionQueue[0].status = .failed
        viewModel.retryTask(viewModel.transcriptionQueue[0])
        XCTAssertEqual(viewModel.transcriptionQueue[0].status, .pending)
        XCTAssertEqual(viewModel.transcriptionQueue[0].progress, 0.0)
        
        // Test clearing tasks
        viewModel.transcriptionQueue[0].status = .completed
        viewModel.clearCompletedTasks()
        XCTAssertTrue(viewModel.transcriptionQueue.isEmpty)
    }
    
    func testTranscriptionViewModel_ResetTranscription() {
        let viewModel = TranscriptionViewModel()
        
        // Set some values
        viewModel.selectedFile = URL(fileURLWithPath: "/tmp/test.mp3")
        viewModel.outputDirectory = URL(fileURLWithPath: "/tmp")
        viewModel.selectedModel = "base"
        viewModel.selectedFormats = [.srt]
        viewModel.selectedLanguage = "en"
        viewModel.transcriptionProgress = 0.5
        viewModel.progressMessage = "Test"
        viewModel.currentError = .userInput(.noFileSelected)
        viewModel.showingError = true
        
        viewModel.resetTranscription()
        
        XCTAssertNil(viewModel.selectedFile)
        XCTAssertNil(viewModel.outputDirectory)
        XCTAssertEqual(viewModel.selectedModel, "large-v3-turbo")
        XCTAssertEqual(viewModel.selectedFormats, [.txt, .srt])
        XCTAssertEqual(viewModel.selectedLanguage, "auto")
        XCTAssertEqual(viewModel.transcriptionProgress, 0.0)
        XCTAssertTrue(viewModel.progressMessage.isEmpty)
        XCTAssertNil(viewModel.currentError)
        XCTAssertFalse(viewModel.showingError)
    }
    
    func testTranscriptionViewModel_ErrorHandling() {
        let viewModel = TranscriptionViewModel()
        
        XCTAssertNil(viewModel.currentError)
        XCTAssertFalse(viewModel.showingError)
        
        // This would be called internally - we can't test the private method directly
        // but we can test the clearError public method
        viewModel.currentError = .userInput(.noFileSelected)
        viewModel.showingError = true
        
        viewModel.clearError()
        
        XCTAssertNil(viewModel.currentError)
        XCTAssertFalse(viewModel.showingError)
    }
    
    // MARK: - ModelManagerViewModel Tests
    
    func testModelManagerViewModel_InitialState() {
        let viewModel = ModelManagerViewModel()
        
        XCTAssertFalse(viewModel.availableModels.isEmpty) // Should load WhisperModel.availableModels
        XCTAssertTrue(viewModel.downloadedModels.isEmpty) // Initially empty, loads async
        XCTAssertNil(viewModel.selectedModel)
        XCTAssertEqual(viewModel.defaultModel, "large-v3-turbo")
        XCTAssertFalse(viewModel.isDownloading)
        XCTAssertTrue(viewModel.downloadProgress.isEmpty)
        XCTAssertTrue(viewModel.downloadStatus.isEmpty)
        XCTAssertTrue(viewModel.downloadQueue.isEmpty)
        XCTAssertFalse(viewModel.showingDownloadSheet)
        XCTAssertNil(viewModel.currentError)
        XCTAssertTrue(viewModel.searchText.isEmpty)
        XCTAssertTrue(viewModel.performanceData.isEmpty)
    }
    
    func testModelManagerViewModel_FilteredModels() {
        let viewModel = ModelManagerViewModel()
        
        // With empty search, should return all models
        XCTAssertEqual(viewModel.filteredModels.count, viewModel.availableModels.count)
        
        // With search text, should filter
        viewModel.searchText = "large"
        let filteredCount = viewModel.filteredModels.count
        let allLargeModels = viewModel.availableModels.filter { $0.name.localizedCaseInsensitiveContains("large") }
        XCTAssertEqual(filteredCount, allLargeModels.count)
        
        // With non-matching search, should return empty
        viewModel.searchText = "nonexistent"
        XCTAssertTrue(viewModel.filteredModels.isEmpty)
    }
    
    func testModelManagerViewModel_DownloadLimits() {
        let viewModel = ModelManagerViewModel()
        
        XCTAssertTrue(viewModel.canDownloadMore) // Initially should be able to download
        
        // Simulate 3 downloads in progress (max allowed)
        viewModel.downloadStatus["model1"] = .downloading
        viewModel.downloadStatus["model2"] = .downloading
        viewModel.downloadStatus["model3"] = .downloading
        
        XCTAssertFalse(viewModel.canDownloadMore) // Should reach limit
    }
    
    // MARK: - ChatbotViewModel Tests
    
    func testChatbotViewModel_InitialState() {
        let viewModel = ChatbotViewModel()
        
        XCTAssertTrue(viewModel.messages.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertTrue(viewModel.searchResults.isEmpty)
        XCTAssertFalse(viewModel.isSearching)
        XCTAssertTrue(viewModel.currentQuery.isEmpty)
        XCTAssertEqual(viewModel.selectedDateFilter, .all)
        XCTAssertEqual(viewModel.selectedFileTypeFilter, .all)
        XCTAssertEqual(viewModel.searchThreshold, 0.3, accuracy: 0.001)
    }
    
    func testChatbotViewModel_DateFilter() {
        let viewModel = ChatbotViewModel()
        
        // Test all filter
        XCTAssertNil(viewModel.selectedDateFilter.dateRange)
        
        // Test today filter
        viewModel.selectedDateFilter = .today
        let todayRange = viewModel.selectedDateFilter.dateRange
        XCTAssertNotNil(todayRange)
        
        let calendar = Calendar.current
        let now = Date()
        let startOfDay = calendar.startOfDay(for: now)
        XCTAssertEqual(todayRange?.start, startOfDay)
        XCTAssertLessThanOrEqual(abs(todayRange!.end.timeIntervalSince(now)), 1.0) // Within 1 second
        
        // Test week filter
        viewModel.selectedDateFilter = .week
        let weekRange = viewModel.selectedDateFilter.dateRange
        XCTAssertNotNil(weekRange)
        XCTAssertLessThan(weekRange!.start, now)
        XCTAssertGreaterThan(weekRange!.duration, 6 * 24 * 3600) // At least 6 days
    }
    
    func testChatbotViewModel_FileTypeFilter() {
        let viewModel = ChatbotViewModel()
        
        // Test all filter
        XCTAssertNil(viewModel.selectedFileTypeFilter.allowedExtensions)
        
        // Test audio filter
        viewModel.selectedFileTypeFilter = .audio
        let audioExtensions = viewModel.selectedFileTypeFilter.allowedExtensions
        XCTAssertNotNil(audioExtensions)
        XCTAssertTrue(audioExtensions!.contains("mp3"))
        XCTAssertTrue(audioExtensions!.contains("wav"))
        
        // Test video filter
        viewModel.selectedFileTypeFilter = .video
        let videoExtensions = viewModel.selectedFileTypeFilter.allowedExtensions
        XCTAssertNotNil(videoExtensions)
        XCTAssertTrue(videoExtensions!.contains("mp4"))
        XCTAssertTrue(videoExtensions!.contains("mov"))
    }
    
    func testChatbotViewModel_MessageHandling() {
        let viewModel = ChatbotViewModel()
        
        XCTAssertTrue(viewModel.messages.isEmpty)
        
        // Test empty message (should be ignored)
        viewModel.sendMessage("")
        XCTAssertTrue(viewModel.messages.isEmpty)
        
        viewModel.sendMessage("   ")
        XCTAssertTrue(viewModel.messages.isEmpty)
        
        // Test valid message
        viewModel.sendMessage("Hello, world!")
        XCTAssertEqual(viewModel.messages.count, 1)
        XCTAssertEqual(viewModel.messages.first?.content, "Hello, world!")
        XCTAssertEqual(viewModel.messages.first?.type, .user)
        XCTAssertEqual(viewModel.currentQuery, "Hello, world!")
        
        // Test clear chat
        viewModel.clearChat()
        XCTAssertTrue(viewModel.messages.isEmpty)
        XCTAssertTrue(viewModel.currentQuery.isEmpty)
    }
}

// MARK: - Mock Classes and Extensions

extension TranscriptionTask {
    // Test helper for creating tasks
    static func testTask() -> TranscriptionTask {
        return TranscriptionTask(
            inputURL: URL(fileURLWithPath: "/tmp/test.mp3"),
            outputDirectory: URL(fileURLWithPath: "/tmp"),
            model: "base",
            formats: [.txt]
        )
    }
}

// MARK: - Download Status for Testing

enum DownloadStatus {
    case notDownloaded
    case downloading
    case downloaded
    case failed
}

// MARK: - Model Performance Data for Testing

struct ModelPerformanceData {
    let averageSpeed: Double
    let memoryUsage: Int64
    let accuracy: Double
}

// MARK: - System Capabilities for Testing

struct SystemCapabilities {
    let totalMemory: Int64
    let availableMemory: Int64
    let processorCount: Int
    let recommendedMaxModelSize: Int64
    
    init() {
        let processInfo = ProcessInfo.processInfo
        self.totalMemory = Int64(processInfo.physicalMemory)
        self.availableMemory = totalMemory / 2 // Simplified
        self.processorCount = processInfo.processorCount
        self.recommendedMaxModelSize = totalMemory > 8_000_000_000 ? 3000 : 1500 // 3GB for 8GB+ systems
    }
}

// MARK: - Chat Message Types

struct ChatMessage: Identifiable, Codable {
    let id: UUID
    let content: String
    let type: MessageType
    let timestamp: Date
    
    enum MessageType: String, Codable {
        case user
        case assistant
        case system
    }
}

// MARK: - Search Result Types

struct TranscriptionSearchResult: Identifiable, Codable {
    let id: UUID
    let content: String
    let sourceFile: String
    let timestamp: TimeInterval?
    let score: Double
    let metadata: [String: String]
    
    init(content: String, sourceFile: String, timestamp: TimeInterval? = nil, score: Double = 0.0, metadata: [String: String] = [:]) {
        self.id = UUID()
        self.content = content
        self.sourceFile = sourceFile
        self.timestamp = timestamp
        self.score = score
        self.metadata = metadata
    }
}

// MARK: - Chat History Manager Mock

class ChatHistoryManager {
    private var history: [ChatMessage] = []
    
    func addMessage(_ message: ChatMessage) {
        history.append(message)
    }
    
    func getHistory() -> [ChatMessage] {
        return history
    }
    
    func clearHistory() {
        history.removeAll()
    }
}

// MARK: - Mock Dependency Manager

class MockDependencyManager {
    static let shared = MockDependencyManager()
    var mockStatus: DependencyStatus = .valid
    
    func validateDependencies() -> DependencyStatus {
        return mockStatus
    }
}

enum DependencyStatus {
    case valid
    case invalid
    case unknown
}