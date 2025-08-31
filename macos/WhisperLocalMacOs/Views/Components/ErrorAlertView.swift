import SwiftUI

/// Comprehensive error alert view with recovery actions and detailed information
struct ErrorAlertView: View {
    let error: AppError
    let onDismiss: () -> Void
    let onRetry: (() -> Void)?
    let onReportBug: ((AppError) -> Void)?
    
    @State private var showDetails = false
    @State private var isReporting = false
    
    init(
        error: AppError,
        onDismiss: @escaping () -> Void,
        onRetry: (() -> Void)? = nil,
        onReportBug: ((AppError) -> Void)? = nil
    ) {
        self.error = error
        self.onDismiss = onDismiss
        self.onRetry = onRetry
        self.onReportBug = onReportBug
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header with severity indicator
            HStack {
                severityIcon
                    .font(.title2)
                    .foregroundColor(severityColor)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("Error")
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    Text(severityDescription)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Severity badge
                Text(error.severity.rawValue.capitalized)
                    .font(.caption2)
                    .fontWeight(.medium)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(severityColor.opacity(0.2))
                    .foregroundColor(severityColor)
                    .clipShape(Capsule())
            }
            
            Divider()
            
            // Error description
            Text(error.localizedDescription)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
            
            // Recovery suggestion
            if let recoverySuggestion = error.recoverySuggestion, !recoverySuggestion.isEmpty {
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: "lightbulb")
                        .foregroundColor(.orange)
                        .font(.body)
                    
                    Text(recoverySuggestion)
                        .font(.body)
                        .foregroundColor(.primary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(.vertical, 8)
                .padding(.horizontal, 12)
                .background(Color.orange.opacity(0.1))
                .cornerRadius(8)
            }
            
            // Details section (expandable)
            if showDetails {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Error Details")
                            .font(.subheadline)
                            .fontWeight(.medium)
                        
                        Spacer()
                        
                        Button(action: copyErrorDetails) {
                            HStack(spacing: 4) {
                                Image(systemName: "doc.on.doc")
                                Text("Copy")
                            }
                            .font(.caption)
                        }
                        .buttonStyle(.plain)
                    }
                    
                    Group {
                        DetailRow(label: "Category", value: error.category.rawValue.replacingOccurrences(of: "_", with: " ").capitalized)
                        DetailRow(label: "Severity", value: error.severity.rawValue.capitalized)
                        DetailRow(label: "Recoverable", value: error.isRecoverable ? "Yes" : "No")
                        
                        if let failureReason = error.failureReason {
                            DetailRow(label: "Failure Reason", value: failureReason)
                        }
                        
                        if let helpAnchor = error.helpAnchor {
                            DetailRow(label: "Help Reference", value: helpAnchor)
                        }
                        
                        DetailRow(label: "Timestamp", value: DateFormatter.errorTimestamp.string(from: Date()))
                    }
                    .font(.caption)
                    .foregroundColor(.secondary)
                }
                .padding(.vertical, 8)
                .padding(.horizontal, 12)
                .background(Color.secondary.opacity(0.1))
                .cornerRadius(8)
            }
            
            // Action buttons
            HStack(spacing: 12) {
                // Details toggle
                Button(action: { showDetails.toggle() }) {
                    HStack(spacing: 4) {
                        Image(systemName: showDetails ? "chevron.up" : "chevron.down")
                        Text(showDetails ? "Hide Details" : "Show Details")
                    }
                    .font(.caption)
                }
                .buttonStyle(.plain)
                
                Spacer()
                
                // Bug report button (if available and critical error)
                if let onReportBug = onReportBug, error.severity >= .high {
                    Button(action: { reportBug() }) {
                        HStack(spacing: 4) {
                            if isReporting {
                                ProgressView()
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "ant")
                            }
                            Text(isReporting ? "Reporting..." : "Report Bug")
                        }
                        .font(.caption)
                    }
                    .disabled(isReporting)
                    .buttonStyle(.plain)
                }
                
                // Retry button (if available and recoverable)
                if let onRetry = onRetry, error.isRecoverable {
                    Button(action: onRetry) {
                        HStack(spacing: 4) {
                            Image(systemName: "arrow.clockwise")
                            Text("Retry")
                        }
                        .font(.caption)
                    }
                    .buttonStyle(.borderedProminent)
                }
                
                // Dismiss button
                Button(action: onDismiss) {
                    Text("OK")
                        .fontWeight(.medium)
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(20)
        .frame(minWidth: 400, maxWidth: 500)
        .background(Color(NSColor.windowBackgroundColor))
    }
    
    // MARK: - Helper Views
    
    private var severityIcon: some View {
        switch error.severity {
        case .low:
            return Image(systemName: "info.circle")
        case .medium:
            return Image(systemName: "exclamationmark.triangle")
        case .high:
            return Image(systemName: "xmark.octagon")
        case .critical:
            return Image(systemName: "xmark.circle.fill")
        }
    }
    
    private var severityColor: Color {
        switch error.severity {
        case .low:
            return .blue
        case .medium:
            return .orange
        case .high:
            return .red
        case .critical:
            return .red
        }
    }
    
    private var severityDescription: String {
        switch error.severity {
        case .low:
            return "Information or minor issue"
        case .medium:
            return "Warning that may affect operation"
        case .high:
            return "Significant error requiring attention"
        case .critical:
            return "Critical error that prevents operation"
        }
    }
    
    // MARK: - Actions
    
    private func copyErrorDetails() {
        let errorDetails = """
        Error Report
        ============
        Time: \(DateFormatter.errorTimestamp.string(from: Date()))
        Category: \(error.category.rawValue.replacingOccurrences(of: "_", with: " ").capitalized)
        Severity: \(error.severity.rawValue.capitalized)
        Recoverable: \(error.isRecoverable ? "Yes" : "No")
        
        Description:
        \(error.localizedDescription)
        
        Recovery Suggestion:
        \(error.recoverySuggestion ?? "None provided")
        
        Failure Reason:
        \(error.failureReason ?? "Not specified")
        
        Help Reference: \(error.helpAnchor ?? "N/A")
        """
        
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(errorDetails, forType: .string)
    }
    
    private func reportBug() {
        guard let onReportBug = onReportBug else { return }
        
        isReporting = true
        
        // Simulate async bug reporting
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            onReportBug(error)
            isReporting = false
        }
    }
}

