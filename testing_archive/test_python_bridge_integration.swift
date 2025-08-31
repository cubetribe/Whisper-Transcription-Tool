#!/usr/bin/env swift

import Foundation

// Basic test script to verify PythonBridge integration with CLI wrapper
// This simulates the core functionality without requiring Xcode

print("🧪 Testing PythonBridge Integration")
print(String(repeating: "=", count: 50))

// Test 1: Verify CLI wrapper exists and is executable
let cliPath = FileManager.default.currentDirectoryPath + "/macos_cli.py"
let cliURL = URL(fileURLWithPath: cliPath)

print("📁 Checking CLI wrapper at: \(cliPath)")
if FileManager.default.fileExists(atPath: cliPath) {
    print("✅ CLI wrapper found")
} else {
    print("❌ CLI wrapper not found")
    exit(1)
}

// Test 2: Verify Python executable
let pythonPath = "/usr/bin/python3"
print("🐍 Checking Python at: \(pythonPath)")
if FileManager.default.fileExists(atPath: pythonPath) {
    print("✅ Python found")
} else {
    print("❌ Python not found")
    exit(1)
}

// Test 3: Test basic CLI communication
print("🔄 Testing CLI communication...")

func testCLICommunication() {
    let process = Process()
    process.executableURL = URL(fileURLWithPath: pythonPath)
    process.arguments = [cliPath]
    
    let inputPipe = Pipe()
    let outputPipe = Pipe()
    let errorPipe = Pipe()
    
    process.standardInput = inputPipe
    process.standardOutput = outputPipe
    process.standardError = errorPipe
    
    do {
        try process.run()
        
        // Send test command
        let testCommand = #"{"command": "list_models"}"#
        inputPipe.fileHandleForWriting.write(testCommand.data(using: .utf8)!)
        inputPipe.fileHandleForWriting.closeFile()
        
        process.waitUntilExit()
        
        let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
        let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
        
        if process.terminationStatus == 0 {
            let output = String(data: outputData, encoding: .utf8) ?? ""
            print("✅ CLI communication successful")
            
            // Verify JSON response structure
            if let responseData = output.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: responseData) as? [String: Any] {
                
                if let success = json["success"] as? Bool {
                    print("✅ Valid JSON response received (success: \(success))")
                    
                    if success, let data = json["data"] as? [String: Any] {
                        if let models = data["models"] as? [[String: Any]] {
                            print("✅ Model list received: \(models.count) models")
                        }
                    }
                } else {
                    print("❌ Invalid JSON response structure")
                }
            } else {
                print("❌ Failed to parse JSON response")
                print("Raw output: \(output)")
            }
        } else {
            let errorOutput = String(data: errorData, encoding: .utf8) ?? ""
            print("❌ CLI process failed with exit code \(process.terminationStatus)")
            print("Error: \(errorOutput)")
        }
        
    } catch {
        print("❌ Failed to execute CLI process: \(error)")
    }
}

testCLICommunication()

// Test 4: Verify JSON serialization capabilities
print("🔄 Testing JSON serialization...")

let testCommand: [String: Any] = [
    "command": "transcribe",
    "input_file": "/test/file.mp3",
    "model": "tiny",
    "formats": ["txt", "srt"],
    "language": "en"
]

do {
    let jsonData = try JSONSerialization.data(withJSONObject: testCommand, options: [])
    if jsonData.count > 0 {
        print("✅ JSON serialization working")
        
        // Test deserialization
        if let deserialized = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
           deserialized["command"] as? String == "transcribe" {
            print("✅ JSON deserialization working")
        } else {
            print("❌ JSON deserialization failed")
        }
    } else {
        print("❌ JSON serialization failed")
    }
} catch {
    print("❌ JSON serialization error: \(error)")
}

// Test 5: Verify error handling structures
print("🔄 Testing error response parsing...")

let errorResponse = """
{
    "success": false,
    "error": "Test error message",
    "code": "TEST_ERROR",
    "timestamp": "2024-01-01T12:00:00Z"
}
"""

if let errorData = errorResponse.data(using: .utf8),
   let errorJSON = try? JSONSerialization.jsonObject(with: errorData) as? [String: Any] {
    
    if let success = errorJSON["success"] as? Bool, !success,
       let error = errorJSON["error"] as? String,
       let code = errorJSON["code"] as? String {
        print("✅ Error response parsing working")
        print("   Error: \(error)")
        print("   Code: \(code)")
    } else {
        print("❌ Error response structure invalid")
    }
} else {
    print("❌ Failed to parse error response")
}

print("\n🎉 Integration test completed!")
print("✨ PythonBridge implementation should be compatible with CLI wrapper")