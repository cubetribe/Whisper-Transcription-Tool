import SwiftUI

struct TranscriptionConfigSection: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Section Header
            HStack {
                Image(systemName: "gearshape.2")
                    .foregroundColor(.accentColor)
                Text("Transcription Settings")
                    .font(.title2)
                    .fontWeight(.semibold)
                Spacer()
            }
            
            // Configuration Grid
            LazyVGrid(columns: [
                GridItem(.flexible(minimum: 200)),
                GridItem(.flexible(minimum: 200))
            ], alignment: .leading, spacing: 20) {
                
                // Model Selection
                ModelSelectionView(viewModel: viewModel)
                
                // Language Selection  
                LanguageSelectionView(viewModel: viewModel)
                
                // Output Formats (spans both columns)
                VStack {
                    OutputFormatSelectionView(viewModel: viewModel)
                }
                .frame(maxWidth: .infinity)
                .gridCellColumns(2)
            }
            
            // Action Buttons
            HStack {
                Spacer()
                
                Button("Reset Settings") {
                    viewModel.resetTranscription()
                }
                .buttonStyle(.bordered)
                .disabled(viewModel.isTranscribing)
                
                Button("Start Transcription") {
                    Task {
                        await viewModel.startTranscription()
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(!viewModel.canStartTranscription)
            }
        }
    }
}

// MARK: - Supporting Views

struct ModelSelectionView: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    
    private var selectedModelInfo: WhisperModel? {
        return viewModel.availableModels.first { $0.name == viewModel.selectedModel }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Whisper Model")
                .font(.headline)
            
            Picker("Model", selection: $viewModel.selectedModel) {
                ForEach(viewModel.availableModels, id: \.name) { model in
                    VStack(alignment: .leading) {
                        Text(model.name)
                            .font(.body)
                        Text("\(Int(model.sizeMB))MB - \(model.performance.accuracy)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .tag(model.name)
                }
            }
            .pickerStyle(.menu)
            .disabled(viewModel.isTranscribing)
            
            // Model info
            if let modelInfo = selectedModelInfo {
                VStack(alignment: .leading, spacing: 4) {
                    Text(modelInfo.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    
                    HStack {
                        Label("\(modelInfo.performance.speedMultiplier, specifier: "%.0f")x speed", 
                              systemImage: "speedometer")
                        Spacer()
                        Label("\(modelInfo.performance.memoryUsage)", 
                              systemImage: "memorychip")
                    }
                    .font(.caption)
                    .foregroundStyle(.tertiary)
                }
                .padding(8)
                .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 6))
            }
        }
    }
}

struct LanguageSelectionView: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Language")
                .font(.headline)
            
            Picker("Language", selection: $viewModel.selectedLanguage) {
                ForEach(Array(viewModel.supportedLanguages.keys.sorted()), id: \.self) { key in
                    Text(viewModel.supportedLanguages[key] ?? key)
                        .tag(key)
                }
            }
            .pickerStyle(.menu)
            .disabled(viewModel.isTranscribing)
            
            Text(viewModel.selectedLanguage == "auto" ? 
                 "Language will be detected automatically" : 
                 "Fixed language for better accuracy")
                .font(.caption)
                .foregroundStyle(.secondary)
                .padding(8)
                .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 6))
        }
    }
}

struct OutputFormatSelectionView: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Output Formats")
                .font(.headline)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 8) {
                ForEach(OutputFormat.allCases, id: \.self) { format in
                    OutputFormatToggle(
                        format: format,
                        isSelected: viewModel.selectedFormats.contains(format)
                    ) {
                        if viewModel.selectedFormats.contains(format) {
                            viewModel.selectedFormats.remove(format)
                        } else {
                            viewModel.selectedFormats.insert(format)
                        }
                    }
                    .disabled(viewModel.isTranscribing)
                }
            }
            
            if viewModel.selectedFormats.isEmpty {
                Text("⚠️ Select at least one output format")
                    .font(.caption)
                    .foregroundColor(.orange)
            } else {
                Text("✓ \(viewModel.selectedFormats.count) format\(viewModel.selectedFormats.count == 1 ? "" : "s") selected")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

struct OutputFormatToggle: View {
    let format: OutputFormat
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: format.systemImage)
                    .foregroundColor(isSelected ? .white : .accentColor)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(format.displayName)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(isSelected ? .white : .primary)
                    
                    Text(format.description)
                        .font(.caption)
                        .foregroundColor(isSelected ? .white.opacity(0.8) : .secondary)
                        .lineLimit(1)
                }
                
                Spacer()
                
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.white)
                }
            }
            .padding(12)
            .background(
                isSelected ? .accentColor : .quaternary.opacity(0.5),
                in: RoundedRectangle(cornerRadius: 8)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .strokeBorder(
                        isSelected ? .clear : .quaternary,
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(.plain)
        .help(format.description)
    }
}

#Preview {
    let viewModel = TranscriptionViewModel()
    viewModel.selectedFile = URL(fileURLWithPath: "/test/audio.mp3")
    viewModel.outputDirectory = URL(fileURLWithPath: "/test/output")
    
    return TranscriptionConfigSection(viewModel: viewModel)
        .padding()
        .frame(width: 700)
}