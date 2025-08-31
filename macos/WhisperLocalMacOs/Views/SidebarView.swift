import SwiftUI

struct SidebarView: View {
    @Binding var selectedTab: SidebarItem
    
    var body: some View {
        List(SidebarItem.allCases, selection: $selectedTab) { item in
            NavigationLink(value: item) {
                HStack(spacing: 12) {
                    Image(systemName: item.systemImage)
                        .foregroundColor(.accentColor)
                        .frame(width: 20)
                    
                    VStack(alignment: .leading, spacing: 2) {
                        Text(item.title)
                            .font(.body)
                            .fontWeight(.medium)
                        
                        Text(item.description)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                    
                    Spacer()
                }
                .padding(.vertical, 2)
            }
        }
        .navigationTitle("Features")
        .listStyle(.sidebar)
    }
}

#Preview {
    NavigationSplitView {
        SidebarView(selectedTab: .constant(.transcribe))
    } detail: {
        Text("Detail View")
    }
    .frame(width: 800, height: 600)
}