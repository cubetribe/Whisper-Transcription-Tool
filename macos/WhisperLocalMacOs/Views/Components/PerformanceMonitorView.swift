import SwiftUI
import Charts

struct PerformanceMonitorView: View {
    @ObservedObject var performanceManager = PerformanceManager.shared
    @State private var showingSystemInfo = false
    @State private var showingOptimizationDetails = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header
            HStack {
                Image(systemName: "speedometer")
                    .font(.title2)
                    .foregroundColor(.blue)
                
                Text("Performance Monitor")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Button("System Info") {
                    showingSystemInfo = true
                }
                .buttonStyle(.bordered)
            }
            
            // Real-time Metrics
            HStack(spacing: 20) {
                // CPU Usage
                MetricCard(
                    title: "CPU Usage",
                    value: "\(performanceManager.cpuUsage, specifier: "%.1f")%",
                    systemImage: "cpu",
                    color: cpuColor(usage: performanceManager.cpuUsage)
                )
                
                // Memory Usage
                MetricCard(
                    title: "Memory Usage", 
                    value: "\(performanceManager.memoryUsage, specifier: "%.1f")%",
                    systemImage: "memorychip",
                    color: memoryColor(usage: performanceManager.memoryUsage)
                )
                
                // Thermal State
                MetricCard(
                    title: "Thermal State",
                    value: performanceManager.thermalState.rawValue,
                    systemImage: "thermometer",
                    color: thermalColor(state: performanceManager.thermalState)
                )
            }
            
            Divider()
            
            // Apple Silicon Optimization Status
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("Hardware Optimization")
                        .font(.headline)
                    
                    Spacer()
                    
                    Button("Details") {
                        showingOptimizationDetails = true
                    }
                    .buttonStyle(.borderless)
                    .font(.subheadline)
                }
                
                HStack(spacing: 16) {
                    // Apple Silicon Status
                    HStack {
                        Image(systemName: performanceManager.isAppleSilicon ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(performanceManager.isAppleSilicon ? .green : .orange)
                        
                        Text("Apple Silicon")
                            .font(.subheadline)
                    }
                    
                    // Metal Support Status
                    HStack {
                        Image(systemName: performanceManager.isMetalSupported ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(performanceManager.isMetalSupported ? .green : .orange)
                        
                        Text("Metal GPU")
                            .font(.subheadline)
                    }
                    
                    if performanceManager.isMetalSupported,
                       let device = performanceManager.metalDevice {
                        HStack {
                            Image(systemName: device.hasUnifiedMemory ? "checkmark.circle.fill" : "minus.circle.fill")
                                .foregroundColor(device.hasUnifiedMemory ? .green : .gray)
                            
                            Text("Unified Memory")
                                .font(.subheadline)
                        }
                    }
                }
            }
            
            Divider()
            
            // Optimization Recommendations
            OptimizationRecommendationsSection()
            
            Spacer()
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
        .sheet(isPresented: $showingSystemInfo) {
            SystemInfoView()
        }
        .sheet(isPresented: $showingOptimizationDetails) {
            OptimizationDetailsView()
        }
    }
    
    // MARK: - Color Helpers
    
    private func cpuColor(usage: Double) -> Color {
        switch usage {
        case 0..<50: return .green
        case 50..<80: return .orange
        default: return .red
        }
    }
    
    private func memoryColor(usage: Double) -> Color {
        switch usage {
        case 0..<70: return .green
        case 70..<85: return .orange
        default: return .red
        }
    }
    
    private func thermalColor(state: PerformanceManager.ThermalState) -> Color {
        switch state {
        case .nominal: return .green
        case .fair: return .yellow
        case .serious: return .orange
        case .critical: return .red
        }
    }
}

struct MetricCard: View {
    let title: String
    let value: String
    let systemImage: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: systemImage)
                    .foregroundColor(color)
                    .font(.title3)
                
                Spacer()
            }
            
            Text(value)
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(color.opacity(0.3), lineWidth: 1)
        )
    }
}

struct OptimizationRecommendationsSection: View {
    @ObservedObject var performanceManager = PerformanceManager.shared
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Optimization Recommendations")
                .font(.headline)
            
            let recommendations = performanceManager.getOptimizationRecommendations()
            
            if recommendations.isEmpty {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    
                    Text("System running optimally")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            } else {
                ForEach(recommendations.indices, id: \.self) { index in
                    RecommendationRow(recommendation: recommendations[index])
                }
            }
            
            // Additional info
            VStack(alignment: .leading, spacing: 4) {
                Text("Optimal Settings:")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                HStack {
                    Text("Recommended Model:")
                    Spacer()
                    Text(performanceManager.getRecommendedModel())
                        .fontWeight(.medium)
                        .fontFamily(.monospaced)
                }
                .font(.caption)
                
                HStack {
                    Text("Optimal Batch Size:")
                    Spacer()
                    Text("\(performanceManager.getOptimalBatchSize())")
                        .fontWeight(.medium)
                        .fontFamily(.monospaced)
                }
                .font(.caption)
            }
            .padding()
            .background(.blue.opacity(0.05), in: RoundedRectangle(cornerRadius: 6))
        }
    }
}

