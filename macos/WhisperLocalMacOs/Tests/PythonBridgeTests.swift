import XCTest
import Foundation
@testable import WhisperLocalMacOs

@MainActor
class PythonBridgeTests: XCTestCase {
    
    var mockPythonBridge: MockPythonBridge!
    
    override func setUp() {
        super.setUp()
        mockPythonBridge = MockPythonBridge()
    }
    
    override func tearDown() {
        mockPythonBridge = nil
        super.tearDown()
    }
    
    // MARK: - Initialization Tests
    
    func testPythonBridge_InitialState() {
        let bridge = PythonBridge()
        
        XCTAssertFalse(bridge.isProcessing)
        XCTAssertNil(bridge.lastError)
        XCTAssertEqual(bridge.currentProgress, 0.0)
        XCTAssertTrue(bridge.progressDescription.isEmpty)
    }
    
    // MARK: - Command Execution Tests
    
    func testExecuteCommand_Success() async throws {
        let command = ["command": "test", "data": "value"]
        let expectedResponse = ["success": true, "data": ["result": "success"]]
        
        mockPythonBridge.mockResponse = expectedResponse
        
        let result = try await mockPythonBridge.executeCommand(command)
        
        XCTAssertEqual(mockPythonBridge.lastCommand as? [String: String], command)
        XCTAssertEqual(result["success"] as? Bool, true)
        XCTAssertNotNil(result["data"])
    }
    
    func testExecuteCommand_PythonError() async {
        let command = ["command": "test"]
        let errorResponse = [
            "success": false, 
            "error": "Python execution failed",
            "code": "EXECUTION_ERROR"
        ] as [String: Any]
        
        mockPythonBridge.mockResponse = errorResponse
        
        do {
            _ = try await mockPythonBridge.executeCommand(command)
            XCTFail("Expected error to be thrown")
        } catch let error as PythonBridgeError {
            switch error {
            case .pythonError(let message, let code):
                XCTAssertEqual(message, "Python execution failed")
                XCTAssertEqual(code, "EXECUTION_ERROR")
            default:
                XCTFail("Wrong error type: \(error)")
            }
        }
    }
    
    func testExecuteCommand_InvalidResponse() async {
        let command = ["command": "test"]
        mockPythonBridge.mockResponse = "invalid response" // Not a dictionary
        
        do {
            _ = try await mockPythonBridge.executeCommand(command)
            XCTFail("Expected error to be thrown")
        } catch let error as PythonBridgeError {
            switch error {
            case .invalidResponse(let message):
                XCTAssertTrue(message.contains("Failed to parse JSON"))
            default:
                XCTFail("Wrong error type: \(error)")
            }
        }
    }
    
    func testExecuteCommand_ProcessAlreadyRunning() async {
        let command = ["command": "test"]
        
        mockPythonBridge.isProcessing = true
        
        do {
            _ = try await mockPythonBridge.executeCommand(command)
            XCTFail("Expected error to be thrown")
        } catch let error as PythonBridgeError {
            switch error {
            case .processAlreadyRunning:
                break // Expected
            default:
                XCTFail("Wrong error type: \(error)")
            }
        }
    }
    
    // MARK: - Transcription Tests
    
    func testTranscribeFile_Success() async throws {
        let tempFile = URL(fileURLWithPath: "/tmp/test.mp3")
        let tempDir = URL(fileURLWithPath: "/tmp")
        let task = TranscriptionTask(
            inputURL: tempFile,
            outputDirectory: tempDir,
            model: "base",
            formats: [.txt, .srt]
        )
        
        let mockResponse = [
            "success": true,
            "data": [
                "output_files": [
                    "/tmp/test.txt",
                    "/tmp/test.srt"
                ],
                "duration": 120.5,
                "language": "en",
                "model_used": "base"
            ]
        ] as [String: Any]
        
        mockPythonBridge.mockResponse = mockResponse
        
        let result = try await mockPythonBridge.transcribeFile(task)
        
        // Verify command was constructed correctly
        let command = mockPythonBridge.lastCommand as? [String: Any]
        XCTAssertEqual(command?["command"] as? String, "transcribe")
        XCTAssertEqual(command?["input_file"] as? String, tempFile.path)
        XCTAssertEqual(command?["output_dir"] as? String, tempDir.path)
        XCTAssertEqual(command?["model"] as? String, "base")
        
        let formats = command?["formats"] as? [String]
        XCTAssertTrue(formats?.contains("txt") == true)
        XCTAssertTrue(formats?.contains("srt") == true)
        
        // Verify result
        XCTAssertTrue(result.success)
        XCTAssertEqual(result.outputFiles.count, 2)
        XCTAssertEqual(result.duration, 120.5)
        XCTAssertEqual(result.language, "en")
        XCTAssertEqual(result.modelUsed, "base")
    }
    
