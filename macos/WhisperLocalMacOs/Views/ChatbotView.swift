import SwiftUI

struct ChatbotView: View {
    @StateObject private var viewModel = ChatbotViewModel()
    @State private var messageText = ""
    @State private var showingSearchFilters = false
    @State private var showingSearchResults = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Chat Header
                ChatHeaderView(
                    messageCount: viewModel.messages.count,
                    isSearching: viewModel.isSearching,
                    onClearChat: viewModel.clearChat,
                    onToggleFilters: { showingSearchFilters.toggle() },
                    onToggleResults: { showingSearchResults.toggle() }
                )
                
                Divider()
                
                // Main Chat Area
                HStack(spacing: 0) {
                    // Messages List
                    MessageListView(messages: viewModel.messages)
                        .frame(minWidth: 400)
                    
                    // Search Results Panel (collapsible)
                    if showingSearchResults && !viewModel.searchResults.isEmpty {
                        Divider()
                        SearchResultsPanel(
                            results: viewModel.searchResults,
                            query: viewModel.currentQuery
                        )
                        .frame(width: 350)
                    }
                }
                
                Divider()
                
                // Message Input
                MessageInputView(
                    text: $messageText,
                    isLoading: viewModel.isLoading,
                    onSend: { text in
                        viewModel.sendMessage(text)
                        messageText = ""
                    }
                )
            }
            .navigationTitle("Transcription Search")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItemGroup(placement: .primaryAction) {
                    Button(action: { showingSearchResults.toggle() }) {
                        Image(systemName: "list.bullet.rectangle")
                            .foregroundColor(showingSearchResults ? .accentColor : .secondary)
                    }
                    .help("Toggle search results panel")
                    
                    Button(action: { showingSearchFilters.toggle() }) {
                        Image(systemName: "line.horizontal.3.decrease.circle")
                            .foregroundColor(showingSearchFilters ? .accentColor : .secondary)
                    }
                    .help("Search filters")
                }
            }
            .sheet(isPresented: $showingSearchFilters) {
                SearchFiltersSheet(viewModel: viewModel)
            }
        }
        .frame(minWidth: 700, minHeight: 500)
    }
}

struct ChatHeaderView: View {
    let messageCount: Int
    let isSearching: Bool
    let onClearChat: () -> Void
    let onToggleFilters: () -> Void
    let onToggleResults: () -> Void
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Transcription Search Chat")
                    .font(.headline)
                    .fontWeight(.medium)
                
                HStack(spacing: 4) {
                    if isSearching {
                        ProgressView()
                            .scaleEffect(0.7)
                        Text("Searching...")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    } else {
                        Text("\(messageCount) messages")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            
            Spacer()
            
            HStack(spacing: 8) {
                Button("Filters", action: onToggleFilters)
                    .buttonStyle(.borderless)
                    .font(.caption)
                
                Button("Results", action: onToggleResults)
                    .buttonStyle(.borderless)
                    .font(.caption)
                
                Button("Clear", action: onClearChat)
                    .buttonStyle(.borderless)
                    .font(.caption)
                    .foregroundColor(.red)
            }
        }
        .padding()
        .background(.regularMaterial)
    }
}

struct MessageListView: View {
    let messages: [ChatMessage]
    
    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    if messages.isEmpty {
                        EmptyStateView()
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else {
                        ForEach(messages) { message in
                            MessageBubble(message: message)
                                .id(message.id)
                        }
                    }
                }
                .padding()
            }
            .onChange(of: messages.count) { _ in
                if let lastMessage = messages.last {
                    withAnimation(.easeOut(duration: 0.5)) {
                        proxy.scrollTo(lastMessage.id, anchor: .bottom)
                    }
                }
            }
        }
    }
}

struct EmptyStateView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "magnifyingglass.circle")
                .font(.system(size: 48))
                .foregroundStyle(.tertiary)
            
            VStack(spacing: 8) {
                Text("Search Your Transcriptions")
                    .font(.title2)
                    .fontWeight(.medium)
                
                Text("Ask questions about your transcribed content and I'll help you find relevant information.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Example queries:")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundStyle(.secondary)
                
                VStack(alignment: .leading, spacing: 4) {
                    ExampleQueryView(text: "What was discussed about budget planning?")
                    ExampleQueryView(text: "Find mentions of project deadlines")
                    ExampleQueryView(text: "Show me conversations about marketing")
                }
            }
            .padding()
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
        }
        .padding(40)
    }
}

struct ExampleQueryView: View {
    let text: String
    
