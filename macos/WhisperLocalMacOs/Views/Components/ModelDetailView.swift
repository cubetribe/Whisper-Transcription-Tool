import SwiftUI

struct ModelDetailView: View {
    let model: WhisperModel
    @ObservedObject var viewModel: ModelManagerViewModel
    @State private var showingBenchmarkResults = false
    
    private var isDownloaded: Bool {
        viewModel.isModelDownloaded(model)
    }
    
    private var downloadStatus: DownloadStatus {
        viewModel.downloadStatus[model.name] ?? .notDownloaded
    }
    
    private var downloadProgress: Double {
        viewModel.downloadProgress[model.name] ?? 0.0
    }
    
    private var performanceData: ModelPerformanceData? {
        viewModel.performanceData[model.name]
    }
    
    private var isDefault: Bool {
        viewModel.defaultModel == model.name
    }
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // Header Section
                ModelHeaderSection(
                    model: model,
                    downloadStatus: downloadStatus,
                    isDefault: isDefault,
                    isRecommended: viewModel.isModelRecommended(model)
                )
                
                // Action Buttons
                ModelActionButtons(
                    model: model,
                    isDownloaded: isDownloaded,
                    downloadStatus: downloadStatus,
                    downloadProgress: downloadProgress,
                    isDefault: isDefault,
                    onDownload: {
                        viewModel.downloadModel(model)
                    },
                    onCancel: {
                        viewModel.cancelDownload(model)
                    },
                    onDelete: {
                        Task {
                            await viewModel.deleteModel(model)
                        }
                    },
                    onSetDefault: {
                        viewModel.setDefaultModel(model.name)
                    }
                )
                
                Divider()
                
                // Model Specifications
                ModelSpecifications(model: model)
                
                if let perfData = performanceData {
                    Divider()
                    
                    // Performance Section
                    ModelPerformanceSection(
                        data: perfData,
                        onBenchmark: {
                            Task {
                                await viewModel.benchmarkModel(model)
                            }
                        },
                        onShowResults: {
                            showingBenchmarkResults = true
                        }
                    )
                }
                
                if isDownloaded {
                    Divider()
                    
                    // Usage Examples
                    ModelUsageExamples(model: model)
                }
                
                Divider()
                
                // Model Compatibility
                ModelCompatibilitySection(
                    model: model,
                    systemCapabilities: viewModel.systemCapabilities
                )
            }
            .padding(24)
        }
        .navigationTitle(model.name)
        .navigationBarTitleDisplayMode(.large)
        .sheet(isPresented: $showingBenchmarkResults) {
            if let perfData = performanceData {
                BenchmarkResultsSheet(model: model, performanceData: perfData)
            }
        }
    }
}

struct ModelHeaderSection: View {
    let model: WhisperModel
    let downloadStatus: DownloadStatus
    let isDefault: Bool
    let isRecommended: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Model Name and Badges
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(model.name)
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        if isRecommended {
                            RecommendedBadge()
                        }
                    }
                    
                    if isDefault {
                        DefaultModelBadge()
                    }
                }
                
                Spacer()
                
                // Large Status Badge
                VStack {
                    StatusBadge(status: downloadStatus, progress: 0)
                        .scaleEffect(1.2)
                }
            }
            
            // Description
            Text(model.description)
                .font(.body)
                .foregroundStyle(.secondary)
            
            // Key Stats
            HStack(spacing: 24) {
                StatItem(
                    label: "Size",
                    value: "\(Int(model.sizeMB)) MB",
                    icon: "arrow.down.circle"
                )
                
                StatItem(
                    label: "Speed",
                    value: "\(model.performance.speedMultiplier, specifier: "%.0f")x",
                    icon: "speedometer"
                )
                
                StatItem(
                    label: "Accuracy",
                    value: model.performance.accuracy,
                    icon: "target"
                )
                
                StatItem(
                    label: "Memory",
                    value: model.performance.memoryUsage,
                    icon: "memorychip"
                )
            }
        }
    }
}

struct RecommendedBadge: View {
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "star.fill")
                .font(.caption)
            Text("RECOMMENDED")
                .font(.caption2)
                .fontWeight(.bold)
        }
        .foregroundColor(.white)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(.yellow, in: Capsule())
    }
}

