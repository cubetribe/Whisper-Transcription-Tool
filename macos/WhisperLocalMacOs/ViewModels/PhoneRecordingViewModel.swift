import Foundation
import SwiftUI
import Combine
import AVFoundation
import AppKit

/// ViewModel for Phone Recording functionality with real-time audio monitoring
@MainActor
class PhoneRecordingViewModel: ObservableObject {

    // MARK: - Published Properties

    @Published var isRecording = false
    @Published var isPaused = false
    @Published var recordingDuration: TimeInterval = 0
    @Published var currentSessionId: String?

    // Configuration
    @Published var userName = ""
    @Published var contactName = ""
    @Published var selectedInputDevice: AudioDevice?
    @Published var selectedOutputDevice: AudioDevice?
    @Published var availableInputDevices: [AudioDevice] = []
    @Published var availableOutputDevices: [AudioDevice] = []

    // Audio Monitoring
    @Published var inputLevels: [Float] = [0.0, 0.0] // Left, Right channels
    @Published var outputLevels: [Float] = [0.0, 0.0]
    @Published var isMonitoring = false

    // BlackHole Status
    @Published var blackHoleInstalled = false
    @Published var blackHoleDevice: AudioDevice?

    // Recording Session
    @Published var currentSession: RecordingSession?
    @Published var recordedFiles: [String: String] = [:] // channel -> file path

    // Error Handling
    @Published var lastError: String?
    @Published var showingError = false

    // Transcription
    @Published var showingTranscriptView = false
    @Published var transcriptionResults: [String: String] = [:] // channel -> transcript
    @Published var isProcessingTranscript = false

    // MARK: - Private Properties

    private let pythonBridge = PythonBridge()
    private var recordingTimer: Timer?
    private var audioMonitorTimer: Timer?
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization

    init() {
        setupBindings()
        checkBlackHoleInstallation()
        loadAudioDevices()
        setupDefaultConfiguration()
    }

    deinit {
        stopMonitoring()
        stopRecording()
    }

    // MARK: - Audio Device Management

    func refreshAudioDevices() {
        loadAudioDevices()
    }

    private func loadAudioDevices() {
        Task {
            do {
                let deviceListCommand: [String: Any] = [
                    "command": "phone",
                    "subcommand": "devices"
                ]

                let response = try await pythonBridge.executeCommand(deviceListCommand)

                if let data = response["data"] as? [String: Any],
                   let devices = data["devices"] as? [[String: Any]] {

                    let audioDevices = devices.compactMap { deviceData -> AudioDevice? in
                        guard let id = deviceData["id"] as? Int,
                              let name = deviceData["name"] as? String,
                              let channelsIn = deviceData["channels_in"] as? Int,
                              let channelsOut = deviceData["channels_out"] as? Int,
                              let sampleRate = deviceData["default_samplerate"] as? Double else {
                            return nil
                        }

                        return AudioDevice(
                            id: id,
                            name: name,
                            channelsIn: channelsIn,
                            channelsOut: channelsOut,
                            defaultSampleRate: sampleRate
                        )
                    }

                    await MainActor.run {
                        self.availableInputDevices = audioDevices.filter { $0.channelsIn > 0 }
                        self.availableOutputDevices = audioDevices.filter { $0.channelsOut > 0 }

                        // Check for BlackHole
                        self.blackHoleDevice = audioDevices.first { $0.name.lowercased().contains("blackhole") }
                        self.blackHoleInstalled = self.blackHoleDevice != nil
                    }
                }
            } catch {
                await MainActor.run {
                    self.handleError("Failed to load audio devices: \(error.localizedDescription)")
                }
            }
        }
    }

