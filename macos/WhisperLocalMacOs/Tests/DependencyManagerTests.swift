import XCTest
import Foundation
@testable import WhisperLocalMacOs

@MainActor
class DependencyManagerTests: XCTestCase {
    
    var mockDependencyManager: MockDependencyManager!
    var mockFileManager: MockFileManager!
    
    override func setUp() {
        super.setUp()
        mockFileManager = MockFileManager()
        mockDependencyManager = MockDependencyManager(fileManager: mockFileManager)
    }
    
    override func tearDown() {
        mockDependencyManager = nil
        mockFileManager = nil
        super.tearDown()
    }
    
    // MARK: - Initialization Tests
    
    func testDependencyManager_InitialState() {
        let manager = DependencyManager.shared
        
        XCTAssertEqual(manager.dependencyStatus, .unknown)
        XCTAssertFalse(manager.isValidating)
        // lastValidation may or may not be nil depending on whether validation ran on init
    }
    
    // MARK: - Path Resolution Tests
    
    func testDependencyManager_PathResolution() {
        let manager = mockDependencyManager!
        
        // Test Python executable path
        let pythonPath = manager.pythonExecutablePath
        XCTAssertTrue(pythonPath.path.contains("python"))
        XCTAssertTrue(pythonPath.path.contains("bin/python3"))
        
        // Test Whisper binary path
        let whisperPath = manager.whisperBinaryPath
        XCTAssertTrue(whisperPath.path.contains("whisper.cpp"))
        XCTAssertTrue(whisperPath.path.contains("whisper-cli"))
        
        // Test FFmpeg binary path
        let ffmpegPath = manager.ffmpegBinaryPath
        XCTAssertTrue(ffmpegPath.path.contains("ffmpeg"))
        XCTAssertTrue(ffmpegPath.path.contains("bin/ffmpeg"))
        
        // Test Python packages path
        let packagesPath = manager.pythonPackagesPath
        XCTAssertTrue(packagesPath.path.contains("site-packages"))
        
        // Test models directory
        let modelsPath = manager.modelsDirectory
        XCTAssertTrue(modelsPath.path.contains("models"))
        
        // Test CLI wrapper path
        let cliPath = manager.cliWrapperPath
        XCTAssertTrue(cliPath.path.contains("macos_cli.py"))
    }
    
    func testDependencyManager_ArchitectureSpecificPaths() {
        let manager = mockDependencyManager!
        
        // Test that architecture is included in paths
        let pythonPath = manager.pythonExecutablePath
        let whisperPath = manager.whisperBinaryPath
        let ffmpegPath = manager.ffmpegBinaryPath
        
        let architecture = ProcessInfo.processInfo.machineArchitecture
        
        XCTAssertTrue(pythonPath.path.contains(architecture))
        XCTAssertTrue(whisperPath.path.contains(architecture))
        XCTAssertTrue(ffmpegPath.path.contains(architecture))
    }
    
    // MARK: - Dependency Validation Tests
    
    func testDependencyValidation_AllValid() async {
        // Setup mock to return valid dependencies
        mockFileManager.mockFileExistsResults = [
            // Dependencies directory
            mockDependencyManager.dependenciesDirectory.path: true,
            // Python
            mockDependencyManager.pythonExecutablePath.path: true,
            // Whisper
            mockDependencyManager.whisperBinaryPath.path: true,
            // FFmpeg
            mockDependencyManager.ffmpegBinaryPath.path: true,
            // CLI wrapper
            mockDependencyManager.cliWrapperPath.path: true,
            // Python packages
            mockDependencyManager.pythonPackagesPath.path: true
        ]
        
        mockFileManager.mockExecutableResults = [
            mockDependencyManager.pythonExecutablePath.path: true,
            mockDependencyManager.whisperBinaryPath.path: true,
            mockDependencyManager.ffmpegBinaryPath.path: true
        ]
        
        let status = await mockDependencyManager.validateDependencies()
        
        XCTAssertEqual(status, .valid)
        XCTAssertTrue(status.isValid)
        XCTAssertFalse(mockDependencyManager.isValidating)
        XCTAssertNotNil(mockDependencyManager.lastValidation)
    }
    