    var body: some View {
        HStack {
            Image(systemName: "quote.bubble")
                .font(.caption2)
                .foregroundStyle(.tertiary)
            
            Text(text)
                .font(.caption)
                .foregroundStyle(.secondary)
                .italic()
        }
    }
}

struct MessageBubble: View {
    let message: ChatMessage
    
    var body: some View {
        HStack {
            if message.type == .user {
                Spacer()
            }
            
            VStack(alignment: message.type == .user ? .trailing : .leading, spacing: 8) {
                // Message Header
                HStack(spacing: 8) {
                    Circle()
                        .fill(message.type.color)
                        .frame(width: 8, height: 8)
                    
                    Text(message.type.displayName)
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(message.type.color)
                    
                    Text(message.timestamp, style: .time)
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                    
                    if message.type != .user {
                        Spacer()
                    }
                }
                
                // Message Content
                VStack(alignment: .leading, spacing: 12) {
                    Text(message.content)
                        .font(.body)
                        .textSelection(.enabled)
                        .padding()
                        .background(
                            message.type == .user ? Color.accentColor.opacity(0.1) : Color.secondary.opacity(0.1),
                            in: RoundedRectangle(cornerRadius: 12)
                        )
                    
                    // Search Results Summary (if available)
                    if let results = message.searchResults, !results.isEmpty {
                        SearchResultsSummary(results: results)
                    }
                }
            }
            .frame(maxWidth: message.type == .user ? 400 : .infinity, alignment: message.type == .user ? .trailing : .leading)
            
            if message.type != .user {
                Spacer()
            }
        }
    }
}

struct SearchResultsSummary: View {
    let results: [TranscriptionSearchResult]
    @State private var showingDetails = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "doc.text.magnifyingglass")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                
                Text("\(results.count) transcription\(results.count == 1 ? "" : "s") found")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundStyle(.secondary)
                
                Spacer()
                
                Button(showingDetails ? "Hide" : "Show Details") {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        showingDetails.toggle()
                    }
                }
                .buttonStyle(.borderless)
                .font(.caption)
            }
            
            if showingDetails {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(results.prefix(3)) { result in
                        SearchResultRow(result: result)
                    }
                    
                    if results.count > 3 {
                        Text("... and \(results.count - 3) more results")
                            .font(.caption2)
                            .foregroundStyle(.tertiary)
                            .italic()
                    }
                }
                .padding(.top, 4)
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
    }
}

struct SearchResultRow: View {
    let result: TranscriptionSearchResult
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(result.sourceFileName)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Text(String(format: "%.2f", result.relevanceScore))
                    .font(.caption2)
                    .fontFamily(.monospaced)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(.quaternary, in: RoundedRectangle(cornerRadius: 4))
            }
            
            Text(result.content.prefix(100) + (result.content.count > 100 ? "..." : ""))
                .font(.caption2)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
    }
}

struct MessageInputView: View {
    @Binding var text: String
    let isLoading: Bool
    let onSend: (String) -> Void
    @FocusState private var isTextFieldFocused: Bool
    
    var body: some View {
        HStack(spacing: 12) {
            TextField("Ask about your transcriptions...", text: $text, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .focused($isTextFieldFocused)
                .disabled(isLoading)
                .onSubmit {
                    if !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isLoading {
                        onSend(text)
                    }
                }
            
            Button(action: {
                if !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    onSend(text)
                }
            }) {
                if isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                } else {
                    Image(systemName: "paperplane.fill")
                        .foregroundColor(.accentColor)
                }
            }
            .buttonStyle(.borderless)
            .disabled(text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isLoading)
        }
        .padding()
        .background(.regularMaterial)
        .onAppear {
            isTextFieldFocused = true
        }
    }
}

struct SearchResultsPanel: View {
    let results: [TranscriptionSearchResult]
    let query: String
    @State private var sortOrder: SortOrder = .relevance
    
    enum SortOrder: String, CaseIterable {
        case relevance = "Relevance"
        case date = "Date"
        case filename = "Filename"
    }
    