    func testTranscribeFile_MissingData() async {
        let task = TranscriptionTask(
            inputURL: URL(fileURLWithPath: "/tmp/test.mp3"),
            outputDirectory: URL(fileURLWithPath: "/tmp"),
            model: "base",
            formats: [.txt]
        )
        
        let mockResponse = ["success": true] // Missing data field
        mockPythonBridge.mockResponse = mockResponse
        
        do {
            _ = try await mockPythonBridge.transcribeFile(task)
            XCTFail("Expected error to be thrown")
        } catch let error as PythonBridgeError {
            switch error {
            case .invalidResponse(let message):
                XCTAssertTrue(message.contains("Missing data"))
            default:
                XCTFail("Wrong error type: \(error)")
            }
        }
    }
    
    // MARK: - Audio Extraction Tests
    
    func testExtractAudio_Success() async throws {
        let videoURL = URL(fileURLWithPath: "/tmp/video.mp4")
        let outputURL = URL(fileURLWithPath: "/tmp/audio.mp3")
        
        let mockResponse = [
            "success": true,
            "data": [
                "output_file": "/tmp/audio.mp3"
            ]
        ] as [String: Any]
        
        mockPythonBridge.mockResponse = mockResponse
        
        let result = try await mockPythonBridge.extractAudio(from: videoURL, to: outputURL)
        
        // Verify command
        let command = mockPythonBridge.lastCommand as? [String: Any]
        XCTAssertEqual(command?["command"] as? String, "extract")
        XCTAssertEqual(command?["input_file"] as? String, videoURL.path)
        XCTAssertEqual(command?["output_file"] as? String, outputURL.path)
        
        // Verify result
        XCTAssertEqual(result.path, "/tmp/audio.mp3")
    }
    
    // MARK: - Model Management Tests
    
    func testListModels_Success() async throws {
        let mockResponse = [
            "success": true,
            "data": [
                "models": [
                    [
                        "name": "base",
                        "size": "142MB",
                        "description": "Base model",
                        "languages": ["en", "es", "fr"]
                    ],
                    [
                        "name": "large-v3",
                        "size": "1550MB", 
                        "description": "Large model v3",
                        "languages": ["en", "es", "fr", "de", "it"]
                    ]
                ]
            ]
        ] as [String: Any]
        
        mockPythonBridge.mockResponse = mockResponse
        
        let models = try await mockPythonBridge.listModels()
        
        // Verify command
        let command = mockPythonBridge.lastCommand as? [String: Any]
        XCTAssertEqual(command?["command"] as? String, "list_models")
        
        // Verify results
        XCTAssertEqual(models.count, 2)
        
        let baseModel = models.first { $0.name == "base" }
        XCTAssertNotNil(baseModel)
        XCTAssertEqual(baseModel?.sizeMB, 142)
        XCTAssertEqual(baseModel?.description, "Base model")
        
        let largeModel = models.first { $0.name == "large-v3" }
        XCTAssertNotNil(largeModel)
        XCTAssertEqual(largeModel?.sizeMB, 1550)
    }
    
    // MARK: - Error Handling Tests
    
    func testLastError_PersistsAfterFailure() async {
        let command = ["command": "test"]
        let errorResponse = [
            "success": false,
            "error": "Test error message"
        ] as [String: Any]
        
        mockPythonBridge.mockResponse = errorResponse
        
        do {
            _ = try await mockPythonBridge.executeCommand(command)
            XCTFail("Expected error")
        } catch {
            // Error should be stored
            XCTAssertNotNil(mockPythonBridge.lastError)
            XCTAssertTrue(mockPythonBridge.lastError?.contains("Test error message") == true)
        }
    }
    
