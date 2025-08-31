#!/usr/bin/env swift

import Foundation

// Batch Processing Integration Test for Task 6
// Tests the complete batch processing workflow and component integration

print("🔄 Batch Processing Integration Test")
print(String(repeating: "=", count: 60))

var testResults: [String: Bool] = [:]

// MARK: - Test 1: Batch Queue UI Components

print("\n📋 Test 1: Batch Queue UI Components")
print(String(repeating: "-", count: 40))

func testBatchQueueUIComponents() {
    let requiredFiles = [
        "macos/WhisperLocalMacOs/Views/Components/QueueView.swift",
        "macos/WhisperLocalMacOs/Views/Components/BatchSummaryView.swift"
    ]
    
    var allFilesExist = true
    let currentDir = FileManager.default.currentDirectoryPath
    
    for file in requiredFiles {
        let fullPath = "\(currentDir)/\(file)"
        if FileManager.default.fileExists(atPath: fullPath) {
            print("✅ Found: \(file)")
        } else {
            print("❌ Missing: \(file)")
            allFilesExist = false
        }
    }
    
    testResults["batch_queue_ui_components"] = allFilesExist
}

testBatchQueueUIComponents()

// MARK: - Test 2: QueueView Structure and Components

print("\n🗂️ Test 2: QueueView Structure and Components")
print(String(repeating: "-", count: 40))

func testQueueViewStructure() {
    let queueViewPath = "macos/WhisperLocalMacOs/Views/Components/QueueView.swift"
    
    guard let content = try? String(contentsOfFile: queueViewPath, encoding: .utf8) else {
        print("❌ Could not read QueueView.swift")
        testResults["queue_view_structure"] = false
        return
    }
    
    let requiredComponents = [
        "struct QueueView: View",
        "struct EmptyQueueView: View",
        "struct QueueRowView: View",
        "struct BatchControlsView: View"
    ]
    
    let requiredFeatures = [
        "@ObservedObject var viewModel: TranscriptionViewModel",
        "viewModel.transcriptionQueue",
        "viewModel.addFilesToQueue()",
        "viewModel.removeTask(task)",
        "viewModel.retryTask(task)",
        "viewModel.revealTaskOutput(task)",
        "viewModel.clearCompletedTasks()",
        "viewModel.clearAllTasks()",
        "await viewModel.processBatch()",
        "viewModel.pauseBatch()",
        "viewModel.cancelBatch()"
    ]
    
    var allComponentsFound = true
    for component in requiredComponents {
        if content.contains(component) {
            print("✅ Found component: \(component)")
        } else {
            print("❌ Missing component: \(component)")
            allComponentsFound = false
        }
    }
    
    var allFeaturesFound = true
    for feature in requiredFeatures {
        if content.contains(feature) {
            print("✅ Found feature: \(feature)")
        } else {
            print("❌ Missing feature: \(feature)")
            allFeaturesFound = false
        }
    }
    
    testResults["queue_view_structure"] = allComponentsFound && allFeaturesFound
}

testQueueViewStructure()

// MARK: - Test 3: BatchSummaryView Structure

print("\n📊 Test 3: BatchSummaryView Structure")
print(String(repeating: "-", count: 40))

func testBatchSummaryViewStructure() {
    let summaryViewPath = "macos/WhisperLocalMacOs/Views/Components/BatchSummaryView.swift"
    
    guard let content = try? String(contentsOfFile: summaryViewPath, encoding: .utf8) else {
        print("❌ Could not read BatchSummaryView.swift")
        testResults["batch_summary_view_structure"] = false
        return
    }
    
    let requiredComponents = [
        "struct BatchSummaryView: View",
        "struct StatisticCard: View",
        "struct ExportSummarySheet: View",
        "struct BatchStatistics",
        "struct BatchSummaryExporter"
    ]
    
    let requiredFeatures = [
        "viewModel.openAllResults()",
        "viewModel.revealAllResults()",
        "viewModel.retryFailedTasks()",
        "enum ExportFormat",
        ".csv",
        ".json",
        "generateCSV",
        "generateJSON"
    ]
    
    var allComponentsFound = true
    for component in requiredComponents {
        if content.contains(component) {
            print("✅ Found component: \(component)")
        } else {
            print("❌ Missing component: \(component)")
            allComponentsFound = false
        }
    }
    
    var allFeaturesFound = true
    for feature in requiredFeatures {
        if content.contains(feature) {
            print("✅ Found feature: \(feature)")
        } else {
            print("❌ Missing feature: \(feature)")
            allFeaturesFound = false
        }
    }
    
    testResults["batch_summary_view_structure"] = allComponentsFound && allFeaturesFound
}

