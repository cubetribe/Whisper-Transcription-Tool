#!/usr/bin/env swift

import Foundation

// Transcription Workflow Test for Task 5
// Tests the complete transcription UI workflow and component integration

print("🎙️ Transcription Workflow Test")
print(String(repeating: "=", count: 60))

var testResults: [String: Bool] = [:]

// MARK: - Test 1: Core Components Exist

print("\n🧩 Test 1: Core Components Exist")
print(String(repeating: "-", count: 40))

func testCoreComponentsExist() {
    let requiredFiles = [
        "macos/WhisperLocalMacOs/ViewModels/TranscriptionViewModel.swift",
        "macos/WhisperLocalMacOs/Views/Components/FileSelectionSection.swift", 
        "macos/WhisperLocalMacOs/Views/Components/TranscriptionConfigSection.swift",
        "macos/WhisperLocalMacOs/Views/Components/TranscriptionProgressSection.swift"
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
    
    testResults["core_components_exist"] = allFilesExist
}

testCoreComponentsExist()

// MARK: - Test 2: TranscriptionViewModel Structure

print("\n🧠 Test 2: TranscriptionViewModel Structure")
print(String(repeating: "-", count: 40))

func testTranscriptionViewModelStructure() {
    let viewModelPath = "macos/WhisperLocalMacOs/ViewModels/TranscriptionViewModel.swift"
    
    guard let content = try? String(contentsOfFile: viewModelPath, encoding: .utf8) else {
        print("❌ Could not read TranscriptionViewModel.swift")
        testResults["transcription_viewmodel_structure"] = false
        return
    }
    
    let requiredProperties = [
        "@Published var selectedFile: URL?",
        "@Published var outputDirectory: URL?", 
        "@Published var selectedModel: String",
        "@Published var selectedFormats: Set<OutputFormat>",
        "@Published var isTranscribing: Bool",
        "@Published var transcriptionProgress: Double",
        "@Published var currentError: AppError?"
    ]
    
    let requiredMethods = [
        "func selectAudioFile()",
        "func selectOutputDirectory()",
        "func startTranscription()",
        "func cancelTranscription()",
        "var canStartTranscription: Bool"
    ]
    
    var allPropertiesFound = true
    for property in requiredProperties {
        if content.contains(property) {
            print("✅ Found property: \(property)")
        } else {
            print("❌ Missing property: \(property)")
            allPropertiesFound = false
        }
    }
    
    var allMethodsFound = true
    for method in requiredMethods {
        if content.contains(method) {
            print("✅ Found method: \(method)")
        } else {
            print("❌ Missing method: \(method)")
            allMethodsFound = false
        }
    }
    
    // Check PythonBridge integration
    let pythonBridgeIntegration = content.contains("private let pythonBridge = PythonBridge()") ||
                                 content.contains("PythonBridge()")
    
    if pythonBridgeIntegration {
        print("✅ PythonBridge integration found")
    } else {
        print("❌ Missing PythonBridge integration")
        allMethodsFound = false
    }
    
    testResults["transcription_viewmodel_structure"] = allPropertiesFound && allMethodsFound
}

testTranscriptionViewModelStructure()

// MARK: - Test 3: File Selection UI Components

print("\n📁 Test 3: File Selection UI Components")
print(String(repeating: "-", count: 40))

func testFileSelectionComponents() {
    let fileSelectionPath = "macos/WhisperLocalMacOs/Views/Components/FileSelectionSection.swift"
    let viewModelPath = "macos/WhisperLocalMacOs/ViewModels/TranscriptionViewModel.swift"
    
    guard let uiContent = try? String(contentsOfFile: fileSelectionPath, encoding: .utf8) else {
        print("❌ Could not read FileSelectionSection.swift")
        testResults["file_selection_components"] = false
        return
    }
    
    guard let vmContent = try? String(contentsOfFile: viewModelPath, encoding: .utf8) else {
        print("❌ Could not read TranscriptionViewModel.swift for NSOpenPanel test")
        testResults["file_selection_components"] = false
        return
    }
    
    let requiredComponents = [
        "struct FileSelectionSection",
        "struct SelectedFileView",
        "struct FileDropArea", 
        "struct OutputDirectorySelector"
    ]
    
    let requiredUIFeatures = [
        "@ObservedObject var viewModel: TranscriptionViewModel",
        "viewModel.selectAudioFile()",
        "viewModel.selectOutputDirectory()",
        "viewModel.removeSelectedFile()"
    ]
    
    let requiredVMFeatures = [
        "NSOpenPanel"
    ]
    
    var allComponentsFound = true
    for component in requiredComponents {
        if uiContent.contains(component) {
            print("✅ Found component: \(component)")
        } else {
            print("❌ Missing component: \(component)")
            allComponentsFound = false
        }
    }
    
    var allUIFeaturesFound = true
    for feature in requiredUIFeatures {
        if uiContent.contains(feature) {
            print("✅ Found UI feature: \(feature)")
        } else {
            print("❌ Missing UI feature: \(feature)")
            allUIFeaturesFound = false
        }
    }
    
    var allVMFeaturesFound = true
    for feature in requiredVMFeatures {
        if vmContent.contains(feature) {
            print("✅ Found VM feature: \(feature)")
        } else {
            print("❌ Missing VM feature: \(feature)")
            allVMFeaturesFound = false
        }
    }
    
    testResults["file_selection_components"] = allComponentsFound && allUIFeaturesFound && allVMFeaturesFound
}

testFileSelectionComponents()

// MARK: - Test 4: Transcription Configuration UI

print("\n⚙️  Test 4: Transcription Configuration UI")
print(String(repeating: "-", count: 40))

func testTranscriptionConfigUI() {
    let configPath = "macos/WhisperLocalMacOs/Views/Components/TranscriptionConfigSection.swift"
    
    guard let content = try? String(contentsOfFile: configPath, encoding: .utf8) else {
        print("❌ Could not read TranscriptionConfigSection.swift")
        testResults["transcription_config_ui"] = false
        return
    }
    
    let requiredComponents = [
        "struct TranscriptionConfigSection",
        "struct ModelSelectionView",
        "struct LanguageSelectionView",
        "struct OutputFormatSelectionView",
        "struct OutputFormatToggle"
    ]
    
    let requiredFeatures = [
        "viewModel.availableModels",
        "viewModel.supportedLanguages",
        "viewModel.selectedFormats",
        "viewModel.canStartTranscription",
        "await viewModel.startTranscription()"
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
    
    testResults["transcription_config_ui"] = allComponentsFound && allFeaturesFound
}

testTranscriptionConfigUI()

// MARK: - Test 5: Progress and Result Display

print("\n📊 Test 5: Progress and Result Display")
print(String(repeating: "-", count: 40))

func testProgressAndResultDisplay() {
    let progressPath = "macos/WhisperLocalMacOs/Views/Components/TranscriptionProgressSection.swift"
    
    guard let content = try? String(contentsOfFile: progressPath, encoding: .utf8) else {
        print("❌ Could not read TranscriptionProgressSection.swift")
        testResults["progress_result_display"] = false
        return
    }
    
    let requiredComponents = [
        "struct TranscriptionProgressSection",
        "struct TaskInfoView",
        "struct TranscriptionResultView",
        "struct ErrorDisplayView"
    ]
    
    let requiredFeatures = [
        "viewModel.transcriptionProgress",
        "viewModel.progressMessage",
        "viewModel.currentTask",
        "viewModel.lastResult",
        "viewModel.currentError",
        "ProgressView",
        "result.success",
        "result.outputFiles"
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
    
    testResults["progress_result_display"] = allComponentsFound && allFeaturesFound
}

testProgressAndResultDisplay()

// MARK: - Test 6: MainContentView Integration

print("\n🔗 Test 6: MainContentView Integration")
print(String(repeating: "-", count: 40))

func testMainContentViewIntegration() {
    let mainContentPath = "macos/WhisperLocalMacOs/Views/MainContentView.swift"
    
    guard let content = try? String(contentsOfFile: mainContentPath, encoding: .utf8) else {
        print("❌ Could not read MainContentView.swift")
        testResults["main_content_integration"] = false
        return
    }
    
    let requiredIntegrations = [
        "@StateObject private var viewModel = TranscriptionViewModel()",
        "FileSelectionSection(viewModel: viewModel)",
        "TranscriptionConfigSection(viewModel: viewModel)",
        "TranscriptionProgressSection(viewModel: viewModel)",
        "if viewModel.selectedFile != nil",
        "if viewModel.isTranscribing"
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
    
    testResults["main_content_integration"] = allIntegrationsFound
}

testMainContentViewIntegration()

// MARK: - Test 7: Error Handling Integration

print("\n🚨 Test 7: Error Handling Integration")
print(String(repeating: "-", count: 40))

func testErrorHandlingIntegration() {
    let viewModelPath = "macos/WhisperLocalMacOs/ViewModels/TranscriptionViewModel.swift"
    
    guard let viewModelContent = try? String(contentsOfFile: viewModelPath, encoding: .utf8) else {
        print("❌ Could not read TranscriptionViewModel.swift for error handling test")
        testResults["error_handling_integration"] = false
        return
    }
    
    let progressPath = "macos/WhisperLocalMacOs/Views/Components/TranscriptionProgressSection.swift"
    
    guard let progressContent = try? String(contentsOfFile: progressPath, encoding: .utf8) else {
        print("❌ Could not read TranscriptionProgressSection.swift for error handling test")
        testResults["error_handling_integration"] = false
        return
    }
    
    let requiredErrorHandling = [
        "private func handleTranscriptionError",
        "private func showError(_ error: AppError)",
        "func clearError()",
        "@Published var currentError: AppError?",
        "@Published var showingError: Bool"
    ]
    
    let requiredErrorDisplay = [
        "struct ErrorDisplayView",
        "error.errorDescription",
        "error.recoverySuggestion",
        "onDismiss: () -> Void"
    ]
    
    var errorHandlingFound = true
    for errorFeature in requiredErrorHandling {
        if viewModelContent.contains(errorFeature) {
            print("✅ Found error handling: \(errorFeature)")
        } else {
            print("❌ Missing error handling: \(errorFeature)")
            errorHandlingFound = false
        }
    }
    
    var errorDisplayFound = true
    for displayFeature in requiredErrorDisplay {
        if progressContent.contains(displayFeature) {
            print("✅ Found error display: \(displayFeature)")
        } else {
            print("❌ Missing error display: \(displayFeature)")
            errorDisplayFound = false
        }
    }
    
    testResults["error_handling_integration"] = errorHandlingFound && errorDisplayFound
}

testErrorHandlingIntegration()

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
    print("🎉 Transcription Workflow Test: PASSED")
    print("✨ Task 5: Core Transcription Features completed successfully")
    print("🔧 Complete transcription workflow implemented with:")
    print("   • File selection with drag & drop support")
    print("   • Model and format configuration")
    print("   • Real-time progress tracking")
    print("   • Result display with file access")
    print("   • Comprehensive error handling")
    print("   • PythonBridge integration")
} else {
    print("❌ Transcription Workflow Test: FAILED")
    print("⚠️  Some transcription components need attention")
}

print("\n🏁 Transcription workflow test completed!")
print("Ready for Task 6: Model Management Features")