    func testDependencyValidation_MissingDependencyDirectory() async {
        // Setup mock to return missing dependencies directory
        mockFileManager.mockFileExistsResults = [
            mockDependencyManager.dependenciesDirectory.path: false
        ]
        
        let status = await mockDependencyManager.validateDependencies()
        
        switch status {
        case .missing(let issues, _):
            XCTAssertTrue(issues.contains(.missingDependencyDirectory))
        default:
            XCTFail("Expected missing status")
        }
        
        XCTAssertFalse(status.isValid)
    }
    
    func testDependencyValidation_InvalidPython() async {
        // Setup mock with missing Python
        mockFileManager.mockFileExistsResults = [
            mockDependencyManager.dependenciesDirectory.path: true,
            mockDependencyManager.pythonExecutablePath.path: false,
            mockDependencyManager.whisperBinaryPath.path: true,
            mockDependencyManager.ffmpegBinaryPath.path: true,
            mockDependencyManager.cliWrapperPath.path: true,
            mockDependencyManager.pythonPackagesPath.path: true
        ]
        
        let status = await mockDependencyManager.validateDependencies()
        
        switch status {
        case .invalid(let issues, _):
            XCTAssertTrue(issues.contains(.pythonNotFound))
        default:
            XCTFail("Expected invalid status")
        }
        
        XCTAssertFalse(status.isValid)
    }
    
    func testDependencyValidation_InvalidWhisper() async {
        // Setup mock with missing Whisper
        mockFileManager.mockFileExistsResults = [
            mockDependencyManager.dependenciesDirectory.path: true,
            mockDependencyManager.pythonExecutablePath.path: true,
            mockDependencyManager.whisperBinaryPath.path: false,
            mockDependencyManager.ffmpegBinaryPath.path: true,
            mockDependencyManager.cliWrapperPath.path: true,
            mockDependencyManager.pythonPackagesPath.path: true
        ]
        
        mockFileManager.mockExecutableResults = [
            mockDependencyManager.pythonExecutablePath.path: true,
            mockDependencyManager.ffmpegBinaryPath.path: true
        ]
        
        let status = await mockDependencyManager.validateDependencies()
        
        switch status {
        case .invalid(let issues, _):
            XCTAssertTrue(issues.contains(.whisperBinaryNotFound))
        default:
            XCTFail("Expected invalid status")
        }
    }
    
    func testDependencyValidation_ValidWithWarnings() async {
        // Setup mock with valid dependencies but some warnings
        mockFileManager.mockFileExistsResults = [
            mockDependencyManager.dependenciesDirectory.path: true,
            mockDependencyManager.pythonExecutablePath.path: true,
            mockDependencyManager.whisperBinaryPath.path: true,
            mockDependencyManager.ffmpegBinaryPath.path: true,
            mockDependencyManager.cliWrapperPath.path: true,
            mockDependencyManager.pythonPackagesPath.path: true
        ]
        
        mockFileManager.mockExecutableResults = [
            mockDependencyManager.pythonExecutablePath.path: true,
            mockDependencyManager.whisperBinaryPath.path: true,
            mockDependencyManager.ffmpegBinaryPath.path: true
        ]
        
        // Simulate a warning (e.g., old version)
        mockDependencyManager.simulateWarning = "Python version is older than recommended"
        
        let status = await mockDependencyManager.validateDependencies()
        
        switch status {
        case .validWithWarnings(let warnings):
            XCTAssertFalse(warnings.isEmpty)
            XCTAssertTrue(warnings.contains("Python version is older than recommended"))
        default:
            XCTFail("Expected valid with warnings status")
        }
        
        XCTAssertTrue(status.isValid)
    }
    
    func testDependencyValidation_MultipleIssues() async {
        // Setup mock with multiple missing dependencies
        mockFileManager.mockFileExistsResults = [
            mockDependencyManager.dependenciesDirectory.path: true,
            mockDependencyManager.pythonExecutablePath.path: false,
            mockDependencyManager.whisperBinaryPath.path: false,
            mockDependencyManager.ffmpegBinaryPath.path: true,
            mockDependencyManager.cliWrapperPath.path: false,
            mockDependencyManager.pythonPackagesPath.path: true
        ]
        
        mockFileManager.mockExecutableResults = [
            mockDependencyManager.ffmpegBinaryPath.path: true
        ]
        
        let status = await mockDependencyManager.validateDependencies()
        
        switch status {
        case .invalid(let issues, _):
            XCTAssertTrue(issues.contains(.pythonNotFound))
            XCTAssertTrue(issues.contains(.whisperBinaryNotFound))
            XCTAssertTrue(issues.contains(.cliWrapperNotFound))
            XCTAssertGreaterThanOrEqual(issues.count, 3)
        default:
            XCTFail("Expected invalid status")
        }
    }
    
