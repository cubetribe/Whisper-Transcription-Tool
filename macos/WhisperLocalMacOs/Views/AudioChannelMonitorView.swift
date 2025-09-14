import SwiftUI

/// View for monitoring real-time audio levels on separate channels
struct AudioChannelMonitorView: View {
    let inputLevels: [Float]
    let outputLevels: [Float]
    let isMonitoring: Bool
    let userName: String
    let contactName: String

    @State private var peakInputLevels: [Float] = [0.0, 0.0]
    @State private var peakOutputLevels: [Float] = [0.0, 0.0]
    @State private var showingChannelDetails = false

    var body: some View {
        VStack(spacing: 16) {
            headerSection
            channelMonitorsSection
            if isMonitoring {
                statisticsSection
            }
        }
        .onChange(of: inputLevels) { _, newLevels in
            updatePeakLevels(newLevels, peaks: &peakInputLevels)
        }
        .onChange(of: outputLevels) { _, newLevels in
            updatePeakLevels(newLevels, peaks: &peakOutputLevels)
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        HStack {
            Label("Audio Levels", systemImage: "waveform")
                .font(.subheadline)
                .fontWeight(.medium)

            Spacer()

            if isMonitoring {
                HStack(spacing: 4) {
                    Circle()
                        .fill(.green)
                        .frame(width: 6, height: 6)
                    Text("MONITORING")
                        .font(.caption2)
                        .fontWeight(.medium)
                        .foregroundColor(.green)
                }
            }

            Button {
                showingChannelDetails.toggle()
            } label: {
                Image(systemName: showingChannelDetails ? "chevron.up" : "info.circle")
                    .font(.caption)
            }
            .buttonStyle(.plain)
            .help("Show channel details")
        }
    }

    // MARK: - Channel Monitors Section

    private var channelMonitorsSection: some View {
        VStack(spacing: 12) {
            // Input Channel (Your voice)
            AudioChannelMeter(
                title: "Input Channel",
                subtitle: userName,
                icon: "mic.fill",
                iconColor: .blue,
                levels: inputLevels,
                peakLevels: peakInputLevels,
                isActive: isMonitoring,
                channelType: .input
            )

            // Output Channel (Contact voice)
            AudioChannelMeter(
                title: "Output Channel",
                subtitle: contactName,
                icon: "speaker.wave.2.fill",
                iconColor: .green,
                levels: outputLevels,
                peakLevels: peakOutputLevels,
                isActive: isMonitoring,
                channelType: .output
            )
        }
    }

    // MARK: - Statistics Section

    private var statisticsSection: some View {
        VStack(spacing: 8) {
            if showingChannelDetails {
                VStack(spacing: 8) {
                    Text("Channel Statistics")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.secondary)

                    HStack {
                        ChannelStatistics(
                            title: "Input",
                            levels: inputLevels,
                            peaks: peakInputLevels
                        )

                        Divider()
                            .frame(height: 40)

                        ChannelStatistics(
                            title: "Output",
                            levels: outputLevels,
                            peaks: peakOutputLevels
                        )
                    }
                }
                .transition(.opacity.combined(with: .scale))
            }
        }
        .animation(.easeInOut(duration: 0.2), value: showingChannelDetails)
    }

    // MARK: - Helper Methods

    private func updatePeakLevels(_ newLevels: [Float], peaks: inout [Float]) {
        for (index, level) in newLevels.enumerated() {
            if index < peaks.count {
                peaks[index] = max(peaks[index], level)

                // Decay peak levels slowly
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    if peaks[index] > 0 {
                        peaks[index] = max(0, peaks[index] - 0.1)
                    }
                }
            }
        }
    }
}

// MARK: - Audio Channel Meter

struct AudioChannelMeter: View {
    let title: String
    let subtitle: String
    let icon: String
    let iconColor: Color
    let levels: [Float]
    let peakLevels: [Float]
    let isActive: Bool
    let channelType: ChannelType