struct DefaultModelBadge: View {
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "checkmark.circle.fill")
                .font(.caption)
            Text("DEFAULT MODEL")
                .font(.caption2)
                .fontWeight(.bold)
        }
        .foregroundColor(.white)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(.blue, in: Capsule())
    }
}

struct StatItem: View {
    let label: String
    let value: String
    let icon: String
    
    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundColor(.accentColor)
            
            Text(value)
                .font(.headline)
                .fontWeight(.semibold)
            
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(minWidth: 60)
    }
}

struct ModelActionButtons: View {
    let model: WhisperModel
    let isDownloaded: Bool
    let downloadStatus: DownloadStatus
    let downloadProgress: Double
    let isDefault: Bool
    
    let onDownload: () -> Void
    let onCancel: () -> Void
    let onDelete: () -> Void
    let onSetDefault: () -> Void
    
    var body: some View {
        VStack(spacing: 12) {
            // Download Progress (if downloading)
            if downloadStatus == .downloading {
                VStack(spacing: 8) {
                    HStack {
                        Text("Downloading...")
                            .font(.subheadline)
                            .fontWeight(.medium)
                        
                        Spacer()
                        
                        Text("\(Int(downloadProgress * 100))%")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .monospacedDigit()
                    }
                    
                    ProgressView(value: downloadProgress)
                        .progressViewStyle(LinearProgressViewStyle(tint: .accentColor))
                }
                .padding()
                .background(.blue.opacity(0.05), in: RoundedRectangle(cornerRadius: 8))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .strokeBorder(.blue.opacity(0.2), lineWidth: 1)
                )
            }
            
            // Action Buttons
            HStack(spacing: 12) {
                if isDownloaded {
                    if !isDefault {
                        Button("Set as Default") {
                            onSetDefault()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                    
                    Button("Delete Model") {
                        onDelete()
                    }
                    .buttonStyle(.bordered)
                    .foregroundColor(.red)
                } else {
                    switch downloadStatus {
                    case .downloading, .queued:
                        Button("Cancel Download") {
                            onCancel()
                        }
                        .buttonStyle(.bordered)
                        .foregroundColor(.red)
                        
                    case .failed:
                        Button("Retry Download") {
                            onDownload()
                        }
                        .buttonStyle(.borderedProminent)
                        
                    default:
                        Button("Download Model") {
                            onDownload()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                
                Spacer()
            }
        }
    }
}

struct ModelSpecifications: View {
    let model: WhisperModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Specifications")
                .font(.title2)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                
                SpecificationCard(
                    title: "Model Size",
                    value: "\(Int(model.sizeMB)) MB",
                    description: "Download size",
                    icon: "arrow.down.circle.fill",
                    color: .blue
                )
                
                SpecificationCard(
                    title: "Performance",
                    value: "\(model.performance.speedMultiplier, specifier: "%.0f")x realtime",
                    description: "Processing speed",
                    icon: "speedometer",
                    color: .green
                )
                
                SpecificationCard(
                    title: "Accuracy",
                    value: model.performance.accuracy,
                    description: "Transcription quality",
                    icon: "target",
                    color: .purple
                )
                
                SpecificationCard(
                    title: "Memory Usage",
                    value: model.performance.memoryUsage,
                    description: "RAM requirement",
                    icon: "memorychip",
                    color: .orange
                )
            }
            
            // Language Support
            VStack(alignment: .leading, spacing: 8) {
                Text("Language Support")
                    .font(.headline)
                
                Text("This model supports \(model.languages.count) languages including English, Spanish, French, German, Italian, Portuguese, Dutch, Polish, Russian, Chinese, Japanese, Korean, and many more.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            .padding()
            .background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 8))
        }
    }
}

struct SpecificationCard: View {
    let title: String
    let value: String
    let description: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.title3)
                
                Spacer()
            }
            
            Text(value)
                .font(.title3)
                .fontWeight(.semibold)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
    }
}

