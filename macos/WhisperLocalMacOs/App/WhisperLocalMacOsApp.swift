import SwiftUI

@main
struct WhisperLocalMacOsApp: App {
    @StateObject private var dependencyManager = DependencyManager.shared
    @StateObject private var performanceManager = PerformanceManager.shared
    @StateObject private var menuBarManager = MenuBarManager.shared
    @StateObject private var quickLookManager = QuickLookManager.shared
    @StateObject private var fileAssociationManager = FileAssociationManager.shared
    @StateObject private var spotlightManager = SpotlightManager.shared
    @StateObject private var resourceMonitor = ResourceMonitor.shared
    @State private var showingDependencyError = false
    
    var body: some Scene {
        WindowGroup {
            Group {
                if dependencyManager.dependencyStatus.isValid {
                    ContentView()
                } else if dependencyManager.isValidating {
                    DependencyValidatingView()
                        .frame(minWidth: 400, minHeight: 300)
                } else {
                    DependencyStatusView()
                        .frame(minWidth: 600, minHeight: 500)
                }
            }
            .onAppear {
                validateDependenciesOnStartup()
                initializeNativeIntegrations()
            }
        }
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified)
    }
    
    private func validateDependenciesOnStartup() {
        Task {
            await dependencyManager.validateDependencies()
            
            // Show error overlay if dependencies are invalid
            if !dependencyManager.dependencyStatus.isValid {
                showingDependencyError = true
            }
        }
    }
    
    private func initializeNativeIntegrations() {
        // Request notification permissions
        let pythonBridge = PythonBridge()
        pythonBridge.requestNotificationPermissions()
        
        // Configure menu bar manager with Python bridge
        menuBarManager.configurePythonBridge(pythonBridge)
        
        // Enable menu bar integration by default
        menuBarManager.setMenuBarItemVisible(true)
        menuBarManager.setQuickTranscriptionEnabled(true)
        
        // Setup file associations
        fileAssociationManager.setupAppDelegateIntegration()
        
        // Initialize Spotlight integration
        if spotlightManager.isSpotlightIndexingEnabled {
            Logger.shared.info("Spotlight integration available and ready", category: .system)
        }
        
        Logger.shared.info("Native macOS integrations initialized", category: .system)
    }
}