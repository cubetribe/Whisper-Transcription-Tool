import SwiftUI

struct MainContentView: View {
    let selectedTab: SidebarItem
    
    var body: some View {
        Group {
            switch selectedTab {
            case .transcribe:
                TranscribeView()
            case .extract:
                ExtractView()
            case .batch:
                BatchView()
            case .models:
                ModelsView()
            case .chatbot:
                ChatbotView()
            case .logs:
                LogsView()
            case .settings:
                SettingsView()
            }
        }
        .navigationTitle(selectedTab.title)
        .navigationBarTitleDisplayMode(.large)
    }
}

// MARK: - Placeholder Views

struct TranscribeView: View {
    @StateObject private var viewModel = TranscriptionViewModel()
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Content area
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // File Selection Section
                    FileSelectionSection(viewModel: viewModel)
                    
                    if viewModel.selectedFile != nil {
                        Divider()
                        
                        // Configuration Section
                        TranscriptionConfigSection(viewModel: viewModel)
                        
                        Divider()
                        
                        // Progress Section (shown during transcription)
                        if viewModel.isTranscribing {
                            TranscriptionProgressSection(viewModel: viewModel)
                        }
                    }
                }
                .padding(24)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
    }
}

struct ExtractView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "scissors")
                .font(.system(size: 64))
                .foregroundColor(.accentColor)
            
            Text("Audio Extraction")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Extract audio from video files")
                .font(.body)
                .foregroundStyle(.secondary)
            
            Text("Coming Soon...")
                .font(.caption)
                .padding()
                .background(.quaternary, in: RoundedRectangle(cornerRadius: 8))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct BatchView: View {
    @StateObject private var viewModel = TranscriptionViewModel()
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Content area
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // File Selection for Output Directory
                    VStack(alignment: .leading, spacing: 16) {
                        HStack {
                            Image(systemName: "folder")
                                .foregroundColor(.accentColor)
                            Text("Output Settings")
                                .font(.title2)
                                .fontWeight(.semibold)
                            Spacer()
                        }
                        
                        OutputDirectorySelector(viewModel: viewModel)
                        
                        if viewModel.outputDirectory != nil {
                            TranscriptionConfigSection(viewModel: viewModel)
                                .padding(.top)
                        }
                    }
                    
                    if viewModel.outputDirectory != nil {
                        Divider()
                        
                        // Queue View
                        QueueView(viewModel: viewModel)
                        
                        if viewModel.isProcessing {
                            Divider()
                            
                            // Overall batch progress
                            VStack(alignment: .leading, spacing: 12) {
                                HStack {
                                    Image(systemName: "hourglass")
                                        .foregroundColor(.blue)
                                        .symbolEffect(.pulse, isActive: viewModel.isProcessing)
                                    
                                    Text("Batch Processing Status")
                                        .font(.title2)
                                        .fontWeight(.semibold)
                                    
                                    Spacer()
                                }
                                
                                VStack(alignment: .leading, spacing: 8) {
                                    Text(viewModel.batchMessage)
                                        .font(.subheadline)
                                    
                                    HStack {
                                        ProgressView(value: viewModel.batchProgress)
                                            .progressViewStyle(LinearProgressViewStyle(tint: .accentColor))
                                        
                                        Text("\(Int(viewModel.batchProgress * 100))%")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                            .monospacedDigit()
                                            .frame(width: 40, alignment: .trailing)
                                    }
                                }
                                .padding()
                                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
                            }
                        }
                        
                        // Show batch summary if any tasks are completed
                        if viewModel.completedTasksCount > 0 || viewModel.failedTasksCount > 0 {
                            Divider()
                            
                            BatchSummaryView(viewModel: viewModel)
                        }
                    }
                }
                .padding(24)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
    }
}

struct ModelsView: View {
    @StateObject private var viewModel = ModelManagerViewModel()
    @State private var showingModelManager = false
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "brain")
                .font(.system(size: 64))
                .foregroundColor(.accentColor)
            
            Text("Model Management")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Download and manage Whisper models for optimal transcription performance")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            
            // Quick Stats
            HStack(spacing: 30) {
                VStack {
                    Text("\(viewModel.availableModels.count)")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.blue)
                    Text("Available")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                VStack {
                    Text("\(viewModel.downloadedModels.count)")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.green)
                    Text("Downloaded")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                VStack {
                    Text("\(viewModel.recommendedModels.count)")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.yellow)
                    Text("Recommended")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding()
            .background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 12))
            
            Button("Open Model Manager") {
                showingModelManager = true
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .sheet(isPresented: $showingModelManager) {
            ModelManagerWindow()
                .frame(width: 900, height: 600)
        }
    }
}

struct LogsView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "doc.text")
                .font(.system(size: 64))
                .foregroundColor(.accentColor)
            
            Text("Application Logs")
                .font(.title)
                .fontWeight(.bold)
            
            Text("View system and transcription logs")
                .font(.body)
                .foregroundStyle(.secondary)
            
            Text("Coming Soon...")
                .font(.caption)
                .padding()
                .background(.quaternary, in: RoundedRectangle(cornerRadius: 8))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct SettingsView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "gearshape")
                .font(.system(size: 64))
                .foregroundColor(.accentColor)
            
            Text("Settings")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Configure application preferences")
                .font(.body)
                .foregroundStyle(.secondary)
            
            Text("Coming Soon...")
                .font(.caption)
                .padding()
                .background(.quaternary, in: RoundedRectangle(cornerRadius: 8))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview("Transcribe") {
    MainContentView(selectedTab: .transcribe)
        .frame(width: 800, height: 600)
}

#Preview("Models") {
    MainContentView(selectedTab: .models)
        .frame(width: 800, height: 600)
}