struct RecommendationRow: View {
    let recommendation: OptimizationRecommendation
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: iconForSeverity(recommendation.severity))
                .foregroundColor(colorForSeverity(recommendation.severity))
                .font(.subheadline)
                .padding(.top, 2)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(recommendation.title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(recommendation.description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(3)
            }
            
            Spacer()
        }
        .padding()
        .background(colorForSeverity(recommendation.severity).opacity(0.05), in: RoundedRectangle(cornerRadius: 6))
    }
    
    private func iconForSeverity(_ severity: OptimizationRecommendation.Severity) -> String {
        switch severity {
        case .info: return "info.circle"
        case .warning: return "exclamationmark.triangle"
        case .critical: return "exclamationmark.octagon"
        }
    }
    
    private func colorForSeverity(_ severity: OptimizationRecommendation.Severity) -> Color {
        switch severity {
        case .info: return .blue
        case .warning: return .orange
        case .critical: return .red
        }
    }
}

struct SystemInfoView: View {
    @ObservedObject var performanceManager = PerformanceManager.shared
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                let systemInfo = performanceManager.getSystemInfo()
                
                Section("Hardware") {
                    InfoRow(label: "Architecture", value: systemInfo.architecture)
                    InfoRow(label: "Processor Cores", value: "\(systemInfo.processorCount)")
                    InfoRow(label: "Total Memory", value: systemInfo.totalMemoryGB)
                    InfoRow(label: "Apple Silicon", value: systemInfo.isAppleSilicon ? "Yes" : "No")
                }
                
                Section("Graphics") {
                    InfoRow(label: "Metal Device", value: systemInfo.metalDeviceName ?? "Not Available")
                    InfoRow(label: "Unified Memory", value: systemInfo.supportsUnifiedMemory ? "Supported" : "Not Supported")
                }
                
                Section("Current Performance") {
                    InfoRow(label: "CPU Usage", value: systemInfo.formattedCPUUsage)
                    InfoRow(label: "Memory Usage", value: systemInfo.formattedMemoryUsage)
                    InfoRow(label: "Thermal State", value: systemInfo.thermalState.rawValue)
                }
            }
            .navigationTitle("System Information")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(width: 500, height: 600)
    }
}

struct OptimizationDetailsView: View {
    @ObservedObject var performanceManager = PerformanceManager.shared
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Apple Silicon Benefits
                    OptimizationCategoryCard(
                        title: "Apple Silicon Optimizations",
                        icon: "cpu",
                        color: .blue,
                        isEnabled: performanceManager.isAppleSilicon
                    ) {
                        OptimizationFeatureRow(
                            title: "Hardware-Accelerated Processing",
                            description: "Native ARM64 optimization for faster transcription",
                            isEnabled: performanceManager.isAppleSilicon
                        )
                        
                        OptimizationFeatureRow(
                            title: "Unified Memory Architecture",
                            description: "Shared memory between CPU and GPU for efficient data processing",
                            isEnabled: performanceManager.metalDevice?.hasUnifiedMemory ?? false
                        )
                        
                        OptimizationFeatureRow(
                            title: "Power Efficiency",
                            description: "Reduced power consumption and heat generation",
                            isEnabled: performanceManager.isAppleSilicon
                        )
                    }
                    
                    // Metal Performance Shaders
                    OptimizationCategoryCard(
                        title: "Metal Performance",
                        icon: "gpu",
                        color: .purple,
                        isEnabled: performanceManager.isMetalSupported
                    ) {
                        OptimizationFeatureRow(
                            title: "GPU Acceleration",
                            description: "Leverage GPU for parallel processing tasks",
                            isEnabled: performanceManager.isMetalSupported
                        )
                        
                        OptimizationFeatureRow(
                            title: "Memory Optimization",
                            description: "Efficient buffer management for large audio files",
                            isEnabled: performanceManager.isMetalSupported
                        )
                    }
                    
                    // Thermal Management
                    OptimizationCategoryCard(
                        title: "Thermal Management",
                        icon: "thermometer",
                        color: thermalColor(performanceManager.thermalState),
                        isEnabled: true
                    ) {
                        OptimizationFeatureRow(
                            title: "Real-time Monitoring",
                            description: "Continuous thermal state monitoring",
                            isEnabled: true
                        )
                        
                        OptimizationFeatureRow(
                            title: "Adaptive Performance",
                            description: "Automatic batch size adjustment based on thermal conditions",
                            isEnabled: performanceManager.thermalState != .nominal
                        )
                        
                        OptimizationFeatureRow(
                            title: "Thermal Alerts",
                            description: "Notifications when system runs too hot",
                            isEnabled: performanceManager.thermalState.shouldThrottle
                        )
                    }
                }
                .padding()
            }
            .navigationTitle("Optimization Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(width: 600, height: 700)
    }
    
    private func thermalColor(_ state: PerformanceManager.ThermalState) -> Color {
        switch state {
        case .nominal: return .green
        case .fair: return .yellow
        case .serious: return .orange
        case .critical: return .red
        }
    }
}

struct OptimizationCategoryCard<Content: View>: View {
    let title: String
    let icon: String
    let color: Color
    let isEnabled: Bool
    @ViewBuilder let content: Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.title3)
                
                Text(title)
                    .font(.headline)
                
                Spacer()
                
                Image(systemName: isEnabled ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .foregroundColor(isEnabled ? .green : .gray)
            }
            
            content
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(color.opacity(0.3), lineWidth: 1)
        )
    }
}

struct OptimizationFeatureRow: View {
    let title: String
    let description: String
    let isEnabled: Bool
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: isEnabled ? "checkmark" : "minus")
                .foregroundColor(isEnabled ? .green : .gray)
                .font(.subheadline)
                .padding(.top, 2)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
            
            Spacer()
        }
    }
}

private struct InfoRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .foregroundStyle(.secondary)
            
            Spacer()
            
            Text(value)
                .fontWeight(.medium)
                .fontFamily(.monospaced)
        }
    }
}

#Preview {
    PerformanceMonitorView()
        .frame(width: 600, height: 500)
}