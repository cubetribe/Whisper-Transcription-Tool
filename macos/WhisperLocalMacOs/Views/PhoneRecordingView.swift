import SwiftUI

/// Main view for Phone Recording functionality with comprehensive UI
struct PhoneRecordingView: View {
    @StateObject private var viewModel = PhoneRecordingViewModel()
    @State private var showingDeviceSettings = false
    @State private var showingSpeakerConfiguration = false
    @State private var showingTranscriptionAlert = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    headerSection

                    if !viewModel.blackHoleInstalled {
                        blackHoleWarningSection
                    }

                    configurationSection

                    if viewModel.blackHoleInstalled {
                        recordingSection
                    }

                    if viewModel.isRecording || !viewModel.recordedFiles.isEmpty {
                        sessionInfoSection
                    }

                    if !viewModel.recordedFiles.isEmpty {
                        recordedFilesSection
                    }
                }
                .padding(.horizontal, 24)
                .padding(.vertical, 16)
            }
            .navigationTitle("Phone Recording")
            .navigationSubtitle(viewModel.isRecording ? "Recording in Progress" : "Ready to Record")
            .toolbar {
                ToolbarItemGroup(placement: .primaryAction) {
                    Button {
                        viewModel.refreshAudioDevices()
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .help("Refresh Audio Devices")
                    }

                    Button {
                        showingDeviceSettings = true
                    } label: {
                        Image(systemName: "speaker.wave.2.fill")
                            .help("Audio Device Settings")
                    }
                }
            }
        }
        .sheet(isPresented: $showingSpeakerConfiguration) {
            SpeakerConfigurationView(
                userName: $viewModel.userName,
                contactName: $viewModel.contactName
            )
        }
        .sheet(isPresented: $showingDeviceSettings) {
            AudioDeviceSettingsView(
                availableInputDevices: viewModel.availableInputDevices,
                availableOutputDevices: viewModel.availableOutputDevices,
                selectedInputDevice: $viewModel.selectedInputDevice,
                selectedOutputDevice: $viewModel.selectedOutputDevice,
                blackHoleDevice: viewModel.blackHoleDevice
            )
        }
        .sheet(isPresented: $viewModel.showingTranscriptView) {
            CallTranscriptView(
                transcriptionResults: viewModel.transcriptionResults,
                userName: viewModel.userName,
                contactName: viewModel.contactName
            )
        }
        .alert("Transcribe Recording?", isPresented: $showingTranscriptionAlert) {
            Button("Yes") {
                viewModel.processTranscription()
            }
            Button("No", role: .cancel) { }
        } message: {
            Text("Would you like to transcribe the recorded audio?")
        }
        .alert("Recording Error", isPresented: $viewModel.showingError) {
            Button("OK") {
                viewModel.showingError = false
            }
        } message: {
            Text(viewModel.lastError ?? "An unknown error occurred")
        }
        .onReceive(NotificationCenter.default.publisher(for: .init("RecordingCompleted"))) { _ in
            showingTranscriptionAlert = true
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        VStack(spacing: 16) {
            HStack {
                Image(systemName: "phone.fill")
                    .font(.system(size: 32))
                    .foregroundStyle(.blue.gradient)

                VStack(alignment: .leading, spacing: 4) {
                    Text("Phone Recording")
                        .font(.title2)
                        .fontWeight(.semibold)

                    Text("Record and transcribe phone conversations with separate audio channels")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.leading)
                }

                Spacer()

                if viewModel.isRecording {
                    RecordingIndicator()
                }
            }

            Divider()
        }
    }

    // MARK: - BlackHole Warning Section

    private var blackHoleWarningSection: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.orange)
                    .font(.title2)

                VStack(alignment: .leading, spacing: 4) {
                    Text("BlackHole Required")
                        .font(.headline)
                        .foregroundColor(.orange)

                    Text("BlackHole is required for system audio capture. Please install it to enable phone recording.")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()
            }

            HStack {
                Button("Install BlackHole") {
                    openBlackHoleInstallation()
                }
                .buttonStyle(.borderedProminent)

                Button("Refresh") {
                    viewModel.checkBlackHoleInstallation()
                }
                .buttonStyle(.bordered)

                Spacer()
            }
        }
        .padding()
        .background(.orange.opacity(0.1))
        .cornerRadius(8)
    }

    // MARK: - Configuration Section

    private var configurationSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Configuration")
                .font(.headline)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                // Speaker Configuration
                VStack(alignment: .leading, spacing: 8) {
                    Label("Speaker Names", systemImage: "person.2.fill")
                        .font(.subheadline)
                        .fontWeight(.medium)

                    VStack(alignment: .leading, spacing: 4) {
                        Text("User: \(viewModel.userName)")
                            .foregroundColor(.secondary)
                        Text("Contact: \(viewModel.contactName)")
                            .foregroundColor(.secondary)
                    }
                    .font(.caption)

                    Button("Configure") {
                        showingSpeakerConfiguration = true
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
                .padding()
                .background(.regularMaterial)
                .cornerRadius(8)

                // Device Configuration
                VStack(alignment: .leading, spacing: 8) {
                    Label("Audio Devices", systemImage: "speaker.wave.2.fill")
                        .font(.subheadline)
                        .fontWeight(.medium)

                    VStack(alignment: .leading, spacing: 4) {
                        if let input = viewModel.selectedInputDevice {
                            Text("Input: \(input.name)")
                                .foregroundColor(.secondary)
                        } else {
                            Text("Input: Not selected")
                                .foregroundColor(.red)
                        }

                        if let output = viewModel.selectedOutputDevice {
                            Text("Output: \(output.name)")
                                .foregroundColor(.secondary)
                        } else {
                            Text("Output: Not selected")
                                .foregroundColor(.red)
                        }
                    }
                    .font(.caption)

                    Button("Configure") {
                        showingDeviceSettings = true
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
                .padding()
                .background(.regularMaterial)
                .cornerRadius(8)
            }
        }
    }

    // MARK: - Recording Section

    private var recordingSection: some View {
        VStack(spacing: 16) {
            Text("Recording Controls")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            VStack(spacing: 16) {
                // Audio Level Monitoring
                AudioChannelMonitorView(
                    inputLevels: viewModel.inputLevels,
                    outputLevels: viewModel.outputLevels,
                    isMonitoring: viewModel.isMonitoring,
                    userName: viewModel.userName,
                    contactName: viewModel.contactName
                )

                // Recording Controls
                RecordingControlsView(
                    isRecording: viewModel.isRecording,
                    isPaused: viewModel.isPaused,
                    canStart: viewModel.canStartRecording,
                    canPause: viewModel.canPauseRecording,
                    canResume: viewModel.canResumeRecording,
                    canStop: viewModel.canStopRecording,
                    onStart: viewModel.startRecording,
                    onPause: viewModel.pauseRecording,
                    onResume: viewModel.resumeRecording,
                    onStop: viewModel.stopRecording
                )

                // Recording Duration
                if viewModel.isRecording {
                    Text("Duration: \(viewModel.formattedRecordingDuration)")
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundColor(.primary)
                        .padding(.vertical, 8)
                }
            }
            .padding()
            .background(.regularMaterial)
            .cornerRadius(12)
        }
    }

    // MARK: - Session Info Section

    private var sessionInfoSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Current Session")
                .font(.headline)

            if let session = viewModel.currentSession {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Session ID")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(session.id)
                            .font(.system(.caption, design: .monospaced))
                    }

                    Spacer()

                    VStack(alignment: .trailing, spacing: 4) {
                        Text("Status")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(session.status.displayName)
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(session.status.color)
                    }
                }

                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Started")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(session.startTime, style: .time)
                            .font(.caption)
                    }

                    Spacer()

                    if let endTime = session.endTime {
                        VStack(alignment: .trailing, spacing: 4) {
                            Text("Ended")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text(endTime, style: .time)
                                .font(.caption)
                        }
                    }
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(8)
    }

    // MARK: - Recorded Files Section

    private var recordedFilesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Recorded Files")
                    .font(.headline)

                Spacer()

                if !viewModel.isProcessingTranscript {
                    Button("Transcribe") {
                        viewModel.processTranscription()
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
                } else {
                    HStack {
                        ProgressView()
                            .controlSize(.small)
                        Text("Processing...")
                            .font(.caption)
                    }
                }
            }

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                ForEach(Array(viewModel.recordedFiles.keys.sorted()), id: \.self) { channel in
                    if let filePath = viewModel.recordedFiles[channel] {
                        RecordedFileCard(
                            channel: channel,
                            filePath: filePath,
                            speakerName: channel.contains("input") ? viewModel.userName : viewModel.contactName
                        )
                    }
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(8)
    }

    // MARK: - Helper Methods

    private func openBlackHoleInstallation() {
        if let url = URL(string: "https://github.com/ExistentialAudio/BlackHole") {
            NSWorkspace.shared.open(url)
        }
    }
}

