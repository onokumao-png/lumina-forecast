import Foundation

/// 相線式。電力計算・電圧降下計算で共通利用する。
enum PhaseSystem: String, CaseIterable, Identifiable {
    case singlePhase2 = "単相2線"
    case singlePhase3 = "単相3線"
    case threePhase3 = "三相3線"

    var id: String { rawValue }

    /// 三相かどうか（電力計算の√3係数判定に使用）
    var isThreePhase: Bool {
        self == .threePhase3
    }
}

/// OK / NG の判定結果。色分け表示に使う。
enum Judgment {
    case ok
    case ng

    var text: String {
        switch self {
        case .ok: return "OK"
        case .ng: return "NG"
        }
    }

    var isOK: Bool { self == .ok }
}
