import SwiftUI

struct QueueView: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Section Header
            HStack {
                Image(systemName: "list.bullet")
                    .foregroundColor(.accentColor)
                Text("Processing Queue")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                // Queue controls
                HStack(spacing: 8) {
                    Text("\(viewModel.transcriptionQueue.count) files")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    if !viewModel.transcriptionQueue.isEmpty {
                        Button("Clear Completed") {
                            viewModel.clearCompletedTasks()
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(viewModel.isProcessing || !viewModel.hasCompletedTasks)
                        
                        Button("Clear All") {
                            viewModel.clearAllTasks()
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .disabled(viewModel.isProcessing)
                    }
                }
            }
            
            // Queue List
            if viewModel.transcriptionQueue.isEmpty {
                // Empty State
                EmptyQueueView {
                    // Trigger add files action
                    viewModel.addFilesToQueue()
                }
            } else {
                // Queue List with files
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(viewModel.transcriptionQueue) { task in
                            QueueRowView(
                                task: task,
                                onRemove: {
                                    viewModel.removeTask(task)
                                },
                                onRetry: {
                                    viewModel.retryTask(task)
                                },
                                onReveal: {
                                    viewModel.revealTaskOutput(task)
                                }
                            )
                            .disabled(viewModel.isProcessing && task.status == .processing)
                        }
                    }
                }
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
                
                // Batch Controls
                BatchControlsView(viewModel: viewModel)
            }
        }
    }
}

// MARK: - Supporting Views

struct EmptyQueueView: View {
    let onAddFiles: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "tray")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text("Queue is Empty")
                .font(.title2)
                .fontWeight(.medium)
            
            Text("Add audio or video files to start batch processing")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            
            Button("Add Files to Queue") {
                onAddFiles()
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(32)
        .background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 16))
    }
}

struct QueueRowView: View {
    let task: TranscriptionTask
    let onRemove: () -> Void
    let onRetry: () -> Void
    let onReveal: () -> Void
    
    private var statusIcon: String {
        switch task.status {
        case .pending:
            return "clock"
        case .processing:
            return "hourglass"
        case .completed:
            return "checkmark.circle.fill"
        case .failed:
            return "xmark.circle.fill"
        case .cancelled:
            return "stop.circle.fill"
        }
    }
    
    private var statusColor: Color {
        switch task.status {
        case .pending:
            return .secondary
        case .processing:
            return .blue
        case .completed:
            return .green
        case .failed:
            return .red
        case .cancelled:
            return .orange
        }
    }
    
