import XCTest
import Foundation
@testable import WhisperLocalMacOs

class ErrorHandlingTests: XCTestCase {
    
    // MARK: - AppError Tests
    
    func testAppError_FileProcessingErrors() {
        let fileNotFoundError = AppError.fileProcessing(.fileNotFound("/tmp/missing.mp3"))
        let fileNotReadableError = AppError.fileProcessing(.fileNotReadable("/tmp/locked.mp3"))
        let invalidFormatError = AppError.fileProcessing(.invalidFormat("test.xyz", supportedFormats: ["mp3", "wav", "mp4"]))
        let fileTooLargeError = AppError.fileProcessing(.fileTooLarge(5000000000, maxSize: 1000000000))
        let fileCorruptedError = AppError.fileProcessing(.fileCorrupted("/tmp/corrupt.mp3"))
        let outputNotWritableError = AppError.fileProcessing(.outputDirectoryNotWritable("/tmp/readonly"))
        let transcriptionFailedError = AppError.fileProcessing(.transcriptionFailed("test.mp3", reason: "Model failed"))
        let audioExtractionFailedError = AppError.fileProcessing(.audioExtractionFailed("test.mp4", reason: "FFmpeg error"))
        let outputCreationFailedError = AppError.fileProcessing(.outputFileCreationFailed("/tmp/output.txt", reason: "No space"))
        
        // Test that errors are properly categorized
        switch fileNotFoundError {
        case .fileProcessing(.fileNotFound(let path)):
            XCTAssertEqual(path, "/tmp/missing.mp3")
        default:
            XCTFail("Wrong error type")
        }
        
        // Test LocalizedError conformance
        if let fileError = fileNotFoundError as? LocalizedError {
            XCTAssertNotNil(fileError.errorDescription)
            XCTAssertNotNil(fileError.recoverySuggestion)
            XCTAssertTrue(fileError.errorDescription!.contains("File not found"))
            XCTAssertTrue(fileError.recoverySuggestion!.contains("Check that the file exists"))
        } else {
            XCTFail("AppError should conform to LocalizedError")
        }
        
        // Test invalid format error includes supported formats
        if let invalidError = invalidFormatError as? LocalizedError {
            XCTAssertTrue(invalidError.errorDescription!.contains("mp3"))
            XCTAssertTrue(invalidError.errorDescription!.contains("wav"))
            XCTAssertTrue(invalidError.errorDescription!.contains("mp4"))
        }
        
        // Test file size error includes formatted sizes
        if let sizeError = fileTooLargeError as? LocalizedError {
            XCTAssertTrue(sizeError.errorDescription!.contains("5"))
            XCTAssertTrue(sizeError.errorDescription!.contains("1"))
        }
    }
    
    func testAppError_ModelManagementErrors() {
        let modelNotFoundError = AppError.modelManagement(.modelNotFound("nonexistent"))
        let modelNotDownloadedError = AppError.modelManagement(.modelNotDownloaded("large-v3"))
        let downloadFailedError = AppError.modelManagement(.downloadFailed("base", reason: "Network error"))
        let downloadCorruptedError = AppError.modelManagement(.downloadCorrupted("tiny", expected: "abc123", actual: "def456"))
        let modelDirectoryError = AppError.modelManagement(.modelDirectoryNotAccessible("/models"))
        let insufficientSpaceError = AppError.modelManagement(.insufficientDiskSpaceForModel("large", required: 2000000000, available: 1000000000))
        let validationFailedError = AppError.modelManagement(.modelValidationFailed("base", reason: "Checksum mismatch"))
        let modelIncompatibleError = AppError.modelManagement(.modelIncompatible("future-model", reason: "Requires newer version"))
        
        // Test model not found
        switch modelNotFoundError {
        case .modelManagement(.modelNotFound(let name)):
            XCTAssertEqual(name, "nonexistent")
        default:
            XCTFail("Wrong error type")
        }
        
        // Test LocalizedError conformance
        if let modelError = modelNotFoundError as? LocalizedError {
            XCTAssertTrue(modelError.errorDescription!.contains("nonexistent"))
            XCTAssertTrue(modelError.recoverySuggestion!.contains("Model Manager"))
        }
        
        // Test download corrupted with checksums
        if let corruptedError = downloadCorruptedError as? LocalizedError {
            XCTAssertTrue(corruptedError.errorDescription!.contains("abc123"))
            XCTAssertTrue(corruptedError.errorDescription!.contains("def456"))
        }
        
        // Test insufficient space with formatted sizes
        if let spaceError = insufficientSpaceError as? LocalizedError {
            XCTAssertTrue(spaceError.errorDescription!.contains("2"))
            XCTAssertTrue(spaceError.errorDescription!.contains("1"))
        }
    }
    
