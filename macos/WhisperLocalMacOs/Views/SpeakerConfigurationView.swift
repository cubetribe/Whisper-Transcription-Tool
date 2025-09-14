import SwiftUI

/// View for configuring speaker names and identities for phone recordings
struct SpeakerConfigurationView: View {
    @Binding var userName: String
    @Binding var contactName: String

    @Environment(\.dismiss) var dismiss
    @State private var tempUserName: String = ""
    @State private var tempContactName: String = ""
    @State private var showingPresets = false

    // Common contact presets
    private let contactPresets = [
        "Contact", "Client", "Customer", "Colleague", "Family Member", "Friend",
        "Support Agent", "Sales Rep", "Manager", "Doctor", "Teacher", "Lawyer"
    ]

    var body: some View {
        NavigationStack {
            Form {
                speakerIdentitySection
                presetsSection
                previewSection
                guidelinesSection
            }
            .navigationTitle("Speaker Configuration")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        saveConfiguration()
                    }
                    .disabled(!isConfigurationValid)
                }
            }
            .onAppear {
                tempUserName = userName
                tempContactName = contactName
            }
        }
        .frame(minWidth: 480, minHeight: 520)
    }

    // MARK: - Speaker Identity Section

    private var speakerIdentitySection: some View {
        Section {
            VStack(alignment: .leading, spacing: 16) {
                // User Name Configuration
                VStack(alignment: .leading, spacing: 8) {
                    Label("Your Name", systemImage: "person.fill")
                        .font(.headline)
                        .foregroundColor(.primary)

                    TextField("Enter your name", text: $tempUserName)
                        .textFieldStyle(.roundedBorder)

                    Text("This name will identify you in the transcript")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Divider()

                // Contact Name Configuration
                VStack(alignment: .leading, spacing: 8) {
                    Label("Contact Name", systemImage: "person.badge.plus.fill")
                        .font(.headline)
                        .foregroundColor(.primary)

                    HStack {
                        TextField("Enter contact name", text: $tempContactName)
                            .textFieldStyle(.roundedBorder)

                        Button {
                            showingPresets.toggle()
                        } label: {
                            Image(systemName: "list.bullet")
                        }
                        .buttonStyle(.bordered)
                        .help("Choose from presets")
                    }

                    Text("Name of the person you're speaking with")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        } header: {
            HStack {
                Image(systemName: "person.2.fill")
                    .foregroundColor(.blue)
                Text("Speaker Identification")
                    .font(.subheadline)
                    .fontWeight(.medium)
            }
        }
    }

    // MARK: - Presets Section

    private var presetsSection: some View {
        Section {
            if showingPresets {
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: 8) {
                    ForEach(contactPresets, id: \.self) { preset in
                        Button(preset) {
                            tempContactName = preset
                            showingPresets = false
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                    }
                }
                .transition(.opacity.combined(with: .scale))
            } else {
                Button("Show Contact Presets") {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        showingPresets = true
                    }
                }
                .buttonStyle(.bordered)
            }
        } header: {
            HStack {
                Image(systemName: "star.fill")
                    .foregroundColor(.orange)
                Text("Quick Presets")
                    .font(.subheadline)
                    .fontWeight(.medium)
            }
        }
    }

    // MARK: - Preview Section

    private var previewSection: some View {
        Section {
            VStack(alignment: .leading, spacing: 12) {
                Text("Transcript Preview")
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)

                VStack(alignment: .leading, spacing: 6) {
                    TranscriptPreviewLine(
                        speakerName: tempUserName.isEmpty ? "Your Name" : tempUserName,
                        text: "Hello, thanks for calling today.",
                        isUser: true
                    )

                    TranscriptPreviewLine(
                        speakerName: tempContactName.isEmpty ? "Contact Name" : tempContactName,
                        text: "Hi, I wanted to discuss the project details with you.",
                        isUser: false
                    )

                    TranscriptPreviewLine(
                        speakerName: tempUserName.isEmpty ? "Your Name" : tempUserName,
                        text: "Of course! Let me pull up the information.",
                        isUser: true
                    )
                }
                .padding()
                .background(.quaternary)
                .cornerRadius(8)
            }
        } header: {
            HStack {
                Image(systemName: "eye.fill")
                    .foregroundColor(.green)
                Text("Transcript Preview")
                    .font(.subheadline)
                    .fontWeight(.medium)
            }
        }
    }

    // MARK: - Guidelines Section

    private var guidelinesSection: some View {
        Section {
            VStack(alignment: .leading, spacing: 8) {
                GuidelineRow(
                    icon: "checkmark.circle.fill",
                    color: .green,
                    text: "Use real names for better transcript organization"
                )

                GuidelineRow(
                    icon: "person.badge.key.fill",
                    color: .blue,
                    text: "Your name helps identify your voice in recordings"
                )

                GuidelineRow(
                    icon: "shield.checkered",
                    color: .orange,
                    text: "Names are only used locally for transcript labeling"
                )

                GuidelineRow(
                    icon: "pencil.and.outline",
                    color: .purple,
                    text: "You can change these names anytime"
                )
            }
        } header: {
            HStack {
                Image(systemName: "info.circle.fill")
                    .foregroundColor(.blue)
                Text("Guidelines")
                    .font(.subheadline)
                    .fontWeight(.medium)
            }
        }
    }

    // MARK: - Helper Views

    private func saveConfiguration() {
        userName = tempUserName.trimmingCharacters(in: .whitespacesAndNewlines)
        contactName = tempContactName.trimmingCharacters(in: .whitespacesAndNewlines)
        dismiss()
    }

    private var isConfigurationValid: Bool {
        !tempUserName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        !tempContactName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
}

// MARK: - Supporting Views

struct TranscriptPreviewLine: View {
    let speakerName: String
    let text: String
    let isUser: Bool

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            // Speaker indicator
            Circle()
                .fill(isUser ? .blue.gradient : .green.gradient)
                .frame(width: 8, height: 8)
                .padding(.top, 4)

            VStack(alignment: .leading, spacing: 2) {
                Text(speakerName)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(isUser ? .blue : .green)

                Text(text)
                    .font(.subheadline)
                    .foregroundColor(.primary)
            }

            Spacer()
        }
    }
}

