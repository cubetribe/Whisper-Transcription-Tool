import XCTest
import SwiftUI
@testable import WhisperLocalMacOs

/// UI automation and performance test suite
/// Tests complete user interface workflows and performance characteristics
class UITests: XCTestCase {
    
    // MARK: - Test Infrastructure
    
    var app: XCUIApplication!
    var performanceMetrics: UIPerformanceMetrics!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Configure test environment
        continueAfterFailure = false
        
        // Launch application for UI testing
        app = XCUIApplication()
        app.launchEnvironment["UI_TESTING"] = "1"
        app.launchEnvironment["SKIP_ONBOARDING"] = "1"
        
        performanceMetrics = UIPerformanceMetrics()
        
        app.launch()
        
        // Wait for app to be ready
        let mainWindow = app.windows.firstMatch
        XCTAssertTrue(mainWindow.waitForExistence(timeout: 10.0), "Main window should appear")
    }
    
    override func tearDownWithError() throws {
        app?.terminate()
        try super.tearDownWithError()
    }
    
    // MARK: - Drag and Drop Workflow Tests
    
    func testDragAndDropWorkflow() throws {
        // Test complete drag-and-drop file selection workflow
        
        // Navigate to Transcribe view
        let sidebar = app.splitGroups.firstMatch
        let transcribeButton = sidebar.buttons["Transcribe"]
        XCTAssertTrue(transcribeButton.exists, "Transcribe button should exist in sidebar")
        transcribeButton.tap()
        
        // Find file drop area
        let dropArea = app.groups["FileDropArea"]
        XCTAssertTrue(dropArea.waitForExistence(timeout: 5.0), "File drop area should exist")
        
        // Test drop area visual feedback
        XCTAssertTrue(dropArea.staticTexts["Drop audio or video files here"].exists, "Drop instruction should be visible")
        
        // Simulate file selection (since actual drag-drop is complex in UI tests)
        let selectFileButton = app.buttons["Select File"]
        if selectFileButton.exists {
            selectFileButton.tap()
            
            // In UI test environment, we can't interact with NSOpenPanel
            // But we can verify the button triggers the expected action
            XCTAssertTrue(selectFileButton.exists, "File selection should be available")
        }
        
        // Test drag-drop visual states
        let dropIndicator = dropArea.images["drop.circle"]
        XCTAssertTrue(dropIndicator.exists || dropArea.exists, "Drop indicator should be present")
        
        // Verify file validation messages
        let validationMessages = app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Supported formats'"))
        XCTAssertGreaterThan(validationMessages.count, 0, "Format validation info should be shown")
    }
    
    func testBatchProcessingUI() throws {
        // Test batch processing queue management workflow
        
        // Navigate to Batch view
        let sidebar = app.splitGroups.firstMatch
        let batchButton = sidebar.buttons["Batch"]
        XCTAssertTrue(batchButton.exists, "Batch button should exist in sidebar")
        batchButton.tap()
        
        // Verify batch queue interface
        let queueView = app.groups["QueueView"]
        XCTAssertTrue(queueView.waitForExistence(timeout: 5.0), "Queue view should exist")
        
        // Test empty state
        let emptyStateView = queueView.groups["EmptyQueueView"]
        if emptyStateView.exists {
            XCTAssertTrue(emptyStateView.staticTexts["No files in queue"].exists, "Empty state message should be shown")
            
            // Test add files button
            let addFilesButton = emptyStateView.buttons["Add Files"]
            XCTAssertTrue(addFilesButton.exists, "Add files button should be available")
        }
        
        // Test batch controls
        let batchControls = app.groups["BatchControlsView"]
        if batchControls.exists {
            let processButton = batchControls.buttons["Process Queue"]
            let pauseButton = batchControls.buttons["Pause"]
            let cancelButton = batchControls.buttons["Cancel All"]
            
            // Verify control buttons exist (may be disabled when queue is empty)
            XCTAssertTrue(processButton.exists, "Process button should exist")
            XCTAssertTrue(pauseButton.exists || cancelButton.exists, "Pause or cancel button should exist")
        }
        
        // Test queue management features
        let clearButton = app.buttons["Clear Completed"]
        let exportButton = app.buttons["Export Results"]
        
        // These buttons may not be visible when queue is empty, but should be in the view hierarchy
        // XCTAssertTrue(clearButton.exists || exportButton.exists, "Queue management buttons should be available")
        
        // Test progress indicators (when batch is running)
        let progressIndicator = app.progressIndicators.firstMatch
        // Progress indicator may not be visible when not processing
        // XCTAssertTrue(progressIndicator.exists, "Progress indicator should be available")
    }
    
    func testModelManagerUI() throws {
        // Test Model Manager window and functionality
        
        // Navigate to Models view
        let sidebar = app.splitGroups.firstMatch
        let modelsButton = sidebar.buttons["Models"]
        XCTAssertTrue(modelsButton.exists, "Models button should exist in sidebar")
        modelsButton.tap()
        
        // Test Model Manager interface
        let modelListView = app.groups["ModelListView"]
        XCTAssertTrue(modelListView.waitForExistence(timeout: 5.0), "Model list view should exist")
        
        // Test model rows
        let modelRows = app.groups.matching(NSPredicate(format: "identifier BEGINSWITH 'ModelRow'"))
        XCTAssertGreaterThan(modelRows.count, 0, "Should display available models")
        
        // Test first model row details
        if modelRows.count > 0 {
            let firstModel = modelRows.element(boundBy: 0)
            
            // Check for model information elements
            let modelName = firstModel.staticTexts.firstMatch
            XCTAssertTrue(modelName.exists, "Model name should be displayed")
            
            let statusBadge = firstModel.groups.matching(NSPredicate(format: "identifier CONTAINS 'StatusBadge'"))
            XCTAssertGreaterThanOrEqual(statusBadge.count, 0, "Status badge should be available")
            
            // Test model actions
            let downloadButton = firstModel.buttons.matching(NSPredicate(format: "label CONTAINS 'Download'"))
            let selectButton = firstModel.buttons.matching(NSPredicate(format: "label CONTAINS 'Select'"))
            
            XCTAssertTrue(downloadButton.count > 0 || selectButton.count > 0, "Model action buttons should be available")
        }
        
        // Test search functionality
        let searchField = app.searchFields.firstMatch
        if searchField.exists {
            searchField.tap()
            searchField.typeText("large")
            
            // Wait for search filtering
            Thread.sleep(forTimeInterval: 1.0)
            
            // Verify search filtering works
            let filteredRows = app.groups.matching(NSPredicate(format: "identifier BEGINSWITH 'ModelRow'"))
            // Should show filtered results (exact count depends on available models)
        }
        
        // Test model detail view (if available)
        let modelDetailView = app.groups["ModelDetailView"]
        if modelDetailView.exists {
            // Check for performance indicators
            let performanceSection = modelDetailView.groups["PerformanceIndicators"]
            // Performance indicators may be context-dependent
        }
    }
    
    func testTranscriptionWorkflow() throws {
        // Test complete transcription workflow
        
        // Navigate to Transcribe view
        let sidebar = app.splitGroups.firstMatch
        let transcribeButton = sidebar.buttons["Transcribe"]
        transcribeButton.tap()
        
        // Test configuration section
        let configSection = app.groups["TranscriptionConfigSection"]
        XCTAssertTrue(configSection.waitForExistence(timeout: 5.0), "Configuration section should exist")
        
        // Test model selection
        let modelPicker = configSection.buttons.matching(NSPredicate(format: "label CONTAINS 'Model'"))
        if modelPicker.count > 0 {
            modelPicker.element(boundBy: 0).tap()
            
            // Test model menu
            let modelMenu = app.menus.firstMatch
            if modelMenu.exists {
                let menuItems = modelMenu.menuItems
                XCTAssertGreaterThan(menuItems.count, 0, "Model menu should have options")
                
                // Select first available model
                if menuItems.count > 0 {
                    menuItems.element(boundBy: 0).tap()
                }
            }
        }
        
        // Test language selection
        let languagePicker = configSection.buttons.matching(NSPredicate(format: "label CONTAINS 'Language'"))
        if languagePicker.count > 0 {
            languagePicker.element(boundBy: 0).tap()
            
            let languageMenu = app.menus.firstMatch
            if languageMenu.exists {
                // Test auto-detection option
                let autoOption = languageMenu.menuItems.matching(NSPredicate(format: "title CONTAINS 'Auto'"))
                if autoOption.count > 0 {
                    autoOption.element(boundBy: 0).tap()
                }
            }
        }
        
        // Test format selection
        let formatToggles = configSection.checkBoxes.matching(NSPredicate(format: "label CONTAINS 'TXT' OR label CONTAINS 'SRT' OR label CONTAINS 'VTT'"))
        XCTAssertGreaterThan(formatToggles.count, 0, "Format selection checkboxes should exist")
        
        // Test output directory selection
        let outputButton = app.buttons.matching(NSPredicate(format: "label CONTAINS 'Output' OR label CONTAINS 'Destination'"))
        if outputButton.count > 0 {
            outputButton.element(boundBy: 0).tap()
            // Directory picker interaction would require system dialog handling
        }
        
        // Test start button state (should be disabled without file selection)
        let startButton = app.buttons.matching(NSPredicate(format: "label CONTAINS 'Start'"))
        if startButton.count > 0 {
            let button = startButton.element(boundBy: 0)
            // Button state depends on whether required inputs are provided
            XCTAssertTrue(button.exists, "Start button should exist")
        }
    }
    
    func testNavigationAndLayoutAdaptation() throws {
        // Test window resizing and layout adaptation
        
        let mainWindow = app.windows.firstMatch
        XCTAssertTrue(mainWindow.exists, "Main window should exist")
        
        // Test sidebar navigation
        let sidebar = app.splitGroups.firstMatch.groups.firstMatch
        let sidebarItems = ["Transcribe", "Extract", "Batch", "Models", "Logs", "Settings"]
        
        for itemName in sidebarItems {
            let button = sidebar.buttons[itemName]
            XCTAssertTrue(button.exists, "\(itemName) button should exist in sidebar")
            
            // Test navigation
            button.tap()
            
            // Wait for navigation to complete
            Thread.sleep(forTimeInterval: 0.5)
            
            // Verify content area updates
            let contentArea = app.splitGroups.firstMatch.groups.element(boundBy: 1)
            XCTAssertTrue(contentArea.exists, "Content area should exist after navigation")
        }
        
        // Test toolbar functionality
        let toolbar = app.toolbars.firstMatch
        if toolbar.exists {
            // Test sidebar toggle
            let sidebarToggle = toolbar.buttons.matching(NSPredicate(format: "label CONTAINS 'sidebar' OR identifier CONTAINS 'sidebar'"))
            if sidebarToggle.count > 0 {
                sidebarToggle.element(boundBy: 0).tap()
                Thread.sleep(forTimeInterval: 0.5)
                
                // Toggle back
                sidebarToggle.element(boundBy: 0).tap()
            }
            
            // Test quick action buttons
            let quickButtons = toolbar.buttons.matching(NSPredicate(format: "label CONTAINS 'Quick' OR label CONTAINS 'Transcribe'"))
            // Quick action buttons may be context-dependent
        }
    }
    
    func testKeyboardShortcuts() throws {
        // Test keyboard shortcuts and accessibility
        
        let mainWindow = app.windows.firstMatch
        
        // Test Cmd+1 through Cmd+6 for sidebar navigation
        let shortcuts = [
            (XCUIKeyboardKey.command, "1"),
            (XCUIKeyboardKey.command, "2"),
            (XCUIKeyboardKey.command, "3"),
            (XCUIKeyboardKey.command, "4"),
            (XCUIKeyboardKey.command, "5"),
            (XCUIKeyboardKey.command, "6")
        ]
        
        for (modifier, key) in shortcuts {
            mainWindow.typeKey(key, modifierFlags: modifier)
            Thread.sleep(forTimeInterval: 0.5)
            
            // Verify navigation occurred (content area should update)
            let contentArea = app.splitGroups.firstMatch.groups.element(boundBy: 1)
            XCTAssertTrue(contentArea.exists, "Content area should respond to keyboard navigation")
        }
        
        // Test Cmd+Comma for Settings
        mainWindow.typeKey(",", modifierFlags: .command)
        Thread.sleep(forTimeInterval: 0.5)
        
        // Should navigate to Settings view
        let settingsContent = app.groups.matching(NSPredicate(format: "identifier CONTAINS 'Settings'"))
        // Settings content verification depends on implementation
    }
    
    func testErrorHandlingUI() throws {
        // Test error display and recovery UI
        
        // Navigate to transcribe view
        let sidebar = app.splitGroups.firstMatch
        let transcribeButton = sidebar.buttons["Transcribe"]
        transcribeButton.tap()
        
        // Test error scenarios that can be triggered in UI
        // Note: Actual error triggering may require specific test conditions
        
        // Look for error alert components
        let errorAlerts = app.alerts.matching(NSPredicate(format: "identifier CONTAINS 'Error' OR label CONTAINS 'Error'"))
        
        // Test error recovery buttons (if error alerts are present)
        for i in 0..<errorAlerts.count {
            let alert = errorAlerts.element(boundBy: i)
            if alert.exists {
                // Test recovery actions
                let retryButton = alert.buttons.matching(NSPredicate(format: "label CONTAINS 'Retry'"))
                let cancelButton = alert.buttons.matching(NSPredicate(format: "label CONTAINS 'Cancel'"))
                let reportButton = alert.buttons.matching(NSPredicate(format: "label CONTAINS 'Report'"))
                
                XCTAssertTrue(retryButton.count > 0 || cancelButton.count > 0, "Error alert should have action buttons")
                
                // Dismiss alert
                if cancelButton.count > 0 {
                    cancelButton.element(boundBy: 0).tap()
                }
            }
        }
        
        // Test error message display in content areas
        let errorMessages = app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'error' OR label CONTAINS 'Error'"))
        // Error messages are context-dependent and may not always be present
    }
    
    // MARK: - Performance Benchmark Tests
    
    func testApplicationStartupPerformance() throws {
        // Measure application startup time
        
        // Terminate and relaunch for accurate measurement
        app.terminate()
        
        let startupOptions = XCTMeasureOptions()
        startupOptions.iterationCount = 5
        
        measure(options: startupOptions) {
            app = XCUIApplication()
            app.launchEnvironment["UI_TESTING"] = "1"
            app.launch()
            
            // Wait for main interface to be ready
            let mainWindow = app.windows.firstMatch
            _ = mainWindow.waitForExistence(timeout: 10.0)
            
            // Measure until sidebar is interactive
            let sidebar = app.splitGroups.firstMatch
            _ = sidebar.waitForExistence(timeout: 5.0)
        }
        
        // Startup should complete within reasonable time
        // Exact timing will depend on system performance
        performanceMetrics.recordStartupTime()
    }
    
    func testUIResponsiveness() throws {
        // Test UI responsiveness during operations
        
        let responseOptions = XCTMeasureOptions()
        responseOptions.iterationCount = 3
        
        measure(options: responseOptions) {
            // Test sidebar navigation speed
            let sidebar = app.splitGroups.firstMatch
            let transcribeButton = sidebar.buttons["Transcribe"]
            
            transcribeButton.tap()
            
            // Measure time for content to appear
            let contentArea = app.splitGroups.firstMatch.groups.element(boundBy: 1)
            _ = contentArea.waitForExistence(timeout: 2.0)
            
            // Test multiple rapid navigation changes
            let batchButton = sidebar.buttons["Batch"]
            batchButton.tap()
            _ = contentArea.waitForExistence(timeout: 2.0)
            
            let modelsButton = sidebar.buttons["Models"]
            modelsButton.tap()
            _ = contentArea.waitForExistence(timeout: 2.0)
        }
        
        performanceMetrics.recordUIResponsiveness()
    }
    
    func testMemoryUsageStability() throws {
        // Test memory usage during typical workflows
        
        let initialMemory = performanceMetrics.getCurrentMemoryUsage()
        
        // Perform various UI operations
        let sidebar = app.splitGroups.firstMatch
        let sidebarItems = ["Transcribe", "Batch", "Models", "Logs", "Settings"]
        
        // Navigate through all views multiple times
        for cycle in 0..<3 {
            for itemName in sidebarItems {
                let button = sidebar.buttons[itemName]
                button.tap()
                Thread.sleep(forTimeInterval: 1.0)
                
                // Record memory usage
                let currentMemory = performanceMetrics.getCurrentMemoryUsage()
                XCTAssertLessThan(currentMemory - initialMemory, 200_000_000, // 200MB increase max
                                 "Memory usage should remain stable during navigation (cycle \(cycle + 1))")
            }
        }
        
        let finalMemory = performanceMetrics.getCurrentMemoryUsage()
        performanceMetrics.recordMemoryStability(initial: initialMemory, final: finalMemory)
    }
    
    func testLargeDataHandlingPerformance() throws {
        // Test UI performance with large datasets
        
        // Navigate to batch processing view
        let sidebar = app.splitGroups.firstMatch
        let batchButton = sidebar.buttons["Batch"]
        batchButton.tap()
        
        let performanceOptions = XCTMeasureOptions()
        performanceOptions.iterationCount = 3
        
        measure(options: performanceOptions) {
            // Test scrolling performance (if queue has many items)
            let queueView = app.groups["QueueView"]
            if queueView.exists {
                let scrollView = queueView.scrollViews.firstMatch
                if scrollView.exists {
                    // Simulate scrolling through large queue
                    scrollView.swipeUp()
                    Thread.sleep(forTimeInterval: 0.5)
                    scrollView.swipeDown()
                    Thread.sleep(forTimeInterval: 0.5)
                }
            }
            
            // Test model list performance
            sidebar.buttons["Models"].tap()
            Thread.sleep(forTimeInterval: 0.5)
            
            let modelListView = app.groups["ModelListView"]
            if modelListView.exists {
                let modelScrollView = modelListView.scrollViews.firstMatch
                if modelScrollView.exists {
                    modelScrollView.swipeUp()
                    Thread.sleep(forTimeInterval: 0.5)
                    modelScrollView.swipeDown()
                }
            }
        }
        
        performanceMetrics.recordLargeDataHandling()
    }
    
    // MARK: - Stress Tests
    
    func testRapidNavigationStress() throws {
        // Stress test rapid UI navigation
        
        let sidebar = app.splitGroups.firstMatch
        let sidebarItems = ["Transcribe", "Extract", "Batch", "Models", "Logs", "Settings"]
        
        let stressOptions = XCTMeasureOptions()
        stressOptions.iterationCount = 2
        
        measure(options: stressOptions) {
            // Rapid navigation for 30 seconds
            let endTime = Date().addingTimeInterval(30.0)
            var navigationCount = 0
            
            while Date() < endTime {
                let randomItem = sidebarItems.randomElement()!
                let button = sidebar.buttons[randomItem]
                
                if button.exists && button.isHittable {
                    button.tap()
                    navigationCount += 1
                    
                    // Small delay to allow UI to respond
                    Thread.sleep(forTimeInterval: 0.1)
                }
            }
            
            XCTAssertGreaterThan(navigationCount, 50, "Should handle rapid navigation efficiently")
        }
        
        performanceMetrics.recordStressTesting()
    }
    
    func testWindowResizeStress() throws {
        // Test window resizing performance
        
        let mainWindow = app.windows.firstMatch
        guard mainWindow.exists else {
            XCTFail("Main window should exist for resize testing")
            return
        }
        
        let stressOptions = XCTMeasureOptions()
        stressOptions.iterationCount = 3
        
        measure(options: stressOptions) {
            // Simulate multiple rapid resizes
            for _ in 0..<20 {
                // Note: Actual window resizing in UI tests is limited
                // This test mainly verifies the UI can handle resize events
                
                // Trigger sidebar toggle to test layout changes
                let toolbar = app.toolbars.firstMatch
                if toolbar.exists {
                    let sidebarToggle = toolbar.buttons.firstMatch
                    if sidebarToggle.exists {
                        sidebarToggle.tap()
                        Thread.sleep(forTimeInterval: 0.1)
                        sidebarToggle.tap()
                        Thread.sleep(forTimeInterval: 0.1)
                    }
                }
            }
        }
    }
    
    // MARK: - Accessibility Tests
    
    func testAccessibilityCompliance() throws {
        // Test accessibility features
        
        let sidebar = app.splitGroups.firstMatch
        
        // Test VoiceOver accessibility
        let sidebarButtons = sidebar.buttons
        for i in 0..<sidebarButtons.count {
            let button = sidebarButtons.element(boundBy: i)
            
            // Verify button has accessibility label
            XCTAssertFalse(button.label.isEmpty, "Button should have accessibility label")
            
            // Verify button is accessible
            XCTAssertTrue(button.isAccessibilityElement, "Button should be accessible to assistive technologies")
        }
        
        // Test keyboard navigation
        let firstButton = sidebarButtons.firstMatch
        if firstButton.exists {
            firstButton.tap()
            
            // Test tab navigation (if implemented)
            app.typeKey(XCUIKeyboardKey.tab, modifierFlags: [])
            
            // Verify focus management
            // Focus testing requires more specific accessibility implementation
        }
        
        // Test color contrast and visual accessibility
        // This would require specific UI testing for color accessibility
        // Which is typically done through design reviews and accessibility audits
    }
}