// MARK: - Recording Indicator

struct RecordingIndicator: View {
    @State private var isPulsing = false

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(.red)
                .frame(width: 8, height: 8)
                .scaleEffect(isPulsing ? 1.2 : 1.0)
                .animation(.easeInOut(duration: 1).repeatForever(), value: isPulsing)
                .onAppear {
                    isPulsing = true
                }

            Text("RECORDING")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(.red)
        }
    }
}

// MARK: - Recorded File Card

struct RecordedFileCard: View {
    let channel: String
    let filePath: String
    let speakerName: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: channel.contains("input") ? "mic.fill" : "speaker.wave.2.fill")
                    .foregroundColor(.blue)

                VStack(alignment: .leading, spacing: 2) {
                    Text(speakerName)
                        .font(.subheadline)
                        .fontWeight(.medium)
                    Text(channel.capitalized)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()
            }

            Text(URL(fileURLWithPath: filePath).lastPathComponent)
                .font(.caption)
                .fontFamily(.monospaced)
                .foregroundColor(.secondary)
                .lineLimit(1)

            HStack {
                Button("Open") {
                    NSWorkspace.shared.selectFile(filePath, inFileViewerRootedAtPath: "")
                }
                .buttonStyle(.bordered)
                .controlSize(.mini)

                Spacer()

                Button("Play") {
                    playAudioFile(filePath)
                }
                .buttonStyle(.bordered)
                .controlSize(.mini)
            }
        }
        .padding(.small)
        .background(.quaternary)
        .cornerRadius(6)
    }

    private func playAudioFile(_ path: String) {
        NSWorkspace.shared.open(URL(fileURLWithPath: path))
    }
}

