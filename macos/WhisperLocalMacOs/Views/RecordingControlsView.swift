import SwiftUI

/// Professional recording controls with intuitive UI/UX
struct RecordingControlsView: View {
    let isRecording: Bool
    let isPaused: Bool
    let canStart: Bool
    let canPause: Bool
    let canResume: Bool
    let canStop: Bool

    let onStart: () -> Void
    let onPause: () -> Void
    let onResume: () -> Void
    let onStop: () -> Void

    @State private var isHoveringStart = false
    @State private var isHoveringStop = false
    @State private var isHoveringPause = false
    @State private var showingKeyboardShortcuts = false

    var body: some View {
        VStack(spacing: 20) {
            primaryControlsSection
            secondaryControlsSection
            keyboardShortcutsSection
        }
    }

    // MARK: - Primary Controls Section

    private var primaryControlsSection: some View {
        VStack(spacing: 16) {
            Text("Recording Controls")
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(.secondary)

            HStack(spacing: 24) {
                // Start/Resume Button
                if !isRecording || isPaused {
                    RecordingButton(
                        icon: isPaused ? "play.fill" : "record.circle.fill",
                        title: isPaused ? "Resume" : "Start Recording",
                        subtitle: isPaused ? "Continue session" : "Begin new session",
                        color: .red,
                        isEnabled: isPaused ? canResume : canStart,
                        isLarge: true,
                        keyboardShortcut: isPaused ? .defaultAction : nil,
                        action: isPaused ? onResume : onStart
                    )
                    .scaleEffect(isHoveringStart ? 1.05 : 1.0)
                    .onHover { hovering in
                        withAnimation(.easeInOut(duration: 0.1)) {
                            isHoveringStart = hovering
                        }
                    }
                }

                // Pause Button (only when recording)
                if isRecording && !isPaused {
                    RecordingButton(
                        icon: "pause.fill",
                        title: "Pause",
                        subtitle: "Temporary stop",
                        color: .orange,
                        isEnabled: canPause,
                        isLarge: true,
                        action: onPause
                    )
                    .scaleEffect(isHoveringPause ? 1.05 : 1.0)
                    .onHover { hovering in
                        withAnimation(.easeInOut(duration: 0.1)) {
                            isHoveringPause = hovering
                        }
                    }
                }

                // Stop Button
                if isRecording {
                    RecordingButton(
                        icon: "stop.fill",
                        title: "Stop Recording",
                        subtitle: "End session",
                        color: .gray,
                        isEnabled: canStop,
                        isLarge: true,
                        action: onStop
                    )
                    .scaleEffect(isHoveringStop ? 1.05 : 1.0)
                    .onHover { hovering in
                        withAnimation(.easeInOut(duration: 0.1)) {
                            isHoveringStop = hovering
                        }
                    }
                }
            }
            .transition(.asymmetric(
                insertion: .scale.combined(with: .opacity),
                removal: .scale.combined(with: .opacity)
            ))
        }
    }

    // MARK: - Secondary Controls Section

    private var secondaryControlsSection: some View {
        HStack(spacing: 16) {
            // Recording Status Indicator
            RecordingStatusIndicator(
                isRecording: isRecording,
                isPaused: isPaused
            )

            Spacer()

            // Quick Actions
            HStack(spacing: 8) {
                if isRecording {
                    Button {
                        // Quick save/bookmark functionality
                    } label: {
                        Image(systemName: "bookmark.fill")
                    }
                    .help("Add bookmark")
                    .disabled(true) // Placeholder functionality

                    Button {
                        // Quick note functionality
                    } label: {
                        Image(systemName: "note.text.badge.plus")
                    }
                    .help("Add note")
                    .disabled(true) // Placeholder functionality
                }

                Button {
                    showingKeyboardShortcuts.toggle()
                } label: {
                    Image(systemName: "keyboard")
                }
                .help("Show keyboard shortcuts")
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
        }
    }

    // MARK: - Keyboard Shortcuts Section

    private var keyboardShortcutsSection: some View {
        VStack(spacing: 8) {
            if showingKeyboardShortcuts {
                VStack(spacing: 8) {
                    Text("Keyboard Shortcuts")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.secondary)

                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], alignment: .leading, spacing: 4) {
                        KeyboardShortcutRow(key: "Space", action: "Start/Pause")
                        KeyboardShortcutRow(key: "⌘+S", action: "Stop")
                        KeyboardShortcutRow(key: "⌘+R", action: "Resume")
                        KeyboardShortcutRow(key: "⌘+N", action: "New Session")
                    }
                }
                .padding()
                .background(.quaternary)
                .cornerRadius(8)
                .transition(.opacity.combined(with: .scale))
            }
        }
        .animation(.easeInOut(duration: 0.2), value: showingKeyboardShortcuts)
    }
}