    var body: some View {
        HStack(spacing: 16) {
            // Status Icon
            Image(systemName: statusIcon)
                .font(.title3)
                .foregroundColor(statusColor)
                .frame(width: 24)
                .symbolEffect(.pulse, isActive: task.status == .processing)
            
            // File Info
            VStack(alignment: .leading, spacing: 4) {
                Text(task.inputURL.lastPathComponent)
                    .font(.headline)
                    .lineLimit(1)
                
                HStack {
                    Text(task.model)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(.quaternary, in: Capsule())
                    
                    Text(task.formats.map(\.rawValue).joined(separator: ", "))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    
                    Spacer()
                    
                    if task.status == .completed {
                        Text("✓ Complete")
                            .font(.caption)
                            .foregroundColor(.green)
                    } else if task.status == .failed {
                        Text("✗ Failed")
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                }
            }
            
            // Progress Bar (only for processing tasks)
            if task.status == .processing {
                VStack(alignment: .trailing, spacing: 4) {
                    Text("\(Int(task.progress * 100))%")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .monospacedDigit()
                    
                    ProgressView(value: task.progress)
                        .progressViewStyle(LinearProgressViewStyle(tint: .accentColor))
                        .frame(width: 80)
                }
            }
            
            // Actions
            HStack(spacing: 4) {
                if task.status == .completed {
                    Button(action: onReveal) {
                        Image(systemName: "folder")
                    }
                    .buttonStyle(.borderless)
                    .help("Reveal in Finder")
                }
                
                if task.status == .failed {
                    Button(action: onRetry) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .buttonStyle(.borderless)
                    .help("Retry")
                }
                
                Button(action: onRemove) {
                    Image(systemName: "trash")
                }
                .buttonStyle(.borderless)
                .foregroundColor(.red)
                .help("Remove from queue")
                .disabled(task.status == .processing)
            }
            .controlSize(.small)
        }
        .padding()
        .background(
            task.status == .processing ? .blue.opacity(0.05) : .clear,
            in: RoundedRectangle(cornerRadius: 8)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(
                    task.status == .processing ? .blue.opacity(0.3) : .clear,
                    lineWidth: 1
                )
        )
        .contextMenu {
            Button("Remove from Queue", action: onRemove)
            
            if task.status == .failed {
                Button("Retry Transcription", action: onRetry)
            }
            
            if task.status == .completed {
                Button("Reveal in Finder", action: onReveal)
                Button("Copy Output Path") {
                    NSPasteboard.general.clearContents()
                    NSPasteboard.general.setString(task.outputDirectory.path, forType: .string)
                }
            }
            
            Divider()
            
            Button("Copy File Path") {
                NSPasteboard.general.clearContents()
                NSPasteboard.general.setString(task.inputURL.path, forType: .string)
            }
        }
    }
}

struct BatchControlsView: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    
    var body: some View {
        HStack {
            // Batch Stats
            VStack(alignment: .leading, spacing: 4) {
                Text("Batch Progress")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                HStack {
                    Text("\(viewModel.completedTasksCount)/\(viewModel.transcriptionQueue.count) completed")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    
                    if viewModel.failedTasksCount > 0 {
                        Text("• \(viewModel.failedTasksCount) failed")
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                }
                
                ProgressView(value: viewModel.batchProgress)
                    .progressViewStyle(LinearProgressViewStyle(tint: .accentColor))
                    .frame(width: 200)
            }
            
            Spacer()
            
            // Batch Actions
            HStack(spacing: 12) {
                if viewModel.isProcessing {
                    Button("Pause Batch") {
                        viewModel.pauseBatch()
                    }
                    .buttonStyle(.bordered)
                    .disabled(!viewModel.canPauseBatch)
                    
                    Button("Cancel Batch") {
                        viewModel.cancelBatch()
                    }
                    .buttonStyle(.bordered)
                    .foregroundColor(.red)
                } else {
                    Button("Add Files") {
                        viewModel.addFilesToQueue()
                    }
                    .buttonStyle(.bordered)
                    
                    Button("Process Queue") {
                        Task {
                            await viewModel.processBatch()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!viewModel.canStartBatch)
                }
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
    }
}

#Preview("With Queue") {
    let viewModel = TranscriptionViewModel()
    
    // Add sample tasks
    let task1 = TranscriptionTask(
        inputURL: URL(fileURLWithPath: "/test/audio1.mp3"),
        outputDirectory: URL(fileURLWithPath: "/test/output"),
        model: "large-v3-turbo",
        formats: [.txt, .srt]
    )
    task1.status = .completed
    task1.progress = 1.0
    
    let task2 = TranscriptionTask(
        inputURL: URL(fileURLWithPath: "/test/video.mp4"),
        outputDirectory: URL(fileURLWithPath: "/test/output"),
        model: "large-v3-turbo",
        formats: [.txt]
    )
    task2.status = .processing
    task2.progress = 0.65
    
    let task3 = TranscriptionTask(
        inputURL: URL(fileURLWithPath: "/test/audio2.wav"),
        outputDirectory: URL(fileURLWithPath: "/test/output"),
        model: "large-v3-turbo",
        formats: [.srt]
    )
    task3.status = .failed
    
    viewModel.transcriptionQueue = [task1, task2, task3]
    
    return QueueView(viewModel: viewModel)
        .padding()
        .frame(width: 800, height: 600)
}

#Preview("Empty Queue") {
    let viewModel = TranscriptionViewModel()
    
    return QueueView(viewModel: viewModel)
        .padding()
        .frame(width: 800, height: 400)
}