    func checkBlackHoleInstallation() {
        Task {
            do {
                let checkCommand: [String: Any] = [
                    "command": "phone",
                    "subcommand": "check"
                ]

                let response = try await pythonBridge.executeCommand(checkCommand)

                if let data = response["data"] as? [String: Any] {
                    await MainActor.run {
                        self.blackHoleInstalled = data["blackhole_available"] as? Bool ?? false

                        if let recommendedSetup = data["recommended_setup"] as? [String: Any] {
                            self.updateRecommendedDevices(recommendedSetup)
                        }
                    }
                }
            } catch {
                await MainActor.run {
                    self.handleError("Failed to check setup: \(error.localizedDescription)")
                }
            }
        }
    }

    private func updateRecommendedDevices(_ setup: [String: Any]) {
        if let inputDevice = setup["input_device"] as? [String: Any],
           let inputId = inputDevice["id"] as? Int {
            self.selectedInputDevice = availableInputDevices.first { $0.id == inputId }
        }

        if let outputDevice = setup["output_device"] as? [String: Any],
           let outputId = outputDevice["id"] as? Int {
            self.selectedOutputDevice = availableOutputDevices.first { $0.id == outputId }
        }
    }

    private func setupDefaultConfiguration() {
        if userName.isEmpty {
            userName = NSFullUserName() ?? "Me"
        }

        if contactName.isEmpty {
            contactName = "Contact"
        }
    }

    // MARK: - Recording Control

    func startRecording() {
        guard !isRecording else { return }
        guard blackHoleInstalled else {
            handleError("BlackHole is required for phone recording. Please install BlackHole first.")
            return
        }

        Task {
            do {
                let recordCommand: [String: Any] = [
                    "command": "phone",
                    "subcommand": "record",
                    "input_device": selectedInputDevice?.id ?? 0,
                    "output_device": selectedOutputDevice?.id ?? 0,
                    "user_name": userName,
                    "contact_name": contactName,
                    "output_dir": getRecordingDirectory()
                ]

                let response = try await pythonBridge.executeCommand(recordCommand)

                if let data = response["data"] as? [String: Any],
                   let sessionId = data["session_id"] as? String {

                    await MainActor.run {
                        self.currentSessionId = sessionId
                        self.isRecording = true
                        self.isPaused = false
                        self.recordingDuration = 0
                        self.startRecordingTimer()
                        self.startMonitoring()

                        // Create session object
                        self.currentSession = RecordingSession(
                            id: sessionId,
                            userName: self.userName,
                            contactName: self.contactName,
                            startTime: Date(),
                            status: .recording
                        )

                        Logger.shared.info("Started phone recording session: \(sessionId)", category: .phoneRecording)
                    }
                }
            } catch {
                await MainActor.run {
                    self.handleError("Failed to start recording: \(error.localizedDescription)")
                }
            }
        }
    }

    func pauseRecording() {
        guard isRecording, !isPaused else { return }

        Task {
            do {
                let pauseCommand: [String: Any] = [
                    "command": "phone",
                    "subcommand": "pause",
                    "session_id": currentSessionId ?? ""
                ]

                _ = try await pythonBridge.executeCommand(pauseCommand)

                await MainActor.run {
                    self.isPaused = true
                    self.recordingTimer?.invalidate()
                    self.currentSession?.status = .paused
                    Logger.shared.info("Paused phone recording", category: .phoneRecording)
                }
            } catch {
                await MainActor.run {
                    self.handleError("Failed to pause recording: \(error.localizedDescription)")
                }
            }
        }
    }

    func resumeRecording() {
        guard isRecording, isPaused else { return }

        Task {
            do {
                let resumeCommand: [String: Any] = [
                    "command": "phone",
                    "subcommand": "resume",
                    "session_id": currentSessionId ?? ""
                ]

                _ = try await pythonBridge.executeCommand(resumeCommand)

                await MainActor.run {
                    self.isPaused = false
                    self.startRecordingTimer()
                    self.currentSession?.status = .recording
                    Logger.shared.info("Resumed phone recording", category: .phoneRecording)
                }
            } catch {
                await MainActor.run {
                    self.handleError("Failed to resume recording: \(error.localizedDescription)")
                }
            }
        }
    }

