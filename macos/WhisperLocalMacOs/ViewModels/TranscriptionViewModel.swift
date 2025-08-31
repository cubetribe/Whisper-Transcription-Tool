import Foundation
import SwiftUI
import AppKit

@MainActor
class TranscriptionViewModel: ObservableObject {
    
    // MARK: - Published Properties
    
    @Published var selectedFile: URL?
    @Published var outputDirectory: URL?
    @Published var selectedModel: String = "large-v3-turbo"
    @Published var selectedFormats: Set<OutputFormat> = [.txt, .srt]
    @Published var selectedLanguage: String = "auto"
    
    // Progress and State
    @Published var isTranscribing: Bool = false
    @Published var transcriptionProgress: Double = 0.0
    @Published var progressMessage: String = ""
    @Published var currentTask: TranscriptionTask?
    @Published var lastResult: TranscriptionResult?
    
    // Error handling
    @Published var currentError: AppError?
    @Published var showingError: Bool = false
    
    // Batch Processing
    @Published var transcriptionQueue: [TranscriptionTask] = []
    @Published var isProcessing: Bool = false
    @Published var isPaused: Bool = false
    @Published var batchProgress: Double = 0.0
    @Published var batchMessage: String = ""
    
    // Services
    private let pythonBridge = PythonBridge()
    private let logger = Logger.shared
    
    // MARK: - Computed Properties
    
    var canStartTranscription: Bool {
        return selectedFile != nil && 
               outputDirectory != nil && 
               !isTranscribing &&
               !selectedFormats.isEmpty
    }
    
    // Batch Processing Computed Properties
    var canStartBatch: Bool {
        return !transcriptionQueue.isEmpty &&
               !isProcessing &&
               transcriptionQueue.contains { $0.status == .pending }
    }
    
    var canPauseBatch: Bool {
        return isProcessing && !isPaused
    }
    
    var completedTasksCount: Int {
        return transcriptionQueue.filter { $0.status == .completed }.count
    }
    
    var failedTasksCount: Int {
        return transcriptionQueue.filter { $0.status == .failed }.count
    }
    
    var hasCompletedTasks: Bool {
        return transcriptionQueue.contains { $0.status == .completed || $0.status == .failed || $0.status == .cancelled }
    }
    
    var availableModels: [WhisperModel] {
        return WhisperModel.availableModels
    }
    
    var supportedLanguages: [String: String] {
        return [
            "auto": "Auto-detect",
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "tr": "Turkish"
        ]
    }
    
    // MARK: - File Selection
    
    func selectAudioFile() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [
            .audio, .mpeg4Audio, .mp3, 
            .movie, .mpeg4Movie, .quickTimeMovie, .avi
        ]
        panel.title = "Select Audio or Video File"
        panel.message = "Choose an audio or video file to transcribe"
        