// MARK: - Supporting Views

private struct DetailRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text("\(label):")
                .fontWeight(.medium)
                .frame(minWidth: 100, alignment: .leading)
            
            Text(value)
                .textSelection(.enabled)
            
            Spacer()
        }
    }
}

// MARK: - Error Recovery Actions

struct ErrorRecoveryActions {
    /// Attempt automatic recovery for the given error
    static func attemptRecovery(for error: AppError) async -> Bool {
        switch error {
        case .fileProcessing(let fileError):
            return await recoverFromFileError(fileError)
        case .modelManagement(let modelError):
            return await recoverFromModelError(modelError)
        case .systemResource(let resourceError):
            return await recoverFromResourceError(resourceError)
        case .pythonBridge(let bridgeError):
            return await recoverFromBridgeError(bridgeError)
        case .userInput, .configuration:
            return false // Requires user intervention
        }
    }
    
    private static func recoverFromFileError(_ error: FileProcessingError) async -> Bool {
        switch error {
        case .fileNotReadable, .outputDirectoryNotWritable:
            // Wait and retry after permission might have changed
            try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
            return true
        case .fileTooLarge:
            // Could attempt compression or chunking, but not implemented
            return false
        default:
            return false
        }
    }
    
    private static func recoverFromModelError(_ error: ModelError) async -> Bool {
        switch error {
        case .modelNotDownloaded:
            // Could trigger automatic download, but requires user confirmation
            return false
        case .downloadFailed:
            // Wait and retry download
            try? await Task.sleep(nanoseconds: 5_000_000_000) // 5 seconds
            return true
        default:
            return false
        }
    }
    
    private static func recoverFromResourceError(_ error: ResourceError) async -> Bool {
        switch error {
        case .cpuOverloaded, .thermalThrottling:
            // Wait for system to cool down
            try? await Task.sleep(nanoseconds: 10_000_000_000) // 10 seconds
            return true
        case .networkUnavailable:
            // Wait and retry network
            try? await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds
            return true
        default:
            return false
        }
    }
    