struct GuidelineRow: View {
    let icon: String
    let color: Color
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: icon)
                .foregroundColor(color)
                .font(.subheadline)
                .frame(width: 16)

            Text(text)
                .font(.subheadline)
                .foregroundColor(.primary)
                .multilineTextAlignment(.leading)

            Spacer()
        }
    }
}

// MARK: - Advanced Configuration Sheet

struct AdvancedSpeakerConfigurationView: View {
    @Binding var userName: String
    @Binding var contactName: String
    @State private var userVoiceProfile: VoiceProfile = VoiceProfile()
    @State private var contactVoiceProfile: VoiceProfile = VoiceProfile()
    @State private var enableVoiceDetection = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Voice Detection") {
                    Toggle("Enable automatic speaker detection", isEnabled: $enableVoiceDetection)

                    if enableVoiceDetection {
                        Text("Uses AI to automatically identify speakers based on voice characteristics")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                if enableVoiceDetection {
                    Section("Voice Profiles") {
                        VoiceProfileEditor(
                            title: "Your Voice Profile",
                            name: userName,
                            profile: $userVoiceProfile
                        )

                        VoiceProfileEditor(
                            title: "Contact Voice Profile",
                            name: contactName,
                            profile: $contactVoiceProfile
                        )
                    }
                }

                Section("Channel Assignment") {
                    Picker("Your voice primarily on", selection: .constant("input")) {
                        Text("Input Channel (Microphone)").tag("input")
                        Text("Output Channel (System Audio)").tag("output")
                        Text("Auto Detect").tag("auto")
                    }

                    Picker("Contact voice primarily on", selection: .constant("output")) {
                        Text("Input Channel (Microphone)").tag("input")
                        Text("Output Channel (System Audio)").tag("output")
                        Text("Auto Detect").tag("auto")
                    }
                }
            }
            .navigationTitle("Advanced Configuration")
        }
    }
}

struct VoiceProfileEditor: View {
    let title: String
    let name: String
    @Binding var profile: VoiceProfile

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.subheadline)
                .fontWeight(.medium)

            Text(name)
                .font(.headline)
                .foregroundColor(.primary)

            VStack(alignment: .leading, spacing: 4) {
                Text("Voice Characteristics")
                    .font(.caption)
                    .foregroundColor(.secondary)

                HStack {
                    Text("Pitch:")
                    Slider(value: $profile.pitch, in: 0...1)
                    Text(profile.pitchDescription)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                HStack {
                    Text("Pace:")
                    Slider(value: $profile.pace, in: 0...1)
                    Text(profile.paceDescription)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .cornerRadius(8)
    }
}

// MARK: - Supporting Models

struct VoiceProfile {
    var pitch: Double = 0.5
    var pace: Double = 0.5
    var volume: Double = 0.5

    var pitchDescription: String {
        switch pitch {
        case 0.0..<0.3: return "Low"
        case 0.3..<0.7: return "Medium"
        default: return "High"
        }
    }

    var paceDescription: String {
        switch pace {
        case 0.0..<0.3: return "Slow"
        case 0.3..<0.7: return "Normal"
        default: return "Fast"
        }
    }
}

#Preview {
    SpeakerConfigurationView(
        userName: .constant("John Doe"),
        contactName: .constant("Client")
    )
}