    enum ChannelType {
        case input, output
    }

    var body: some View {
        VStack(spacing: 8) {
            // Channel Header
            HStack {
                HStack(spacing: 6) {
                    Image(systemName: icon)
                        .foregroundColor(iconColor)
                        .font(.subheadline)

                    VStack(alignment: .leading, spacing: 1) {
                        Text(title)
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(.primary)

                        Text(subtitle)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()

                // Peak level indicator
                if levels.count > 0 {
                    Text("\(Int(levels.max() ?? 0 * 100))%")
                        .font(.caption2)
                        .fontFamily(.monospaced)
                        .foregroundColor(levelColor(levels.max() ?? 0))
                }
            }

            // Level Meters
            HStack(spacing: 4) {
                ForEach(0..<max(levels.count, 2), id: \.self) { channelIndex in
                    let level = channelIndex < levels.count ? levels[channelIndex] : 0.0
                    let peak = channelIndex < peakLevels.count ? peakLevels[channelIndex] : 0.0

                    VStack(spacing: 2) {
                        Text("L\(channelIndex + 1)")
                            .font(.caption2)
                            .foregroundColor(.secondary)

                        LevelMeter(
                            level: level,
                            peak: peak,
                            isActive: isActive,
                            channelType: channelType
                        )
                    }
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(isActive ? .regularMaterial : .quaternary)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(isActive ? iconColor.opacity(0.3) : Color.clear, lineWidth: 1)
        )
    }

    private func levelColor(_ level: Float) -> Color {
        switch level {
        case 0.0..<0.3: return .secondary
        case 0.3..<0.7: return .primary
        case 0.7..<0.9: return .orange
        default: return .red
        }
    }
}

// MARK: - Level Meter

struct LevelMeter: View {
    let level: Float
    let peak: Float
    let isActive: Bool
    let channelType: AudioChannelMeter.ChannelType

    @State private var animatedLevel: Float = 0.0
    @State private var animatedPeak: Float = 0.0

    var body: some View {
        GeometryReader { geometry in
            let height = geometry.size.height
            let levelHeight = height * CGFloat(animatedLevel)
            let peakHeight = height * CGFloat(animatedPeak)

            ZStack(alignment: .bottom) {
                // Background
                Rectangle()
                    .fill(.quaternary)

                // Level gradient
                Rectangle()
                    .fill(levelGradient)
                    .frame(height: max(0, levelHeight))

                // Peak indicator
                if animatedPeak > 0.05 {
                    Rectangle()
                        .fill(peakColor)
                        .frame(height: 2)
                        .offset(y: -peakHeight + 1)
                }

                // Scale markings
                scaleMarkings(height: height)
            }
        }
        .frame(width: 20, height: 80)
        .cornerRadius(2)
        .onChange(of: level) { _, newLevel in
            withAnimation(.easeOut(duration: 0.1)) {
                animatedLevel = newLevel
            }
        }
        .onChange(of: peak) { _, newPeak in
            withAnimation(.easeOut(duration: 0.1)) {
                animatedPeak = newPeak
            }
        }
    }

    private var levelGradient: LinearGradient {
        let colors: [Color] = [
            .green,
            .green,
            .yellow,
            .orange,
            .red
        ]

        return LinearGradient(
            colors: colors,
            startPoint: .bottom,
            endPoint: .top
        )
    }

    private var peakColor: Color {
        switch animatedPeak {
        case 0.0..<0.7: return .green
        case 0.7..<0.9: return .orange
        default: return .red
        }
    }

    private func scaleMarkings(height: CGFloat) -> some View {
        VStack(spacing: 0) {
            ForEach([1.0, 0.8, 0.6, 0.4, 0.2, 0.0], id: \.self) { mark in
                HStack {
                    Rectangle()
                        .fill(.primary.opacity(0.3))
                        .frame(width: 4, height: 1)
                    Spacer()
                }
                if mark != 0.0 {
                    Spacer()
                }
            }
        }
        .frame(height: height)
    }
}

// MARK: - Channel Statistics

struct ChannelStatistics: View {
    let title: String
    let levels: [Float]
    let peaks: [Float]

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .fontWeight(.medium)

            VStack(alignment: .leading, spacing: 2) {
                StatRow(
                    label: "Current",
                    value: "\(Int((levels.max() ?? 0) * 100))%",
                    color: .primary
                )

                StatRow(
                    label: "Peak",
                    value: "\(Int((peaks.max() ?? 0) * 100))%",
                    color: .orange
                )

                StatRow(
                    label: "Average",
                    value: "\(Int(levels.reduce(0, +) / Float(max(levels.count, 1)) * 100))%",
                    color: .secondary
                )
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct StatRow: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack {
            Text("\(label):")
                .font(.caption2)
                .foregroundColor(.secondary)

            Spacer()

            Text(value)
                .font(.caption2)
                .fontFamily(.monospaced)
                .foregroundColor(color)
        }
    }
}

// MARK: - Advanced Audio Monitor

struct AdvancedAudioMonitorView: View {
    let inputLevels: [Float]
    let outputLevels: [Float]
    let isMonitoring: Bool

    @State private var showingFrequencyAnalysis = false
    @State private var selectedTimeRange: TimeRange = .live

    enum TimeRange: String, CaseIterable {
        case live = "Live"
        case minute1 = "1 min"
        case minute5 = "5 min"
        case minute15 = "15 min"
    }

    var body: some View {
        VStack(spacing: 16) {
            HStack {
                Text("Advanced Audio Monitoring")
                    .font(.headline)

                Spacer()

                Picker("Time Range", selection: $selectedTimeRange) {
                    ForEach(TimeRange.allCases, id: \.self) { range in
                        Text(range.rawValue).tag(range)
                    }
                }
                .pickerStyle(.segmented)
                .frame(width: 200)
            }

            if showingFrequencyAnalysis {
                FrequencyAnalysisView(
                    inputLevels: inputLevels,
                    outputLevels: outputLevels
                )
            }

            HStack {
                Toggle("Frequency Analysis", isOn: $showingFrequencyAnalysis)
                Spacer()
            }
        }
    }
}

struct FrequencyAnalysisView: View {
    let inputLevels: [Float]
    let outputLevels: [Float]

    var body: some View {
        VStack(spacing: 8) {
            Text("Frequency Analysis")
                .font(.subheadline)
                .fontWeight(.medium)

            HStack(spacing: 20) {
                FrequencyBars(levels: inputLevels, title: "Input")
                FrequencyBars(levels: outputLevels, title: "Output")
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(8)
    }
}

struct FrequencyBars: View {
    let levels: [Float]
    let title: String

    private let frequencyBands = ["60Hz", "170Hz", "310Hz", "600Hz", "1kHz", "3kHz", "6kHz", "12kHz"]

    var body: some View {
        VStack(spacing: 4) {
            Text(title)
                .font(.caption)
                .fontWeight(.medium)

            HStack(alignment: .bottom, spacing: 2) {
                ForEach(0..<8, id: \.self) { index in
                    let height = CGFloat.random(in: 4...40)
                    Rectangle()
                        .fill(.blue.gradient)
                        .frame(width: 8, height: height)
                        .cornerRadius(1)
                }
            }
            .frame(height: 50)

            HStack {
                Text("60Hz")
                    .font(.caption2)
                Spacer()
                Text("12kHz")
                    .font(.caption2)
            }
        }
    }
}

#Preview {
    AudioChannelMonitorView(
        inputLevels: [0.6, 0.4],
        outputLevels: [0.3, 0.5],
        isMonitoring: true,
        userName: "John Doe",
        contactName: "Client"
    )
    .padding()
}