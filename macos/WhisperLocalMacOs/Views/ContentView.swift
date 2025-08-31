import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack {
            Image(systemName: "waveform")
                .imageScale(.large)
                .foregroundStyle(.tint)
            Text("WhisperLocal macOS")
                .font(.title)
            Text("Whisper Transcription Tool v0.9.6.0")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
        .frame(minWidth: 800, minHeight: 600)
    }
}

#Preview {
    ContentView()
}