// MARK: - Recording Button

struct RecordingButton: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color
    let isEnabled: Bool
    let isLarge: Bool
    let keyboardShortcut: KeyEquivalent?
    let action: () -> Void

    init(
        icon: String,
        title: String,
        subtitle: String,
        color: Color,
        isEnabled: Bool = true,
        isLarge: Bool = false,
        keyboardShortcut: KeyEquivalent? = nil,
        action: @escaping () -> Void
    ) {
        self.icon = icon
        self.title = title
        self.subtitle = subtitle
        self.color = color
        self.isEnabled = isEnabled
        self.isLarge = isLarge
        self.keyboardShortcut = keyboardShortcut
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: isLarge ? 28 : 20, weight: .medium))
                    .foregroundColor(isEnabled ? color : .secondary)

                VStack(spacing: 2) {
                    Text(title)
                        .font(isLarge ? .subheadline : .caption)
                        .fontWeight(.semibold)
                        .foregroundColor(isEnabled ? .primary : .secondary)

                    Text(subtitle)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
            }
            .frame(width: isLarge ? 120 : 80, height: isLarge ? 80 : 60)
        }
        .buttonStyle(RecordingButtonStyle(
            isEnabled: isEnabled,
            color: color,
            isLarge: isLarge
        ))
        .disabled(!isEnabled)
        .help(isEnabled ? "\(title) - \(subtitle)" : "Not available")
        .if(keyboardShortcut != nil) { view in
            view.keyboardShortcut(keyboardShortcut!)
        }
    }
}

// MARK: - Recording Button Style

struct RecordingButtonStyle: ButtonStyle {
    let isEnabled: Bool
    let color: Color
    let isLarge: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .background(
                RoundedRectangle(cornerRadius: isLarge ? 16 : 12)
                    .fill(backgroundColor(isPressed: configuration.isPressed))
                    .shadow(
                        color: shadowColor(isPressed: configuration.isPressed),
                        radius: configuration.isPressed ? 2 : 4,
                        x: 0,
                        y: configuration.isPressed ? 1 : 2
                    )
            )
            .overlay(
                RoundedRectangle(cornerRadius: isLarge ? 16 : 12)
                    .stroke(borderColor, lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }

    private func backgroundColor(isPressed: Bool) -> Color {
        if !isEnabled {
            return .quaternary
        }

        if isPressed {
            return color.opacity(0.2)
        }

        return .regularMaterial
    }

    private func shadowColor(isPressed: Bool) -> Color {
        if !isEnabled {
            return .clear
        }

        return color.opacity(isPressed ? 0.2 : 0.3)
    }

    private var borderColor: Color {
        if !isEnabled {
            return .secondary.opacity(0.3)
        }

        return color.opacity(0.4)
    }
}

// MARK: - Recording Status Indicator

struct RecordingStatusIndicator: View {
    let isRecording: Bool
    let isPaused: Bool

    @State private var pulseAnimation = false