    func stopRecording() {
        guard isRecording else { return }

        Task {
            do {
                let stopCommand: [String: Any] = [
                    "command": "phone",
                    "subcommand": "stop",
                    "session_id": currentSessionId ?? ""
                ]

                let response = try await pythonBridge.executeCommand(stopCommand)

                if let data = response["data"] as? [String: Any] {
                    await MainActor.run {
                        self.handleRecordingCompletion(data)
                    }
                }
            } catch {
                await MainActor.run {
                    self.handleError("Failed to stop recording: \(error.localizedDescription)")
                    self.resetRecordingState()
                }
            }
        }
    }

    private func handleRecordingCompletion(_ data: [String: Any]) {
        isRecording = false
        isPaused = false
        recordingTimer?.invalidate()
        stopMonitoring()

        if let filePaths = data["file_paths"] as? [String: String] {
            recordedFiles = filePaths
            currentSession?.recordedFiles = filePaths
        }

        if let duration = data["duration_seconds"] as? Double {
            recordingDuration = duration
            currentSession?.duration = duration
        }

        currentSession?.status = .completed
        currentSession?.endTime = Date()

        Logger.shared.info("Completed phone recording session", category: .phoneRecording)

        // Show notification
        showCompletionNotification()

        // Optionally start transcription
        if !recordedFiles.isEmpty {
            offerTranscription()
        }
    }

    private func resetRecordingState() {
        isRecording = false
        isPaused = false
        recordingDuration = 0
        currentSessionId = nil
        currentSession = nil
        recordedFiles.removeAll()
        recordingTimer?.invalidate()
        stopMonitoring()
    }

    // MARK: - Audio Monitoring