    // MARK: - Dependency Status Tests
    
    func testDependencyStatus_Descriptions() {
        let validStatus = DependencyStatus.valid
        XCTAssertEqual(validStatus.description, "All dependencies are valid and ready to use")
        XCTAssertTrue(validStatus.isValid)
        
        let warningsStatus = DependencyStatus.validWithWarnings(warnings: ["Warning 1"])
        XCTAssertTrue(warningsStatus.description.contains("valid with warnings"))
        XCTAssertTrue(warningsStatus.isValid)
        
        let invalidStatus = DependencyStatus.invalid(issues: [.pythonNotFound], warnings: [])
        XCTAssertTrue(invalidStatus.description.contains("invalid"))
        XCTAssertFalse(invalidStatus.isValid)
        
        let missingStatus = DependencyStatus.missing(issues: [.missingDependencyDirectory], warnings: [])
        XCTAssertTrue(missingStatus.description.contains("missing"))
        XCTAssertFalse(missingStatus.isValid)
        
        let unknownStatus = DependencyStatus.unknown
        XCTAssertEqual(unknownStatus.description, "Dependency status not yet determined")
        XCTAssertFalse(unknownStatus.isValid)
    }
    
    func testDependencyIssue_Descriptions() {
        let issues: [DependencyIssue] = [
            .missingDependencyDirectory,
            .pythonNotFound,
            .pythonNotExecutable,
            .pythonVersionIncompatible("3.6"),
            .pythonPackagesMissing(["whisper"]),
            .whisperBinaryNotFound,
            .whisperBinaryNotExecutable,
            .whisperVersionIncompatible("1.0.0"),
            .ffmpegNotFound,
            .ffmpegNotExecutable,
            .cliWrapperNotFound,
            .cliWrapperNotReadable,
            .modelsDirectoryNotAccessible,
            .invalidBundleStructure
        ]
        
        for issue in issues {
            XCTAssertFalse(issue.description.isEmpty, "Issue \(issue) should have a description")
            XCTAssertFalse(issue.recoverySuggestion.isEmpty, "Issue \(issue) should have a recovery suggestion")
        }
        
        // Test specific descriptions
        XCTAssertTrue(DependencyIssue.pythonVersionIncompatible("3.6").description.contains("3.6"))
        XCTAssertTrue(DependencyIssue.pythonPackagesMissing(["whisper", "torch"]).description.contains("whisper"))
        XCTAssertTrue(DependencyIssue.whisperVersionIncompatible("1.0.0").description.contains("1.0.0"))
    }
    
    // MARK: - Binary Validation Tests
    
    func testBinaryValidation_ExecutableCheck() async {
        let manager = mockDependencyManager!
        
        // Test valid executable
        mockFileManager.mockFileExistsResults = [
            manager.pythonExecutablePath.path: true
        ]
        mockFileManager.mockExecutableResults = [
            manager.pythonExecutablePath.path: true
        ]
        
        let validResult = await manager.validateBinary(at: manager.pythonExecutablePath, name: "Python")
        switch validResult {
        case .valid:
            break // Expected
        default:
            XCTFail("Expected valid result")
        }
        
        // Test non-executable file
        mockFileManager.mockFileExistsResults = [
            manager.pythonExecutablePath.path: true
        ]
        mockFileManager.mockExecutableResults = [
            manager.pythonExecutablePath.path: false
        ]
        
        let nonExecutableResult = await manager.validateBinary(at: manager.pythonExecutablePath, name: "Python")
        switch nonExecutableResult {
        case .invalid(.pythonNotExecutable):
            break // Expected
        default:
            XCTFail("Expected non-executable result")
        }
        
        // Test missing file
        mockFileManager.mockFileExistsResults = [
            manager.pythonExecutablePath.path: false
        ]
        
        let missingResult = await manager.validateBinary(at: manager.pythonExecutablePath, name: "Python")
        switch missingResult {
        case .invalid(.pythonNotFound):
            break // Expected
        default:
            XCTFail("Expected missing file result")
        }
    }
    
