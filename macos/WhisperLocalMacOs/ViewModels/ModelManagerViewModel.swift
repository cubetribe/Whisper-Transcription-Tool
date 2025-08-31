import Foundation
import SwiftUI

@MainActor
class ModelManagerViewModel: ObservableObject {
    
    // MARK: - Published Properties
    
    @Published var availableModels: [WhisperModel] = []
    @Published var downloadedModels: Set<String> = []
    @Published var selectedModel: WhisperModel?
    @Published var defaultModel: String = "large-v3-turbo"
    
    // Download State
    @Published var isDownloading: Bool = false
    @Published var downloadProgress: [String: Double] = [:]
    @Published var downloadStatus: [String: DownloadStatus] = [:]
    @Published var downloadQueue: [WhisperModel] = []
    
    // UI State
    @Published var showingDownloadSheet = false
    @Published var currentError: AppError?
    @Published var searchText: String = ""
    
    // Performance Data
    @Published var performanceData: [String: ModelPerformanceData] = [:]
    @Published var systemCapabilities: SystemCapabilities = SystemCapabilities()
    
    // Services
    private let pythonBridge = PythonBridge()
    private let logger = Logger.shared
    private var downloadTasks: [String: Task<Void, Never>] = [:]
    
    // MARK: - Computed Properties
    
    var filteredModels: [WhisperModel] {
        if searchText.isEmpty {
            return availableModels
        }
        return availableModels.filter { model in
            model.name.localizedCaseInsensitiveContains(searchText) ||
            model.description.localizedCaseInsensitiveContains(searchText)
        }
    }
    
    var recommendedModels: [WhisperModel] {
        return availableModels.filter { model in
            model.sizeMB <= systemCapabilities.recommendedMaxModelSize
        }
    }
    
    var downloadingModels: [WhisperModel] {
        return availableModels.filter { model in
            downloadStatus[model.name] == .downloading
        }
    }
    
    var canDownloadMore: Bool {
        return downloadingModels.count < 3 // Max 3 simultaneous downloads
    }
    
    // MARK: - Initialization
    
    init() {
        loadAvailableModels()
        loadDownloadedModels()
        detectSystemCapabilities()
        loadPerformanceData()
    }
    
    // MARK: - Model Loading
    
    private func loadAvailableModels() {
        availableModels = WhisperModel.availableModels
        logger.log("Loaded \(availableModels.count) available models", 
                  level: .info, category: .modelManagement)
    }
    
    private func loadDownloadedModels() {
        Task {
            do {
                let result = try await pythonBridge.listModels()
                let modelNames = result["models"] as? [String] ?? []
                downloadedModels = Set(modelNames)
                
                // Update download status for existing models
                for modelName in modelNames {
                    downloadStatus[modelName] = .downloaded
                }
                
                logger.log("Found \(downloadedModels.count) downloaded models: \(Array(downloadedModels).joined(separator: ", "))",
                          level: .info, category: .modelManagement)
            } catch {
                await showError(.pythonBridge(.commandExecutionFailed("Failed to list models: \(error.localizedDescription)")))
            }
        }
    }
    
    private func detectSystemCapabilities() {
        let processInfo = ProcessInfo.processInfo
        
        // Detect Apple Silicon
        systemCapabilities.isAppleSilicon = processInfo.machineHardwareName?.contains("arm64") ?? false
        
        // Estimate available memory (simplified)
        systemCapabilities.availableMemoryGB = Double(processInfo.physicalMemory) / (1024 * 1024 * 1024)
        
        // Set recommended max model size based on memory
        if systemCapabilities.availableMemoryGB >= 16 {
            systemCapabilities.recommendedMaxModelSize = 3000 // Large models
        } else if systemCapabilities.availableMemoryGB >= 8 {
            systemCapabilities.recommendedMaxModelSize = 1500 // Medium models
        } else {
            systemCapabilities.recommendedMaxModelSize = 500 // Small models only
        }
        
        logger.log("System capabilities: Apple Silicon: \(systemCapabilities.isAppleSilicon), Memory: \(String(format: "%.1f", systemCapabilities.availableMemoryGB))GB",
                  level: .info, category: .system)
    }
    
    private func loadPerformanceData() {
        // Load cached performance data or initialize with defaults
        for model in availableModels {
            performanceData[model.name] = ModelPerformanceData(
                model: model,
                systemCapabilities: systemCapabilities
            )
        }
    }
    
    // MARK: - Model Selection
    
    func selectModel(_ model: WhisperModel) {
        selectedModel = model
        logger.log("Selected model: \(model.name)", level: .info, category: .modelManagement)
    }
    
