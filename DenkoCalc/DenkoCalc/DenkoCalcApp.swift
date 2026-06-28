import SwiftUI

/// アプリのエントリポイント。
/// 現場でのオフライン利用を前提とするため、外部依存・ネットワークは持たない。
@main
struct DenkoCalcApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