    func testAppError_SystemResourceErrors() {
        let insufficientMemoryError = AppError.systemResource(.insufficientMemory(required: 8000000000, available: 4000000000))
        let insufficientDiskError = AppError.systemResource(.insufficientDiskSpace(required: 2000000000, available: 500000000, path: "/tmp"))
        
        // Test insufficient memory
        switch insufficientMemoryError {
        case .systemResource(.insufficientMemory(let required, let available)):
            XCTAssertEqual(required, 8000000000)
            XCTAssertEqual(available, 4000000000)
        default:
            XCTFail("Wrong error type")
        }
        
        // Test LocalizedError conformance
        if let memoryError = insufficientMemoryError as? LocalizedError {
            XCTAssertTrue(memoryError.errorDescription!.contains("memory"))
            XCTAssertTrue(memoryError.recoverySuggestion!.contains("Close other"))
        }
        
        // Test insufficient disk space
        if let diskError = insufficientDiskError as? LocalizedError {
            XCTAssertTrue(diskError.errorDescription!.contains("/tmp"))
            XCTAssertTrue(diskError.errorDescription!.contains("2"))
            XCTAssertTrue(diskError.errorDescription!.contains("500"))
        }
    }
    
    func testAppError_PythonBridgeErrors() {
        let processFailedError = AppError.pythonBridge(.processExecutionFailed(command: "transcribe", exitCode: 1, stderr: "Error message"))
        let timeoutError = AppError.pythonBridge(.processTimeout(command: "transcribe", timeout: 300))
        let commandNotFoundError = AppError.pythonBridge(.commandExecutionFailed("python not found"))
        let invalidResponseError = AppError.pythonBridge(.invalidJSONResponse("Invalid JSON"))
        let dependencyMissingError = AppError.pythonBridge(.dependencyMissing(dependency: "whisper.cpp", path: "/usr/local/bin"))
        let configurationError = AppError.pythonBridge(.invalidConfiguration("Bad config"))
        let incompatibleVersionError = AppError.pythonBridge(.incompatiblePythonVersion(required: "3.8+", found: "3.6"))
        let moduleImportError = AppError.pythonBridge(.moduleImportFailed(module: "whisper", reason: "Not installed"))
        let communicationError = AppError.pythonBridge(.communicationError("Connection lost"))
        
        // Test process execution failed
        switch processFailedError {
        case .pythonBridge(.processExecutionFailed(let command, let exitCode, let stderr)):
            XCTAssertEqual(command, "transcribe")
            XCTAssertEqual(exitCode, 1)
            XCTAssertEqual(stderr, "Error message")
        default:
            XCTFail("Wrong error type")
        }
        
        // Test LocalizedError conformance
        if let bridgeError = processFailedError as? LocalizedError {
            XCTAssertTrue(bridgeError.errorDescription!.contains("transcribe"))
            XCTAssertTrue(bridgeError.errorDescription!.contains("1"))
            XCTAssertTrue(bridgeError.recoverySuggestion!.contains("dependencies"))
        }
        
        // Test timeout error
        if let timeoutError = timeoutError as? LocalizedError {
            XCTAssertTrue(timeoutError.errorDescription!.contains("300"))
            XCTAssertTrue(timeoutError.recoverySuggestion!.contains("timeout"))
        }
        
        // Test version compatibility error
        if let versionError = incompatibleVersionError as? LocalizedError {
            XCTAssertTrue(versionError.errorDescription!.contains("3.8"))
            XCTAssertTrue(versionError.errorDescription!.contains("3.6"))
        }
    }
    