    // MARK: - Environment Setup Tests
    
    func testEnvironmentSetup_PythonPath() {
        let manager = mockDependencyManager!
        let environment = manager.createExecutionEnvironment()
        
        XCTAssertNotNil(environment["PYTHONPATH"])
        XCTAssertTrue(environment["PYTHONPATH"]!.contains("site-packages"))
        
        XCTAssertNotNil(environment["DYLD_LIBRARY_PATH"])
        XCTAssertNotNil(environment["PATH"])
        
        // Test that Python executable directory is in PATH
        let pythonDir = manager.pythonExecutablePath.deletingLastPathComponent().path
        XCTAssertTrue(environment["PATH"]!.contains(pythonDir))
    }
    
    func testEnvironmentSetup_LibraryPath() {
        let manager = mockDependencyManager!
        let environment = manager.createExecutionEnvironment()
        
        let libraryPath = environment["DYLD_LIBRARY_PATH"] ?? ""
        
        // Should include Python lib directory
        let architecture = ProcessInfo.processInfo.machineArchitecture
        XCTAssertTrue(libraryPath.contains("python-\(architecture)/lib"))
        
        // Should include Whisper lib directory
        XCTAssertTrue(libraryPath.contains("whisper.cpp-\(architecture)/lib"))
    }
    
    // MARK: - Recovery Tests
    
    func testDependencyRecovery_AttemptRecovery() async {
        let manager = mockDependencyManager!
        
        // Test recovery for missing dependencies
        mockFileManager.mockFileExistsResults = [
            manager.dependenciesDirectory.path: false
        ]
        
        let initialStatus = await manager.validateDependencies()
        XCTAssertFalse(initialStatus.isValid)
        
        // Attempt recovery (this would typically involve extracting embedded dependencies)
        let recoverySuccess = await manager.attemptRecovery()
        
        if recoverySuccess {
            // After recovery, validation should pass
            mockFileManager.mockFileExistsResults = [
                manager.dependenciesDirectory.path: true,
                manager.pythonExecutablePath.path: true,
                manager.whisperBinaryPath.path: true,
                manager.ffmpegBinaryPath.path: true,
                manager.cliWrapperPath.path: true,
                manager.pythonPackagesPath.path: true
            ]
            
            mockFileManager.mockExecutableResults = [
                manager.pythonExecutablePath.path: true,
                manager.whisperBinaryPath.path: true,
                manager.ffmpegBinaryPath.path: true
            ]
            
            let recoveredStatus = await manager.validateDependencies()
            XCTAssertTrue(recoveredStatus.isValid)
        }
    }
    
    // MARK: - Performance Tests
    
    func testDependencyValidation_Performance() async {
        measure {
            let expectation = XCTestExpectation(description: "Validation completes")
            
            Task {
                _ = await mockDependencyManager.validateDependencies()
                expectation.fulfill()
            }
            
            wait(for: [expectation], timeout: 5.0)
        }
    }
    
    func testDependencyValidation_ConcurrentAccess() async {
        let manager = mockDependencyManager!
        
        // Setup valid dependencies
        mockFileManager.mockFileExistsResults = [
            manager.dependenciesDirectory.path: true,
            manager.pythonExecutablePath.path: true,
            manager.whisperBinaryPath.path: true,
            manager.ffmpegBinaryPath.path: true,
            manager.cliWrapperPath.path: true,
            manager.pythonPackagesPath.path: true
        ]
        
        mockFileManager.mockExecutableResults = [
            manager.pythonExecutablePath.path: true,
            manager.whisperBinaryPath.path: true,
            manager.ffmpegBinaryPath.path: true
        ]
        
        // Run multiple concurrent validations
        async let result1 = manager.validateDependencies()
        async let result2 = manager.validateDependencies()
        async let result3 = manager.validateDependencies()
        
        let results = await [result1, result2, result3]
        
        // All should succeed
        for result in results {
            XCTAssertTrue(result.isValid)
        }
    }
}

// MARK: - Mock Classes

@MainActor
class MockDependencyManager: DependencyManager {
    let mockFileManager: MockFileManager
    var simulateWarning: String?
    
    init(fileManager: MockFileManager) {
        self.mockFileManager = fileManager
        super.init()
    }
    