// MARK: - Audio Device Settings View

struct AudioDeviceSettingsView: View {
    let availableInputDevices: [AudioDevice]
    let availableOutputDevices: [AudioDevice]
    @Binding var selectedInputDevice: AudioDevice?
    @Binding var selectedOutputDevice: AudioDevice?
    let blackHoleDevice: AudioDevice?

    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("Input Device") {
                    Picker("Input Device", selection: $selectedInputDevice) {
                        Text("None").tag(nil as AudioDevice?)
                        ForEach(availableInputDevices) { device in
                            Text(device.displayName).tag(device as AudioDevice?)
                        }
                    }
                    .pickerStyle(.menu)

                    if let device = selectedInputDevice {
                        Text("Sample Rate: \(device.defaultSampleRate, specifier: "%.0f") Hz")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Section("Output Device") {
                    Picker("Output Device", selection: $selectedOutputDevice) {
                        Text("None").tag(nil as AudioDevice?)
                        ForEach(availableOutputDevices) { device in
                            Text(device.displayName).tag(device as AudioDevice?)
                        }
                    }
                    .pickerStyle(.menu)

                    if let device = selectedOutputDevice {
                        Text("Sample Rate: \(device.defaultSampleRate, specifier: "%.0f") Hz")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                if let blackHole = blackHoleDevice {
                    Section("BlackHole Device") {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            Text(blackHole.displayName)
                        }
                    }
                }
            }
            .navigationTitle("Audio Device Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(minWidth: 400, minHeight: 300)
    }
}

#Preview {
    PhoneRecordingView()
}