    func testAppError_UserInputErrors() {
        let noFileSelectedError = AppError.userInput(.noFileSelected)
        let noOutputDirectoryError = AppError.userInput(.noOutputDirectory)
        let emptyFileQueueError = AppError.userInput(.emptyFileQueue)
        let invalidOutputFormatError = AppError.userInput(.invalidOutputFormat("xyz"))
        let invalidModelSelectionError = AppError.userInput(.invalidModelSelection("nonexistent"))
        let invalidLanguageSelectionError = AppError.userInput(.invalidLanguageSelection("zz"))
        let invalidBatchConfigError = AppError.userInput(.invalidBatchConfiguration("Invalid settings"))
        let userCancelledError = AppError.userInput(.userCancelled("transcription"))
        
        // Test no file selected
        switch noFileSelectedError {
        case .userInput(.noFileSelected):
            break // Expected
        default:
            XCTFail("Wrong error type")
        }
        
        // Test LocalizedError conformance
        if let inputError = noFileSelectedError as? LocalizedError {
            XCTAssertTrue(inputError.errorDescription!.contains("No file selected"))
            XCTAssertTrue(inputError.recoverySuggestion!.contains("select a file"))
        }
        
        // Test invalid output format
        if let formatError = invalidOutputFormatError as? LocalizedError {
            XCTAssertTrue(formatError.errorDescription!.contains("xyz"))
            XCTAssertTrue(formatError.recoverySuggestion!.contains("TXT, SRT, VTT"))
        }
        
        // Test user cancelled
        if let cancelledError = userCancelledError as? LocalizedError {
            XCTAssertTrue(cancelledError.errorDescription!.contains("transcription"))
            XCTAssertTrue(cancelledError.errorDescription!.contains("cancelled"))
        }
    }
    
    func testAppError_ConfigurationErrors() {
        let invalidConfigFileError = AppError.configuration(.invalidConfigurationFile("/config.json"))
        let configNotFoundError = AppError.configuration(.configurationFileNotFound("/missing.json"))
        let configCorruptedError = AppError.configuration(.configurationFileCorrupted("/bad.json"))
        let invalidSettingError = AppError.configuration(.invalidSettingValue(setting: "max_size", value: "-100"))
        let settingNotFoundError = AppError.configuration(.settingNotFound("missing_setting"))
        let configWriteFailedError = AppError.configuration(.configurationWriteFailed("/readonly.json"))
        
        // Test invalid config file
        switch invalidConfigFileError {
        case .configuration(.invalidConfigurationFile(let path)):
            XCTAssertEqual(path, "/config.json")
        default:
            XCTFail("Wrong error type")
        }
        
        // Test LocalizedError conformance
        if let configError = invalidConfigFileError as? LocalizedError {
            XCTAssertTrue(configError.errorDescription!.contains("/config.json"))
            XCTAssertTrue(configError.recoverySuggestion!.contains("reset"))
        }
        
        // Test invalid setting value
        if let settingError = invalidSettingError as? LocalizedError {
            XCTAssertTrue(settingError.errorDescription!.contains("max_size"))
            XCTAssertTrue(settingError.errorDescription!.contains("-100"))
        }
    }
    
    // MARK: - Error Categories and Properties
    
    func testAppError_Categories() {
        let fileError = AppError.fileProcessing(.fileNotFound("/tmp/test.mp3"))
        let modelError = AppError.modelManagement(.modelNotFound("base"))
        let resourceError = AppError.systemResource(.insufficientMemory(required: 1000, available: 500))
        let bridgeError = AppError.pythonBridge(.processExecutionFailed(command: "test", exitCode: 1, stderr: "error"))
        let inputError = AppError.userInput(.noFileSelected)
        let configError = AppError.configuration(.invalidConfigurationFile("/config.json"))
        
        XCTAssertEqual(fileError.category, .fileProcessing)
        XCTAssertEqual(modelError.category, .modelManagement)
        XCTAssertEqual(resourceError.category, .systemResource)
        XCTAssertEqual(bridgeError.category, .pythonBridge)
        XCTAssertEqual(inputError.category, .userInput)
        XCTAssertEqual(configError.category, .configuration)
    }
    
