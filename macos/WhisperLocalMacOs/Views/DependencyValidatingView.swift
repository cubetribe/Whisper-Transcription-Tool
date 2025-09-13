import SwiftUI

struct DependencyValidatingView: View {
    var body: some View {
        VStack(spacing: 20) {
            ProgressView()
                .scaleEffect(1.5)
            
            Text("Validating Dependencies...")
                .font(.headline)
            
            Text("Please wait while we check system requirements")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .padding(40)
    }
}