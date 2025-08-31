import SwiftUI

struct ContentView: View {
    @State private var selectedTab: SidebarItem = .transcribe
    @State private var columnVisibility: NavigationSplitViewVisibility = .all
    
    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            SidebarView(selectedTab: $selectedTab)
                .navigationSplitViewColumnWidth(min: 200, ideal: 250, max: 300)
        } detail: {
            MainContentView(selectedTab: selectedTab)
        }
        .navigationTitle("Whisper Local")
        .navigationSubtitle("Audio Transcription v0.9.6.0")
        .toolbar {
            ToolbarView()
        }
        .frame(minWidth: 1000, minHeight: 700)
    }
}

#Preview {
    ContentView()
        .frame(width: 1200, height: 800)
}