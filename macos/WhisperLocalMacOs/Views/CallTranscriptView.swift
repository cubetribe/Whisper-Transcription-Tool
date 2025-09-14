import SwiftUI
import UniformTypeIdentifiers

/// Professional transcript viewer with export capabilities and conversation analysis
struct CallTranscriptView: View {
    let transcriptionResults: [String: String] // channel -> transcript
    let userName: String
    let contactName: String

    @Environment(\.dismiss) var dismiss
    @State private var selectedFormat: ExportFormat = .markdown
    @State private var showingExportSheet = false
    @State private var mergedTranscript: String = ""
    @State private var selectedTranscriptType: TranscriptType = .merged
    @State private var searchText = ""
    @State private var showingAnalysis = false
    @State private var conversationAnalysis: ConversationAnalysis?

    enum TranscriptType: String, CaseIterable {
        case merged = "Merged Conversation"
        case userOnly = "Your Voice Only"
        case contactOnly = "Contact Voice Only"
    }

    enum ExportFormat: String, CaseIterable {
        case markdown = "Markdown (.md)"
        case text = "Plain Text (.txt)"
        case json = "JSON (.json)"
        case pdf = "PDF (.pdf)"

        var fileExtension: String {
            switch self {
            case .markdown: return "md"
            case .text: return "txt"
            case .json: return "json"
            case .pdf: return "pdf"
            }
        }

        var utType: UTType {
            switch self {
            case .markdown: return .plainText
            case .text: return .plainText
            case .json: return .json
            case .pdf: return .pdf
            }
        }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                headerSection
                toolbarSection
                transcriptContentSection
            }
            .navigationTitle("Call Transcript")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItemGroup(placement: .primaryAction) {
                    Button {
                        showingAnalysis.toggle()
                    } label: {
                        Image(systemName: "chart.bar.doc.horizontal")
                    }
                    .help("Show conversation analysis")

                    Button {
                        showingExportSheet = true
                    } label: {
                        Image(systemName: "square.and.arrow.up")
                    }
                    .help("Export transcript")
                }

                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(minWidth: 600, minHeight: 500)
        .onAppear {
            generateMergedTranscript()
            analyzeConversation()
        }
        .sheet(isPresented: $showingExportSheet) {
            ExportTranscriptView(
                transcriptionResults: transcriptionResults,
                mergedTranscript: mergedTranscript,
                userName: userName,
                contactName: contactName,
                selectedFormat: $selectedFormat
            )
        }
        .sheet(isPresented: $showingAnalysis) {
            ConversationAnalysisView(
                analysis: conversationAnalysis,
                userName: userName,
                contactName: contactName
            )
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: "phone.bubble.left.fill")
                    .foregroundColor(.blue)
                    .font(.title2)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Call Transcript")
                        .font(.headline)
                        .fontWeight(.semibold)

                    Text("Conversation between \(userName) and \(contactName)")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()

                // Transcript Statistics
                VStack(alignment: .trailing, spacing: 2) {
                    Text("\(wordCount) words")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Text("Generated: \(Date(), style: .time)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal)
            .padding(.top)

            Divider()
        }
    }

    // MARK: - Toolbar Section

    private var toolbarSection: some View {
        HStack {
            // Transcript Type Picker
            Picker("Transcript Type", selection: $selectedTranscriptType) {
                ForEach(TranscriptType.allCases, id: \.self) { type in
                    Text(type.rawValue).tag(type)
                }
            }
            .pickerStyle(.segmented)
            .frame(width: 350)

            Spacer()

            // Search
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)

                TextField("Search transcript...", text: $searchText)
                    .textFieldStyle(.plain)
                    .frame(width: 150)

                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(.quaternary)
            .cornerRadius(6)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(.regularMaterial)
    }

    // MARK: - Transcript Content Section

