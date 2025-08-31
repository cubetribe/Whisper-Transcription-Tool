import SwiftUI
import AppKit

struct BatchSummaryView: View {
    @ObservedObject var viewModel: TranscriptionViewModel
    @State private var showingExportSheet = false
    @State private var exportFormat: ExportFormat = .csv
    
    private var batchStatistics: BatchStatistics {
        BatchStatistics(from: viewModel.transcriptionQueue)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header
            HStack {
                Image(systemName: "chart.bar.doc.horizontal")
                    .foregroundColor(.accentColor)
                Text("Batch Summary")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Button("Export Summary") {
                    showingExportSheet = true
                }
                .buttonStyle(.bordered)
            }
            
            // Statistics Grid
            LazyVGrid(columns: [
                GridItem(.flexible(minimum: 150)),
                GridItem(.flexible(minimum: 150)),
                GridItem(.flexible(minimum: 150)),
                GridItem(.flexible(minimum: 150))
            ], spacing: 16) {
                
                StatisticCard(
                    title: "Total Files",
                    value: "\(batchStatistics.totalFiles)",
                    icon: "doc.text",
                    color: .secondary
                )
                
                StatisticCard(
                    title: "Completed",
                    value: "\(batchStatistics.completedFiles)",
                    icon: "checkmark.circle.fill",
                    color: .green
                )
                
                StatisticCard(
                    title: "Failed",
                    value: "\(batchStatistics.failedFiles)",
                    icon: "xmark.circle.fill",
                    color: .red
                )
                
                StatisticCard(
                    title: "Success Rate",
                    value: "\(Int(batchStatistics.successRate * 100))%",
                    icon: "chart.pie",
                    color: batchStatistics.successRate > 0.8 ? .green : .orange
                )
            }
            
            // Processing Time and Performance
            LazyVGrid(columns: [
                GridItem(.flexible(minimum: 200)),
                GridItem(.flexible(minimum: 200))
            ], spacing: 16) {
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Processing Time")
                        .font(.headline)
                    
                    HStack {
                        Image(systemName: "clock")
                            .foregroundColor(.blue)
                        Text("Total: \(formatDuration(batchStatistics.totalProcessingTime))")
                            .font(.subheadline)
                    }
                    
                    HStack {
                        Image(systemName: "speedometer")
                            .foregroundColor(.blue)
                        Text("Average: \(formatDuration(batchStatistics.averageProcessingTime))")
                            .font(.subheadline)
                    }
                }
                .padding()
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("File Types")
                        .font(.headline)
                    
                    ForEach(Array(batchStatistics.fileTypeBreakdown.keys.sorted()), id: \.self) { type in
                        HStack {
                            Image(systemName: type.lowercased().contains("mp4") || type.lowercased().contains("mov") ? "video" : "waveform")
                                .foregroundColor(.accentColor)
                                .frame(width: 16)
                            
                            Text(type.uppercased())
                                .font(.caption)
                                .fontFamily(.monospaced)
                            
                            Spacer()
                            
                            Text("\(batchStatistics.fileTypeBreakdown[type] ?? 0)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .padding()
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
            }
            
            // Quick Actions
            HStack(spacing: 12) {
                Button("Open All Results") {
                    viewModel.openAllResults()
                }
                .buttonStyle(.bordered)
                .disabled(batchStatistics.completedFiles == 0)
                
                Button("Reveal All in Finder") {
                    viewModel.revealAllResults()
                }
                .buttonStyle(.bordered)
                .disabled(batchStatistics.completedFiles == 0)
                
                if batchStatistics.failedFiles > 0 {
                    Button("Retry Failed") {
                        viewModel.retryFailedTasks()
                    }
                    .buttonStyle(.borderedProminent)
                }
                
                Spacer()
                
                if batchStatistics.completedFiles > 0 {
                    Button("Play Success Sound") {
                        playCompletionSound()
                    }
                    .buttonStyle(.borderless)
                    .help("Play completion notification sound")
                }
            }
        }
        .padding()
        .background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 12))
        .sheet(isPresented: $showingExportSheet) {
            ExportSummarySheet(
                statistics: batchStatistics,
                tasks: viewModel.transcriptionQueue,
                exportFormat: $exportFormat
            )
        }
    }
    
    private func formatDuration(_ seconds: TimeInterval) -> String {
        if seconds < 60 {
            return String(format: "%.0fs", seconds)
        } else if seconds < 3600 {
            let minutes = Int(seconds / 60)
            let remainingSeconds = Int(seconds.truncatingRemainder(dividingBy: 60))
            return "\(minutes)m \(remainingSeconds)s"
        } else {
            let hours = Int(seconds / 3600)
            let remainingMinutes = Int((seconds / 60).truncatingRemainder(dividingBy: 60))
            return "\(hours)h \(remainingMinutes)m"
        }
    }
    
    private func playCompletionSound() {
        NSSound(named: .glass)?.play()
    }
}