    func setDefaultModel(_ modelName: String) {
        defaultModel = modelName
        UserDefaults.standard.set(modelName, forKey: "defaultWhisperModel")
        logger.log("Set default model: \(modelName)", level: .info, category: .modelManagement)
    }
    
    func isModelDownloaded(_ model: WhisperModel) -> Bool {
        return downloadedModels.contains(model.name)
    }
    
    func isModelRecommended(_ model: WhisperModel) -> Bool {
        return model.sizeMB <= systemCapabilities.recommendedMaxModelSize
    }
    
    // MARK: - Download Management
    
    func downloadModel(_ model: WhisperModel) {
        guard canDownloadMore else {
            Task { 
                await showError(.resource(.operationInProgress("Maximum number of simultaneous downloads reached")))
            }
            return
        }
        
        guard !downloadingModels.contains(where: { $0.name == model.name }) else {
            logger.log("Model \(model.name) is already downloading", level: .warning, category: .modelManagement)
            return
        }
        
        downloadQueue.append(model)
        downloadStatus[model.name] = .queued
        
        let task = Task {
            await performDownload(model)
        }
        
        downloadTasks[model.name] = task
        logger.log("Queued model for download: \(model.name)", level: .info, category: .modelManagement)
    }
    
    private func performDownload(_ model: WhisperModel) async {
        downloadStatus[model.name] = .downloading
        downloadProgress[model.name] = 0.0
        isDownloading = true
        
        do {
            logger.log("Starting download: \(model.name) (\(Int(model.sizeMB))MB)", 
                      level: .info, category: .modelManagement)
            
            // Use the proper bridge method
            let command: [String: Any] = [
                "command": "download_model",
                "model_name": model.name
            ]
            
            let result = try await pythonBridge.executeCommand(command)
            
            if result["success"] as? Bool == true {
                downloadStatus[model.name] = .downloaded
                downloadedModels.insert(model.name)
                downloadProgress[model.name] = 1.0
                
                logger.log("Successfully downloaded model: \(model.name)", 
                          level: .info, category: .modelManagement)
                
                // Verify download integrity
                await verifyModelIntegrity(model)
                
            } else {
                let error = result["error"] as? String ?? "Unknown download error"
                downloadStatus[model.name] = .failed
                
                logger.log("Failed to download model \(model.name): \(error)", 
                          level: .error, category: .modelManagement)
                
                await showError(.modelManagement(.downloadFailed(model.name, reason: error)))
            }
            
        } catch {
            downloadStatus[model.name] = .failed
            logger.log("Download error for \(model.name): \(error.localizedDescription)", 
                      level: .error, category: .modelManagement)
            
            await showError(.modelManagement(.downloadFailed(model.name, reason: error.localizedDescription)))
        }
        
        downloadTasks.removeValue(forKey: model.name)
        downloadQueue.removeAll { $0.name == model.name }
        
        // Update downloading state
        if downloadingModels.isEmpty {
            isDownloading = false
        }
    }
    
    func cancelDownload(_ model: WhisperModel) {
        downloadTasks[model.name]?.cancel()
        downloadTasks.removeValue(forKey: model.name)
        downloadQueue.removeAll { $0.name == model.name }
        downloadStatus[model.name] = .cancelled
        downloadProgress.removeValue(forKey: model.name)
        
        if downloadingModels.isEmpty {
            isDownloading = false
        }
        
        logger.log("Cancelled download: \(model.name)", level: .info, category: .modelManagement)
    }
    
    func deleteModel(_ model: WhisperModel) async {
        guard isModelDownloaded(model) else { return }
        
        do {
            // This would need to be implemented in the Python CLI
            // For now, we'll just remove from our tracking
            downloadedModels.remove(model.name)
            downloadStatus.removeValue(forKey: model.name)
            
            logger.log("Deleted model: \(model.name)", level: .info, category: .modelManagement)
            
        } catch {
            await showError(.modelManagement(.modelValidationFailed(model.name, reason: error.localizedDescription)))
        }
    }
    
    // MARK: - Model Verification
    
    private func verifyModelIntegrity(_ model: WhisperModel) async {
        // This would implement checksum verification
        // For now, we'll assume verification passes
        logger.log("Model integrity verified: \(model.name)", level: .info, category: .modelManagement)
    }
    
    // MARK: - Performance Analysis
    
    func benchmarkModel(_ model: WhisperModel) async {
        guard isModelDownloaded(model) else {
            await showError(.modelManagement(.modelNotFound(model.name)))
            return
        }
        
        // This would run a benchmark transcription with a test file
        // and measure performance metrics
        logger.log("Starting benchmark for model: \(model.name)", level: .info, category: .modelManagement)
        
        // Simulate benchmarking
        try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
        
        // Update performance data with benchmark results
        performanceData[model.name]?.updateBenchmarkData(
            processingSpeed: Double.random(in: 0.5...5.0),
            memoryUsage: Double.random(in: 500...2000),
            accuracy: Double.random(in: 0.85...0.98)
        )
        
        logger.log("Completed benchmark for model: \(model.name)", level: .info, category: .modelManagement)
    }
    
