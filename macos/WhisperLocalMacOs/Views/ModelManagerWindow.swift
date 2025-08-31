import SwiftUI

struct ModelManagerWindow: View {
    @StateObject private var viewModel = ModelManagerViewModel()
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationSplitView {
            ModelListView(viewModel: viewModel)
        } detail: {
            if let selectedModel = viewModel.selectedModel {
                ModelDetailView(model: selectedModel, viewModel: viewModel)
            } else {
                ModelSelectionPrompt()
            }
        }
        .navigationTitle("Model Manager")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("Done") {
                    dismiss()
                }
            }
        }
        .onDisappear {
            viewModel.cleanup()
        }
        .alert("Model Manager Error", isPresented: .constant(viewModel.currentError != nil)) {
            Button("OK") {
                viewModel.clearError()
            }
        } message: {
            if let error = viewModel.currentError {
                Text(error.localizedDescription)
            }
        }
    }
}

struct ModelListView: View {
    @ObservedObject var viewModel: ModelManagerViewModel
    @State private var showingSystemInfo = false
    
    var body: some View {
        VStack(spacing: 0) {
            // Search Bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                
                TextField("Search models...", text: $viewModel.searchText)
                    .textFieldStyle(.plain)
            }
            .padding()
            .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 8))
            .padding()
            
            // System Capabilities Banner
            SystemCapabilitiesBanner(capabilities: viewModel.systemCapabilities) {
                showingSystemInfo = true
            }
            .padding(.horizontal)
            
            // Model List
            List(viewModel.filteredModels, selection: $viewModel.selectedModel) { model in
                ModelRowView(
                    model: model,
                    isDownloaded: viewModel.isModelDownloaded(model),
                    isRecommended: viewModel.isModelRecommended(model),
                    downloadStatus: viewModel.downloadStatus[model.name] ?? .notDownloaded,
                    downloadProgress: viewModel.downloadProgress[model.name] ?? 0.0,
                    performanceData: viewModel.performanceData[model.name],
                    isDefault: viewModel.defaultModel == model.name,
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
                    },
                    onBenchmark: {
                        Task {
                            await viewModel.benchmarkModel(model)
                        }
                    }
                )
                .tag(model)
            }
            .listStyle(.sidebar)
        }
        .navigationTitle("Models")
        .navigationBarTitleDisplayMode(.large)
        .sheet(isPresented: $showingSystemInfo) {
            SystemInfoSheet(capabilities: viewModel.systemCapabilities)
        }
    }
}

struct ModelRowView: View {
    let model: WhisperModel
    let isDownloaded: Bool
    let isRecommended: Bool
    let downloadStatus: DownloadStatus
    let downloadProgress: Double
    let performanceData: ModelPerformanceData?
    let isDefault: Bool
    
    let onDownload: () -> Void
    let onCancel: () -> Void
    let onDelete: () -> Void
    let onSetDefault: () -> Void
    let onBenchmark: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    HStack {
                        Text(model.name)
                            .font(.headline)
                        
                        if isDefault {
                            Text("DEFAULT")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .foregroundColor(.white)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(.blue, in: Capsule())
                        }
                        
                        if isRecommended {
                            Image(systemName: "star.fill")
                                .font(.caption)
                                .foregroundColor(.yellow)
                        }
                    }
                    
                    Text("\(Int(model.sizeMB))MB • \(model.performance.accuracy)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
                
                // Status Badge
                StatusBadge(status: downloadStatus, progress: downloadProgress)
            }
            
            // Description
            Text(model.description)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
            
            // Performance Indicators
            if let perfData = performanceData {
                PerformanceIndicators(data: perfData)
            }
            
            // Download Progress
            if downloadStatus == .downloading {
                ProgressView(value: downloadProgress)
                    .progressViewStyle(LinearProgressViewStyle())
                    .scaleEffect(y: 0.5)
            }
        }
        .padding(.vertical, 4)
        .contentShape(Rectangle())
        .contextMenu {
            if isDownloaded {
                Button("Set as Default") {
                    onSetDefault()
                }
                .disabled(isDefault)
                
                Button("Benchmark Performance") {
                    onBenchmark()
                }
                
                Divider()
                
                Button("Delete Model", role: .destructive) {
                    onDelete()
                }
            } else if downloadStatus == .downloading {
                Button("Cancel Download") {
                    onCancel()
                }
            } else {
                Button("Download Model") {
                    onDownload()
                }
            }
        }
    }
}

struct StatusBadge: View {
    let status: DownloadStatus
    let progress: Double
    