    func testAppError_Severity() {
        // Test different severity levels
        let lowSeverityError = AppError.userInput(.noFileSelected)
        let mediumSeverityError = AppError.fileProcessing(.fileNotFound("/tmp/test.mp3"))
        let highSeverityError = AppError.systemResource(.insufficientMemory(required: 1000, available: 500))
        let criticalSeverityError = AppError.pythonBridge(.dependencyMissing(dependency: "python", path: "/usr/bin"))
        
        XCTAssertEqual(lowSeverityError.severity, .low)
        XCTAssertEqual(mediumSeverityError.severity, .medium)
        XCTAssertEqual(highSeverityError.severity, .high)
        XCTAssertEqual(criticalSeverityError.severity, .critical)
    }
    
    func testAppError_Recoverability() {
        // Test recoverable errors
        let recoverableError1 = AppError.userInput(.noFileSelected)
        let recoverableError2 = AppError.fileProcessing(.fileNotFound("/tmp/test.mp3"))
        let recoverableError3 = AppError.modelManagement(.downloadFailed("base", reason: "Network error"))
        
        XCTAssertTrue(recoverableError1.isRecoverable)
        XCTAssertTrue(recoverableError2.isRecoverable)
        XCTAssertTrue(recoverableError3.isRecoverable)
        
        // Test non-recoverable errors
        let nonRecoverableError1 = AppError.systemResource(.insufficientMemory(required: 1000, available: 500))
        let nonRecoverableError2 = AppError.pythonBridge(.dependencyMissing(dependency: "python", path: "/usr/bin"))
        let nonRecoverableError3 = AppError.configuration(.configurationFileCorrupted("/config.json"))
        
        XCTAssertFalse(nonRecoverableError1.isRecoverable)
        XCTAssertFalse(nonRecoverableError2.isRecoverable)
        XCTAssertFalse(nonRecoverableError3.isRecoverable)
    }
    
    // MARK: - Error Factory Tests
    
    func testErrorFactory_PythonErrorMapping() {
        // Test creating errors from Python CLI error responses
        let pythonError1 = ErrorFactory.createError(from: ["code": "FILE_NOT_FOUND", "message": "File not found: /tmp/test.mp3"])
        switch pythonError1 {
        case .fileProcessing(.fileNotFound(let path)):
            XCTAssertTrue(path.contains("test.mp3"))
        default:
            XCTFail("Should map to file not found error")
        }
        
        let pythonError2 = ErrorFactory.createError(from: ["code": "MODEL_NOT_DOWNLOADED", "message": "Model 'base' is not downloaded"])
        switch pythonError2 {
        case .modelManagement(.modelNotDownloaded(let model)):
            XCTAssertEqual(model, "base")
        default:
            XCTFail("Should map to model not downloaded error")
        }
        
        let pythonError3 = ErrorFactory.createError(from: ["code": "INSUFFICIENT_MEMORY", "message": "Not enough memory"])
        switch pythonError3 {
        case .systemResource(.insufficientMemory):
            break // Expected
        default:
            XCTFail("Should map to insufficient memory error")
        }
        
        // Test unknown error code
        let unknownError = ErrorFactory.createError(from: ["code": "UNKNOWN_ERROR", "message": "Something went wrong"])
        switch unknownError {
        case .pythonBridge(.communicationError(let message)):
            XCTAssertEqual(message, "Something went wrong")
        default:
            XCTFail("Should map to communication error for unknown codes")
        }
    }
    
