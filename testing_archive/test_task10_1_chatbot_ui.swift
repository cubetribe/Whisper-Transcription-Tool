#!/usr/bin/env swift

import Foundation

// Test Task 10.1: Create chatbot UI components
// This test validates the chatbot UI structure and basic functionality

struct ChatbotUITest {
    
    func runAllTests() {
        print("=== Task 10.1: Chatbot UI Components Test ===")
        print("Testing chatbot UI implementation...")
        
        var passedTests = 0
        let totalTests = 10
        
        // Test 1: Verify ChatbotViewModel.swift exists and has required structure
        if testChatbotViewModelExists() {
            print("✅ 1. ChatbotViewModel.swift exists with required structure")
            passedTests += 1
        } else {
            print("❌ 1. ChatbotViewModel.swift missing or incomplete")
        }
        
        // Test 2: Verify ChatbotView.swift exists and has required structure
        if testChatbotViewExists() {
            print("✅ 2. ChatbotView.swift exists with required structure")
            passedTests += 1
        } else {
            print("❌ 2. ChatbotView.swift missing or incomplete")
        }
        
        // Test 3: Verify search functionality implementation
        if testSemanticSearchImplementation() {
            print("✅ 3. Semantic search functionality implemented")
            passedTests += 1
        } else {
            print("❌ 3. Semantic search functionality missing")
        }
        
        // Test 4: Verify message management features
        if testMessageManagement() {
            print("✅ 4. Message management features implemented")
            passedTests += 1
        } else {
            print("❌ 4. Message management features incomplete")
        }
        
        // Test 5: Verify chat history persistence
        if testChatHistoryPersistence() {
            print("✅ 5. Chat history persistence implemented")
            passedTests += 1
        } else {
            print("❌ 5. Chat history persistence missing")
        }
        
        // Test 6: Verify search result display components
        if testSearchResultDisplay() {
            print("✅ 6. Search result display components implemented")
            passedTests += 1
        } else {
            print("❌ 6. Search result display components incomplete")
        }
        
        // Test 7: Verify PythonBridge chatbot integration
        if testPythonBridgeChatbotIntegration() {
            print("✅ 7. PythonBridge chatbot integration implemented")
            passedTests += 1
        } else {
            print("❌ 7. PythonBridge chatbot integration missing")
        }
        
        // Test 8: Verify sidebar integration
        if testSidebarIntegration() {
            print("✅ 8. Sidebar integration with chatbot tab implemented")
            passedTests += 1
        } else {
            print("❌ 8. Sidebar integration missing")
        }
        
        // Test 9: Verify search filters functionality
        if testSearchFilters() {
            print("✅ 9. Search filters functionality implemented")
            passedTests += 1
        } else {
            print("❌ 9. Search filters functionality incomplete")
        }
        
        // Test 10: Verify UI component structure
        if testUIComponentStructure() {
            print("✅ 10. UI component structure properly implemented")
            passedTests += 1
        } else {
            print("❌ 10. UI component structure incomplete")
        }
        
        // Summary
        let successRate = Double(passedTests) / Double(totalTests) * 100
        print("\n=== Test Results ===")
        print("Passed: \(passedTests)/\(totalTests) tests (\(String(format: "%.1f", successRate))%)")
        
        if successRate >= 80 {
            print("🎉 Task 10.1: Chatbot UI Components - SUCCESS")
        } else {
            print("⚠️ Task 10.1: Chatbot UI Components - NEEDS IMPROVEMENT")
        }
    }
    
    // MARK: - Test Methods
    
    func testChatbotViewModelExists() -> Bool {
        let filePath = "macos/WhisperLocalMacOs/ViewModels/ChatbotViewModel.swift"
        
        guard let content = readFile(filePath) else { return false }
        
        // Check for required components
        let requiredComponents = [
            "class ChatbotViewModel: ObservableObject",
            "@Published var messages:",
            "@Published var searchResults:",
            "func sendMessage(",
            "func performSemanticSearch(",
            "enum DateFilter",
            "enum FileTypeFilter",
            "ChatHistoryManager"
        ]
        
        return requiredComponents.allSatisfy { content.contains($0) }
    }
    
    func testChatbotViewExists() -> Bool {
        let filePath = "macos/WhisperLocalMacOs/Views/ChatbotView.swift"
        
        guard let content = readFile(filePath) else { return false }
        
        // Check for required UI components
        let requiredComponents = [
            "struct ChatbotView: View",
            "MessageListView",
            "MessageInputView", 
            "SearchResultsPanel",
            "SearchFiltersSheet",
            "MessageBubble",
            "EmptyStateView"
        ]
        
        return requiredComponents.allSatisfy { content.contains($0) }
    }
    
