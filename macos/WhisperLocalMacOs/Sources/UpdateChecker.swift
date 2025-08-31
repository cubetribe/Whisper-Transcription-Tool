import Foundation
import SwiftUI

// MARK: - Update Models

struct UpdateInfo: Codable {
    let latestVersion: String
    let downloadURL: String
    let releaseNotes: String
    let releaseDate: String
    let minimumSystemVersion: String
    let isSecurityUpdate: Bool
    
    enum CodingKeys: String, CodingKey {
        case latestVersion = "latest_version"
        case downloadURL = "download_url"
        case releaseNotes = "release_notes"
        case releaseDate = "release_date"
        case minimumSystemVersion = "minimum_system_version"
        case isSecurityUpdate = "is_security_update"
    }
}

struct UpdateCheckResponse: Codable {
    let updateAvailable: Bool
    let updateInfo: UpdateInfo?
    let checkDate: String
    
    enum CodingKeys: String, CodingKey {
        case updateAvailable = "update_available"
        case updateInfo = "update_info"
        case checkDate = "check_date"
    }
}

// MARK: - Update Checker

@MainActor
class UpdateChecker: ObservableObject {
    
    @Published var updateAvailable = false
    @Published var updateInfo: UpdateInfo?
    @Published var isChecking = false
    @Published var lastCheckDate: Date?
    @Published var checkError: String?
    
    // Configuration
    private let updateURL = "https://api.github.com/repos/your-username/whisper-clean/releases/latest"
    private let userDefaults = UserDefaults.standard
    private let lastCheckKey = "UpdateChecker.LastCheck"
    private let skipVersionKey = "UpdateChecker.SkipVersion"
    
    // Update check interval (24 hours)
    private let checkInterval: TimeInterval = 24 * 60 * 60
    
    init() {
        loadLastCheckDate()
        
        // Auto-check on app launch if enough time has passed
        Task {
            await checkForUpdatesIfNeeded()
        }
    }
    
    // MARK: - Public Methods
    
    func checkForUpdatesIfNeeded() async {
        guard shouldCheckForUpdates() else { return }
        await checkForUpdates()
    }
    
    func checkForUpdates() async {
        guard !isChecking else { return }
        
        isChecking = true
        checkError = nil
        
        defer {
            isChecking = false
        }
        
        do {
            let latestRelease = try await fetchLatestRelease()
            await processUpdateInfo(latestRelease)
            saveLastCheckDate()
        } catch {
            checkError = error.localizedDescription
            print("Update check failed: \(error)")
        }
    }
    
    func skipVersion(_ version: String) {
        userDefaults.set(version, forKey: skipVersionKey)
        updateAvailable = false
        updateInfo = nil
    }
    
    func downloadUpdate() {
        guard let updateInfo = updateInfo,
              let downloadURL = URL(string: updateInfo.downloadURL) else {
            return
        }
        
        NSWorkspace.shared.open(downloadURL)
    }
    
    // MARK: - Private Methods
    
    private func shouldCheckForUpdates() -> Bool {
        guard let lastCheck = lastCheckDate else { return true }
        return Date().timeIntervalSince(lastCheck) >= checkInterval
    }
    
    private func fetchLatestRelease() async throws -> GitHubRelease {
        guard let url = URL(string: updateURL) else {
            throw UpdateError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.setValue("application/vnd.github.v3+json", forHTTPHeaderField: "Accept")
        request.setValue("WhisperLocal/1.0", forHTTPHeaderField: "User-Agent")
        request.timeoutInterval = 30
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw UpdateError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw UpdateError.httpError(httpResponse.statusCode)
        }
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        return try decoder.decode(GitHubRelease.self, from: data)
    }
    
    private func processUpdateInfo(_ release: GitHubRelease) async {
        let currentVersion = getCurrentVersion()
        
        guard isNewerVersion(release.tagName.replacingOccurrences(of: "v", with: ""), than: currentVersion) else {
            updateAvailable = false
            updateInfo = nil
            return
        }
        
        // Check if user has skipped this version
        let skippedVersion = userDefaults.string(forKey: skipVersionKey)
        if skippedVersion == release.tagName {
            updateAvailable = false
            updateInfo = nil
            return
        }
        
        // Find DMG download URL
        guard let dmgAsset = release.assets.first(where: { $0.name.hasSuffix(".dmg") }) else {
            updateAvailable = false
            updateInfo = nil
            return
        }
        
        updateInfo = UpdateInfo(
            latestVersion: release.tagName,
            downloadURL: dmgAsset.downloadURL,
            releaseNotes: release.body ?? "No release notes available.",
            releaseDate: formatReleaseDate(release.publishedAt),
            minimumSystemVersion: "12.0",
            isSecurityUpdate: release.body?.lowercased().contains("security") ?? false
        )
        
        updateAvailable = true
    }
    
    private func getCurrentVersion() -> String {
        guard let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String else {
            return "1.0.0"
        }
        return version
    }
    