    var body: some View {
        HStack(spacing: 4) {
            if status == .downloading {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle())
                    .scaleEffect(0.6)
            } else {
                Image(systemName: statusIcon)
                    .font(.caption)
            }
            
            Text(status.displayName)
                .font(.caption2)
                .fontWeight(.medium)
        }
        .foregroundColor(status.color)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(status.color.opacity(0.1), in: Capsule())
    }
    
    private var statusIcon: String {
        switch status {
        case .notDownloaded: return "arrow.down.circle"
        case .queued: return "clock"
        case .downloading: return "arrow.down.circle.fill"
        case .downloaded: return "checkmark.circle.fill"
        case .failed: return "xmark.circle.fill"
        case .cancelled: return "stop.circle.fill"
        case .verifying: return "checkmark.shield"
        }
    }
}

struct PerformanceIndicators: View {
    let data: ModelPerformanceData
    
    var body: some View {
        HStack(spacing: 12) {
            PerformanceMetric(
                icon: "speedometer",
                value: "\(String(format: "%.1f", data.displayProcessingSpeed))x",
                label: "Speed",
                color: .blue
            )
            
            PerformanceMetric(
                icon: "memorychip",
                value: "\(Int(data.displayMemoryUsage))MB",
                label: "Memory",
                color: .orange
            )
            
            PerformanceMetric(
                icon: "target",
                value: "\(Int(data.displayAccuracy * 100))%",
                label: "Accuracy",
                color: .green
            )
        }
    }
}

struct PerformanceMetric: View {
    let icon: String
    let value: String
    let label: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 2) {
            HStack(spacing: 2) {
                Image(systemName: icon)
                    .font(.caption2)
                Text(value)
                    .font(.caption2)
                    .fontWeight(.medium)
            }
            .foregroundColor(color)
            
            Text(label)
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
    }
}

struct SystemCapabilitiesBanner: View {
    let capabilities: SystemCapabilities
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack {
                Image(systemName: capabilities.isAppleSilicon ? "cpu" : "desktopcomputer")
                    .foregroundColor(capabilities.performanceProfile.color)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("System: \(capabilities.performanceProfile.displayName)")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Text("\(capabilities.isAppleSilicon ? "Apple Silicon" : "Intel") • \(String(format: "%.0f", capabilities.availableMemoryGB))GB RAM")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
                
                Image(systemName: "info.circle")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding()
            .background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(.plain)
    }
}

struct ModelSelectionPrompt: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "brain")
                .font(.system(size: 48))
                .foregroundColor(.accentColor)
            
            Text("Select a Model")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Choose a Whisper model from the list to view detailed information, performance metrics, and download options.")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct SystemInfoSheet: View {
    let capabilities: SystemCapabilities
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                HStack {
                    Image(systemName: capabilities.isAppleSilicon ? "cpu" : "desktopcomputer")
                        .font(.title)
                        .foregroundColor(capabilities.performanceProfile.color)
                    
                    VStack(alignment: .leading) {
                        Text("System Information")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text(capabilities.performanceProfile.displayName)
                            .font(.subheadline)
                            .foregroundColor(capabilities.performanceProfile.color)
                    }
                }
                
                Divider()
                
                // System Details
                VStack(alignment: .leading, spacing: 16) {
                    SystemInfoRow(
                        label: "Architecture",
                        value: capabilities.isAppleSilicon ? "Apple Silicon (ARM64)" : "Intel (x86_64)",
                        icon: "cpu"
                    )
                    
                    SystemInfoRow(
                        label: "Available Memory",
                        value: "\(String(format: "%.1f", capabilities.availableMemoryGB)) GB",
                        icon: "memorychip"
                    )
                    
                    SystemInfoRow(
                        label: "Recommended Max Model Size",
                        value: "\(Int(capabilities.recommendedMaxModelSize)) MB",
                        icon: "scale.3d"
                    )
                    
                    SystemInfoRow(
                        label: "Performance Profile",
                        value: capabilities.performanceProfile.displayName,
                        icon: "speedometer"
                    )
                }
                
                Spacer()
                
                // Performance Notes
                VStack(alignment: .leading, spacing: 8) {
                    Text("Performance Notes")
                        .font(.headline)
                    
                    Text("Models within the recommended size will provide optimal performance on your system. Larger models may run slower or require more memory than available.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding()
                .background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 8))
            }
            .padding()
            .navigationTitle("System Information")
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

struct SystemInfoRow: View {
    let label: String
    let value: String
    let icon: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .frame(width: 20)
                .foregroundColor(.accentColor)
            
            Text(label)
                .fontWeight(.medium)
            
            Spacer()
            
            Text(value)
                .foregroundStyle(.secondary)
        }
    }
}

#Preview("Model Manager Window") {
    ModelManagerWindow()
        .frame(width: 900, height: 600)
}

#Preview("Model List") {
    NavigationView {
        ModelListView(viewModel: ModelManagerViewModel())
    }
    .frame(width: 400, height: 600)
}