// MARK: - Supporting Views

struct StatisticCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.title2)
                
                Spacer()
            }
            
            Text(value)
                .font(.title)
                .fontWeight(.bold)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
    }
}

struct ExportSummarySheet: View {
    let statistics: BatchStatistics
    let tasks: [TranscriptionTask]
    @Binding var exportFormat: ExportFormat
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Export Batch Summary")
                .font(.title2)
                .fontWeight(.semibold)
            
            VStack(alignment: .leading, spacing: 12) {
                Text("Export Format:")
                    .font(.headline)
                
                Picker("Format", selection: $exportFormat) {
                    ForEach(ExportFormat.allCases, id: \.self) { format in
                        HStack {
                            Image(systemName: format.icon)
                            Text(format.displayName)
                        }
                        .tag(format)
                    }
                }
                .pickerStyle(.segmented)
            }
            
            // Preview
            VStack(alignment: .leading, spacing: 8) {
                Text("Preview:")
                    .font(.headline)
                
                ScrollView {
                    Text(generateExportPreview())
                        .font(.caption)
                        .fontFamily(.monospaced)
                        .padding()
                        .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 6))
                }
                .frame(height: 200)
            }
            
            HStack {
                Button("Cancel") {
                    dismiss()
                }
                .buttonStyle(.bordered)
                
                Spacer()
                
                Button("Export") {
                    exportSummary()
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(24)
        .frame(width: 500, height: 400)
    }
    
    private func generateExportPreview() -> String {
        switch exportFormat {
        case .csv:
            return generateCSVPreview()
        case .json:
            return generateJSONPreview()
        }
    }
    
    private func generateCSVPreview() -> String {
        var csv = "File,Status,Model,Formats,Processing Time,Error\n"
        
        for task in tasks.prefix(5) {
            let status = task.status.rawValue
            let model = task.model
            let formats = task.formats.map(\.rawValue).joined(separator: ";")
            let processingTime = String(format: "%.1f", task.processingTime ?? 0)
            let error = task.errorMessage?.replacingOccurrences(of: "\"", with: "\"\"") ?? ""
            
            csv += "\"\(task.inputURL.lastPathComponent)\",\(status),\(model),\"\(formats)\",\(processingTime),\"\(error)\"\n"
        }
        
        if tasks.count > 5 {
            csv += "... and \(tasks.count - 5) more files\n"
        }
        
        return csv
    }
    
    private func generateJSONPreview() -> String {
        let summary = [
            "batch_summary": [
                "total_files": statistics.totalFiles,
                "completed_files": statistics.completedFiles,
                "failed_files": statistics.failedFiles,
                "success_rate": statistics.successRate,
                "total_processing_time": statistics.totalProcessingTime,
                "average_processing_time": statistics.averageProcessingTime
            ],
            "file_types": statistics.fileTypeBreakdown
        ]
        
        if let jsonData = try? JSONSerialization.data(withJSONObject: summary, options: .prettyPrinted),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            return jsonString
        }
        
        return "{ \"error\": \"Failed to generate JSON preview\" }"
    }
    
    private func exportSummary() {
        let savePanel = NSSavePanel()
        savePanel.allowedContentTypes = [exportFormat.contentType]
        savePanel.nameFieldStringValue = "batch-summary.\(exportFormat.fileExtension)"
        
        savePanel.begin { result in
            if result == .OK, let url = savePanel.url {
                do {
                    let content = exportFormat == .csv ? 
                        BatchSummaryExporter.generateCSV(from: tasks, statistics: statistics) :
                        BatchSummaryExporter.generateJSON(from: tasks, statistics: statistics)
                    
                    try content.write(to: url, atomically: true, encoding: .utf8)
                    
                    // Show success notification
                    DispatchQueue.main.async {
                        dismiss()
                    }
                } catch {
                    // Handle error
                    print("Failed to export summary: \(error)")
                }
            }
        }
    }
}

// MARK: - Data Models

enum ExportFormat: CaseIterable {
    case csv
    case json
    
    var displayName: String {
        switch self {
        case .csv: return "CSV"
        case .json: return "JSON"
        }
    }
    
    var icon: String {
        switch self {
        case .csv: return "tablecells"
        case .json: return "curlybraces"
        }
    }
    
    var fileExtension: String {
        switch self {
        case .csv: return "csv"
        case .json: return "json"
        }
    }
    
    var contentType: UTType {
        switch self {
        case .csv: return .commaSeparatedText
        case .json: return .json
        }
    }
}

struct BatchStatistics {
    let totalFiles: Int
    let completedFiles: Int
    let failedFiles: Int
    let successRate: Double
    let totalProcessingTime: TimeInterval
    let averageProcessingTime: TimeInterval
    let fileTypeBreakdown: [String: Int]
    
