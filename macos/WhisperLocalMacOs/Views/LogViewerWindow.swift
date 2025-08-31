import SwiftUI
import UniformTypeIdentifiers

/// Comprehensive log viewer window with filtering, search, and export functionality
struct LogViewerWindow: View {
    @StateObject private var logger = Logger.shared
    @State private var searchText = ""
    @State private var selectedLevel: LogLevel? = nil
    @State private var selectedCategory: LogCategory? = nil
    @State private var selectedEntry: LogEntry? = nil
    @State private var showingExportPanel = false
    @State private var autoScroll = true
    @State private var isExporting = false
    @State private var showingClearConfirmation = false
    @State private var isFollowingLatest = true
    @State private var refreshTimer: Timer? = nil
    
    private let exportType = UTType.plainText
    
    // Filtered logs computed property
    private var filteredLogs: [LogEntry] {
        var logs = logger.recentLogs
        
        // Filter by search text
        if !searchText.isEmpty {
            logs = logs.filter { entry in
                entry.message.localizedCaseInsensitiveContains(searchText) ||
                entry.category.displayName.localizedCaseInsensitiveContains(searchText) ||
                entry.file.localizedCaseInsensitiveContains(searchText) ||
                entry.function.localizedCaseInsensitiveContains(searchText)
            }
        }
        
        // Filter by level
        if let selectedLevel = selectedLevel {
            logs = logs.filter { $0.level.severity >= selectedLevel.severity }
        }
        
        // Filter by category
        if let selectedCategory = selectedCategory {
            logs = logs.filter { $0.category == selectedCategory }
        }
        
        return logs.sorted { $0.timestamp > $1.timestamp }
    }
    
    var body: some View {
        NavigationSplitView {
            // Sidebar with filters and controls
            VStack(spacing: 16) {
                // Search
                VStack(alignment: .leading, spacing: 8) {
                    Text("Search")
                        .font(.headline)
                    
                    TextField("Search logs...", text: $searchText)
                        .textFieldStyle(.roundedBorder)
                }
                
                Divider()
                
                // Level filter
                VStack(alignment: .leading, spacing: 8) {
                    Text("Log Level")
                        .font(.headline)
                    
                    Picker("Level", selection: $selectedLevel) {
                        Text("All Levels").tag(nil as LogLevel?)
                        ForEach(LogLevel.allCases, id: \.self) { level in
                            HStack {
                                Text(level.icon)
                                Text(level.rawValue.capitalized)
                            }
                            .tag(level as LogLevel?)
                        }
                    }
                    .pickerStyle(.menu)
                }
                
                // Category filter
                VStack(alignment: .leading, spacing: 8) {
                    Text("Category")
                        .font(.headline)
                    
                    Picker("Category", selection: $selectedCategory) {
                        Text("All Categories").tag(nil as LogCategory?)
                        ForEach(LogCategory.allCases, id: \.self) { category in
                            HStack {
                                Image(systemName: category.icon)
                                Text(category.displayName)
                            }
                            .tag(category as LogCategory?)
                        }
                    }
                    .pickerStyle(.menu)
                }
                
                Divider()
                
                // Stats
                VStack(alignment: .leading, spacing: 8) {
                    Text("Statistics")
                        .font(.headline)
                    
                    LogStatsView(logs: filteredLogs)
                }
                
                Spacer()
                
                // Controls
                VStack(spacing: 8) {
                    Toggle("Auto-scroll to latest", isOn: $autoScroll)
                        .font(.caption)
                    
                    Toggle("Follow latest logs", isOn: $isFollowingLatest)
                        .font(.caption)
                        .onChange(of: isFollowingLatest) { following in
                            if following {
                                startRefreshTimer()
                            } else {
                                stopRefreshTimer()
                            }
                        }
                    
                    Divider()
                    
                    Button("Clear Filters") {
                        clearFilters()
                    }
                    .buttonStyle(.plain)
                    .font(.caption)
                    
                    Button("Export Logs") {
                        showingExportPanel = true
                    }
                    .buttonStyle(.borderedProminent)
                    .font(.caption)
                    .disabled(isExporting)
                    
                    Button("Clear Logs") {
                        showingClearConfirmation = true
                    }
                    .buttonStyle(.bordered)
                    .foregroundColor(.red)
                    .font(.caption)
                }
            }
            .padding()
            .frame(minWidth: 250, maxWidth: 300)
        } detail: {
            // Main log view
            VStack(spacing: 0) {
                // Header with count and controls
                HStack {
                    Text("\(filteredLogs.count) logs")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    
                    if !searchText.isEmpty || selectedLevel != nil || selectedCategory != nil {
                        Text("(filtered from \(logger.recentLogs.count))")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    HStack(spacing: 8) {
                        Button(action: refreshLogs) {
                            Image(systemName: "arrow.clockwise")
                        }
                        .buttonStyle(.borderless)
                        .help("Refresh logs")
                        
                        Button(action: scrollToLatest) {
                            Image(systemName: autoScroll ? "eye.fill" : "eye")
                        }
                        .buttonStyle(.borderless)
                        .help("Scroll to latest")
                    }
                }
                .padding(.horizontal)
                .padding(.top, 8)
                
                Divider()
                
                // Log list
                if filteredLogs.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "doc.text.magnifyingglass")
                            .font(.system(size: 48))
                            .foregroundColor(.secondary)
                        
                        Text("No logs found")
                            .font(.title2)
                            .fontWeight(.medium)
                        
                        if !searchText.isEmpty || selectedLevel != nil || selectedCategory != nil {
                            Text("Try adjusting your search or filters")
                                .font(.body)
                                .foregroundColor(.secondary)
                                .multilineTextAlignment(.center)
                        } else {
                            Text("Application logs will appear here")
                                .font(.body)
                                .foregroundColor(.secondary)
                        }
                        
                        Button("Clear Filters") {
                            clearFilters()
                        }
                        .buttonStyle(.bordered)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    LogListView(
                        logs: filteredLogs,
                        selectedEntry: $selectedEntry,
                        autoScroll: autoScroll
                    )
                }
            }
        }
        .navigationTitle("Log Viewer")
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                Button(action: { showingExportPanel = true }) {
                    HStack {
                        Image(systemName: "square.and.arrow.up")
                        Text("Export")
                    }
                }
                .disabled(isExporting || filteredLogs.isEmpty)
                