    private func isNewerVersion(_ newVersion: String, than currentVersion: String) -> Bool {
        return newVersion.compare(currentVersion, options: .numeric) == .orderedDescending
    }
    
    private func formatReleaseDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }
        
        let displayFormatter = DateFormatter()
        displayFormatter.dateStyle = .medium
        displayFormatter.timeStyle = .none
        return displayFormatter.string(from: date)
    }
    
    private func loadLastCheckDate() {
        if let timestamp = userDefaults.object(forKey: lastCheckKey) as? Date {
            lastCheckDate = timestamp
        }
    }
    
    private func saveLastCheckDate() {
        let now = Date()
        userDefaults.set(now, forKey: lastCheckKey)
        lastCheckDate = now
    }
}

// MARK: - GitHub API Models

private struct GitHubRelease: Codable {
    let tagName: String
    let name: String
    let body: String?
    let publishedAt: String
    let assets: [GitHubAsset]
    
    enum CodingKeys: String, CodingKey {
        case tagName = "tag_name"
        case name
        case body
        case publishedAt = "published_at"
        case assets
    }
}

private struct GitHubAsset: Codable {
    let name: String
    let downloadURL: String
    let size: Int64
    
    enum CodingKeys: String, CodingKey {
        case name
        case downloadURL = "browser_download_url"
        case size
    }
}

// MARK: - Update Errors

enum UpdateError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(Int)
    case decodingError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid update URL"
        case .invalidResponse:
            return "Invalid response from update server"
        case .httpError(let code):
            return "HTTP error: \(code)"
        case .decodingError:
            return "Failed to decode update information"
        }
    }
}

// MARK: - Update Notification View

struct UpdateNotificationView: View {
    @ObservedObject var updateChecker: UpdateChecker
    @State private var showingDetails = false
    
    var body: some View {
        if updateChecker.updateAvailable, let updateInfo = updateChecker.updateInfo {
            VStack(spacing: 12) {
                HStack {
                    Image(systemName: updateInfo.isSecurityUpdate ? "exclamationmark.shield.fill" : "arrow.down.circle.fill")
                        .foregroundColor(updateInfo.isSecurityUpdate ? .red : .blue)
                        .font(.title2)
                    
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Update Available")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        Text("Version \(updateInfo.latestVersion)")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Button("Details") {
                        showingDetails = true
                    }
                    .buttonStyle(.bordered)
                    
                    Button("Update") {
                        updateChecker.downloadUpdate()
                    }
                    .buttonStyle(.borderedProminent)
                }
                
                if updateInfo.isSecurityUpdate {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.orange)
                        Text("This update contains important security fixes.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                }
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color(NSColor.separatorColor), lineWidth: 1)
            )
            .sheet(isPresented: $showingDetails) {
                UpdateDetailsView(updateInfo: updateInfo, updateChecker: updateChecker)
            }
        }
    }
}

// MARK: - Update Details View

struct UpdateDetailsView: View {
    let updateInfo: UpdateInfo
    let updateChecker: UpdateChecker
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Header
                    HStack {
                        Image(systemName: "arrow.down.circle.fill")
                            .font(.largeTitle)
                            .foregroundColor(.blue)
                        
                        VStack(alignment: .leading) {
                            Text("WhisperLocal \(updateInfo.latestVersion)")
                                .font(.title2)
                                .bold()
                            Text("Released \(updateInfo.releaseDate)")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                    }
                    
                    Divider()
                    
                    // Release Notes
                    VStack(alignment: .leading, spacing: 8) {
                        Text("What's New")
                            .font(.headline)
                        
                        Text(updateInfo.releaseNotes)
                            .font(.body)
                            .textSelection(.enabled)
                    }
                    
                    Divider()
                    
                    // System Requirements
                    VStack(alignment: .leading, spacing: 8) {
                        Text("System Requirements")
                            .font(.headline)
                        
                        Label("macOS \(updateInfo.minimumSystemVersion) or later", systemImage: "desktopcomputer")
                            .font(.body)
                    }
                    
                    if updateInfo.isSecurityUpdate {
                        Divider()
                        
                        HStack {
                            Image(systemName: "exclamationmark.shield.fill")
                                .foregroundColor(.red)
                            VStack(alignment: .leading) {
                                Text("Security Update")
                                    .font(.headline)
                                    .foregroundColor(.red)
                                Text("This update contains important security fixes and is recommended for all users.")
                                    .font(.body)
                            }
                        }
                        .padding()
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(8)
                    }
                    
                    Spacer()
                }
                .padding()
            }
            .navigationTitle("Update Available")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Skip This Version") {
                        updateChecker.skipVersion(updateInfo.latestVersion)
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Download") {
                        updateChecker.downloadUpdate()
                        dismiss()
                    }
                    .buttonStyle(.borderedProminent)
                }
                
                ToolbarItem(placement: .cancellationAction) {
                    Button("Later") {
                        dismiss()
                    }
                }
            }
        }
        .frame(width: 500, height: 400)
    }
}