    init(from tasks: [TranscriptionTask]) {
        totalFiles = tasks.count
        completedFiles = tasks.filter { $0.status == .completed }.count
        failedFiles = tasks.filter { $0.status == .failed }.count
        successRate = totalFiles > 0 ? Double(completedFiles) / Double(totalFiles) : 0.0
        
        let processingTimes = tasks.compactMap { $0.processingTime }
        totalProcessingTime = processingTimes.reduce(0, +)
        averageProcessingTime = processingTimes.isEmpty ? 0 : totalProcessingTime / Double(processingTimes.count)
        
        // Calculate file type breakdown
        var breakdown: [String: Int] = [:]
        for task in tasks {
            let ext = task.inputURL.pathExtension.lowercased()
            breakdown[ext] = (breakdown[ext] ?? 0) + 1
        }
        fileTypeBreakdown = breakdown
    }
}

// MARK: - Export Utility

struct BatchSummaryExporter {
    static func generateCSV(from tasks: [TranscriptionTask], statistics: BatchStatistics) -> String {
        var csv = "File,Status,Model,Formats,Processing Time (s),Error Message,Input Path,Output Path\n"
        
        for task in tasks {
            let fields = [
                escapeCSVField(task.inputURL.lastPathComponent),
                task.status.rawValue,
                task.model,
                escapeCSVField(task.formats.map(\.rawValue).joined(separator: "; ")),
                String(format: "%.2f", task.processingTime ?? 0),
                escapeCSVField(task.errorMessage ?? ""),
                escapeCSVField(task.inputURL.path),
                escapeCSVField(task.outputDirectory.path)
            ]
            csv += fields.joined(separator: ",") + "\n"
        }
        
        return csv
    }
    
    static func generateJSON(from tasks: [TranscriptionTask], statistics: BatchStatistics) -> String {
        let export = BatchExportData(
            summary: BatchSummaryData(statistics: statistics),
            tasks: tasks.map { TaskExportData(task: $0) }
        )
        
        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted
        encoder.dateEncodingStrategy = .iso8601
        
        do {
            let data = try encoder.encode(export)
            return String(data: data, encoding: .utf8) ?? "Failed to encode JSON"
        } catch {
            return "{ \"error\": \"Failed to encode batch summary: \(error.localizedDescription)\" }"
        }
    }
    
    private static func escapeCSVField(_ field: String) -> String {
        let escaped = field.replacingOccurrences(of: "\"", with: "\"\"")
        return "\"\(escaped)\""
    }
}

struct BatchExportData: Codable {
    let timestamp = Date()
    let summary: BatchSummaryData
    let tasks: [TaskExportData]
}

struct BatchSummaryData: Codable {
    let totalFiles: Int
    let completedFiles: Int
    let failedFiles: Int
    let successRate: Double
    let totalProcessingTime: TimeInterval
    let averageProcessingTime: TimeInterval
    let fileTypeBreakdown: [String: Int]
    
    init(statistics: BatchStatistics) {
        self.totalFiles = statistics.totalFiles
        self.completedFiles = statistics.completedFiles
        self.failedFiles = statistics.failedFiles
        self.successRate = statistics.successRate
        self.totalProcessingTime = statistics.totalProcessingTime
        self.averageProcessingTime = statistics.averageProcessingTime
        self.fileTypeBreakdown = statistics.fileTypeBreakdown
    }
}

struct TaskExportData: Codable {
    let fileName: String
    let status: String
    let model: String
    let formats: [String]
    let processingTime: Double?
    let errorMessage: String?
    let inputPath: String
    let outputPath: String
    
    init(task: TranscriptionTask) {
        self.fileName = task.inputURL.lastPathComponent
        self.status = task.status.rawValue
        self.model = task.model
        self.formats = task.formats.map(\.rawValue)
        self.processingTime = task.processingTime
        self.errorMessage = task.errorMessage
        self.inputPath = task.inputURL.path
        self.outputPath = task.outputDirectory.path
    }
}

#Preview {
    let viewModel = TranscriptionViewModel()
    
    // Add sample completed tasks
    let task1 = TranscriptionTask(
        inputURL: URL(fileURLWithPath: "/test/audio1.mp3"),
        outputDirectory: URL(fileURLWithPath: "/test/output"),
        model: "large-v3-turbo",
        formats: [.txt, .srt]
    )
    task1.status = .completed
    task1.processingTime = 15.3
    
    let task2 = TranscriptionTask(
        inputURL: URL(fileURLWithPath: "/test/video.mp4"),
        outputDirectory: URL(fileURLWithPath: "/test/output"),
        model: "large-v3-turbo",
        formats: [.txt]
    )
    task2.status = .failed
    task2.errorMessage = "File not found"
    
    viewModel.transcriptionQueue = [task1, task2]
    
    return BatchSummaryView(viewModel: viewModel)
        .padding()
        .frame(width: 800)
}