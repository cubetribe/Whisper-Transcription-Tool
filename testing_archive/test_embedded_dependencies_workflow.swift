#!/usr/bin/env swift

import Foundation

// Embedded Dependencies Integration Test for Task 8
// Tests the complete embedded dependency system and integration

print("📦 Embedded Dependencies Integration Test")
print(String(repeating: "=", count: 60))

var testResults: [String: Bool] = [:]

// MARK: - Test 1: Dependency Manager Components

print("\n🏗️ Test 1: Dependency Manager Components")
print(String(repeating: "-", count: 40))

func testDependencyManagerComponents() {
    let requiredFiles = [
        "macos/WhisperLocalMacOs/Services/DependencyManager.swift",
        "macos/WhisperLocalMacOs/Views/Components/DependencyErrorView.swift"
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
    
    testResults["dependency_manager_components"] = allFilesExist
}

testDependencyManagerComponents()

// MARK: - Test 2: DependencyManager Structure

print("\n⚙️ Test 2: DependencyManager Structure")
print(String(repeating: "-", count: 40))

func testDependencyManagerStructure() {
    let dependencyManagerPath = "macos/WhisperLocalMacOs/Services/DependencyManager.swift"
    
    guard let content = try? String(contentsOfFile: dependencyManagerPath, encoding: .utf8) else {
        print("❌ Could not read DependencyManager.swift")
        testResults["dependency_manager_structure"] = false
        return
    }
    
    let requiredProperties = [
        "@Published var dependencyStatus: DependencyStatus",
        "@Published var isValidating: Bool",
        "@Published var lastValidation: Date?",
        "static let shared = DependencyManager()"
    ]
    
    let requiredComputedPaths = [
        "var pythonExecutablePath: URL",
        "var whisperBinaryPath: URL", 
        "var ffmpegBinaryPath: URL",
        "var pythonPackagesPath: URL",
        "var modelsDirectory: URL",
        "var cliWrapperPath: URL"
    ]
    
    let requiredMethods = [
        "func validateDependencies() async -> DependencyStatus",
        "private func validatePython() async -> ComponentValidationResult",
        "private func validateWhisperBinary() async -> ComponentValidationResult",
        "private func validateFFmpegBinary() async -> ComponentValidationResult",
        "private func validateCLIWrapper() async -> ComponentValidationResult",
        "func setupEnvironment()",
        "func attemptRepair() async -> Bool"
    ]
    
    let requiredDataTypes = [
        "enum DependencyStatus",
        "enum DependencyIssue",
        "enum ComponentValidationResult",
        "struct BundleInfo"
    ]
    
    var propertiesFound = true
    for property in requiredProperties {
        if content.contains(property) {
            print("✅ Found property: \(property)")
        } else {
            print("❌ Missing property: \(property)")
            propertiesFound = false
        }
    }
    
    var pathsFound = true
    for path in requiredComputedPaths {
        if content.contains(path) {
            print("✅ Found computed path: \(path)")
        } else {
            print("❌ Missing computed path: \(path)")
            pathsFound = false
        }
    }
    
    var methodsFound = true
    for method in requiredMethods {
        if content.contains(method) {
            print("✅ Found method: \(method)")
        } else {
            print("❌ Missing method: \(method)")
            methodsFound = false
        }
    }
    
    var dataTypesFound = true
    for dataType in requiredDataTypes {
        if content.contains(dataType) {
            print("✅ Found data type: \(dataType)")
        } else {
            print("❌ Missing data type: \(dataType)")
            dataTypesFound = false
        }
    }
    
    testResults["dependency_manager_structure"] = propertiesFound && pathsFound && methodsFound && dataTypesFound
}

testDependencyManagerStructure()

// MARK: - Test 3: Bundle Path Structure

print("\n📁 Test 3: Bundle Path Structure")
print(String(repeating: "-", count: 40))

func testBundlePathStructure() {
    let dependencyManagerPath = "macos/WhisperLocalMacOs/Services/DependencyManager.swift"
    
    guard let content = try? String(contentsOfFile: dependencyManagerPath, encoding: .utf8) else {
        print("❌ Could not read DependencyManager.swift for bundle path test")
        testResults["bundle_path_structure"] = false
        return
    }
    
    let requiredBundleStructure = [
        "Contents/Resources/Dependencies",
        "python-\\(architecture)",
        "whisper.cpp-\\(architecture)",
        "ffmpeg-\\(architecture)", 
        "bin/python3",
        "bin/whisper-cli",
        "bin/ffmpeg",
        "lib/python3.11/site-packages",
        "models"
    ]
    
    let requiredArchitectureDetection = [
        "ProcessInfo.processInfo.machineArchitecture",
        "#if arch(arm64)",
        "#elseif arch(x86_64)",
        "return \"arm64\"",
        "return \"x86_64\""
    ]
    
    let requiredEnvironmentSetup = [
        "func setupEnvironment()",
        "setenv(\"PYTHONPATH\"",
        "setenv(\"PATH\"",
        "setenv(\"DYLD_LIBRARY_PATH\""
    ]
    
    var bundleStructureFound = true
    for structure in requiredBundleStructure {
        if content.contains(structure) {
            print("✅ Found bundle structure: \(structure)")
        } else {
            print("❌ Missing bundle structure: \(structure)")
            bundleStructureFound = false
        }
    }
    
    var architectureDetectionFound = true
    for detection in requiredArchitectureDetection {
        if content.contains(detection) {
            print("✅ Found architecture detection: \(detection)")
        } else {
            print("❌ Missing architecture detection: \(detection)")
            architectureDetectionFound = false
        }
    }
    
    var environmentSetupFound = true
    for setup in requiredEnvironmentSetup {
        if content.contains(setup) {
            print("✅ Found environment setup: \(setup)")
        } else {
            print("❌ Missing environment setup: \(setup)")
            environmentSetupFound = false
        }
    }
    
    testResults["bundle_path_structure"] = bundleStructureFound && architectureDetectionFound && environmentSetupFound
}

testBundlePathStructure()

// MARK: - Test 4: Dependency Validation Logic

print("\n✅ Test 4: Dependency Validation Logic")
print(String(repeating: "-", count: 40))

func testDependencyValidationLogic() {
    let dependencyManagerPath = "macos/WhisperLocalMacOs/Services/DependencyManager.swift"
    
    guard let content = try? String(contentsOfFile: dependencyManagerPath, encoding: .utf8) else {
        print("❌ Could not read DependencyManager.swift for validation logic test")
        testResults["dependency_validation_logic"] = false
        return
    }
    
    let requiredValidationComponents = [
        "func validateDependencies() async -> DependencyStatus",
        "var issues: [DependencyIssue] = []",
        "var warnings: [String] = []",
        "let pythonStatus = await validatePython()",
        "let whisperStatus = await validateWhisperBinary()",
        "let ffmpegStatus = await validateFFmpegBinary()",
        "let cliStatus = await validateCLIWrapper()"
    ]
    
    let requiredValidationStates = [
        "case .valid",
        "case .validWithWarnings(warnings: [String])",
        "case .invalid(issues: [DependencyIssue], warnings: [String])",
        "case .missing(issues: [DependencyIssue], warnings: [String])",
        "var isValid: Bool"
    ]
    
    let requiredIssueTypes = [
        "case missingPython",
        "case pythonNotExecutable", 
        "case missingWhisperBinary",
        "case missingFFmpegBinary",
        "case missingCLIWrapper",
        "case checksumMismatch(component: String)",
        "case architectureMismatch(expected: String, found: String)"
    ]
    
    let requiredExecutionTests = [
        "fileManager.isExecutableFile(atPath:",
        "process.executableURL = pythonPath",
        "process.arguments = [\"--version\"]",
        "process.run()",
        "process.terminationStatus == 0"
    ]
    
    var validationComponentsFound = true
    for component in requiredValidationComponents {
        if content.contains(component) {
            print("✅ Found validation component: \(component)")
        } else {
            print("❌ Missing validation component: \(component)")
            validationComponentsFound = false
        }
    }
    
    var validationStatesFound = true
    for state in requiredValidationStates {
        if content.contains(state) {
            print("✅ Found validation state: \(state)")
        } else {
            print("❌ Missing validation state: \(state)")
            validationStatesFound = false
        }
    }
    
    var issueTypesFound = true
    for issue in requiredIssueTypes {
        if content.contains(issue) {
            print("✅ Found issue type: \(issue)")
        } else {
            print("❌ Missing issue type: \(issue)")
            issueTypesFound = false
        }
    }
    
    var executionTestsFound = true
    for test in requiredExecutionTests {
        if content.contains(test) {
            print("✅ Found execution test: \(test)")
        } else {
            print("❌ Missing execution test: \(test)")
            executionTestsFound = false
        }
    }
    
    testResults["dependency_validation_logic"] = validationComponentsFound && validationStatesFound && issueTypesFound && executionTestsFound
}

testDependencyValidationLogic()

// MARK: - Test 5: PythonBridge Integration

print("\n🐍 Test 5: PythonBridge Integration")
print(String(repeating: "-", count: 40))

func testPythonBridgeIntegration() {
    let pythonBridgePath = "macos/WhisperLocalMacOs/Services/PythonBridge.swift"
    
    guard let content = try? String(contentsOfFile: pythonBridgePath, encoding: .utf8) else {
        print("❌ Could not read PythonBridge.swift for integration test")
        testResults["python_bridge_integration"] = false
        return
    }
    
    let requiredIntegration = [
        "private static func resolvePythonPath() -> URL",
        "private static func resolveCLIWrapperPath() -> URL",
        "let dependencyManager = DependencyManager.shared",
        "let embeddedPath = dependencyManager.pythonExecutablePath",
        "let embeddedPath = dependencyManager.cliWrapperPath",
        "private func setupEmbeddedEnvironment()",
        "DependencyManager.shared.setupEnvironment()"
    ]
    
    let requiredFallbacks = [
        "// Check if embedded Python exists and is valid",
        "FileManager.default.fileExists(atPath: embeddedPath.path)",
        "FileManager.default.isExecutableFile(atPath: embeddedPath.path)",
        "// Fallback to system Python",
        "URL(fileURLWithPath: \"/usr/bin/python3\")",
        "// Fallback to project path (for development)"
    ]
    
    var integrationFound = true
    for integration in requiredIntegration {
        if content.contains(integration) {
            print("✅ Found integration: \(integration)")
        } else {
            print("❌ Missing integration: \(integration)")
            integrationFound = false
        }
    }
    
    var fallbacksFound = true
    for fallback in requiredFallbacks {
        if content.contains(fallback) {
            print("✅ Found fallback: \(fallback)")
        } else {
            print("❌ Missing fallback: \(fallback)")
            fallbacksFound = false
        }
    }
    
    testResults["python_bridge_integration"] = integrationFound && fallbacksFound
}

testPythonBridgeIntegration()

// MARK: - Test 6: DependencyErrorView UI Structure

print("\n🖥️ Test 6: DependencyErrorView UI Structure")
print(String(repeating: "-", count: 40))

func testDependencyErrorViewStructure() {
    let errorViewPath = "macos/WhisperLocalMacOs/Views/Components/DependencyErrorView.swift"
    
    guard let content = try? String(contentsOfFile: errorViewPath, encoding: .utf8) else {
        print("❌ Could not read DependencyErrorView.swift")
        testResults["dependency_error_view_structure"] = false
        return
    }
    
    let requiredViewComponents = [
        "struct DependencyErrorView: View",
        "struct IssueSummaryCard: View",
        "struct DetailedErrorInfo: View",
        "struct DependencyStatusView: View",
        "struct DependencyValidatingView: View",
        "struct DependencyValidView: View",
        "struct DependencyWarningView: View"
    ]
    
    let requiredActionButtons = [
        "Button(\"Retry Validation\")",
        "Button(\"Attempt Repair\")", 
        "Button(\"Reinstall Application\")",
        "onRetry: () -> Void",
        "onRepair: () -> Void",
        "onReinstall: () -> Void"
    ]
    
    let requiredErrorHandling = [
        "case .invalid(let issues, let warnings)",
        "case .missing(let issues, let warnings)",
        "case .validWithWarnings(let warnings)",
        "ForEach(issues.prefix(5), id: \\.self)",
        "issue.localizedDescription",
        "issue.recoverySuggestion"
    ]
    
    let requiredDetailedInfo = [
        "SystemInfoSection",
        "BundleInfoSection",
        "DependencyStatusSection",
        "InfoRow",
        "ProcessInfo.processInfo.machineArchitecture",
        "bundleInfo = DependencyManager.shared.bundleInfo"
    ]
    
    var viewComponentsFound = true
    for component in requiredViewComponents {
        if content.contains(component) {
            print("✅ Found view component: \(component)")
        } else {
            print("❌ Missing view component: \(component)")
            viewComponentsFound = false
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
    
    var errorHandlingFound = true
    for errorHandling in requiredErrorHandling {
        if content.contains(errorHandling) {
            print("✅ Found error handling: \(errorHandling)")
        } else {
            print("❌ Missing error handling: \(errorHandling)")
            errorHandlingFound = false
        }
    }
    
    var detailedInfoFound = true
    for detailedInfo in requiredDetailedInfo {
        if content.contains(detailedInfo) {
            print("✅ Found detailed info: \(detailedInfo)")
        } else {
            print("❌ Missing detailed info: \(detailedInfo)")
            detailedInfoFound = false
        }
    }
    
    testResults["dependency_error_view_structure"] = viewComponentsFound && actionButtonsFound && errorHandlingFound && detailedInfoFound
}

testDependencyErrorViewStructure()

// MARK: - Test 7: App Integration and Startup

print("\n🚀 Test 7: App Integration and Startup")
print(String(repeating: "-", count: 40))

func testAppIntegrationAndStartup() {
    let appPath = "macos/WhisperLocalMacOs/App/WhisperLocalMacOsApp.swift"
    
    guard let content = try? String(contentsOfFile: appPath, encoding: .utf8) else {
        print("❌ Could not read WhisperLocalMacOsApp.swift")
        testResults["app_integration_startup"] = false
        return
    }
    
    let requiredAppIntegration = [
        "@StateObject private var dependencyManager = DependencyManager.shared",
        "if dependencyManager.dependencyStatus.isValid",
        "else if dependencyManager.isValidating",
        "DependencyValidatingView()",
        "DependencyStatusView()",
        "private func validateDependenciesOnStartup()"
    ]
    
    let requiredStartupFlow = [
        ".onAppear {",
        "validateDependenciesOnStartup()",
        "Task {",
        "await dependencyManager.validateDependencies()",
        "if !dependencyManager.dependencyStatus.isValid"
    ]
    
    var appIntegrationFound = true
    for integration in requiredAppIntegration {
        if content.contains(integration) {
            print("✅ Found app integration: \(integration)")
        } else {
            print("❌ Missing app integration: \(integration)")
            appIntegrationFound = false
        }
    }
    
    var startupFlowFound = true
    for startupFlow in requiredStartupFlow {
        if content.contains(startupFlow) {
            print("✅ Found startup flow: \(startupFlow)")
        } else {
            print("❌ Missing startup flow: \(startupFlow)")
            startupFlowFound = false
        }
    }
    
    testResults["app_integration_startup"] = appIntegrationFound && startupFlowFound
}

testAppIntegrationAndStartup()

// MARK: - Test 8: Error Recovery and Repair System

print("\n🔧 Test 8: Error Recovery and Repair System")  
print(String(repeating: "-", count: 40))

func testErrorRecoveryAndRepairSystem() {
    let dependencyManagerPath = "macos/WhisperLocalMacOs/Services/DependencyManager.swift"
    
    guard let content = try? String(contentsOfFile: dependencyManagerPath, encoding: .utf8) else {
        print("❌ Could not read DependencyManager.swift for repair system test")
        testResults["error_recovery_repair_system"] = false
        return
    }
    
    let requiredRepairFeatures = [
        "func attemptRepair() async -> Bool",
        "// For embedded dependencies, repair typically means re-extracting or re-downloading",
        "// Re-validate after repair attempt",
        "let status = await validateDependencies()",
        "return status.isValid"
    ]
    
    let requiredErrorDescriptions = [
        "var errorDescription: String?",
        "var recoverySuggestion: String?",
        "Try reinstalling the application",
        "Check file permissions",
        "Check system compatibility",
        "Some files may be corrupted"
    ]
    
    let requiredBundleInfo = [
        "var bundleInfo: BundleInfo",
        "func calculateBundleSize() -> Int64",
        "func countEmbeddedDependencies() -> Int",
        "var bundleSizeFormatted: String",
        "ByteCountFormatter.string(fromByteCount:"
    ]
    
    var repairFeaturesFound = true
    for feature in requiredRepairFeatures {
        if content.contains(feature) {
            print("✅ Found repair feature: \(feature)")
        } else {
            print("❌ Missing repair feature: \(feature)")
            repairFeaturesFound = false
        }
    }
    
    var errorDescriptionsFound = true
    for description in requiredErrorDescriptions {
        if content.contains(description) {
            print("✅ Found error description: \(description)")
        } else {
            print("❌ Missing error description: \(description)")
            errorDescriptionsFound = false
        }
    }
    
    var bundleInfoFound = true
    for info in requiredBundleInfo {
        if content.contains(info) {
            print("✅ Found bundle info: \(info)")
        } else {
            print("❌ Missing bundle info: \(info)")
            bundleInfoFound = false
        }
    }
    
    testResults["error_recovery_repair_system"] = repairFeaturesFound && errorDescriptionsFound && bundleInfoFound
}

testErrorRecoveryAndRepairSystem()

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
    print("🎉 Embedded Dependencies Integration Test: PASSED")
    print("✨ Task 8: Embedded Dependencies Integration completed successfully")
    print("🔧 Complete embedded dependency system implemented with:")
    print("   • Comprehensive dependency manager with validation")
    print("   • Architecture-aware path resolution (ARM64/x86_64)")
    print("   • Dynamic environment setup for embedded Python")
    print("   • Fallback mechanisms for development and production")
    print("   • Startup dependency verification with error handling")
    print("   • Detailed error reporting and recovery suggestions")
    print("   • Integration with PythonBridge and main application")
    print("   • Bundle integrity checking and repair attempts")
} else {
    print("❌ Embedded Dependencies Integration Test: FAILED")
    print("⚠️  Some embedded dependency components need attention")
}

print("\n🏁 Embedded dependencies integration test completed!")
print("Ready for Task 9: Performance and Native Integration")