struct ModelPerformanceSection: View {
    let data: ModelPerformanceData
    let onBenchmark: () -> Void
    let onShowResults: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Performance")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                if data.hasBenchmarkData {
                    Button("View Results") {
                        onShowResults()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
                
                Button(data.hasBenchmarkData ? "Re-benchmark" : "Benchmark") {
                    onBenchmark()
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
            }
            
            // Performance Metrics
            HStack(spacing: 16) {
                PerformanceMetricCard(
                    title: "Processing Speed",
                    value: "\(String(format: "%.1f", data.displayProcessingSpeed))x",
                    subtitle: data.hasBenchmarkData ? "Measured" : "Estimated",
                    icon: "speedometer",
                    color: .blue,
                    isBenchmarked: data.hasBenchmarkData
                )
                
                PerformanceMetricCard(
                    title: "Memory Usage",
                    value: "\(Int(data.displayMemoryUsage)) MB",
                    subtitle: data.hasBenchmarkData ? "Measured" : "Estimated",
                    icon: "memorychip",
                    color: .orange,
                    isBenchmarked: data.hasBenchmarkData
                )
                
                PerformanceMetricCard(
                    title: "Accuracy",
                    value: "\(Int(data.displayAccuracy * 100))%",
                    subtitle: data.hasBenchmarkData ? "Measured" : "Estimated",
                    icon: "target",
                    color: .green,
                    isBenchmarked: data.hasBenchmarkData
                )
            }
            
            if let lastBenchmarked = data.lastBenchmarked {
                Text("Last benchmarked: \(lastBenchmarked, style: .relative) ago")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

struct PerformanceMetricCard: View {
    let title: String
    let value: String
    let subtitle: String
    let icon: String
    let color: Color
    let isBenchmarked: Bool
    
    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.title3)
                
                if isBenchmarked {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                        .font(.caption)
                }
                
                Spacer()
            }
            
            VStack(alignment: .leading, spacing: 2) {
                Text(value)
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(subtitle)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(isBenchmarked ? .regularMaterial : .quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(isBenchmarked ? color.opacity(0.3) : .clear, lineWidth: 1)
        )
    }
}

struct ModelUsageExamples: View {
    let model: WhisperModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Usage Examples")
                .font(.title2)
                .fontWeight(.semibold)
            
            VStack(alignment: .leading, spacing: 12) {
                UsageExample(
                    title: "Best for:",
                    items: model.useCases,
                    icon: "star.fill",
                    color: .yellow
                )
                
                UsageExample(
                    title: "Ideal file types:",
                    items: ["MP3, WAV, M4A audio files", "MP4, MOV, AVI video files", "Podcasts and interviews", "Meeting recordings"],
                    icon: "doc.fill",
                    color: .blue
                )
                
                UsageExample(
                    title: "Performance tips:",
                    items: model.performanceTips,
                    icon: "lightbulb.fill",
                    color: .orange
                )
            }
        }
    }
}

struct UsageExample: View {
    let title: String
    let items: [String]
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                Text(title)
                    .font(.headline)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                ForEach(items, id: \.self) { item in
                    HStack(alignment: .top, spacing: 8) {
                        Text("•")
                            .foregroundColor(color)
                        Text(item)
                            .font(.subheadline)
                        Spacer()
                    }
                }
            }
        }
        .padding()
        .background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 8))
    }
}

struct ModelCompatibilitySection: View {
    let model: WhisperModel
    let systemCapabilities: SystemCapabilities
    
    private var isCompatible: Bool {
        model.sizeMB <= systemCapabilities.recommendedMaxModelSize
    }
    
    private var compatibilityLevel: CompatibilityLevel {
        let memoryRatio = model.sizeMB / systemCapabilities.recommendedMaxModelSize
        
        if memoryRatio <= 0.5 {
            return .excellent
        } else if memoryRatio <= 1.0 {
            return .good
        } else if memoryRatio <= 2.0 {
            return .fair
        } else {
            return .poor
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("System Compatibility")
                .font(.title2)
                .fontWeight(.semibold)
            
            CompatibilityCard(level: compatibilityLevel, model: model, capabilities: systemCapabilities)
        }
    }
}