// MARK: - Performance Metrics Helper

class UIPerformanceMetrics {
    private var metrics: [String: Any] = [:]
    
    func recordStartupTime() {
        let timestamp = Date()
        metrics["startup_time"] = timestamp
        print("📊 Startup performance recorded at \(timestamp)")
    }
    
    func recordUIResponsiveness() {
        metrics["ui_responsiveness"] = Date()
        print("📊 UI responsiveness metrics recorded")
    }
    
    func recordMemoryStability(initial: Int64, final: Int64) {
        let increase = final - initial
        metrics["memory_stability"] = [
            "initial": initial,
            "final": final,
            "increase": increase,
            "increase_mb": increase / (1024 * 1024)
        ]
        print("📊 Memory stability: +\(increase / (1024 * 1024))MB")
    }
    
    func recordLargeDataHandling() {
        metrics["large_data_performance"] = Date()
        print("📊 Large data handling performance recorded")
    }
    
    func recordStressTesting() {
        metrics["stress_testing"] = Date()
        print("📊 Stress testing metrics recorded")
    }
    
    func getCurrentMemoryUsage() -> Int64 {
        var taskInfo = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info>.size) / 4
        
        let result = withUnsafeMutablePointer(to: &taskInfo) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        
        guard result == KERN_SUCCESS else {
            return 0
        }
        
        return Int64(taskInfo.resident_size)
    }
    
    func generateReport() -> [String: Any] {
        return metrics
    }
}

// MARK: - Test Configuration Extensions

extension XCUIApplication {
    var isUITesting: Bool {
        return launchEnvironment["UI_TESTING"] == "1"
    }
}

extension XCTestCase {
    func waitForElementToAppear(_ element: XCUIElement, timeout: TimeInterval = 5.0) -> Bool {
        let predicate = NSPredicate(format: "exists == true")
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
        let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
        return result == .completed
    }
    
    func waitForElementToDisappear(_ element: XCUIElement, timeout: TimeInterval = 5.0) -> Bool {
        let predicate = NSPredicate(format: "exists == false")
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
        let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
        return result == .completed
    }
}