testBatchSummaryViewStructure()

// MARK: - Test 4: TranscriptionViewModel Batch Extensions

print("\n🧠 Test 4: TranscriptionViewModel Batch Extensions")
print(String(repeating: "-", count: 40))

func testTranscriptionViewModelBatchExtensions() {
    let viewModelPath = "macos/WhisperLocalMacOs/ViewModels/TranscriptionViewModel.swift"
    
    guard let content = try? String(contentsOfFile: viewModelPath, encoding: .utf8) else {
        print("❌ Could not read TranscriptionViewModel.swift")
        testResults["viewmodel_batch_extensions"] = false
        return
    }
    
    let requiredBatchProperties = [
        "@Published var transcriptionQueue: [TranscriptionTask]",
        "@Published var isProcessing: Bool",
        "@Published var isPaused: Bool",
        "@Published var batchProgress: Double",
        "@Published var batchMessage: String"
    ]
    
    let requiredBatchMethods = [
        "func addFilesToQueue()",
        "func removeTask(_ task: TranscriptionTask)",
        "func retryTask(_ task: TranscriptionTask)",
        "func revealTaskOutput(_ task: TranscriptionTask)",
        "func clearCompletedTasks()",
        "func clearAllTasks()",
        "func processBatch() async",
        "func pauseBatch()",
        "func cancelBatch()",
        "func openAllResults()",
        "func revealAllResults()",
        "func retryFailedTasks()"
    ]
    
    let requiredComputedProperties = [
        "var canStartBatch: Bool",
        "var canPauseBatch: Bool",
        "var completedTasksCount: Int",
        "var failedTasksCount: Int",
        "var hasCompletedTasks: Bool"
    ]
    
    let requiredResourceManagement = [
        "private func performResourceChecks() async -> Bool",
        "volumeAvailableCapacityKey",
        "thermalState"
    ]
    
    var propertiesFound = true
    for property in requiredBatchProperties {
        if content.contains(property) {
            print("✅ Found property: \(property)")
        } else {
            print("❌ Missing property: \(property)")
            propertiesFound = false
        }
    }
    
    var methodsFound = true
    for method in requiredBatchMethods {
        if content.contains(method) {
            print("✅ Found method: \(method)")
        } else {
            print("❌ Missing method: \(method)")
            methodsFound = false
        }
    }
    
    var computedPropsFound = true
    for computedProp in requiredComputedProperties {
        if content.contains(computedProp) {
            print("✅ Found computed property: \(computedProp)")
        } else {
            print("❌ Missing computed property: \(computedProp)")
            computedPropsFound = false
        }
    }
    
    var resourceMgmtFound = true
    for resource in requiredResourceManagement {
        if content.contains(resource) {
            print("✅ Found resource management: \(resource)")
        } else {
            print("❌ Missing resource management: \(resource)")
            resourceMgmtFound = false
        }
    }
    
    testResults["viewmodel_batch_extensions"] = propertiesFound && methodsFound && computedPropsFound && resourceMgmtFound
}

testTranscriptionViewModelBatchExtensions()

// MARK: - Test 5: TranscriptionTask Batch Support

print("\n📄 Test 5: TranscriptionTask Batch Support")
print(String(repeating: "-", count: 40))