    func testProcessingState_ManagesProperly() async throws {
        let command = ["command": "test"]
        let successResponse = ["success": true, "data": [:]] as [String: Any]
        
        mockPythonBridge.mockResponse = successResponse
        
        XCTAssertFalse(mockPythonBridge.isProcessing)
        
        let _ = try await mockPythonBridge.executeCommand(command)
        
        // Should be false after completion
        XCTAssertFalse(mockPythonBridge.isProcessing)
        XCTAssertNil(mockPythonBridge.lastError) // Should clear error on success
    }
    
    // MARK: - Integration Tests
    
    func testChatbotCommands_ExecuteCorrectly() async throws {
        // Test chatbot search command
        let searchResponse = [
            "success": true,
            "data": [
                "results": [
                    [
                        "content": "Test transcription content",
                        "source_file": "test.mp3",
                        "timestamp": 15.5,
                        "score": 0.85
                    ]
                ]
            ]
        ] as [String: Any]
        
        mockPythonBridge.mockResponse = searchResponse
        
        let searchCommand = [
            "command": "chatbot",
            "subcommand": "search",
            "query": "test query",
            "threshold": 0.3,
            "limit": 10
        ] as [String: Any]
        
        let result = try await mockPythonBridge.executeCommand(searchCommand)
        
        XCTAssertEqual(mockPythonBridge.lastCommand as? [String: Any], searchCommand)
        XCTAssertTrue(result["success"] as? Bool == true)
        XCTAssertNotNil(result["data"])
    }
    
    func testIndexTranscription_ExecuteCorrectly() async throws {
        let indexResponse = [
            "success": true,
            "data": [
                "indexed": true,
                "document_count": 1
            ]
        ] as [String: Any]
        
        mockPythonBridge.mockResponse = indexResponse
        
        let indexCommand = [
            "command": "chatbot",
            "subcommand": "index",
            "file_path": "/tmp/test.txt"
        ] as [String: Any]
        
        let result = try await mockPythonBridge.executeCommand(indexCommand)
        
        XCTAssertEqual(mockPythonBridge.lastCommand as? [String: Any], indexCommand)
        XCTAssertTrue(result["success"] as? Bool == true)
        
        let data = result["data"] as? [String: Any]
        XCTAssertEqual(data?["indexed"] as? Bool, true)
        XCTAssertEqual(data?["document_count"] as? Int, 1)
    }
}

// MARK: - Mock PythonBridge

@MainActor
class MockPythonBridge: PythonBridge {
    var mockResponse: Any = ["success": true]
    var lastCommand: Any?
    var shouldThrowError = false
    var mockError: Error?
    
    override func executeCommand(_ command: [String: Any]) async throws -> [String: Any] {
        lastCommand = command
        
        if shouldThrowError {
            if let error = mockError {
                throw error
            } else {
                throw PythonBridgeError.executionFailed("Mock error")
            }
        }
        
        // Handle process state
        if isProcessing {
            throw PythonBridgeError.processAlreadyRunning
        }
        
        isProcessing = true
        defer { isProcessing = false }
        
        // Simulate processing delay
        try await Task.sleep(nanoseconds: 1_000_000) // 1ms
        
        if let response = mockResponse as? [String: Any] {
            // Check for error in mock response
            if let success = response["success"] as? Bool, !success {
                let errorMessage = response["error"] as? String ?? "Mock error"
                let errorCode = response["code"] as? String ?? "MOCK_ERROR"
                lastError = errorMessage
                throw PythonBridgeError.pythonError(errorMessage, code: errorCode)
            }
            
            lastError = nil // Clear error on success
            return response
        } else {
            throw PythonBridgeError.invalidResponse("Failed to parse JSON response")
        }
    }
}

// MARK: - PythonBridge Error Types

enum PythonBridgeError: Error, LocalizedError {
    case processAlreadyRunning
    case invalidResponse(String)
    case pythonError(String, code: String)
    case executionFailed(String)
    case dependencyMissing(String)
    case invalidConfiguration(String)
    
    var errorDescription: String? {
        switch self {
        case .processAlreadyRunning:
            return "A Python process is already running"
        case .invalidResponse(let message):
            return "Invalid response: \(message)"
        case .pythonError(let message, let code):
            return "Python error (\(code)): \(message)"
        case .executionFailed(let message):
            return "Execution failed: \(message)"
        case .dependencyMissing(let dependency):
            return "Missing dependency: \(dependency)"
        case .invalidConfiguration(let message):
            return "Invalid configuration: \(message)"
        }
    }
}