struct CompatibilityCard: View {
    let level: CompatibilityLevel
    let model: WhisperModel
    let capabilities: SystemCapabilities
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: level.icon)
                    .foregroundColor(level.color)
                    .font(.title2)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(level.title)
                        .font(.headline)
                        .foregroundColor(level.color)
                    
                    Text(level.description)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
            }
            
            // Compatibility Details
            VStack(alignment: .leading, spacing: 8) {
                CompatibilityRow(
                    label: "Memory Requirement",
                    value: "\(Int(model.sizeMB * 1.2)) MB",
                    available: "\(Int(capabilities.availableMemoryGB * 1024)) MB",
                    isGood: model.sizeMB * 1.2 < capabilities.availableMemoryGB * 1024 * 0.8
                )
                
                CompatibilityRow(
                    label: "Performance",
                    value: capabilities.isAppleSilicon ? "Optimized" : "Compatible",
                    available: capabilities.performanceProfile.displayName,
                    isGood: capabilities.isAppleSilicon
                )
            }
            
            if level == .poor {
                Text("⚠️ This model may not perform well on your system. Consider using a smaller model for better performance.")
                    .font(.caption)
                    .foregroundColor(.orange)
                    .padding(.top, 8)
            }
        }
        .padding()
        .background(level.color.opacity(0.05), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(level.color.opacity(0.2), lineWidth: 1)
        )
    }
}

struct CompatibilityRow: View {
    let label: String
    let value: String
    let available: String
    let isGood: Bool
    
    var body: some View {
        HStack {
            Text(label)
                .font(.subheadline)
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 2) {
                Text(value)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text("Available: \(available)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            
            Image(systemName: isGood ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                .foregroundColor(isGood ? .green : .orange)
                .font(.caption)
        }
    }
}

enum CompatibilityLevel {
    case excellent
    case good
    case fair
    case poor
    
    var title: String {
        switch self {
        case .excellent: return "Excellent Compatibility"
        case .good: return "Good Compatibility"
        case .fair: return "Fair Compatibility"
        case .poor: return "Poor Compatibility"
        }
    }
    
    var description: String {
        switch self {
        case .excellent: return "Optimal performance expected"
        case .good: return "Good performance expected"
        case .fair: return "May run slower than optimal"
        case .poor: return "May not run well on this system"
        }
    }
    
    var color: Color {
        switch self {
        case .excellent: return .green
        case .good: return .blue
        case .fair: return .orange
        case .poor: return .red
        }
    }
    
    var icon: String {
        switch self {
        case .excellent: return "checkmark.circle.fill"
        case .good: return "checkmark.circle"
        case .fair: return "exclamationmark.triangle"
        case .poor: return "xmark.circle"
        }
    }
}

struct BenchmarkResultsSheet: View {
    let model: WhisperModel
    let performanceData: ModelPerformanceData
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header
                VStack(spacing: 8) {
                    Text("Benchmark Results")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text(model.name)
                        .font(.headline)
                        .foregroundStyle(.secondary)
                    
                    if let lastBenchmarked = performanceData.lastBenchmarked {
                        Text("Tested \(lastBenchmarked, style: .relative) ago")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                }
                
                // Detailed Results
                if performanceData.hasBenchmarkData {
                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 16) {
                        
                        BenchmarkResultCard(
                            title: "Processing Speed",
                            measured: "\(String(format: "%.2f", performanceData.benchmarkProcessingSpeed ?? 0))x",
                            estimated: "\(String(format: "%.2f", performanceData.estimatedProcessingSpeed))x",
                            icon: "speedometer",
                            color: .blue
                        )
                        
                        BenchmarkResultCard(
                            title: "Memory Usage",
                            measured: "\(Int(performanceData.benchmarkMemoryUsage ?? 0)) MB",
                            estimated: "\(Int(performanceData.estimatedMemoryUsage)) MB",
                            icon: "memorychip",
                            color: .orange
                        )
                        
                        BenchmarkResultCard(
                            title: "Accuracy Score",
                            measured: "\(Int((performanceData.benchmarkAccuracy ?? 0) * 100))%",
                            estimated: "\(Int(performanceData.estimatedAccuracy * 100))%",
                            icon: "target",
                            color: .green
                        )
                    }
                }
                
                Spacer()
            }
            .padding()
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

struct BenchmarkResultCard: View {
    let title: String
    let measured: String
    let estimated: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.largeTitle)
                .foregroundColor(color)
            
            VStack(spacing: 4) {
                Text(measured)
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundColor(color)
                
                Text(title)
                    .font(.headline)
                
                Text("Est: \(estimated)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
}

#Preview("Model Detail") {
    ModelDetailView(
        model: WhisperModel.availableModels[3], // large-v3-turbo
        viewModel: ModelManagerViewModel()
    )
    .frame(width: 500, height: 800)
}