    override func validateDependencies() async -> DependencyStatus {
        isValidating = true
        defer { isValidating = false }
        
        var issues: [DependencyIssue] = []
        var warnings: [String] = []
        
        if let warning = simulateWarning {
            warnings.append(warning)
        }
        
        // Check dependencies directory
        if !mockFileManager.fileExists(atPath: dependenciesDirectory.path) {
            issues.append(.missingDependencyDirectory)
            dependencyStatus = .missing(issues: issues, warnings: warnings)
            return dependencyStatus
        }
        
        // Validate Python
        if !mockFileManager.fileExists(atPath: pythonExecutablePath.path) {
            issues.append(.pythonNotFound)
        } else if !mockFileManager.isExecutableFile(atPath: pythonExecutablePath.path) {
            issues.append(.pythonNotExecutable)
        }
        
        // Validate Whisper
        if !mockFileManager.fileExists(atPath: whisperBinaryPath.path) {
            issues.append(.whisperBinaryNotFound)
        } else if !mockFileManager.isExecutableFile(atPath: whisperBinaryPath.path) {
            issues.append(.whisperBinaryNotExecutable)
        }
        
        // Validate FFmpeg
        if !mockFileManager.fileExists(atPath: ffmpegBinaryPath.path) {
            issues.append(.ffmpegNotFound)
        } else if !mockFileManager.isExecutableFile(atPath: ffmpegBinaryPath.path) {
            issues.append(.ffmpegNotExecutable)
        }
        
        // Validate CLI wrapper
        if !mockFileManager.fileExists(atPath: cliWrapperPath.path) {
            issues.append(.cliWrapperNotFound)
        }
        
        // Determine status
        if issues.isEmpty {
            if warnings.isEmpty {
                dependencyStatus = .valid
            } else {
                dependencyStatus = .validWithWarnings(warnings: warnings)
            }
        } else {
            dependencyStatus = .invalid(issues: issues, warnings: warnings)
        }
        
        lastValidation = Date()
        return dependencyStatus
    }
    
    func validateBinary(at path: URL, name: String) async -> ValidationResult {
        if !mockFileManager.fileExists(atPath: path.path) {
            switch name {
            case "Python":
                return .invalid(.pythonNotFound)
            case "Whisper":
                return .invalid(.whisperBinaryNotFound)
            case "FFmpeg":
                return .invalid(.ffmpegNotFound)
            default:
                return .invalid(.invalidBundleStructure)
            }
        }
        
        if !mockFileManager.isExecutableFile(atPath: path.path) {
            switch name {
            case "Python":
                return .invalid(.pythonNotExecutable)
            case "Whisper":
                return .invalid(.whisperBinaryNotExecutable)
            case "FFmpeg":
                return .invalid(.ffmpegNotExecutable)
            default:
                return .invalid(.invalidBundleStructure)
            }
        }
        
        return .valid
    }
    
    func createExecutionEnvironment() -> [String: String] {
        var environment = ProcessInfo.processInfo.environment
        
        // Add Python path
        let pythonPackagesPath = self.pythonPackagesPath.path
        environment["PYTHONPATH"] = pythonPackagesPath
        
        // Add binary directories to PATH
        let pythonBinDir = pythonExecutablePath.deletingLastPathComponent().path
        let whisperBinDir = whisperBinaryPath.deletingLastPathComponent().path
        let ffmpegBinDir = ffmpegBinaryPath.deletingLastPathComponent().path
        
        let currentPath = environment["PATH"] ?? ""
        environment["PATH"] = "\(pythonBinDir):\(whisperBinDir):\(ffmpegBinDir):\(currentPath)"
        
        // Add library paths
        let architecture = ProcessInfo.processInfo.machineArchitecture
        let pythonLibDir = dependenciesDirectory.appendingPathComponent("python-\(architecture)/lib").path
        let whisperLibDir = dependenciesDirectory.appendingPathComponent("whisper.cpp-\(architecture)/lib").path
        
        environment["DYLD_LIBRARY_PATH"] = "\(pythonLibDir):\(whisperLibDir)"
        
        return environment
    }
    
    func attemptRecovery() async -> Bool {
        // Simulate recovery attempt
        try? await Task.sleep(nanoseconds: 100_000_000) // 100ms
        return true // Assume recovery succeeds in tests
    }
}

class MockFileManager {
    var mockFileExistsResults: [String: Bool] = [:]
    var mockExecutableResults: [String: Bool] = [:]
    
