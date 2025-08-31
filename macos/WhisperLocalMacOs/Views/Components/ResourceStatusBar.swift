import SwiftUI

struct ResourceStatusBar: View {
    @ObservedObject var resourceMonitor = ResourceMonitor.shared
    @State private var showingResourceDetails = false
    
    var body: some View {
        HStack(spacing: 12) {
            // Resource Status Indicator
            HStack(spacing: 6) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)
                
                Text(resourceMonitor.resourceStatus.rawValue)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(statusColor)
            }
            
            Divider()
                .frame(height: 16)
            
            // Memory Usage
            ResourceMetricView(
                icon: "memorychip",
                label: "Memory",
                value: "\(resourceMonitor.memoryUsage, specifier: "%.0f")%",
                color: memoryColor
            )
            
            // Disk Space
            let diskSpaceGB = Double(resourceMonitor.diskSpaceAvailable) / (1024 * 1024 * 1024)
            ResourceMetricView(
                icon: "internaldrive",
                label: "Disk",
                value: "\(diskSpaceGB, specifier: "%.1f")GB",
                color: diskSpaceColor
            )
            
            // Thermal State
            ResourceMetricView(
                icon: "thermometer",
                label: "Thermal",
                value: thermalStateText,
                color: thermalColor
            )
            
            // Warnings Indicator
            if !resourceMonitor.activeWarnings.isEmpty {
                Divider()
                    .frame(height: 16)
                
                HStack(spacing: 4) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)
                        .font(.caption)
                    
                    Text("\(resourceMonitor.activeWarnings.count)")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.orange)
                }
                .help("Active resource warnings")
            }
            
            Spacer()
            
            // Details Button
            Button("Details") {
                showingResourceDetails = true
            }
            .buttonStyle(.borderless)
            .font(.caption)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
        .sheet(isPresented: $showingResourceDetails) {
            ResourceDetailsView()
        }
    }
    
    // MARK: - Computed Properties
    
    private var statusColor: Color {
        switch resourceMonitor.resourceStatus {
        case .optimal: return .green
        case .warning: return .orange
        case .critical: return .red
        }
    }
    
    private var memoryColor: Color {
        switch resourceMonitor.memoryUsage {
        case 0..<70: return .green
        case 70..<80: return .yellow
        case 80..<90: return .orange
        default: return .red
        }
    }
    
    private var diskSpaceColor: Color {
        let diskSpaceGB = Double(resourceMonitor.diskSpaceAvailable) / (1024 * 1024 * 1024)
        switch diskSpaceGB {
        case 10...: return .green
        case 5..<10: return .yellow
        case 2..<5: return .orange
        default: return .red
        }
    }
    
    private var thermalColor: Color {
        switch resourceMonitor.thermalState {
        case .nominal: return .green
        case .fair: return .yellow
        case .serious: return .orange
        case .critical: return .red
        @unknown default: return .gray
        }
    }
    
    private var thermalStateText: String {
        switch resourceMonitor.thermalState {
        case .nominal: return "Normal"
        case .fair: return "Warm"
        case .serious: return "Hot"
        case .critical: return "Critical"
        @unknown default: return "Unknown"
        }
    }
}

struct ResourceMetricView: View {
    let icon: String
    let label: String
    let value: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .foregroundColor(color)
                .font(.caption)
            
            VStack(alignment: .leading, spacing: 1) {
                Text(label)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                
                Text(value)
                    .font(.caption)
                    .fontWeight(.medium)
                    .fontFamily(.monospaced)
                    .foregroundColor(color)
            }
        }
        .help("\(label): \(value)")
    }
}

struct ResourceDetailsView: View {
    @ObservedObject var resourceMonitor = ResourceMonitor.shared
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Overall Status
                    ResourceStatusSection()
                    
                    Divider()
                    
                    // Resource Metrics
                    ResourceMetricsSection()
                    
                    Divider()
                    
                    // Active Warnings
                    ResourceWarningsSection()
                    
                    Divider()
                    
                    // Resource Recommendations
                    ResourceRecommendationsSection()
                }
                .padding()
            }
            .navigationTitle("System Resources")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(width: 600, height: 500)
    }
}

struct ResourceStatusSection: View {
    @ObservedObject var resourceMonitor = ResourceMonitor.shared
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Resource Status")
                .font(.headline)
            
            HStack {
                Circle()
                    .fill(statusColor)
                    .frame(width: 20, height: 20)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(resourceMonitor.resourceStatus.rawValue)
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundColor(statusColor)
                    
                    Text(resourceMonitor.resourceStatus.description)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
            }
        }
    }
    
    private var statusColor: Color {
        switch resourceMonitor.resourceStatus {
        case .optimal: return .green
        case .warning: return .orange
        case .critical: return .red
        }
    }
}

struct ResourceMetricsSection: View {
    @ObservedObject var resourceMonitor = ResourceMonitor.shared
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Resource Metrics")
                .font(.headline)
            
