import SwiftUI

struct DependencyErrorView: View {
    let dependencyStatus: DependencyStatus
    let onRetry: () -> Void
    let onRepair: () -> Void
    let onReinstall: () -> Void
    
    @State private var showingDetailedInfo = false
    @State private var isRepairing = false
    
    var body: some View {
        VStack(spacing: 24) {
            // Error Icon and Title
            VStack(spacing: 16) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 64))
                    .foregroundColor(.red)
                
                Text("Dependencies Issue")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text(dependencyStatus.description)
                    .font(.title2)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            // Issue Summary
            if case .invalid(let issues, let warnings) = dependencyStatus {
                IssueSummaryCard(issues: issues, warnings: warnings)
            } else if case .missing(let issues, let warnings) = dependencyStatus {
                IssueSummaryCard(issues: issues, warnings: warnings)
            }
            
            // Action Buttons
            VStack(spacing: 12) {
                HStack(spacing: 12) {
                    Button("Retry Validation") {
                        onRetry()
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.large)
                    
                    Button("Attempt Repair") {
                        isRepairing = true
                        onRepair()
                        
                        // Reset repair state after delay
                        DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                            isRepairing = false
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .disabled(isRepairing)
                }
                
                Button("Reinstall Application") {
                    onReinstall()
                }
                .buttonStyle(.bordered)
                .foregroundColor(.red)
                .controlSize(.large)
            }
            
            // Detailed Information Toggle
            VStack(spacing: 12) {
                Button(showingDetailedInfo ? "Hide Details" : "Show Details") {
                    withAnimation {
                        showingDetailedInfo.toggle()
                    }
                }
                .buttonStyle(.borderless)
                .font(.subheadline)
                
                if showingDetailedInfo {
                    DetailedErrorInfo(dependencyStatus: dependencyStatus)
                        .transition(.opacity.combined(with: .slide))
                }
            }
        }
        .padding(32)
        .frame(maxWidth: 600)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
}

struct IssueSummaryCard: View {
    let issues: [DependencyIssue]
    let warnings: [String]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Issues Found")
                .font(.headline)
                .foregroundColor(.red)
            
            // Critical Issues
            if !issues.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Critical Issues (\(issues.count))")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.red)
                    
                    ForEach(issues.prefix(5), id: \.self) { issue in
                        HStack(alignment: .top, spacing: 8) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(.red)
                                .font(.caption)
                                .padding(.top, 2)
                            
                            VStack(alignment: .leading, spacing: 2) {
                                Text(issue.localizedDescription)
                                    .font(.subheadline)
                                
                                if let recovery = issue.recoverySuggestion {
                                    Text(recovery)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                    
                    if issues.count > 5 {
                        Text("... and \(issues.count - 5) more issues")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .padding(.leading, 16)
                    }
                }
            }
            
            // Warnings
            if !warnings.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Warnings (\(warnings.count))")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.orange)
                    
                    ForEach(warnings.prefix(3), id: \.self) { warning in
                        HStack(alignment: .top, spacing: 8) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.orange)
                                .font(.caption)
                                .padding(.top, 2)
                            
                            Text(warning)
                                .font(.subheadline)
                        }
                    }
                    
                    if warnings.count > 3 {
                        Text("... and \(warnings.count - 3) more warnings")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .padding(.leading, 16)
                    }
                }
            }
        }
        .padding()
        .background(.red.opacity(0.05), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(.red.opacity(0.2), lineWidth: 1)
        )
    }
}

struct DetailedErrorInfo: View {
    let dependencyStatus: DependencyStatus
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Detailed Information")
                .font(.headline)
            
            // System Information
            SystemInfoSection()
            
            // Bundle Information
            BundleInfoSection()
            
            // Dependency Status
            DependencyStatusSection(status: dependencyStatus)
        }
        .padding()
        .background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 8))
    }
}

struct SystemInfoSection: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("System Information")
                .font(.subheadline)
                .fontWeight(.medium)
            
            VStack(alignment: .leading, spacing: 4) {
                InfoRow(label: "Architecture", value: ProcessInfo.processInfo.machineArchitecture)
                InfoRow(label: "macOS Version", value: ProcessInfo.processInfo.operatingSystemVersionString)
                InfoRow(label: "Memory", value: "\(ProcessInfo.processInfo.physicalMemory / (1024*1024*1024)) GB")
            }
        }
    }
}

struct BundleInfoSection: View {
    @State private var bundleInfo: BundleInfo?
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Application Bundle")
                .font(.subheadline)
                .fontWeight(.medium)
            