        if panel.runModal() == .OK, let url = panel.urls.first {
            selectedFile = url
            logger.log("Selected file for transcription: \(url.lastPathComponent)", 
                      level: .info, category: .transcription)
            
            // Auto-select output directory based on file location
            if outputDirectory == nil {
                outputDirectory = url.deletingLastPathComponent()
            }
        }
    }
    
    func selectOutputDirectory() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.title = "Select Output Directory"
        panel.message = "Choose where to save transcription files"
        
        if panel.runModal() == .OK, let url = panel.urls.first {
            outputDirectory = url
            logger.log("Selected output directory: \(url.path)", 
                      level: .info, category: .transcription)
        }
    }
    
    func removeSelectedFile() {
        selectedFile = nil
        currentTask = nil
        lastResult = nil
        transcriptionProgress = 0.0
        progressMessage = ""
        logger.log("Removed selected file", level: .info, category: .ui)
    }
    
    // MARK: - Transcription Control
    
    func startTranscription() async {
        guard let inputFile = selectedFile,
              let outputDir = outputDirectory else {
            await showError(.userInput(.emptyFileQueue))
            return
        }
        
        do {
            isTranscribing = true
            transcriptionProgress = 0.0
            progressMessage = "Preparing transcription..."
            
            // Create transcription task
            currentTask = TranscriptionTask(
                inputURL: inputFile,
                outputDirectory: outputDir,
                model: selectedModel,
                formats: Array(selectedFormats)
            )
            
            guard let task = currentTask else {
                await showError(.userInput(.invalidBatchConfiguration("Failed to create transcription task")))
                return
            }
            
            logger.log("Starting transcription: \(inputFile.lastPathComponent) -> \(selectedFormats.map(\.rawValue).joined(separator: ", "))", 
                      level: .info, category: .transcription)
            
            // Update progress
            progressMessage = "Transcribing with \(selectedModel)..."
            transcriptionProgress = 0.1
            
            // Start transcription via PythonBridge
            let result = try await pythonBridge.transcribeFile(task)
            
            // Update UI with result
            lastResult = result
            transcriptionProgress = 1.0
            progressMessage = result.success ? "Transcription completed successfully!" : "Transcription failed"
            
            if result.success {
                logger.log("Transcription completed successfully: \(result.outputFiles.count) files created", 
                          level: .info, category: .transcription)
            } else {
                logger.log("Transcription failed: \(result.error ?? "Unknown error")", 
                          level: .error, category: .transcription)
            }
            
        } catch {
            await handleTranscriptionError(error)
        }
        
        isTranscribing = false
    }
    
    func cancelTranscription() {
        // TODO: Implement cancellation via PythonBridge
        isTranscribing = false
        transcriptionProgress = 0.0
        progressMessage = "Transcription cancelled"
        logger.log("Transcription cancelled by user", level: .warning, category: .transcription)
    }
    
    // MARK: - Error Handling
    
    private func handleTranscriptionError(_ error: Error) async {
        logger.log("Transcription error: \(error.localizedDescription)", 
                  level: .error, category: .transcription)
        
        if let appError = error as? AppError {
            await showError(appError)
        } else {
            await showError(.pythonBridge(.processExecutionFailed(
                command: "transcribe", 
                exitCode: -1, 
                stderr: error.localizedDescription
            )))
        }
    }
    
    @MainActor
    private func showError(_ error: AppError) {
        currentError = error
        showingError = true
    }
    
    func clearError() {
        currentError = nil
        showingError = false
    }
    
    // MARK: - Convenience Methods
    
    func resetTranscription() {
        selectedFile = nil
        outputDirectory = nil
        currentTask = nil
        lastResult = nil
        transcriptionProgress = 0.0
        progressMessage = ""
        selectedFormats = [.txt, .srt]
        selectedModel = "large-v3-turbo"
        selectedLanguage = "auto"
        clearError()
        logger.log("Transcription view reset", level: .info, category: .ui)
    }
    
    // MARK: - Batch Processing Methods
    
    func addFilesToQueue() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [.audio, .movie, .mpeg4Movie, .quickTimeMovie, .avi]
        
        if let window = NSApplication.shared.keyWindow {
            panel.beginSheetModal(for: window) { [weak self] response in
                if response == .OK {
                    self?.processSelectedFiles(panel.urls)
                }
            }
        }
    }
    
    private func processSelectedFiles(_ urls: [URL]) {
        guard let outputDir = outputDirectory else {
            Task { await showError(.userInput(.noOutputDirectory)) }
            return
        }
        
        for url in urls {
            let task = TranscriptionTask(
                inputURL: url,
                outputDirectory: outputDir,
                model: selectedModel,
                formats: Array(selectedFormats)
            )
            transcriptionQueue.append(task)
        }
        
        logger.log("Added \(urls.count) files to batch queue", level: .info, category: .batchProcessingProcessing)
    }
    
    func removeTask(_ task: TranscriptionTask) {
        transcriptionQueue.removeAll { $0.id == task.id }
        updateBatchProgress()
        logger.log("Removed task from queue: \(task.inputURL.lastPathComponent)", level: .info, category: .batchProcessing)
    }
    
    func retryTask(_ task: TranscriptionTask) {
        if let index = transcriptionQueue.firstIndex(where: { $0.id == task.id }) {
            transcriptionQueue[index].status = .pending
            transcriptionQueue[index].progress = 0.0
            updateBatchProgress()
            logger.log("Retry task: \(task.inputURL.lastPathComponent)", level: .info, category: .batchProcessing)
        }
    }
    
    func revealTaskOutput(_ task: TranscriptionTask) {
        if task.status == .completed {
            NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: task.outputDirectory.path)
        }
    }
    
    func clearCompletedTasks() {
        transcriptionQueue.removeAll { task in
            task.status == .completed || task.status == .failed || task.status == .cancelled
        }
        updateBatchProgress()
        logger.log("Cleared completed tasks from queue", level: .info, category: .batchProcessing)
    }
    
    func clearAllTasks() {
        transcriptionQueue.removeAll()
        updateBatchProgress()
        logger.log("Cleared all tasks from queue", level: .info, category: .batchProcessing)
    }
    
    func processBatch() async {
        guard canStartBatch else { return }
        
        // Pre-processing checks
        guard await performResourceChecks() else {
            await showError(.resource(.insufficientDiskSpace))
            return
        }
        
        isProcessing = true
        isPaused = false
        batchMessage = "Starting batch processing..."
        logger.log("Starting batch processing: \(transcriptionQueue.count) files", level: .info, category: .batchProcessing)
        
        for (index, task) in transcriptionQueue.enumerated() {
            guard task.status == .pending else { continue }
            
            // Check for pause or cancellation
            if isPaused {
                batchMessage = "Batch processing paused"
                break
            }
            
            if !isProcessing {
                batchMessage = "Batch processing cancelled"
                break
            }
            
            // Update batch message
            batchMessage = "Processing \(index + 1) of \(transcriptionQueue.count): \(task.inputURL.lastPathComponent)"
            
            // Mark task as processing
            if let taskIndex = transcriptionQueue.firstIndex(where: { $0.id == task.id }) {
                transcriptionQueue[taskIndex].status = .processing
                transcriptionQueue[taskIndex].markStarted()
            }
            
            do {
                // Process the task
                let result = try await pythonBridge.transcribeFile(task)
                
                // Update task with result
                if let taskIndex = transcriptionQueue.firstIndex(where: { $0.id == task.id }) {
                    if result.success {
                        transcriptionQueue[taskIndex].markCompleted()
                        logger.log("Batch task completed: \(task.inputURL.lastPathComponent)", 
                                  level: .info, category: .batchProcessing)
                    } else {
                        transcriptionQueue[taskIndex].markFailed(result.error ?? "Unknown error")
                        logger.log("Batch task failed: \(task.inputURL.lastPathComponent) - \(result.error ?? "Unknown error")", 
                                  level: .error, category: .batchProcessing)
                    }
                }
                
            } catch {
                // Mark task as failed
                if let taskIndex = transcriptionQueue.firstIndex(where: { $0.id == task.id }) {
                    transcriptionQueue[taskIndex].markFailed(error.localizedDescription)
                }
                
                logger.log("Batch task error: \(task.inputURL.lastPathComponent) - \(error.localizedDescription)", 
                          level: .error, category: .batchProcessing)
                
                // Continue processing other files (error isolation)
                continue
            }
            
            updateBatchProgress()
        }
        
        isProcessing = false
        isPaused = false
        
        let completedCount = completedTasksCount
        let failedCount = failedTasksCount
        batchMessage = "Batch complete: \(completedCount) successful, \(failedCount) failed"
        
        logger.log("Batch processing completed: \(completedCount) successful, \(failedCount) failed", 
                  level: .info, category: .batchProcessing)
    }
    
    func pauseBatch() {
        isPaused = true
        batchMessage = "Pausing batch processing..."
        logger.log("Batch processing paused", level: .info, category: .batchProcessing)
    }
    
    func cancelBatch() {
        isProcessing = false
        isPaused = false
        batchMessage = "Cancelling batch processing..."
        
        // Mark all processing tasks as cancelled
        for index in transcriptionQueue.indices {
            if transcriptionQueue[index].status == .processing {
                transcriptionQueue[index].status = .cancelled
            }
        }
        
        updateBatchProgress()
        logger.log("Batch processing cancelled", level: .info, category: .batchProcessing)
    }
    
    private func updateBatchProgress() {
        let totalTasks = transcriptionQueue.count
        guard totalTasks > 0 else {
            batchProgress = 0.0
            return
        }
        
        let completedTasks = transcriptionQueue.filter { 
            $0.status == .completed || $0.status == .failed || $0.status == .cancelled 
        }.count
        
        batchProgress = Double(completedTasks) / Double(totalTasks)
    }
    
    // MARK: - Resource Management
    
    private func performResourceChecks() async -> Bool {
        // Check disk space
        guard let outputDir = outputDirectory else { return false }
        
        do {
            let resourceValues = try outputDir.resourceValues(forKeys: [.volumeAvailableCapacityKey])
            if let availableCapacity = resourceValues.volumeAvailableCapacity {
                // Require at least 1GB free space
                if availableCapacity < 1024 * 1024 * 1024 {
                    logger.log("Insufficient disk space: \(availableCapacity) bytes available", 
                              level: .warning, category: .system)
                    return false
                }
            }
        } catch {
            logger.log("Failed to check disk space: \(error.localizedDescription)", 
                      level: .error, category: .system)
            return false
        }
        
        // Check memory pressure (simplified)
        let processInfo = ProcessInfo.processInfo
        if processInfo.thermalState == .critical {
            logger.log("System thermal state is critical, delaying batch processing", 
                      level: .warning, category: .system)
            return false
        }
        
        return true
    }
    
    private func monitorResourceUsage() {
        // This could be expanded to monitor memory usage, CPU temperature, etc.
        // For now, we'll keep it simple and rely on OS process management
    }
    
    // MARK: - Batch Results Actions
    
    func openAllResults() {
        let completedTasks = transcriptionQueue.filter { $0.status == .completed }
        for task in completedTasks {
            if let firstOutputFile = task.outputFiles.first {
                NSWorkspace.shared.open(firstOutputFile)
            }
        }
        logger.log("Opened \(completedTasks.count) result files", level: .info, category: .ui)
    }
    
    func revealAllResults() {
        let completedTasks = transcriptionQueue.filter { $0.status == .completed }
        let outputDirectories = Set(completedTasks.map { $0.outputDirectory })
        
        for directory in outputDirectories {
            NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: directory.path)
        }
        logger.log("Revealed \(outputDirectories.count) result directories", level: .info, category: .ui)
    }
    
    func retryFailedTasks() {
        for index in transcriptionQueue.indices {
            if transcriptionQueue[index].status == .failed {
                transcriptionQueue[index].status = .pending
                transcriptionQueue[index].progress = 0.0
                transcriptionQueue[index].error = nil
                transcriptionQueue[index].startTime = nil
                transcriptionQueue[index].completionTime = nil
            }
        }
        updateBatchProgress()
        logger.log("Reset failed tasks for retry", level: .info, category: .batchProcessing)
    }
}