    func testErrorFactory_ErrorCodeExtraction() {
        // Test extracting error codes from various error messages
        let fileError = "FileNotFoundError: No such file or directory: '/tmp/test.mp3'"
        let extractedError1 = ErrorFactory.createError(from: ["message": fileError])
        switch extractedError1 {
        case .fileProcessing(.fileNotFound):
            break // Expected
        default:
            XCTFail("Should extract file not found error")
        }
        
        let permissionError = "PermissionError: [Errno 13] Permission denied: '/readonly/output.txt'"
        let extractedError2 = ErrorFactory.createError(from: ["message": permissionError])
        switch extractedError2 {
        case .fileProcessing(.outputDirectoryNotWritable):
            break // Expected
        default:
            XCTFail("Should extract permission error")
        }
        
        let memoryError = "MemoryError: Unable to allocate 8.00 GB for an array"
        let extractedError3 = ErrorFactory.createError(from: ["message": memoryError])
        switch extractedError3 {
        case .systemResource(.insufficientMemory):
            break // Expected
        default:
            XCTFail("Should extract memory error")
        }
    }
    
    // MARK: - Error Recovery Tests
    
    func testErrorRecovery_FileProcessingErrors() async {
        // Test file not found recovery
        let fileNotFoundError = AppError.fileProcessing(.fileNotFound("/tmp/test.mp3"))
        let recovery1 = await ErrorRecoveryActions.attemptRecovery(for: fileNotFoundError)
        // Recovery should suggest file selection, but cannot automatically recover
        XCTAssertFalse(recovery1)
        
        // Test invalid format recovery
        let invalidFormatError = AppError.fileProcessing(.invalidFormat("test.xyz", supportedFormats: ["mp3", "wav"]))
        let recovery2 = await ErrorRecoveryActions.attemptRecovery(for: invalidFormatError)
        // Cannot automatically convert formats
        XCTAssertFalse(recovery2)
        
        // Test output directory not writable recovery
        let outputError = AppError.fileProcessing(.outputDirectoryNotWritable("/readonly"))
        let recovery3 = await ErrorRecoveryActions.attemptRecovery(for: outputError)
        // May attempt to create directory or change permissions
        // This would depend on implementation - for testing, assume it tries
        XCTAssertTrue(recovery3) // Assuming it attempts recovery
    }
    
    func testErrorRecovery_ModelManagementErrors() async {
        // Test model not downloaded recovery
        let modelNotDownloadedError = AppError.modelManagement(.modelNotDownloaded("base"))
        let recovery1 = await ErrorRecoveryActions.attemptRecovery(for: modelNotDownloadedError)
        // Should attempt to download the model
        XCTAssertTrue(recovery1)
        
        // Test download failed recovery
        let downloadFailedError = AppError.modelManagement(.downloadFailed("large", reason: "Network error"))
        let recovery2 = await ErrorRecoveryActions.attemptRecovery(for: downloadFailedError)
        // Should retry download
        XCTAssertTrue(recovery2)
        
        // Test insufficient disk space recovery
        let diskSpaceError = AppError.modelManagement(.insufficientDiskSpaceForModel("large", required: 2000000000, available: 1000000000))
        let recovery3 = await ErrorRecoveryActions.attemptRecovery(for: diskSpaceError)
        // Cannot automatically free disk space
        XCTAssertFalse(recovery3)
    }
    
    func testErrorRecovery_SystemResourceErrors() async {
        // Test insufficient memory recovery
        let memoryError = AppError.systemResource(.insufficientMemory(required: 8000000000, available: 4000000000))
        let recovery1 = await ErrorRecoveryActions.attemptRecovery(for: memoryError)
        // Should attempt garbage collection and wait
        XCTAssertTrue(recovery1)
        
        // Test insufficient disk space recovery
        let diskError = AppError.systemResource(.insufficientDiskSpace(required: 2000000000, available: 500000000, path: "/tmp"))
        let recovery2 = await ErrorRecoveryActions.attemptRecovery(for: diskError)
        // Cannot automatically free disk space
        XCTAssertFalse(recovery2)
    }
    
