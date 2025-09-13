import SwiftUI

struct DependencyStatusView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 60))
                .foregroundColor(.orange)
            
            Text("Dependencies Missing")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Some required system components are missing or invalid.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            
            Button("Retry") {
                // TODO: Implement retry logic
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(40)
    }
}