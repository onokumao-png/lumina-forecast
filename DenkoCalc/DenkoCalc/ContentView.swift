import SwiftUI

/// 下部タブで5つの計算画面を切り替えるルートビュー。
/// 将来のPro版機能（履歴・お気に入り・各種計算）はタブを追加するだけで拡張できる構成。
struct ContentView: View {
    var body: some View {
        TabView {
            PowerView()
                .tabItem {
                    Label("電力", systemImage: "bolt.fill")
                }

            VoltageDropView()
                .tabItem {
                    Label("電圧降下", systemImage: "arrow.down.right.circle.fill")
                }

            GroundingView()
                .tabItem {
                    Label("接地", systemImage: "leaf.fill")
                }

            ConduitView()
                .tabItem {
                    Label("管占積", systemImage: "circle.grid.cross.fill")
                }

            AmpacityView()
                .tabItem {
                    Label("早見表", systemImage: "list.bullet.rectangle.fill")
                }
        }
        // 現場で見やすいよう、強調色を統一
        .tint(AppTheme.accent)
    }
}

#Preview {
    ContentView()
}