    var sortedResults: [TranscriptionSearchResult] {
        switch sortOrder {
        case .relevance:
            return results.sorted { $0.relevanceScore > $1.relevanceScore }
        case .date:
            return results.sorted { (lhs, rhs) in
                guard let lhsDate = lhs.timestamp, let rhsDate = rhs.timestamp else {
                    return lhs.timestamp != nil
                }
                return lhsDate > rhsDate
            }
        case .filename:
            return results.sorted { $0.sourceFileName < $1.sourceFileName }
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Panel Header
            VStack(alignment: .leading, spacing: 8) {
                Text("Search Results")
                    .font(.headline)
                    .fontWeight(.medium)
                
                Text("Query: \"\(query)\"")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
                
                HStack {
                    Text("\(results.count) result\(results.count == 1 ? "" : "s")")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    
                    Spacer()
                    
                    Picker("Sort", selection: $sortOrder) {
                        ForEach(SortOrder.allCases, id: \.self) { order in
                            Text(order.rawValue).tag(order)
                        }
                    }
                    .pickerStyle(.menu)
                    .font(.caption)
                }
            }
            .padding()
            .background(.regularMaterial)
            
            Divider()
            
            // Results List
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(sortedResults) { result in
                        DetailedSearchResultCard(result: result)
                    }
                }
                .padding()
            }
        }
        .background(.background)
    }
}

struct DetailedSearchResultCard: View {
    let result: TranscriptionSearchResult
    @State private var showingFullContent = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(result.sourceFileName)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    
                    if let timestamp = result.timestamp {
                        Text(timestamp, style: .date)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
                
                Spacer()
                
                // Relevance Score
                VStack(alignment: .trailing, spacing: 2) {
                    Text(String(format: "%.2f", result.relevanceScore))
                        .font(.caption)
                        .fontFamily(.monospaced)
                        .fontWeight(.medium)
                        .foregroundColor(relevanceColor)
                    
                    Text("relevance")
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(relevanceColor.opacity(0.1), in: RoundedRectangle(cornerRadius: 6))
            }
            
            Divider()
            
            // Content
            VStack(alignment: .leading, spacing: 8) {
                Text("Content Match:")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundStyle(.secondary)
                
                Text(showingFullContent ? result.content : String(result.content.prefix(200)) + (result.content.count > 200 ? "..." : ""))
                    .font(.caption)
                    .textSelection(.enabled)
                    .foregroundColor(.primary)
                    .padding(8)
                    .background(.quaternary.opacity(0.5), in: RoundedRectangle(cornerRadius: 6))
                
                if result.content.count > 200 {
                    Button(showingFullContent ? "Show Less" : "Show More") {
                        showingFullContent.toggle()
                    }
                    .buttonStyle(.borderless)
                    .font(.caption)
                }
                
                // Context (if available)
                if let context = result.context, !context.isEmpty {
                    Text("Context:")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundStyle(.secondary)
                    
                    Text(context)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .italic()
                        .padding(6)
                        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 4))
                }
            }
            
            // Actions
            HStack(spacing: 8) {
                Button("Open File") {
                    openTranscriptionFile()
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
                .font(.caption)
                
                Button("Copy Content") {
                    copyToClipboard()
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
                .font(.caption)
                
                Spacer()
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 8))
    }
    
    private var relevanceColor: Color {
        switch result.relevanceScore {
        case 0.8...: return .green
        case 0.6..<0.8: return .orange
        default: return .secondary
        }
    }
    
    private func openTranscriptionFile() {
        let url = URL(fileURLWithPath: result.sourceFile)
        NSWorkspace.shared.open(url)
    }
    
    private func copyToClipboard() {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(result.content, forType: .string)
    }
}

struct SearchFiltersSheet: View {
    @ObservedObject var viewModel: ChatbotViewModel
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            Form {
                Section("Date Range") {
                    Picker("Filter by date", selection: $viewModel.selectedDateFilter) {
                        ForEach(ChatbotViewModel.DateFilter.allCases, id: \.self) { filter in
                            Text(filter.rawValue).tag(filter)
                        }
                    }
                    .pickerStyle(.segmented)
                }
                
                Section("File Type") {
                    Picker("Filter by file type", selection: $viewModel.selectedFileTypeFilter) {
                        ForEach(ChatbotViewModel.FileTypeFilter.allCases, id: \.self) { filter in
                            Text(filter.rawValue).tag(filter)
                        }
                    }
                    .pickerStyle(.segmented)
                }
                
                Section("Search Sensitivity") {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Relevance Threshold")
                            Spacer()
                            Text(String(format: "%.2f", viewModel.searchThreshold))
                                .fontFamily(.monospaced)
                                .foregroundStyle(.secondary)
                        }
                        
                        Slider(value: $viewModel.searchThreshold, in: 0.1...1.0, step: 0.1) {
                            Text("Threshold")
                        } minimumValueLabel: {
                            Text("0.1")
                                .font(.caption)
                        } maximumValueLabel: {
                            Text("1.0")
                                .font(.caption)
                        }
                        
                        Text("Lower values return more results but may be less relevant")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Search Filters")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(width: 500, height: 400)
    }
}

#Preview {
    ChatbotView()
        .frame(width: 1000, height: 700)
}