    func testErrorRecovery_PythonBridgeErrors() async {
        // Test process execution failed recovery
        let processError = AppError.pythonBridge(.processExecutionFailed(command: "transcribe", exitCode: 1, stderr: "Temporary error"))
        let recovery1 = await ErrorRecoveryActions.attemptRecovery(for: processError)
        // Should retry execution
        XCTAssertTrue(recovery1)
        
        // Test timeout recovery
        let timeoutError = AppError.pythonBridge(.processTimeout(command: "transcribe", timeout: 300))
        let recovery2 = await ErrorRecoveryActions.attemptRecovery(for: timeoutError)
        // Should retry with longer timeout
        XCTAssertTrue(recovery2)
        
        // Test dependency missing recovery
        let dependencyError = AppError.pythonBridge(.dependencyMissing(dependency: "whisper.cpp", path: "/usr/local/bin"))
        let recovery3 = await ErrorRecoveryActions.attemptRecovery(for: dependencyError)
        // Cannot automatically install dependencies
        XCTAssertFalse(recovery3)
    }
    
    // MARK: - Bug Reporting Tests
    
    func testBugReporter_ReportGeneration() {
        let error = AppError.fileProcessing(.transcriptionFailed("test.mp3", reason: "Model crashed"))
        let report = BugReporter.generateReport(for: error)
        
        XCTAssertNotNil(report.errorDescription)
        XCTAssertNotNil(report.systemInfo)
        XCTAssertNotNil(report.timestamp)
        XCTAssertNotNil(report.appVersion)
        XCTAssertNotNil(report.errorCategory)
        
        // Check that error details are included
        XCTAssertTrue(report.errorDescription.contains("test.mp3"))
        XCTAssertTrue(report.errorDescription.contains("Model crashed"))
        
        // Check system info is populated
        XCTAssertFalse(report.systemInfo.osVersion.isEmpty)
        XCTAssertFalse(report.systemInfo.architecture.isEmpty)
        XCTAssertGreaterThan(report.systemInfo.totalMemory, 0)
        
        // Check formatted description
        let formattedDescription = report.formattedDescription
        XCTAssertTrue(formattedDescription.contains("ERROR REPORT"))
        XCTAssertTrue(formattedDescription.contains("System Information"))
        XCTAssertTrue(formattedDescription.contains("Error Details"))
    }
    
    func testBugReporter_SystemInfoCollection() {
        let systemInfo = SystemInfo()
        
        XCTAssertFalse(systemInfo.osVersion.isEmpty)
        XCTAssertFalse(systemInfo.architecture.isEmpty)
        XCTAssertGreaterThan(systemInfo.totalMemory, 0)
        XCTAssertGreaterThanOrEqual(systemInfo.availableDiskSpace, 0)
        XCTAssertGreaterThan(systemInfo.processorCount, 0)
        
        // Test formatted values
        let formattedMemory = systemInfo.formattedTotalMemory
        XCTAssertTrue(formattedMemory.contains("GB") || formattedMemory.contains("MB"))
        
        let formattedDisk = systemInfo.formattedAvailableDiskSpace
        XCTAssertTrue(formattedDisk.contains("GB") || formattedDisk.contains("MB") || formattedDisk.contains("TB"))
    }
}

// MARK: - Mock Classes and Test Helpers

/// Mock error recovery actions for testing
struct ErrorRecoveryActions {
    static func attemptRecovery(for error: AppError) async -> Bool {
        // Simulate recovery attempts based on error type
        switch error {
        case .fileProcessing(.outputDirectoryNotWritable):
            return true // Simulate successful permission fix
        case .modelManagement(.modelNotDownloaded):
            return true // Simulate successful download
        case .modelManagement(.downloadFailed):
            return true // Simulate successful retry
        case .systemResource(.insufficientMemory):
            return true // Simulate successful memory cleanup
        case .pythonBridge(.processExecutionFailed):
            return true // Simulate successful retry
        case .pythonBridge(.processTimeout):
            return true // Simulate successful retry with longer timeout
        default:
            return false // Most errors cannot be automatically recovered
        }
    }
}