    func fileExists(atPath path: String) -> Bool {
        return mockFileExistsResults[path] ?? false
    }
    
    func isExecutableFile(atPath path: String) -> Bool {
        return mockExecutableResults[path] ?? false
    }
}

// MARK: - Dependency Status and Issue Enums

enum DependencyStatus: Equatable {
    case unknown
    case valid
    case validWithWarnings(warnings: [String])
    case invalid(issues: [DependencyIssue], warnings: [String])
    case missing(issues: [DependencyIssue], warnings: [String])
    
    var isValid: Bool {
        switch self {
        case .valid, .validWithWarnings:
            return true
        default:
            return false
        }
    }
    
    var description: String {
        switch self {
        case .unknown:
            return "Dependency status not yet determined"
        case .valid:
            return "All dependencies are valid and ready to use"
        case .validWithWarnings(let warnings):
            return "Dependencies are valid with warnings: \(warnings.joined(separator: ", "))"
        case .invalid(let issues, _):
            return "Dependencies are invalid: \(issues.count) issues found"
        case .missing(let issues, _):
            return "Dependencies are missing: \(issues.count) issues found"
        }
    }
}

enum DependencyIssue: Equatable {
    case missingDependencyDirectory
    case pythonNotFound
    case pythonNotExecutable
    case pythonVersionIncompatible(String)
    case pythonPackagesMissing([String])
    case whisperBinaryNotFound
    case whisperBinaryNotExecutable
    case whisperVersionIncompatible(String)
    case ffmpegNotFound
    case ffmpegNotExecutable
    case cliWrapperNotFound
    case cliWrapperNotReadable
    case modelsDirectoryNotAccessible
    case invalidBundleStructure
    
    var description: String {
        switch self {
        case .missingDependencyDirectory:
            return "Dependencies directory is missing from app bundle"
        case .pythonNotFound:
            return "Python executable not found"
        case .pythonNotExecutable:
            return "Python executable is not executable"
        case .pythonVersionIncompatible(let version):
            return "Python version \(version) is incompatible"
        case .pythonPackagesMissing(let packages):
            return "Missing Python packages: \(packages.joined(separator: ", "))"
        case .whisperBinaryNotFound:
            return "Whisper.cpp binary not found"
        case .whisperBinaryNotExecutable:
            return "Whisper.cpp binary is not executable"
        case .whisperVersionIncompatible(let version):
            return "Whisper.cpp version \(version) is incompatible"
        case .ffmpegNotFound:
            return "FFmpeg binary not found"
        case .ffmpegNotExecutable:
            return "FFmpeg binary is not executable"
        case .cliWrapperNotFound:
            return "CLI wrapper script not found"
        case .cliWrapperNotReadable:
            return "CLI wrapper script is not readable"
        case .modelsDirectoryNotAccessible:
            return "Models directory is not accessible"
        case .invalidBundleStructure:
            return "Invalid app bundle structure"
        }
    }
    
    var recoverySuggestion: String {
        switch self {
        case .missingDependencyDirectory, .invalidBundleStructure:
            return "Reinstall the application to restore missing components"
        case .pythonNotFound, .pythonNotExecutable:
            return "Check Python installation in app bundle"
        case .pythonVersionIncompatible:
            return "Update to a version with compatible Python"
        case .pythonPackagesMissing:
            return "Reinstall the application to restore Python packages"
        case .whisperBinaryNotFound, .whisperBinaryNotExecutable:
            return "Check Whisper.cpp installation in app bundle"
        case .whisperVersionIncompatible:
            return "Update to a version with compatible Whisper.cpp"
        case .ffmpegNotFound, .ffmpegNotExecutable:
            return "Check FFmpeg installation in app bundle"
        case .cliWrapperNotFound, .cliWrapperNotReadable:
            return "Reinstall the application to restore CLI wrapper"
        case .modelsDirectoryNotAccessible:
            return "Check file permissions for models directory"
        }
    }
}

enum ValidationResult {
    case valid
    case invalid(DependencyIssue)
    case warning(String)
}

// Extension for ProcessInfo
extension ProcessInfo {
    var machineArchitecture: String {
        #if arch(arm64)
        return "arm64"
        #elseif arch(x86_64)
        return "x86_64"
        #else
        return "unknown"
        #endif
    }
}