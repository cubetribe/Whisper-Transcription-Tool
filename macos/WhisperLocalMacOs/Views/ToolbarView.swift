import SwiftUI

struct ToolbarView: ToolbarContent {
    @State private var showingModelManager = false
    
    var body: some ToolbarContent {
        // Leading toolbar items
        ToolbarItemGroup(placement: .navigation) {
            Button(action: {
                // Toggle sidebar visibility
                NSApp.keyWindow?.firstResponder?.tryToPerform(#selector(NSSplitViewController.toggleSidebar(_:)), with: nil)
            }) {
                Image(systemName: "sidebar.left")
            }
            .help("Toggle Sidebar")
        }
        
        // Principal toolbar items (center)
        ToolbarItemGroup(placement: .principal) {
            HStack(spacing: 16) {
                // Quick Action: New Transcription
                Button(action: {
                    // TODO: Open file picker for transcription
                    print("Quick transcribe action")
                }) {
                    Label("Transcribe", systemImage: "waveform.circle")
                }
                .buttonStyle(.borderedProminent)
                .help("Start new transcription")
                
                // Quick Action: Extract Audio
                Button(action: {
                    // TODO: Open file picker for extraction
                    print("Quick extract action")
                }) {
                    Label("Extract", systemImage: "scissors")
                }
                .buttonStyle(.bordered)
                .help("Extract audio from video")
            }
        }
        
        // Trailing toolbar items
        ToolbarItemGroup(placement: .primaryAction) {
            // Status indicator
            HStack(spacing: 8) {
                Image(systemName: "circle.fill")
                    .foregroundColor(.green)
                    .font(.caption)
                
                Text("Ready")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .help("Application Status")
            
            Divider()
            
            // Model Manager
            Button(action: {
                showingModelManager = true
            }) {
                Image(systemName: "brain")
            }
            .help("Manage Models")
            
            // Settings shortcut
            Button(action: {
                // TODO: Open settings
                print("Open settings")
            }) {
                Image(systemName: "gearshape")
            }
            .help("Settings")
            
            // Help menu
            Menu {
                Button("Documentation") {
                    // TODO: Open documentation
                    print("Open documentation")
                }
                
                Button("Report Issue") {
                    // TODO: Open issue reporting
                    print("Report issue")
                }
                
                Divider()
                
                Button("About Whisper Local") {
                    // TODO: Show about window
                    print("Show about")
                }
            } label: {
                Image(systemName: "questionmark.circle")
            }
            .help("Help")
        }
        .sheet(isPresented: $showingModelManager) {
            ModelManagerWindow()
                .frame(width: 900, height: 600)
        }
    }
}

#Preview {
    NavigationStack {
        VStack {
            Text("Main Content Area")
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .navigationTitle("Whisper Local")
        .toolbar {
            ToolbarView()
        }
    }
    .frame(width: 1000, height: 700)
}