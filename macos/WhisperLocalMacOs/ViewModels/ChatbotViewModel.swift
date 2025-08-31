import Foundation
import SwiftUI
import Combine

@MainActor
class ChatbotViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isLoading = false
    @Published var searchResults: [TranscriptionSearchResult] = []
    @Published var isSearching = false
    @Published var currentQuery = ""
    
    // Search filters
    @Published var selectedDateFilter: DateFilter = .all
    @Published var selectedFileTypeFilter: FileTypeFilter = .all
    @Published var searchThreshold: Double = 0.3
    
    private let pythonBridge = PythonBridge()
    private let chatHistoryManager = ChatHistoryManager()
    private var cancellables = Set<AnyCancellable>()
    
    enum DateFilter: String, CaseIterable {
        case all = "All Time"
        case today = "Today"
        case week = "Past Week"
        case month = "Past Month"
        case year = "Past Year"
        
        var dateRange: DateInterval? {
            let calendar = Calendar.current
            let now = Date()
            
            switch self {
            case .all:
                return nil
            case .today:
                let startOfDay = calendar.startOfDay(for: now)
                return DateInterval(start: startOfDay, end: now)
            case .week:
                let weekAgo = calendar.date(byAdding: .weekOfYear, value: -1, to: now)!
                return DateInterval(start: weekAgo, end: now)
            case .month:
                let monthAgo = calendar.date(byAdding: .month, value: -1, to: now)!
                return DateInterval(start: monthAgo, end: now)
            case .year:
                let yearAgo = calendar.date(byAdding: .year, value: -1, to: now)!
                return DateInterval(start: yearAgo, end: now)
            }
        }
    }
    
    enum FileTypeFilter: String, CaseIterable {
        case all = "All Types"
        case audio = "Audio Only"
        case video = "Video Only"
        case phone = "Phone Recordings"
        
        var allowedExtensions: [String]? {
            switch self {
            case .all:
                return nil
            case .audio:
                return ["mp3", "wav", "m4a", "flac", "aac"]
            case .video:
                return ["mp4", "mov", "avi", "mkv"]
            case .phone:
                return ["mp3", "wav"] // Typically phone recordings
            }
        }
    }
    
    init() {
        loadChatHistory()
        setupSearchObserver()
        Logger.shared.info("ChatbotViewModel initialized", category: .ui)
    }
    
    // MARK: - Chat Management
    
    func sendMessage(_ text: String) {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        let userMessage = ChatMessage(
            id: UUID(),
            content: text,
            type: .user,
            timestamp: Date()
        )
        
        messages.append(userMessage)
        currentQuery = text
        
        // Save message to history
        chatHistoryManager.addMessage(userMessage)
        
        // Perform semantic search
        performSemanticSearch(query: text)
    }
    
    func clearChat() {
        messages.removeAll()
        searchResults.removeAll()
        currentQuery = ""
        chatHistoryManager.clearHistory()
        
        Logger.shared.info("Chat history cleared", category: .ui)
    }
    
    func loadChatHistory() {
        messages = chatHistoryManager.loadMessages()
        
        // Load the last search results if available
        if let lastUserMessage = messages.last(where: { $0.type == .user }) {
            currentQuery = lastUserMessage.content
        }
        
        Logger.shared.info("Loaded \(messages.count) chat messages from history", category: .ui)
    }
    
    // MARK: - Semantic Search
    
    private func performSemanticSearch(query: String) {
        isLoading = true
        isSearching = true
        
        Task {
            do {
                let results = try await searchTranscriptions(query: query)
                
                await MainActor.run {
                    self.searchResults = results
                    self.isLoading = false
                    self.isSearching = false
                    
                    // Add assistant response with results
                    let assistantMessage = ChatMessage(
                        id: UUID(),
                        content: self.formatSearchResults(results, for: query),
                        type: .assistant,
                        timestamp: Date(),
                        searchResults: results
                    )
                    
                    self.messages.append(assistantMessage)
                    self.chatHistoryManager.addMessage(assistantMessage)
                    
                    Logger.shared.info("Semantic search completed: \(results.count) results", category: .chatbot)
                }
                
            } catch {
                await MainActor.run {
                    self.isLoading = false
                    self.isSearching = false
                    
                    let errorMessage = ChatMessage(
                        id: UUID(),
                        content: "Sorry, I encountered an error while searching: \(error.localizedDescription)",
                        type: .error,
                        timestamp: Date()
                    )
                    
                    self.messages.append(errorMessage)
                    self.chatHistoryManager.addMessage(errorMessage)
                    
                    Logger.shared.error("Semantic search failed: \(error)", category: .chatbot)
                }
            }
        }
    }
    
    private func searchTranscriptions(query: String) async throws -> [TranscriptionSearchResult] {
        // Apply filters to search parameters
        var searchParams: [String: Any] = [
            "query": query,
            "threshold": searchThreshold
        ]
        
        // Date filter
        if let dateRange = selectedDateFilter.dateRange {
            searchParams["start_date"] = dateRange.start.timeIntervalSince1970
            searchParams["end_date"] = dateRange.end.timeIntervalSince1970
        }
        
        // File type filter
        if let extensions = selectedFileTypeFilter.allowedExtensions {
            searchParams["file_extensions"] = extensions
        }
        
        // Use Python bridge to search via module4_chatbot
        let searchCommand = [
            "search",
            "--query", query,
            "--threshold", String(searchThreshold),
            "--format", "json"
        ]
        
        let result = try await pythonBridge.executeChatbotCommand(searchCommand)
        
        // Parse JSON response
        guard let data = result.data(using: .utf8),
              let json = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            throw ChatbotError.invalidSearchResponse
        }
        
        return try json.map { dict in
            guard let sourceFile = dict["source_file"] as? String,
                  let content = dict["content"] as? String,
                  let score = dict["score"] as? Double else {
                throw ChatbotError.invalidSearchResult
            }
            
            let timestamp = (dict["timestamp"] as? Double).map { Date(timeIntervalSince1970: $0) }
            let context = dict["context"] as? String
            
            return TranscriptionSearchResult(
                id: UUID(),
                sourceFile: sourceFile,
                content: content,
                context: context,
                relevanceScore: score,
                timestamp: timestamp
            )
        }
    }
    
    private func formatSearchResults(_ results: [TranscriptionSearchResult], for query: String) -> String {
        guard !results.isEmpty else {
            return "I couldn't find any transcriptions matching '\(query)'. Try adjusting your search terms or filters."
        }
        
        let resultCount = results.count
        var response = "I found \(resultCount) result\(resultCount == 1 ? "" : "s") for '\(query)':\n\n"
        
        for (index, result) in results.prefix(5).enumerated() {
            response += "\(index + 1). **\(result.sourceFileName)**"
            
            if let timestamp = result.timestamp {
                let formatter = DateFormatter()
                formatter.dateStyle = .medium
                formatter.timeStyle = .short
                response += " (\(formatter.string(from: timestamp)))"
            }
            
            response += "\n"
            response += "Match Score: \(String(format: "%.2f", result.relevanceScore))\n"
            response += "Content: \(result.content.prefix(200))\(result.content.count > 200 ? "..." : "")\n\n"
        }
        
        if results.count > 5 {
            response += "... and \(results.count - 5) more results. Use the search results panel to see all matches."
        }
        
        return response
    }
    
    // MARK: - Search Observer
    
    private func setupSearchObserver() {
        // Debounce search when filters change
        Publishers.CombineLatest3(
            $selectedDateFilter,
            $selectedFileTypeFilter,
            $searchThreshold
        )
        .debounce(for: .milliseconds(500), scheduler: RunLoop.main)
        .sink { [weak self] _, _, _ in
            guard let self = self, !self.currentQuery.isEmpty else { return }
            self.performSemanticSearch(query: self.currentQuery)
        }
        .store(in: &cancellables)
    }
}