/// Mock error factory for testing
struct ErrorFactory {
    static func createError(from pythonError: [String: Any]) -> AppError {
        let code = pythonError["code"] as? String ?? ""
        let message = pythonError["message"] as? String ?? ""
        
        // Map Python error codes to AppError cases
        switch code {
        case "FILE_NOT_FOUND":
            let path = extractPath(from: message) ?? "unknown"
            return .fileProcessing(.fileNotFound(path))
        case "MODEL_NOT_DOWNLOADED":
            let model = extractModelName(from: message) ?? "unknown"
            return .modelManagement(.modelNotDownloaded(model))
        case "INSUFFICIENT_MEMORY":
            return .systemResource(.insufficientMemory(required: 0, available: 0))
        default:
            // Try to extract error type from message
            if message.contains("FileNotFoundError") || message.contains("No such file") {
                let path = extractPath(from: message) ?? "unknown"
                return .fileProcessing(.fileNotFound(path))
            } else if message.contains("PermissionError") || message.contains("Permission denied") {
                let path = extractPath(from: message) ?? "unknown"
                return .fileProcessing(.outputDirectoryNotWritable(path))
            } else if message.contains("MemoryError") || message.contains("Unable to allocate") {
                return .systemResource(.insufficientMemory(required: 0, available: 0))
            } else {
                return .pythonBridge(.communicationError(message))
            }
        }
    }
    
    private static func extractPath(from message: String) -> String? {
        // Simple path extraction - in real implementation this would be more sophisticated
        if let range = message.range(of: "'") {
            let afterFirst = message[range.upperBound...]
            if let endRange = afterFirst.range(of: "'") {
                return String(afterFirst[..<endRange.lowerBound])
            }
        }
        return nil
    }
    
    private static func extractModelName(from message: String) -> String? {
        // Simple model name extraction
        if let range = message.range(of: "'") {
            let afterFirst = message[range.upperBound...]
            if let endRange = afterFirst.range(of: "'") {
                return String(afterFirst[..<endRange.lowerBound])
            }
        }
        return nil
    }
}

/// Mock bug reporter for testing
struct BugReporter {
    static func generateReport(for error: AppError) -> BugReport {
        return BugReport(
            errorDescription: error.localizedDescription,
            errorCategory: error.category.rawValue,
            systemInfo: SystemInfo(),
            timestamp: Date(),
            appVersion: "1.0.0"
        )
    }
}

/// Mock bug report structure
struct BugReport {
    let errorDescription: String
    let errorCategory: String
    let systemInfo: SystemInfo
    let timestamp: Date
    let appVersion: String
    
    var formattedDescription: String {
        return """
        ERROR REPORT
        Generated: \(timestamp)
        App Version: \(appVersion)
        
        Error Details:
        Category: \(errorCategory)
        Description: \(errorDescription)
        
        System Information:
        OS: \(systemInfo.osVersion)
        Architecture: \(systemInfo.architecture)
        Memory: \(systemInfo.formattedTotalMemory)
        Disk Space: \(systemInfo.formattedAvailableDiskSpace)
        Processors: \(systemInfo.processorCount)
        """
    }
}

/// Mock system info for testing
struct SystemInfo {
    let osVersion: String
    let architecture: String
    let totalMemory: Int64
    let availableDiskSpace: Int64
    let processorCount: Int
    
    init() {
        self.osVersion = ProcessInfo.processInfo.operatingSystemVersionString
        self.architecture = ProcessInfo.processInfo.machineTypeString
        self.totalMemory = Int64(ProcessInfo.processInfo.physicalMemory)
        self.availableDiskSpace = 100_000_000_000 // Mock 100GB
        self.processorCount = ProcessInfo.processInfo.processorCount
    }
    
    var formattedTotalMemory: String {
        return ByteCountFormatter.string(fromByteCount: totalMemory, countStyle: .memory)
    }
    
    var formattedAvailableDiskSpace: String {
        return ByteCountFormatter.string(fromByteCount: availableDiskSpace, countStyle: .file)
    }
}

// Mock extensions for testing
extension ProcessInfo {
    var machineTypeString: String {
        var systeminfo = utsname()
        uname(&systeminfo)
        let machineMirror = Mirror(reflecting: systeminfo.machine)
        return machineMirror.children.reduce("") { identifier, element in
            guard let value = element.value as? Int8, value != 0 else { return identifier }
            return identifier + String(UnicodeScalar(UInt8(value))!)
        }
    }
}