    var body: some View {
        HStack(spacing: 8) {
            statusIcon
            statusText
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(statusBackgroundColor)
        .cornerRadius(20)
    }

    private var statusIcon: some View {
        Group {
            if isRecording && !isPaused {
                Circle()
                    .fill(.red)
                    .frame(width: 8, height: 8)
                    .scaleEffect(pulseAnimation ? 1.2 : 1.0)
                    .animation(.easeInOut(duration: 1).repeatForever(), value: pulseAnimation)
                    .onAppear {
                        pulseAnimation = true
                    }
            } else if isPaused {
                Image(systemName: "pause.fill")
                    .foregroundColor(.orange)
                    .font(.caption2)
            } else {
                Circle()
                    .fill(.secondary)
                    .frame(width: 8, height: 8)
            }
        }
    }

    private var statusText: some View {
        Text(statusMessage)
            .font(.caption)
            .fontWeight(.medium)
            .foregroundColor(statusTextColor)
    }

    private var statusMessage: String {
        if isRecording && !isPaused {
            return "RECORDING"
        } else if isPaused {
            return "PAUSED"
        } else {
            return "READY"
        }
    }

    private var statusTextColor: Color {
        if isRecording && !isPaused {
            return .red
        } else if isPaused {
            return .orange
        } else {
            return .secondary
        }
    }

    private var statusBackgroundColor: Color {
        if isRecording && !isPaused {
            return .red.opacity(0.1)
        } else if isPaused {
            return .orange.opacity(0.1)
        } else {
            return .secondary.opacity(0.1)
        }
    }
}

// MARK: - Keyboard Shortcut Row

struct KeyboardShortcutRow: View {
    let key: String
    let action: String

    var body: some View {
        HStack {
            Text(key)
                .font(.caption2)
                .fontFamily(.monospaced)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(.regularMaterial)
                .cornerRadius(4)

            Text(action)
                .font(.caption2)
                .foregroundColor(.secondary)

            Spacer()
        }
    }
}

// MARK: - Advanced Recording Controls

struct AdvancedRecordingControlsView: View {
    @Binding var recordingQuality: RecordingQuality
    @Binding var autoStop: Bool
    @Binding var autoStopDuration: Int

    enum RecordingQuality: String, CaseIterable {
        case high = "High Quality"
        case medium = "Medium Quality"
        case low = "Low Quality"

        var bitrate: String {
            switch self {
            case .high: return "320 kbps"
            case .medium: return "192 kbps"
            case .low: return "128 kbps"
            }
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Advanced Settings")
                .font(.subheadline)
                .fontWeight(.medium)

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Quality:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Spacer()

                    Picker("Quality", selection: $recordingQuality) {
                        ForEach(RecordingQuality.allCases, id: \.self) { quality in
                            Text("\(quality.rawValue) (\(quality.bitrate))").tag(quality)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 200)
                }

                Toggle("Auto-stop recording", isOn: $autoStop)
                    .font(.caption)

                if autoStop {
                    HStack {
                        Text("Duration:")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Spacer()

                        Stepper("\(autoStopDuration) minutes", value: $autoStopDuration, in: 1...120)
                            .font(.caption)
                    }
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(8)
    }
}

// MARK: - Utility Extensions

extension View {
    @ViewBuilder
    func `if`<Content: View>(_ condition: Bool, transform: (Self) -> Content) -> some View {
        if condition {
            transform(self)
        } else {
            self
        }
    }
}

#Preview {
    VStack(spacing: 20) {
        // Not recording state
        RecordingControlsView(
            isRecording: false,
            isPaused: false,
            canStart: true,
            canPause: false,
            canResume: false,
            canStop: false,
            onStart: {},
            onPause: {},
            onResume: {},
            onStop: {}
        )

        Divider()

        // Recording state
        RecordingControlsView(
            isRecording: true,
            isPaused: false,
            canStart: false,
            canPause: true,
            canResume: false,
            canStop: true,
            onStart: {},
            onPause: {},
            onResume: {},
            onStop: {}
        )

        Divider()

        // Paused state
        RecordingControlsView(
            isRecording: true,
            isPaused: true,
            canStart: false,
            canPause: false,
            canResume: true,
            canStop: true,
            onStart: {},
            onPause: {},
            onResume: {},
            onStop: {}
        )
    }
    .padding()
}