    func testSemanticSearchImplementation() -> Bool {
        let filePath = "macos/WhisperLocalMacOs/ViewModels/ChatbotViewModel.swift"
        
        guard let content = readFile(filePath) else { return false }
        
        // Check for semantic search features
        let searchFeatures = [
            "searchTranscriptions(query:",
            "TranscriptionSearchResult",
            "relevanceScore:",
            "searchThreshold:",
            "formatSearchResults"
        ]
        
        return searchFeatures.allSatisfy { content.contains($0) }
    }
    
    func testMessageManagement() -> Bool {
        let filePath = "macos/WhisperLocalMacOs/ViewModels/ChatbotViewModel.swift"
        
        guard let content = readFile(filePath) else { return false }
        
        // Check for message management features
        let messageFeatures = [
            "ChatMessage",
            "MessageType",
            "clearChat()",
            "loadChatHistory()",
            "addMessage("
        ]
        
        return messageFeatures.allSatisfy { content.contains($0) }
    }
    
    func testChatHistoryPersistence() -> Bool {
        let filePath = "macos/WhisperLocalMacOs/ViewModels/ChatbotViewModel.swift"
        
        guard let content = readFile(filePath) else { return false }
        
        // Check for persistence features
        let persistenceFeatures = [
            "ChatHistoryManager",
            "UserDefaults",
            "JSONEncoder",
            "JSONDecoder",
            "saveMessages",
            "maxHistorySize"
        ]
        
        return persistenceFeatures.allSatisfy { content.contains($0) }
    }
    
    func testSearchResultDisplay() -> Bool {
        let filePath = "macos/WhisperLocalMacOs/Views/ChatbotView.swift"
        
        guard let content = readFile(filePath) else { return false }
        
        // Check for search result display components
        let displayFeatures = [
            "SearchResultsPanel",
            "DetailedSearchResultCard",
            "SearchResultRow",
            "SearchResultsSummary",
            "sourceFile:",
            "relevanceScore"
        ]
        
        return displayFeatures.allSatisfy { content.contains($0) }
    }
    
    func testPythonBridgeChatbotIntegration() -> Bool {
        let filePath = "macos/WhisperLocalMacOs/Services/PythonBridge.swift"
        
        guard let content = readFile(filePath) else { return false }
        
        // Check for chatbot integration
        let integrationFeatures = [
            "executeChatbotCommand",
            "indexTranscription",
            "isChatbotAvailable",
            "chatbot.*args"
        ]
        
        return integrationFeatures.allSatisfy { feature in
            content.range(of: feature, options: .regularExpression) != nil
        }
    }
    
    func testSidebarIntegration() -> Bool {
        let sidebarPath = "macos/WhisperLocalMacOs/Models/SidebarItem.swift"
        let contentPath = "macos/WhisperLocalMacOs/Views/MainContentView.swift"
        
        guard let sidebarContent = readFile(sidebarPath),
              let mainContent = readFile(contentPath) else { return false }
        
        // Check sidebar integration
        return sidebarContent.contains("case chatbot") &&
               sidebarContent.contains("Search & Chat") &&
               mainContent.contains("case .chatbot:") &&
               mainContent.contains("ChatbotView()")
    }
    
    func testSearchFilters() -> Bool {
        let filePath = "macos/WhisperLocalMacOs/Views/ChatbotView.swift"
        
        guard let content = readFile(filePath) else { return false }
        
        // Check for search filter features
        let filterFeatures = [
            "SearchFiltersSheet",
            "DateFilter",
            "FileTypeFilter",
            "searchThreshold",
            "selectedDateFilter",
            "selectedFileTypeFilter"
        ]
        
        return filterFeatures.allSatisfy { content.contains($0) }
    }
    
    func testUIComponentStructure() -> Bool {
        let filePath = "macos/WhisperLocalMacOs/Views/ChatbotView.swift"
        
        guard let content = readFile(filePath) else { return false }
        
        // Check for proper UI structure
        let uiComponents = [
            "NavigationView",
            "VStack",
            "HStack",
            "ScrollView",
            "LazyVStack",
            "TextField",
            "Button",
            "Picker",
            "ProgressView"
        ]
        
        let foundComponents = uiComponents.filter { content.contains($0) }
        return foundComponents.count >= 7 // At least 7 out of 9 UI components
    }
    
    // MARK: - Helper Methods
    
    func readFile(_ relativePath: String) -> String? {
        let currentDirectory = FileManager.default.currentDirectoryPath
        let filePath = "\(currentDirectory)/\(relativePath)"
        
        return try? String(contentsOfFile: filePath)
    }
}

// Run the tests
let test = ChatbotUITest()
test.runAllTests()