    private static func recoverFromBridgeError(_ error: BridgeError) async -> Bool {
        switch error {
        case .communicationTimeout:
            // Retry with longer timeout
            return true
        case .processExecutionFailed:
            // Wait and retry process
            try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
            return true
        default:
            return false
        }
    }
}

// MARK: - Bug Reporting

struct BugReporter {
    /// Generate a comprehensive bug report for the error
    static func generateReport(for error: AppError) -> BugReport {
        BugReport(
            error: error,
            timestamp: Date(),
            systemInfo: SystemInfo.current,
            appVersion: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown"
        )
    }
    
    /// Submit bug report (placeholder implementation)
    static func submitReport(_ report: BugReport) async throws {
        // In a real implementation, this would send to analytics service
        // For now, we'll just log it
        print("Bug Report Submitted:")
        print(report.formattedDescription)
    }
}

struct BugReport {
    let error: AppError
    let timestamp: Date
    let systemInfo: SystemInfo
    let appVersion: String
    
    var formattedDescription: String {
        """
        BUG REPORT
        ==========
        App Version: \(appVersion)
        Timestamp: \(DateFormatter.errorTimestamp.string(from: timestamp))
        
        ERROR DETAILS
        -------------
        Category: \(error.category.rawValue)
        Severity: \(error.severity.rawValue)
        Recoverable: \(error.isRecoverable)
        Description: \(error.localizedDescription)
        Recovery: \(error.recoverySuggestion ?? "None")
        Failure Reason: \(error.failureReason ?? "Not specified")
        
        SYSTEM INFORMATION
        ------------------
        macOS Version: \(systemInfo.osVersion)
        Architecture: \(systemInfo.architecture)
        Memory: \(systemInfo.totalMemory) GB
        Available Disk: \(systemInfo.availableDiskSpace) GB
        """
    }
}

struct SystemInfo {
    let osVersion: String
    let architecture: String
    let totalMemory: Int
    let availableDiskSpace: Int
    
    static var current: SystemInfo {
        let processInfo = ProcessInfo.processInfo
        let osVersion = processInfo.operatingSystemVersionString
        
        #if arch(arm64)
        let architecture = "Apple Silicon (ARM64)"
        #elseif arch(x86_64)
        let architecture = "Intel (x86_64)"
        #else
        let architecture = "Unknown"
        #endif
        
        let totalMemory = Int(processInfo.physicalMemory / (1024 * 1024 * 1024))
        
        // Get available disk space
        var availableDiskSpace: Int = 0
        if let homeURL = FileManager.default.urls(for: .homeDirectory, in: .userDomainMask).first,
           let resourceValues = try? homeURL.resourceValues(forKeys: [.volumeAvailableCapacityKey]) {
            availableDiskSpace = Int((resourceValues.volumeAvailableCapacity ?? 0) / (1024 * 1024 * 1024))
        }
        
        return SystemInfo(
            osVersion: osVersion,
            architecture: architecture,
            totalMemory: totalMemory,
            availableDiskSpace: availableDiskSpace
        )
    }
}

// MARK: - Extensions

private extension DateFormatter {
    static let errorTimestamp: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .medium
        return formatter
    }()
}

// MARK: - Preview

#if DEBUG
struct ErrorAlertView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            ErrorAlertView(
                error: .fileProcessing(.fileNotFound("/path/to/file.mp3")),
                onDismiss: {},
                onRetry: {}
            )
            .previewDisplayName("File Error")
            
            ErrorAlertView(
                error: .systemResource(.insufficientMemory(required: 2_000_000_000, available: 500_000_000)),
                onDismiss: {},
                onReportBug: { _ in }
            )
            .previewDisplayName("System Error")
            
            ErrorAlertView(
                error: .pythonBridge(.pythonNotFound(searchPaths: ["/usr/bin/python", "/usr/local/bin/python"])),
                onDismiss: {}
            )
            .previewDisplayName("Critical Error")
        }
        .frame(width: 500, height: 400)
    }
}
#endif