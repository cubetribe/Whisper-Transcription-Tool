import SwiftUI
import AppKit

struct FileSelectionSection: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Section Header
            HStack {
                Image(systemName: "doc.badge.plus")
                    .foregroundColor(.accentColor)
                Text("File Selection")
                    .font(.title2)
                    .fontWeight(.semibold)
                Spacer()
            }
            
            // File Selection Area
            if let selectedFile = viewModel.selectedFile {
                // Selected file display
                SelectedFileView(file: selectedFile) {
                    viewModel.removeSelectedFile()
                }
            } else {
                // File drop area
                FileDropArea {
                    viewModel.selectAudioFile()
                }
            }
            
            // Output Directory Selection
            if viewModel.selectedFile != nil {
                OutputDirectorySelector(viewModel: viewModel)
            }
        }
    }
}

// MARK: - Supporting Views

struct SelectedFileView: View {
    let file: URL
    let onRemove: () -> Void
    
    private var fileSize: String {
        do {
            let attributes = try FileManager.default.attributesOfItem(atPath: file.path)
            if let size = attributes[.size] as? Int64 {
                return ByteCountFormatter.string(fromByteCount: size, countStyle: .file)
            }
        } catch {}
        return "Unknown size"
    }
    
    private var fileType: String {
        let ext = file.pathExtension.lowercased()
        switch ext {
        case "mp3", "wav", "m4a", "aac":
            return "Audio File"
        case "mp4", "mov", "avi", "mkv":
            return "Video File"
        default:
            return "Media File"
        }
    }
    
    var body: some View {
        HStack(spacing: 16) {
            // File icon
            Image(systemName: file.pathExtension.lowercased().contains("mp4") || 
                             file.pathExtension.lowercased().contains("mov") || 
                             file.pathExtension.lowercased().contains("avi") 
                             ? "video.fill" : "waveform")
                .font(.system(size: 32))
                .foregroundColor(.accentColor)
                .frame(width: 48, height: 48)
                .background(.quaternary, in: RoundedRectangle(cornerRadius: 8))
            
            // File info
            VStack(alignment: .leading, spacing: 4) {
                Text(file.lastPathComponent)
                    .font(.headline)
                    .lineLimit(1)
                
                Text(fileType)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                
                Text(fileSize)
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
            
            Spacer()
            
            // Remove button
            Button(action: onRemove) {
                Image(systemName: "xmark.circle.fill")
                    .font(.title2)
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
            .help("Remove file")
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
}

struct FileDropArea: View {
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 16) {
                Image(systemName: "plus.circle.dashed")
                    .font(.system(size: 48))
                    .foregroundColor(.accentColor)
                
                Text("Select Audio or Video File")
                    .font(.headline)
                
                Text("Choose an audio or video file to transcribe")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                
                Text("Supported: MP3, WAV, M4A, MP4, MOV, AVI")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
            .frame(maxWidth: .infinity)
            .padding(32)
            .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 16))
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .strokeBorder(.quaternary, style: StrokeStyle(lineWidth: 2, dash: [8, 4]))
            )
        }
        .buttonStyle(.plain)
        .help("Click to select a file")
    }
}

struct OutputDirectorySelector: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Output Directory")
                .font(.headline)
            
            HStack {
                if let outputDir = viewModel.outputDirectory {
                    HStack(spacing: 12) {
                        Image(systemName: "folder.fill")
                            .foregroundColor(.accentColor)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text(outputDir.lastPathComponent)
                                .font(.subheadline)
                                .fontWeight(.medium)
                            Text(outputDir.path)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(1)
                        }
                        
                        Spacer()
                    }
                    .padding(.vertical, 8)
                    .padding(.horizontal, 12)
                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
                    
                    Button("Change") {
                        viewModel.selectOutputDirectory()
                    }
                    .buttonStyle(.bordered)
                } else {
                    Button("Select Output Directory") {
                        viewModel.selectOutputDirectory()
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
        }
    }
}

#Preview("With File") {
    let viewModel = TranscriptionViewModel()
    viewModel.selectedFile = URL(fileURLWithPath: "/test/audio.mp3")
    viewModel.outputDirectory = URL(fileURLWithPath: "/test/output")
    
    return FileSelectionSection(viewModel: viewModel)
        .padding()
        .frame(width: 600)
}

#Preview("Empty") {
    let viewModel = TranscriptionViewModel()
    
    return FileSelectionSection(viewModel: viewModel)
        .padding()
        .frame(width: 600)
}