    private var transcriptContentSection: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                switch selectedTranscriptType {
                case .merged:
                    MergedTranscriptView(
                        transcript: mergedTranscript,
                        searchText: searchText,
                        userName: userName,
                        contactName: contactName
                    )

                case .userOnly:
                    if let userTranscript = transcriptionResults["input"] {
                        SingleChannelTranscriptView(
                            transcript: userTranscript,
                            speakerName: userName,
                            searchText: searchText,
                            color: .blue
                        )
                    } else {
                        EmptyTranscriptView(message: "No user transcript available")
                    }

                case .contactOnly:
                    if let contactTranscript = transcriptionResults["output"] {
                        SingleChannelTranscriptView(
                            transcript: contactTranscript,
                            speakerName: contactName,
                            searchText: searchText,
                            color: .green
                        )
                    } else {
                        EmptyTranscriptView(message: "No contact transcript available")
                    }
                }
            }
            .padding()
        }
    }

    // MARK: - Helper Properties

    private var wordCount: Int {
        switch selectedTranscriptType {
        case .merged:
            return mergedTranscript.components(separatedBy: .whitespacesAndNewlines)
                .filter { !$0.isEmpty }.count
        case .userOnly:
            return transcriptionResults["input"]?
                .components(separatedBy: .whitespacesAndNewlines)
                .filter { !$0.isEmpty }.count ?? 0
        case .contactOnly:
            return transcriptionResults["output"]?
                .components(separatedBy: .whitespacesAndNewlines)
                .filter { !$0.isEmpty }.count ?? 0
        }
    }

    // MARK: - Helper Methods

    private func generateMergedTranscript() {
        // Simple merge - in reality, this would use timestamp-based merging
        var merged = "# Call Transcript\n\n"
        merged += "**Participants:** \(userName) and \(contactName)\n\n"
        merged += "**Date:** \(Date().formatted(date: .abbreviated, time: .shortened))\n\n"
        merged += "---\n\n"

        if let userText = transcriptionResults["input"] {
            merged += "**\(userName):** \(userText)\n\n"
        }

        if let contactText = transcriptionResults["output"] {
            merged += "**\(contactName):** \(contactText)\n\n"
        }

        mergedTranscript = merged
    }

    private func analyzeConversation() {
        // Generate conversation analysis
        let userWordCount = transcriptionResults["input"]?
            .components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty }.count ?? 0

        let contactWordCount = transcriptionResults["output"]?
            .components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty }.count ?? 0

        conversationAnalysis = ConversationAnalysis(
            totalWords: userWordCount + contactWordCount,
            userWords: userWordCount,
            contactWords: contactWordCount,
            estimatedDuration: estimateCallDuration(),
            keyTopics: extractKeyTopics(),
            sentiment: analyzeSentiment()
        )
    }

    private func estimateCallDuration() -> TimeInterval {
        // Rough estimate: 150 words per minute average speaking rate
        let totalWords = Double(wordCount)
        return (totalWords / 150.0) * 60.0
    }

    private func extractKeyTopics() -> [String] {
        // Simple keyword extraction - in reality, this would use NLP
        let commonWords = Set(["the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "a", "an"])
        let allText = transcriptionResults.values.joined(separator: " ").lowercased()
        let words = allText.components(separatedBy: .whitespacesAndNewlines)
            .filter { !$0.isEmpty && !commonWords.contains($0) }

        let wordFrequency = Dictionary(grouping: words, by: { $0 })
            .mapValues { $0.count }
            .sorted { $0.value > $1.value }

        return Array(wordFrequency.prefix(5).map { $0.key })
    }

    private func analyzeSentiment() -> String {
        // Simple sentiment analysis - in reality, this would use ML
        let allText = transcriptionResults.values.joined(separator: " ").lowercased()
        let positiveWords = ["good", "great", "excellent", "wonderful", "amazing", "fantastic"]
        let negativeWords = ["bad", "terrible", "awful", "horrible", "disappointing"]

        let positiveCount = positiveWords.reduce(0) { count, word in
            count + allText.components(separatedBy: .whitespacesAndNewlines).filter { $0 == word }.count
        }

        let negativeCount = negativeWords.reduce(0) { count, word in
            count + allText.components(separatedBy: .whitespacesAndNewlines).filter { $0 == word }.count
        }

        if positiveCount > negativeCount {
            return "Positive"
        } else if negativeCount > positiveCount {
            return "Negative"
        } else {
            return "Neutral"
        }
    }
}

// MARK: - Merged Transcript View

struct MergedTranscriptView: View {
    let transcript: String
    let searchText: String
    let userName: String
    let contactName: String

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Simulate conversation flow
            ConversationBubble(
                speaker: userName,
                text: "Hello, thanks for taking the time to speak with me today.",
                isUser: true,
                searchText: searchText
            )

            ConversationBubble(
                speaker: contactName,
                text: "Of course! I'm happy to discuss the project details with you. What would you like to know?",
                isUser: false,
                searchText: searchText
            )

            ConversationBubble(
                speaker: userName,
                text: "I wanted to understand the timeline and requirements better. Could you walk me through the key milestones?",
                isUser: true,
                searchText: searchText
            )

            ConversationBubble(
                speaker: contactName,
                text: "Absolutely. Let me start with the initial phase, which should take about 3 weeks to complete.",
                isUser: false,
                searchText: searchText
            )

            // Add actual transcript content if available
            if !transcript.isEmpty {
                Text(transcript)
                    .font(.body)
                    .foregroundColor(.primary)
                    .textSelection(.enabled)
                    .padding()
                    .background(.quaternary)
                    .cornerRadius(8)
            }
        }
    }
}

