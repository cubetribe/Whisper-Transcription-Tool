import SwiftUI

struct TranscriptionProgressSection: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Section Header
            HStack {
                Image(systemName: viewModel.transcriptionProgress >= 1.0 ? "checkmark.circle.fill" : "hourglass")
                    .foregroundColor(viewModel.transcriptionProgress >= 1.0 ? .green : .accentColor)
                    .symbolEffect(.pulse, isActive: viewModel.isTranscribing)
                
                Text("Transcription Progress")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                if viewModel.isTranscribing {
                    Button("Cancel") {
                        viewModel.cancelTranscription()
                    }
                    .buttonStyle(.bordered)
                    .foregroundColor(.red)
                }
            }
            
            // Progress Content
            VStack(alignment: .leading, spacing: 12) {
                // Progress Bar
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text(viewModel.progressMessage.isEmpty ? "Preparing..." : viewModel.progressMessage)
                            .font(.subheadline)
                            .fontWeight(.medium)
                        
                        Spacer()
                        
                        Text("\(Int(viewModel.transcriptionProgress * 100))%")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .monospacedDigit()
                    }
                    
                    ProgressView(value: viewModel.transcriptionProgress)
                        .progressViewStyle(LinearProgressViewStyle(tint: .accentColor))
                        .scaleEffect(y: 1.5)
                }
                
                // Task Information
                if let task = viewModel.currentTask {
                    TaskInfoView(task: task)
                }
                
                // Result Information
                if let result = viewModel.lastResult {
                    TranscriptionResultView(result: result)
                }
                
                // Error Display
                if let error = viewModel.currentError {
                    ErrorDisplayView(error: error) {
                        viewModel.clearError()
                    }
                }
            }
            .padding()
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
        }
    }
}

// MARK: - Supporting Views

struct TaskInfoView: View {
    let task: TranscriptionTask
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Task Details")
                .font(.headline)
                .foregroundColor(.secondary)
            
            LazyVGrid(columns: [
                GridItem(.flexible(minimum: 120)),
                GridItem(.flexible(minimum: 120))
            ], alignment: .leading, spacing: 8) {
                
                InfoRow(label: "Input File", value: task.inputURL.lastPathComponent, icon: "doc.fill")
                InfoRow(label: "Model", value: task.model, icon: "brain")
                InfoRow(label: "Formats", value: task.formats.map(\.rawValue).joined(separator: ", "), icon: "doc.badge.gearshape")
                InfoRow(label: "Status", value: task.status.rawValue.capitalized, icon: "info.circle")
            }
        }
    }
}

struct TranscriptionResultView: View {
    let result: TranscriptionResult
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: result.success ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .foregroundColor(result.success ? .green : .red)
                
                Text("Transcription Result")
                    .font(.headline)
                
                Spacer()
                
                if result.success {
                    Text("\(result.processingTime, specifier: "%.1f")s")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .monospacedDigit()
                }
            }
            
            if result.success {
                // Success information
                VStack(alignment: .leading, spacing: 8) {
                    Text("✓ Transcription completed successfully")
                        .foregroundColor(.green)
                    
                    Text("Output files:")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    ForEach(result.outputFiles, id: \.self) { file in
                        HStack(spacing: 8) {
                            Image(systemName: "doc.text.fill")
                                .foregroundColor(.accentColor)
                                .frame(width: 16)
                            
                            Text(URL(fileURLWithPath: file).lastPathComponent)
                                .font(.caption)
                                .fontFamily(.monospaced)
                            
                            Spacer()
                            
                            Button("Reveal") {
                                NSWorkspace.shared.selectFile(file, inFileViewerRootedAtPath: "")
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.mini)
                        }
                    }
                }
                
                // Quality assessment
                if result.quality != .unknown {
                    HStack {
                        Text("Quality Assessment:")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        
                        Text(result.quality.description)
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(result.quality.color)
                    }
                }
                
            } else {
                // Error information
                VStack(alignment: .leading, spacing: 6) {
                    Text("❌ Transcription failed")
                        .foregroundColor(.red)
                    
                    if let error = result.error {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .padding(8)
                            .background(.red.opacity(0.1), in: RoundedRectangle(cornerRadius: 6))
                    }
                }
            }
        }
        .padding()
        .background(result.success ? .green.opacity(0.05) : .red.opacity(0.05), 
                   in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(result.success ? .green.opacity(0.2) : .red.opacity(0.2), lineWidth: 1)
        )
    }
}

struct ErrorDisplayView: View {
    let error: AppError
    let onDismiss: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.orange)
                
                Text("Error")
                    .font(.headline)
                    .foregroundColor(.orange)
                
                Spacer()
                
                Button(action: onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
            }
            
            if let description = error.errorDescription {
                Text(description)
                    .font(.subheadline)
            }
            
            if let suggestion = error.recoverySuggestion {
                Text("💡 \(suggestion)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.orange.opacity(0.05), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(.orange.opacity(0.2), lineWidth: 1)
        )
    }
}

struct InfoRow: View {
    let label: String
    let value: String
    let icon: String
    
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .foregroundColor(.accentColor)
                .frame(width: 16)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                
                Text(value)
                    .font(.caption)
                    .fontWeight(.medium)
                    .lineLimit(1)
            }
            
            Spacer()
        }
    }
}

// MARK: - Extensions

extension TranscriptionResult.Quality {
    var description: String {
        switch self {
        case .excellent:
            return "Excellent"
        case .good:
            return "Good"
        case .fair:
            return "Fair"
        case .poor:
            return "Poor"
        case .unknown:
            return "Unknown"
        }
    }
    
    var color: Color {
        switch self {
        case .excellent:
            return .green
        case .good:
            return .blue
        case .fair:
            return .orange
        case .poor:
            return .red
        case .unknown:
            return .secondary
        }
    }
}

#Preview("In Progress") {
    let viewModel = TranscriptionViewModel()
    viewModel.isTranscribing = true
    viewModel.transcriptionProgress = 0.65
    viewModel.progressMessage = "Transcribing with large-v3-turbo..."
    viewModel.currentTask = TranscriptionTask(
        inputURL: URL(fileURLWithPath: "/test/audio.mp3"),
        outputDirectory: URL(fileURLWithPath: "/test/output"),
        model: "large-v3-turbo",
        formats: [.txt, .srt]
    )
    
    return TranscriptionProgressSection(viewModel: viewModel)
        .padding()
        .frame(width: 600)
}

#Preview("Completed") {
    let viewModel = TranscriptionViewModel()
    viewModel.isTranscribing = false
    viewModel.transcriptionProgress = 1.0
    viewModel.progressMessage = "Transcription completed successfully!"
    viewModel.lastResult = TranscriptionResult(
        inputFile: "/test/audio.mp3",
        outputFiles: ["/test/audio.txt", "/test/audio.srt"],
        processingTime: 12.5,
        modelUsed: "large-v3-turbo",
        language: "en",
        success: true,
        error: nil,
        timestamp: Date()
    )
    
    return TranscriptionProgressSection(viewModel: viewModel)
        .padding()
        .frame(width: 600)
}