            if let info = bundleInfo {
                VStack(alignment: .leading, spacing: 4) {
                    InfoRow(label: "Bundle Path", value: info.bundlePath)
                    InfoRow(label: "Dependencies Path", value: info.dependenciesPath)
                    InfoRow(label: "Bundle Size", value: info.bundleSizeFormatted)
                    InfoRow(label: "Dependency Count", value: "\(info.dependencyCount)")
                }
            } else {
                Text("Loading bundle information...")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .onAppear {
            bundleInfo = DependencyManager.shared.bundleInfo
        }
    }
}

struct DependencyStatusSection: View {
    let status: DependencyStatus
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Dependency Status")
                .font(.subheadline)
                .fontWeight(.medium)
            
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Circle()
                        .fill(Color(status.color))
                        .frame(width: 8, height: 8)
                    
                    Text("Overall Status")
                        .font(.caption)
                    
                    Spacer()
                    
                    Text(status.description)
                        .font(.caption)
                        .fontFamily(.monospaced)
                }
                
                if case .invalid(let issues, _) = status {
                    Text("Issues: \(issues.map(\.localizedDescription).joined(separator: ", "))")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(3)
                }
            }
        }
    }
}

struct InfoRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text("\(label):")
                .font(.caption)
                .fontWeight(.medium)
                .foregroundStyle(.secondary)
            
            Spacer()
            
            Text(value)
                .font(.caption)
                .fontFamily(.monospaced)
                .lineLimit(1)
                .truncationMode(.middle)
        }
    }
}

// MARK: - Dependency Status View

struct DependencyStatusView: View {
    @ObservedObject var dependencyManager = DependencyManager.shared
    @State private var showingErrorDetails = false
    
    var body: some View {
        Group {
            switch dependencyManager.dependencyStatus {
            case .unknown, .validating:
                DependencyValidatingView()
                
            case .valid:
                DependencyValidView()
                
            case .validWithWarnings(let warnings):
                DependencyWarningView(warnings: warnings)
                
            case .invalid(let issues, let warnings), .missing(let issues, let warnings):
                DependencyErrorView(
                    dependencyStatus: dependencyManager.dependencyStatus,
                    onRetry: {
                        Task {
                            await dependencyManager.validateDependencies()
                        }
                    },
                    onRepair: {
                        Task {
                            await dependencyManager.attemptRepair()
                        }
                    },
                    onReinstall: {
                        openReinstallationGuide()
                    }
                )
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    private func openReinstallationGuide() {
        if let url = URL(string: "https://github.com/your-repo/whisper-macos/releases/latest") {
            NSWorkspace.shared.open(url)
        }
    }
}

struct DependencyValidatingView: View {
    var body: some View {
        VStack(spacing: 20) {
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle())
                .scaleEffect(1.5)
            
            Text("Validating Dependencies...")
                .font(.title2)
                .fontWeight(.medium)
            
            Text("Please wait while we check all required components")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }
}

struct DependencyValidView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64))
                .foregroundColor(.green)
            
            Text("All Dependencies Valid")
                .font(.title2)
                .fontWeight(.medium)
            
            Text("All required components are properly installed and functioning")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
    }
}

struct DependencyWarningView: View {
    let warnings: [String]
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 64))
                .foregroundColor(.orange)
            
            Text("Dependencies Valid with Warnings")
                .font(.title2)
                .fontWeight(.medium)
            
            Text("Some components have minor issues but should work normally")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            
            // Warning List
            VStack(alignment: .leading, spacing: 8) {
                ForEach(warnings.prefix(3), id: \.self) { warning in
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: "exclamationmark.triangle")
                            .foregroundColor(.orange)
                            .font(.caption)
                        
                        Text(warning)
                            .font(.subheadline)
                    }
                }
                
                if warnings.count > 3 {
                    Text("... and \(warnings.count - 3) more warnings")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding()
            .background(.orange.opacity(0.05), in: RoundedRectangle(cornerRadius: 8))
        }
    }
}

#Preview("Dependency Error") {
    DependencyErrorView(
        dependencyStatus: .invalid(
            issues: [
                .missingPython,
                .whisperBinaryNotExecutable,
                .missingFFmpegBinary
            ],
            warnings: [
                "Python version may be outdated",
                "Some models are not available"
            ]
        ),
        onRetry: {},
        onRepair: {},
        onReinstall: {}
    )
}

#Preview("Dependency Status Valid") {
    DependencyValidView()
}

#Preview("Dependency Status Validating") {
    DependencyValidatingView()
}