                Button(action: refreshLogs) {
                    Image(systemName: "arrow.clockwise")
                }
                .help("Refresh logs")
            }
        }
        .fileExporter(
            isPresented: $showingExportPanel,
            document: LogExportDocument(logs: filteredLogs),
            contentType: exportType,
            defaultFilename: "whisper-logs-\(DateFormatter.filenameFriendly.string(from: Date()))"
        ) { result in
            handleExportResult(result)
        }
        .confirmationDialog(
            "Clear Logs",
            isPresented: $showingClearConfirmation
        ) {
            Button("Clear All Logs", role: .destructive) {
                clearLogs()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This will permanently delete all log entries. This action cannot be undone.")
        }
        .onAppear {
            if isFollowingLatest {
                startRefreshTimer()
            }
        }
        .onDisappear {
            stopRefreshTimer()
        }
        .sheet(item: $selectedEntry) { entry in
            LogDetailView(entry: entry)
        }
    }
    
    // MARK: - Actions
    
    private func clearFilters() {
        searchText = ""
        selectedLevel = nil
        selectedCategory = nil
    }
    
    private func refreshLogs() {
        // Logger automatically updates, just trigger UI refresh
        logger.objectWillChange.send()
    }
    
    private func scrollToLatest() {
        autoScroll = true
        // This will be handled by LogListView
    }
    
    private func clearLogs() {
        // This would need to be implemented in Logger
        // For now, we'll just clear the display filters
        clearFilters()
    }
    
    private func handleExportResult(_ result: Result<URL, Error>) {
        isExporting = false
        
        switch result {
        case .success(let url):
            logger.info("Logs exported successfully to \(url.path)", category: .system)
            
            // Show in Finder
            NSWorkspace.shared.activateFileViewerSelecting([url])
            
        case .failure(let error):
            logger.error("Failed to export logs", category: .system, error: error)
        }
    }
    
    private func startRefreshTimer() {
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
            refreshLogs()
        }
    }
    
    private func stopRefreshTimer() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }
}

// MARK: - Supporting Views

struct LogListView: View {
    let logs: [LogEntry]
    @Binding var selectedEntry: LogEntry?
    let autoScroll: Bool
    
    var body: some View {
        ScrollViewReader { proxy in
            List(logs) { entry in
                LogRowView(entry: entry)
                    .onTapGesture {
                        selectedEntry = entry
                    }
                    .id(entry.id)
                    .contextMenu {
                        Button("Copy Message") {
                            NSPasteboard.general.clearContents()
                            NSPasteboard.general.setString(entry.message, forType: .string)
                        }
                        
                        Button("Copy Full Entry") {
                            NSPasteboard.general.clearContents()
                            NSPasteboard.general.setString(entry.formattedForExport, forType: .string)
                        }
                        
                        Button("Show Details") {
                            selectedEntry = entry
                        }
                    }
            }
            .listStyle(.inset)
            .onChange(of: logs.count) { _ in
                if autoScroll && !logs.isEmpty {
                    withAnimation(.easeInOut(duration: 0.5)) {
                        proxy.scrollTo(logs.first?.id, anchor: .top)
                    }
                }
            }
        }
    }
}

struct LogRowView: View {
    let entry: LogEntry
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                // Level indicator
                HStack(spacing: 4) {
                    Text(entry.level.icon)
                        .font(.caption)
                    Text(entry.level.rawValue.uppercased())
                        .font(.caption2)
                        .fontWeight(.medium)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(levelColor.opacity(0.2))
                        .foregroundColor(levelColor)
                        .clipShape(Capsule())
                }
                