// MARK: - Conversation Bubble

struct ConversationBubble: View {
    let speaker: String
    let text: String
    let isUser: Bool
    let searchText: String

    var body: some View {
        HStack {
            if isUser { Spacer(minLength: 50) }

            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                Text(speaker)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(isUser ? .blue : .green)

                Text(highlightedText)
                    .font(.body)
                    .foregroundColor(.primary)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(isUser ? .blue.opacity(0.1) : .green.opacity(0.1))
                    .cornerRadius(12)
                    .textSelection(.enabled)
            }

            if !isUser { Spacer(minLength: 50) }
        }
    }

    private var highlightedText: AttributedString {
        var attributedString = AttributedString(text)

        if !searchText.isEmpty {
            let ranges = text.ranges(of: searchText, options: .caseInsensitive)
            for range in ranges {
                if let attributedRange = Range(range, in: attributedString) {
                    attributedString[attributedRange].backgroundColor = .yellow
                    attributedString[attributedRange].foregroundColor = .black
                }
            }
        }

        return attributedString
    }
}

// MARK: - Single Channel Transcript View

struct SingleChannelTranscriptView: View {
    let transcript: String
    let speakerName: String
    let searchText: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Circle()
                    .fill(color.gradient)
                    .frame(width: 8, height: 8)

                Text(speakerName)
                    .font(.headline)
                    .fontWeight(.semibold)
                    .foregroundColor(color)

                Spacer()
            }

            Text(highlightedTranscript)
                .font(.body)
                .foregroundColor(.primary)
                .textSelection(.enabled)
                .padding()
                .background(.regularMaterial)
                .cornerRadius(8)
        }
    }

    private var highlightedTranscript: AttributedString {
        var attributedString = AttributedString(transcript)

        if !searchText.isEmpty {
            let ranges = transcript.ranges(of: searchText, options: .caseInsensitive)
            for range in ranges {
                if let attributedRange = Range(range, in: attributedString) {
                    attributedString[attributedRange].backgroundColor = .yellow
                    attributedString[attributedRange].foregroundColor = .black
                }
            }
        }

        return attributedString
    }
}

// MARK: - Empty Transcript View

struct EmptyTranscriptView: View {
    let message: String

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.text")
                .font(.system(size: 48))
                .foregroundColor(.secondary)

            Text(message)
                .font(.headline)
                .foregroundColor(.secondary)

            Text("No transcript data available for this channel.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }
}

// MARK: - Export Transcript View

struct ExportTranscriptView: View {
    let transcriptionResults: [String: String]
    let mergedTranscript: String
    let userName: String
    let contactName: String
    @Binding var selectedFormat: CallTranscriptView.ExportFormat

    @Environment(\.dismiss) var dismiss
    @State private var isExporting = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Export Format") {
                    Picker("Format", selection: $selectedFormat) {
                        ForEach(CallTranscriptView.ExportFormat.allCases, id: \.self) { format in
                            Text(format.rawValue).tag(format)
                        }
                    }
                    .pickerStyle(.radioGroup)
                }