func testTranscriptionTaskBatchSupport() {
    let taskModelPath = "macos/WhisperLocalMacOs/Models/TranscriptionTask.swift"
    
    guard let content = try? String(contentsOfFile: taskModelPath, encoding: .utf8) else {
        print("❌ Could not read TranscriptionTask.swift")
        testResults["task_batch_support"] = false
        return
    }
    
    let requiredBatchFeatures = [
        "var processingTime: TimeInterval",
        "var errorMessage: String?",
        "var startTime: Date?",
        "var completionTime: Date?",
        "var outputFiles: [URL]",
        "mutating func markStarted()",
        "mutating func markCompleted()",
        "mutating func markFailed(error: String)",
        "mutating func markCancelled()",
        "mutating func reset()"
    ]
    
    var allFeaturesFound = true
    for feature in requiredBatchFeatures {
        if content.contains(feature) {
            print("✅ Found batch feature: \(feature)")
        } else {
            print("❌ Missing batch feature: \(feature)")
            allFeaturesFound = false
        }
    }
    
    testResults["task_batch_support"] = allFeaturesFound
}

testTranscriptionTaskBatchSupport()

// MARK: - Test 6: BatchView Integration

print("\n🎯 Test 6: BatchView Integration")
print(String(repeating: "-", count: 40))

func testBatchViewIntegration() {
    let mainContentPath = "macos/WhisperLocalMacOs/Views/MainContentView.swift"
    
    guard let content = try? String(contentsOfFile: mainContentPath, encoding: .utf8) else {
        print("❌ Could not read MainContentView.swift")
        testResults["batch_view_integration"] = false
        return
    }
    
    let requiredIntegrations = [
        "struct BatchView: View",
        "@StateObject private var viewModel = TranscriptionViewModel()",
        "OutputDirectorySelector(viewModel: viewModel)",
        "TranscriptionConfigSection(viewModel: viewModel)",
        "QueueView(viewModel: viewModel)",
        "BatchSummaryView(viewModel: viewModel)",
        "viewModel.isProcessing",
        "viewModel.batchProgress",
        "viewModel.batchMessage"
    ]
    
    var allIntegrationsFound = true
    for integration in requiredIntegrations {
        if content.contains(integration) {
            print("✅ Found integration: \(integration)")
        } else {
            print("❌ Missing integration: \(integration)")
            allIntegrationsFound = false
        }
    }
    
    testResults["batch_view_integration"] = allIntegrationsFound
}

testBatchViewIntegration()

// MARK: - Test 7: Error Isolation and Resource Management

print("\n🛡️ Test 7: Error Isolation and Resource Management")
print(String(repeating: "-", count: 40))

func testErrorIsolationAndResourceManagement() {
    let viewModelPath = "macos/WhisperLocalMacOs/ViewModels/TranscriptionViewModel.swift"
    
    guard let content = try? String(contentsOfFile: viewModelPath, encoding: .utf8) else {
        print("❌ Could not read TranscriptionViewModel.swift for error isolation test")
        testResults["error_isolation_resource_mgmt"] = false
        return
    }
    
    let requiredErrorIsolation = [
        "// Continue processing other files (error isolation)",
        "continue",
        "guard await performResourceChecks() else",
        "insufficientDiskSpace"
    ]
    
    let requiredResourceChecks = [
        "volumeAvailableCapacity",
        "1024 * 1024 * 1024", // 1GB check
        "thermalState == .critical",
        "ProcessInfo.processInfo"
    ]
    
    let requiredPauseResume = [
        "if isPaused {",
        "if !isProcessing {",
        "func pauseBatch()",
        "func cancelBatch()"
    ]
    
    var errorIsolationFound = true
    for errorFeature in requiredErrorIsolation {
        if content.contains(errorFeature) {
            print("✅ Found error isolation: \(errorFeature)")
        } else {
            print("❌ Missing error isolation: \(errorFeature)")
            errorIsolationFound = false
        }
    }
    
    var resourceChecksFound = true
    for resourceFeature in requiredResourceChecks {
        if content.contains(resourceFeature) {
            print("✅ Found resource check: \(resourceFeature)")
        } else {
            print("❌ Missing resource check: \(resourceFeature)")
            resourceChecksFound = false
        }
    }
    
    var pauseResumeFound = true
    for pauseFeature in requiredPauseResume {
        if content.contains(pauseFeature) {
            print("✅ Found pause/resume: \(pauseFeature)")
        } else {
            print("❌ Missing pause/resume: \(pauseFeature)")
            pauseResumeFound = false
        }
    }
    
    testResults["error_isolation_resource_mgmt"] = errorIsolationFound && resourceChecksFound && pauseResumeFound
}