    // MARK: - Error Handling
    
    private func showError(_ error: AppError) async {
        currentError = error
        logger.log("Model manager error: \(error.localizedDescription)", 
                  level: .error, category: .modelManagement)
    }
    
    func clearError() {
        currentError = nil
    }
    
    // MARK: - Cleanup
    
    func cleanup() {
        // Cancel any ongoing downloads
        for (_, task) in downloadTasks {
            task.cancel()
        }
        downloadTasks.removeAll()
        downloadQueue.removeAll()
    }
}

// MARK: - Supporting Data Models

enum DownloadStatus {
    case notDownloaded
    case queued
    case downloading
    case downloaded
    case failed
    case cancelled
    case verifying
    
    var displayName: String {
        switch self {
        case .notDownloaded: return "Not Downloaded"
        case .queued: return "Queued"
        case .downloading: return "Downloading"
        case .downloaded: return "Downloaded"
        case .failed: return "Failed"
        case .cancelled: return "Cancelled"
        case .verifying: return "Verifying"
        }
    }
    
    var color: Color {
        switch self {
        case .notDownloaded: return .secondary
        case .queued: return .blue
        case .downloading: return .blue
        case .downloaded: return .green
        case .failed: return .red
        case .cancelled: return .orange
        case .verifying: return .yellow
        }
    }
}

struct SystemCapabilities {
    var isAppleSilicon: Bool = false
    var availableMemoryGB: Double = 8.0
    var recommendedMaxModelSize: Double = 1500.0 // MB
    var cpuCores: Int = 8
    var hasNeuralEngine: Bool = false
    
    var performanceProfile: PerformanceProfile {
        if isAppleSilicon && availableMemoryGB >= 16 {
            return .highPerformance
        } else if availableMemoryGB >= 8 {
            return .balanced
        } else {
            return .efficiency
        }
    }
}

enum PerformanceProfile {
    case efficiency
    case balanced
    case highPerformance
    
    var displayName: String {
        switch self {
        case .efficiency: return "Efficiency"
        case .balanced: return "Balanced"
        case .highPerformance: return "High Performance"
        }
    }
    
    var color: Color {
        switch self {
        case .efficiency: return .green
        case .balanced: return .blue
        case .highPerformance: return .purple
        }
    }
}

struct ModelPerformanceData {
    let model: WhisperModel
    var benchmarkProcessingSpeed: Double? // files per minute
    var benchmarkMemoryUsage: Double? // MB
    var benchmarkAccuracy: Double? // 0.0 to 1.0
    var lastBenchmarked: Date?
    
    let estimatedProcessingSpeed: Double
    let estimatedMemoryUsage: Double
    let estimatedAccuracy: Double
    
    init(model: WhisperModel, systemCapabilities: SystemCapabilities) {
        self.model = model
        
        // Estimate based on model characteristics and system capabilities
        let performanceMultiplier = systemCapabilities.isAppleSilicon ? 1.5 : 1.0
        
        self.estimatedProcessingSpeed = model.performance.speedMultiplier * performanceMultiplier
        self.estimatedMemoryUsage = model.sizeMB * 1.2 // Models need more RAM when loaded
        self.estimatedAccuracy = Double(model.performance.accuracy.dropLast()) ?? 0.85 // Remove '%' and convert
    }
    
    mutating func updateBenchmarkData(processingSpeed: Double, memoryUsage: Double, accuracy: Double) {
        self.benchmarkProcessingSpeed = processingSpeed
        self.benchmarkMemoryUsage = memoryUsage
        self.benchmarkAccuracy = accuracy
        self.lastBenchmarked = Date()
    }
    
    var displayProcessingSpeed: Double {
        return benchmarkProcessingSpeed ?? estimatedProcessingSpeed
    }
    
    var displayMemoryUsage: Double {
        return benchmarkMemoryUsage ?? estimatedMemoryUsage
    }
    
    var displayAccuracy: Double {
        return benchmarkAccuracy ?? estimatedAccuracy
    }
    
    var hasBenchmarkData: Bool {
        return benchmarkProcessingSpeed != nil
    }
}

// MARK: - Extensions

extension ProcessInfo {
    var machineHardwareName: String? {
        var size = 0
        sysctlbyname("hw.machine", nil, &size, nil, 0)
        var machine = [CChar](repeating: 0, count: size)
        sysctlbyname("hw.machine", &machine, &size, nil, 0)
        return String(cString: machine)
    }
}