    func startMonitoring() {
        guard !isMonitoring else { return }

        isMonitoring = true
        audioMonitorTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            Task {
                await self.updateAudioLevels()
            }
        }
    }

    func stopMonitoring() {
        isMonitoring = false
        audioMonitorTimer?.invalidate()
        audioMonitorTimer = nil
        inputLevels = [0.0, 0.0]
        outputLevels = [0.0, 0.0]
    }

    private func updateAudioLevels() async {
        // Simulate audio level monitoring
        // In a real implementation, this would query the actual audio levels
        await MainActor.run {
            if isRecording && !isPaused {
                // Simulate varying audio levels
                inputLevels = [
                    Float.random(in: 0.1...0.8),
                    Float.random(in: 0.1...0.8)
                ]
                outputLevels = [
                    Float.random(in: 0.05...0.6),
                    Float.random(in: 0.05...0.6)
                ]
            } else {
                inputLevels = [0.0, 0.0]
                outputLevels = [0.0, 0.0]
            }
        }
    }

    // MARK: - Transcription

    func processTranscription() {
        guard !recordedFiles.isEmpty else { return }

        isProcessingTranscript = true
        transcriptionResults.removeAll()

        Task {
            do {
                for (channel, filePath) in recordedFiles {
                    let transcribeCommand: [String: Any] = [
                        "command": "transcribe",
                        "input_file": filePath,
                        "model": "large-v3-turbo",
                        "formats": ["txt"],
                        "language": "auto"
                    ]

                    let response = try await pythonBridge.executeCommand(transcribeCommand)

                    if let data = response["data"] as? [String: Any],
                       let outputFiles = data["output_files"] as? [String],
                       let txtFile = outputFiles.first {

                        // Read transcript content
                        if let transcript = try? String(contentsOfFile: txtFile) {
                            await MainActor.run {
                                self.transcriptionResults[channel] = transcript
                            }
                        }
                    }
                }

                await MainActor.run {
                    self.isProcessingTranscript = false
                    self.showingTranscriptView = true
                    Logger.shared.info("Completed transcription processing", category: .phoneRecording)
                }
            } catch {
                await MainActor.run {
                    self.isProcessingTranscript = false
                    self.handleError("Transcription failed: \(error.localizedDescription)")
                }
            }
        }
    }

    // MARK: - Helper Methods

    private func startRecordingTimer() {
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            Task { @MainActor in
                self.recordingDuration += 1
            }
        }
    }

    private func getRecordingDirectory() -> String {
        let documentsPath = FileManager.default.urls(for: .documentsDirectory, in: .userDomainMask).first!
        let recordingsPath = documentsPath.appendingPathComponent("PhoneRecordings")

        try? FileManager.default.createDirectory(at: recordingsPath, withIntermediateDirectories: true)

        return recordingsPath.path
    }

    private func handleError(_ message: String) {
        lastError = message
        showingError = true
        Logger.shared.error("Phone recording error: \(message)", category: .phoneRecording)
    }

    private func setupBindings() {
        // Listen for Python bridge errors
        pythonBridge.$lastError
            .compactMap { $0 }
            .sink { [weak self] error in
                self?.handleError(error)
            }
            .store(in: &cancellables)
    }

    private func showCompletionNotification() {
        let title = "Phone Recording Complete"
        let body = "Recording saved successfully. Duration: \(formatDuration(recordingDuration))"
        pythonBridge.showCompletionNotification(title: title, body: body)
    }

    private func offerTranscription() {
        // Show alert asking if user wants to transcribe
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            // This would typically be handled by the view
        }
    }

    private func formatDuration(_ duration: TimeInterval) -> String {
        let hours = Int(duration) / 3600
        let minutes = Int(duration) % 3600 / 60
        let seconds = Int(duration) % 60

        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, minutes, seconds)
        } else {
            return String(format: "%d:%02d", minutes, seconds)
        }
    }

    // MARK: - Configuration Validation

    func validateConfiguration() -> Bool {
        guard blackHoleInstalled else { return false }
        guard selectedInputDevice != nil else { return false }
        guard selectedOutputDevice != nil else { return false }
        guard !userName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return false }
        guard !contactName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return false }

        return true
    }

    var formattedRecordingDuration: String {
        formatDuration(recordingDuration)
    }

    var canStartRecording: Bool {
        !isRecording && validateConfiguration()
    }

    var canPauseRecording: Bool {
        isRecording && !isPaused
    }

    var canResumeRecording: Bool {
        isRecording && isPaused
    }

    var canStopRecording: Bool {
        isRecording
    }
}

// MARK: - Supporting Models

struct AudioDevice: Identifiable, Hashable {
    let id: Int
    let name: String
    let channelsIn: Int
    let channelsOut: Int
    let defaultSampleRate: Double

    var displayName: String {
        return "\(name) (\(channelsIn)in/\(channelsOut)out)"
    }
}

class RecordingSession: ObservableObject {
    let id: String
    let userName: String
    let contactName: String
    let startTime: Date
    var endTime: Date?
    var duration: TimeInterval = 0
    var status: RecordingStatus = .notStarted
    var recordedFiles: [String: String] = [:]

    init(id: String, userName: String, contactName: String, startTime: Date, status: RecordingStatus = .notStarted) {
        self.id = id
        self.userName = userName
        self.contactName = contactName
        self.startTime = startTime
        self.status = status
    }
}

enum RecordingStatus {
    case notStarted
    case recording
    case paused
    case completed
    case error

    var displayName: String {
        switch self {
        case .notStarted: return "Not Started"
        case .recording: return "Recording"
        case .paused: return "Paused"
        case .completed: return "Completed"
        case .error: return "Error"
        }
    }

    var color: Color {
        switch self {
        case .notStarted: return .secondary
        case .recording: return .red
        case .paused: return .orange
        case .completed: return .green
        case .error: return .red
        }
    }
}

// MARK: - Logger Extension

extension Logger.Category {
    static let phoneRecording = Logger.Category("PhoneRecording")
}