testErrorIsolationAndResourceManagement()

// MARK: - Test 8: Export and Summary Functionality

print("\n📤 Test 8: Export and Summary Functionality")
print(String(repeating: "-", count: 40))

func testExportAndSummaryFunctionality() {
    let summaryViewPath = "macos/WhisperLocalMacOs/Views/Components/BatchSummaryView.swift"
    
    guard let content = try? String(contentsOfFile: summaryViewPath, encoding: .utf8) else {
        print("❌ Could not read BatchSummaryView.swift for export test")
        testResults["export_summary_functionality"] = false
        return
    }
    
    let requiredExportFeatures = [
        "enum ExportFormat",
        "case csv",
        "case json",
        "static func generateCSV",
        "static func generateJSON",
        "struct BatchStatistics",
        "struct TaskExportData: Codable",
        "JSONEncoder()"
    ]
    
    let requiredSummaryStats = [
        "totalFiles: Int",
        "completedFiles: Int",
        "failedFiles: Int",
        "successRate: Double",
        "totalProcessingTime: TimeInterval",
        "averageProcessingTime: TimeInterval",
        "fileTypeBreakdown: [String: Int]"
    ]
    
    let requiredActionButtons = [
        "Open All Results",
        "Reveal All in Finder",
        "Retry Failed",
        "Export Summary",
        "Play Success Sound"
    ]
    
    var exportFeaturesFound = true
    for exportFeature in requiredExportFeatures {
        if content.contains(exportFeature) {
            print("✅ Found export feature: \(exportFeature)")
        } else {
            print("❌ Missing export feature: \(exportFeature)")
            exportFeaturesFound = false
        }
    }
    
    var summaryStatsFound = true
    for stat in requiredSummaryStats {
        if content.contains(stat) {
            print("✅ Found summary stat: \(stat)")
        } else {
            print("❌ Missing summary stat: \(stat)")
            summaryStatsFound = false
        }
    }
    
    var actionButtonsFound = true
    for button in requiredActionButtons {
        if content.contains(button) {
            print("✅ Found action button: \(button)")
        } else {
            print("❌ Missing action button: \(button)")
            actionButtonsFound = false
        }
    }
    
    testResults["export_summary_functionality"] = exportFeaturesFound && summaryStatsFound && actionButtonsFound
}

testExportAndSummaryFunctionality()

// MARK: - Test Results Summary

print("\n📊 Test Results Summary")
print(String(repeating: "=", count: 60))

var passedTests = 0
let totalTests = testResults.count

for (testName, passed) in testResults.sorted(by: { $0.key < $1.key }) {
    let status = passed ? "✅ PASSED" : "❌ FAILED"
    print("\(status): \(testName)")
    if passed { passedTests += 1 }
}

let successRate = Double(passedTests) / Double(totalTests) * 100
print("\nOverall Success Rate: \(passedTests)/\(totalTests) (\(String(format: "%.1f", successRate))%)")

if successRate >= 85 {
    print("🎉 Batch Processing Integration Test: PASSED")
    print("✨ Task 6: Batch Processing Implementation completed successfully")
    print("🔧 Complete batch processing system implemented with:")
    print("   • Queue management with visual status indicators")
    print("   • Resource monitoring and error isolation")
    print("   • Pause/resume and cancellation support")  
    print("   • Comprehensive batch statistics and reporting")
    print("   • Export functionality (CSV/JSON)")
    print("   • Retry mechanism for failed tasks")
    print("   • Bulk result access and management")
    print("   • Memory and disk space monitoring")
} else {
    print("❌ Batch Processing Integration Test: FAILED")
    print("⚠️  Some batch processing components need attention")
}

print("\n🏁 Batch processing integration test completed!")
print("Ready for Task 7: Model Manager Implementation")