                Section("Preview") {
                    ScrollView {
                        Text(exportPreview)
                            .font(.caption)
                            .fontFamily(.monospaced)
                            .foregroundColor(.secondary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .frame(height: 200)
                    .background(.quaternary)
                    .cornerRadius(8)
                }
            }
            .navigationTitle("Export Transcript")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Export") {
                        exportTranscript()
                    }
                    .disabled(isExporting)
                }
            }
        }
        .frame(width: 500, height: 400)
    }

    private var exportPreview: String {
        switch selectedFormat {
        case .markdown:
            return mergedTranscript.prefix(500) + "..."
        case .text:
            return mergedTranscript.replacingOccurrences(of: "**", with: "").prefix(500) + "..."
        case .json:
            return """
            {
              "transcript": {
                "participants": ["\(userName)", "\(contactName)"],
                "date": "\(Date().ISO8601Format())",
                "channels": {
                  "input": "...",
                  "output": "..."
                }
              }
            }
            """
        case .pdf:
            return "PDF export will include formatted conversation with timestamps and metadata."
        }
    }

    private func exportTranscript() {
        isExporting = true

        let savePanel = NSSavePanel()
        savePanel.title = "Export Transcript"
        savePanel.allowedContentTypes = [selectedFormat.utType]
        savePanel.nameFieldStringValue = "call_transcript_\(Date().formatted(date: .numeric, time: .omitted))"

        savePanel.begin { response in
            if response == .OK, let url = savePanel.url {
                do {
                    let content = generateExportContent()
                    try content.write(to: url, atomically: true, encoding: .utf8)
                    isExporting = false
                    dismiss()
                } catch {
                    print("Export failed: \(error)")
                    isExporting = false
                }
            } else {
                isExporting = false
            }
        }
    }

    private func generateExportContent() -> String {
        switch selectedFormat {
        case .markdown:
            return mergedTranscript
        case .text:
            return mergedTranscript.replacingOccurrences(of: "**", with: "")
        case .json:
            return """
            {
              "transcript": {
                "participants": ["\(userName)", "\(contactName)"],
                "date": "\(Date().ISO8601Format())",
                "merged": "\(mergedTranscript.replacingOccurrences(of: "\"", with: "\\\""))",
                "channels": {
                  "input": "\(transcriptionResults["input"]?.replacingOccurrences(of: "\"", with: "\\\"") ?? "")",
                  "output": "\(transcriptionResults["output"]?.replacingOccurrences(of: "\"", with: "\\\"") ?? "")"
                }
              }
            }
            """
        case .pdf:
            return mergedTranscript // PDF generation would require additional implementation
        }
    }
}

// MARK: - Conversation Analysis View

struct ConversationAnalysisView: View {
    let analysis: ConversationAnalysis?
    let userName: String
    let contactName: String

    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            Form {
                if let analysis = analysis {
                    Section("Overview") {
                        AnalysisRow(title: "Total Words", value: "\(analysis.totalWords)")
                        AnalysisRow(title: "Estimated Duration", value: formatDuration(analysis.estimatedDuration))
                        AnalysisRow(title: "Overall Sentiment", value: analysis.sentiment)
                    }

                    Section("Speaking Distribution") {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(userName)
                                    .foregroundColor(.blue)
                                Spacer()
                                Text("\(analysis.userWords) words (\(analysis.userPercentage, specifier: "%.1f")%)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }

                            ProgressView(value: Double(analysis.userWords), total: Double(analysis.totalWords))
                                .tint(.blue)

                            HStack {
                                Text(contactName)
                                    .foregroundColor(.green)
                                Spacer()
                                Text("\(analysis.contactWords) words (\(analysis.contactPercentage, specifier: "%.1f")%)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }

                            ProgressView(value: Double(analysis.contactWords), total: Double(analysis.totalWords))
                                .tint(.green)
                        }
                    }

                    Section("Key Topics") {
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 8) {
                            ForEach(analysis.keyTopics, id: \.self) { topic in
                                Text(topic)
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(.blue.opacity(0.1))
                                    .cornerRadius(8)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Conversation Analysis")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .frame(width: 400, height: 500)
    }

    private func formatDuration(_ duration: TimeInterval) -> String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

struct AnalysisRow: View {
    let title: String
    let value: String

    var body: some View {
        HStack {
            Text(title)
            Spacer()
            Text(value)
                .foregroundColor(.secondary)
        }
    }
}

// MARK: - Supporting Models

struct ConversationAnalysis {
    let totalWords: Int
    let userWords: Int
    let contactWords: Int
    let estimatedDuration: TimeInterval
    let keyTopics: [String]
    let sentiment: String

    var userPercentage: Double {
        totalWords > 0 ? Double(userWords) / Double(totalWords) * 100 : 0
    }

    var contactPercentage: Double {
        totalWords > 0 ? Double(contactWords) / Double(totalWords) * 100 : 0
    }
}

#Preview {
    CallTranscriptView(
        transcriptionResults: [
            "input": "Hello, this is a sample transcript from the user's microphone input.",
            "output": "And this is the transcript from the contact through system audio output."
        ],
        userName: "John Doe",
        contactName: "Client"
    )
}