                // Category
                HStack(spacing: 4) {
                    Image(systemName: entry.category.icon)
                        .font(.caption2)
                    Text(entry.category.displayName)
                        .font(.caption2)
                        .fontWeight(.medium)
                }
                .foregroundColor(.secondary)
                
                Spacer()
                
                // Timestamp
                Text(DateFormatter.logTimeFormatter.string(from: entry.timestamp))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            // Message
            Text(entry.message)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
            
            // Error info if present
            if let error = entry.error {
                Text("Error: \(error)")
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.top, 2)
            }
            
            // Location info
            Text("\(entry.file):\(entry.line) in \(entry.function)")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
    
    private var levelColor: Color {
        switch entry.level {
        case .debug: return .gray
        case .info: return .blue
        case .warning: return .orange
        case .error: return .red
        case .critical: return .purple
        }
    }
}

struct LogStatsView: View {
    let logs: [LogEntry]
    
    private var stats: [LogLevel: Int] {
        Dictionary(grouping: logs) { $0.level }
            .mapValues { $0.count }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            ForEach(LogLevel.allCases, id: \.self) { level in
                let count = stats[level] ?? 0
                if count > 0 {
                    HStack {
                        Text(level.icon)
                            .font(.caption2)
                        Text(level.rawValue.capitalized)
                            .font(.caption2)
                            .fontWeight(.medium)
                        Spacer()
                        Text("\(count)")
                            .font(.caption2)
                            .fontWeight(.medium)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            if stats.isEmpty {
                Text("No logs")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
    }
}

struct LogDetailView: View {
    let entry: LogEntry
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Log Entry Details")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text(DateFormatter.fullFormatter.string(from: entry.timestamp))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Button("Done") {
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
            }
            
            Divider()
            
            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    DetailGroup(title: "Basic Information") {
                        DetailField(label: "Level", value: "\(entry.level.icon) \(entry.level.rawValue.capitalized)")
                        DetailField(label: "Category", value: entry.category.displayName)
                        DetailField(label: "Timestamp", value: DateFormatter.fullFormatter.string(from: entry.timestamp))
                    }
                    
                    DetailGroup(title: "Message") {
                        Text(entry.message)
                            .textSelection(.enabled)
                            .padding()
                            .background(Color.secondary.opacity(0.1))
                            .cornerRadius(8)
                    }
                    
                    if let error = entry.error {
                        DetailGroup(title: "Error Information") {
                            Text(error)
                                .textSelection(.enabled)
                                .padding()
                                .background(Color.red.opacity(0.1))
                                .cornerRadius(8)
                        }
                    }
                    
                    DetailGroup(title: "Source Location") {
                        DetailField(label: "File", value: entry.file)
                        DetailField(label: "Function", value: entry.function)
                        DetailField(label: "Line", value: "\(entry.line)")
                    }
                    
                    DetailGroup(title: "Export") {
                        Button("Copy to Clipboard") {
                            NSPasteboard.general.clearContents()
                            NSPasteboard.general.setString(entry.formattedForExport, forType: .string)
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding()
            }
        }
        .padding()
        .frame(minWidth: 500, minHeight: 400)
    }
}

struct DetailGroup<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
                .fontWeight(.semibold)
            
            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct DetailField: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack(alignment: .top) {
            Text("\(label):")
                .font(.body)
                .fontWeight(.medium)
                .frame(minWidth: 80, alignment: .leading)
            
            Text(value)
                .font(.body)
                .textSelection(.enabled)
            
            Spacer()
        }
    }
}

// MARK: - Log Export Document

struct LogExportDocument: FileDocument {
    static var readableContentTypes: [UTType] { [.plainText] }
    
    let logs: [LogEntry]
    
    init(logs: [LogEntry]) {
        self.logs = logs
    }
    
    init(configuration: ReadConfiguration) throws {
        // Not used for export-only document
        self.logs = []
    }
    
    func fileWrapper(configuration: WriteConfiguration) throws -> FileWrapper {
        let exportContent = generateExportContent()
        let data = exportContent.data(using: .utf8) ?? Data()
        return FileWrapper(regularFileWithContents: data)
    }
    
    private func generateExportContent() -> String {
        var content = """
        WhisperLocalMacOs Log Export
        ============================
        Generated: \(DateFormatter.fullFormatter.string(from: Date()))
        Total Entries: \(logs.count)
        
        
        """
        
        let sortedLogs = logs.sorted { $0.timestamp < $1.timestamp }
        
        for entry in sortedLogs {
            content += entry.formattedForExport + "\n\n"
        }
        
        return content
    }
}

// MARK: - Date Formatter Extensions

private extension DateFormatter {
    static let logTimeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        return formatter
    }()
    
    static let fullFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .full
        formatter.timeStyle = .medium
        return formatter
    }()
    
    static let filenameFriendly: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd-HHmmss"
        return formatter
    }()
}

// MARK: - Preview

#if DEBUG
struct LogViewerWindow_Previews: PreviewProvider {
    static var previews: some View {
        LogViewerWindow()
            .frame(width: 900, height: 600)
    }
}
#endif