// MARK: - Supporting Types

struct ChatMessage: Identifiable, Codable {
    let id: UUID
    let content: String
    let type: MessageType
    let timestamp: Date
    var searchResults: [TranscriptionSearchResult]?
    
    enum MessageType: String, Codable {
        case user, assistant, error, system
        
        var displayName: String {
            switch self {
            case .user: return "You"
            case .assistant: return "Assistant"
            case .error: return "Error"
            case .system: return "System"
            }
        }
        
        var color: Color {
            switch self {
            case .user: return .blue
            case .assistant: return .green
            case .error: return .red
            case .system: return .gray
            }
        }
    }
}

struct TranscriptionSearchResult: Identifiable, Codable {
    let id: UUID
    let sourceFile: String
    let content: String
    let context: String?
    let relevanceScore: Double
    let timestamp: Date?
    
    var sourceFileName: String {
        URL(fileURLWithPath: sourceFile).lastPathComponent
    }
}

enum ChatbotError: LocalizedError {
    case invalidSearchResponse
    case invalidSearchResult
    case searchTimeout
    case chatbotUnavailable
    
    var errorDescription: String? {
        switch self {
        case .invalidSearchResponse:
            return "Invalid response from search service"
        case .invalidSearchResult:
            return "Could not parse search result"
        case .searchTimeout:
            return "Search request timed out"
        case .chatbotUnavailable:
            return "Chatbot service is not available"
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .invalidSearchResponse, .invalidSearchResult:
            return "Please try a different search query"
        case .searchTimeout:
            return "Please try again with a shorter query"
        case .chatbotUnavailable:
            return "Make sure the chatbot service is properly installed and configured"
        }
    }
}

// MARK: - Chat History Management

@MainActor
class ChatHistoryManager {
    private let userDefaults = UserDefaults.standard
    private let historyKey = "chatbot_history"
    private let maxHistorySize = 1000
    
    func addMessage(_ message: ChatMessage) {
        var messages = loadMessages()
        messages.append(message)
        
        // Keep only the most recent messages
        if messages.count > maxHistorySize {
            messages = Array(messages.suffix(maxHistorySize))
        }
        
        saveMessages(messages)
    }
    
    func loadMessages() -> [ChatMessage] {
        guard let data = userDefaults.data(forKey: historyKey),
              let messages = try? JSONDecoder().decode([ChatMessage].self, from: data) else {
            return []
        }
        return messages
    }
    
    private func saveMessages(_ messages: [ChatMessage]) {
        guard let data = try? JSONEncoder().encode(messages) else { return }
        userDefaults.set(data, forKey: historyKey)
    }
    
    func clearHistory() {
        userDefaults.removeObject(forKey: historyKey)
    }
}