            let statistics = resourceMonitor.getResourceStatistics()
            
            VStack(spacing: 12) {
                ResourceMetricRow(
                    icon: "memorychip",
                    title: "Memory Usage",
                    value: statistics.formattedMemoryUsage,
                    progress: statistics.memoryUsagePercentage / 100.0,
                    color: memoryColor(statistics.memoryUsagePercentage)
                )
                
                ResourceMetricRow(
                    icon: "internaldrive",
                    title: "Available Disk Space",
                    value: statistics.formattedDiskSpace,
                    progress: nil,
                    color: diskSpaceColor(statistics.availableDiskSpaceGB)
                )
                
                ResourceMetricRow(
                    icon: "thermometer",
                    title: "Thermal State",
                    value: statistics.thermalStateDescription,
                    progress: nil,
                    color: thermalColor(statistics.thermalState)
                )
            }
        }
    }
    
    private func memoryColor(_ usage: Double) -> Color {
        switch usage {
        case 0..<70: return .green
        case 70..<80: return .yellow
        case 80..<90: return .orange
        default: return .red
        }
    }
    
    private func diskSpaceColor(_ spaceGB: Double) -> Color {
        switch spaceGB {
        case 10...: return .green
        case 5..<10: return .yellow
        case 2..<5: return .orange
        default: return .red
        }
    }
    
    private func thermalColor(_ state: ProcessInfo.ThermalState) -> Color {
        switch state {
        case .nominal: return .green
        case .fair: return .yellow
        case .serious: return .orange
        case .critical: return .red
        @unknown default: return .gray
        }
    }
}

struct ResourceMetricRow: View {
    let icon: String
    let title: String
    let value: String
    let progress: Double?
    let color: Color
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(color)
                .font(.title3)
                .frame(width: 24)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(value)
                    .font(.caption)
                    .fontFamily(.monospaced)
                    .foregroundColor(color)
                
                if let progress = progress {
                    ProgressView(value: progress)
                        .progressViewStyle(LinearProgressViewStyle(tint: color))
                        .frame(width: 200)
                }
            }
            
            Spacer()
        }
        .padding(.vertical, 4)
    }
}

struct ResourceWarningsSection: View {
    @ObservedObject var resourceMonitor = ResourceMonitor.shared
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Active Warnings")
                .font(.headline)
            
            if resourceMonitor.activeWarnings.isEmpty {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    
                    Text("No resource warnings")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            } else {
                ForEach(resourceMonitor.activeWarnings) { warning in
                    ResourceWarningRow(warning: warning)
                }
            }
        }
    }
}

struct ResourceWarningRow: View {
    let warning: ResourceWarning
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: warningIcon)
                .foregroundColor(warningColor)
                .font(.subheadline)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(warning.message)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(warning.recommendation)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            
            Spacer()
            
            Text(warning.timestamp, style: .time)
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .padding()
        .background(warningColor.opacity(0.1), in: RoundedRectangle(cornerRadius: 8))
    }
    
    private var warningIcon: String {
        switch warning.severity {
        case .info: return "info.circle"
        case .warning: return "exclamationmark.triangle"
        case .critical: return "exclamationmark.octagon"
        }
    }
    
    private var warningColor: Color {
        switch warning.severity {
        case .info: return .blue
        case .warning: return .orange
        case .critical: return .red
        }
    }
}

struct ResourceRecommendationsSection: View {
    @ObservedObject var resourceMonitor = ResourceMonitor.shared
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Recommendations")
                .font(.headline)
            
            let batchSizeRecommendation = resourceMonitor.getOptimalBatchSizeRecommendation()
            
            VStack(alignment: .leading, spacing: 8) {
                RecommendationRow(
                    icon: "list.number",
                    title: "Optimal Batch Size",
                    value: "\(batchSizeRecommendation) files",
                    description: "Recommended batch size based on current system resources"
                )
                
                let statistics = resourceMonitor.getResourceStatistics()
                RecommendationRow(
                    icon: "doc.text",
                    title: "Large File Processing",
                    value: statistics.canProcessLargeFiles ? "Supported" : "Not Recommended",
                    description: statistics.canProcessLargeFiles ? "System can handle large files" : "Consider processing smaller files or freeing up resources"
                )
                
                RecommendationRow(
                    icon: "clock",
                    title: "Processing Timing",
                    value: resourceMonitor.resourceStatus == .optimal ? "Optimal" : "Consider Later",
                    description: resourceMonitor.resourceStatus == .optimal ? "Good time for processing" : "Consider waiting or reducing system load"
                )
            }
        }
    }
}

struct RecommendationRow: View {
    let icon: String
    let title: String
    let value: String
    let description: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.blue)
                .font(.subheadline)
                .frame(width: 20)
            
            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(title)
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Spacer()
                    
                    Text(value)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .fontFamily(.monospaced)
                        .foregroundColor(.blue)
                }
                
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 2)
    }
}

#Preview {
    ResourceStatusBar()
        .frame(width: 600)
        .padding()
}