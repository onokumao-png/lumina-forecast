import Foundation
import SwiftUI

/// 接地計算画面のViewModel。
@MainActor
final class GroundingViewModel: ObservableObject {

    // MARK: - 入力
    @Published var type: GroundingType = .typeD
    @Published var measuredText: String = ""
    @Published var groundFaultCurrentText: String = ""  // B種用 Ig
    @Published var fastBreak: Bool = false               // 0.5秒以内遮断あり

    // MARK: - 結果
    @Published var result: GroundingCalculator.Result?

    /// B種のとき1線地絡電流の入力欄を表示
    var showsGroundFaultCurrent: Bool { type == .typeB }
    /// C/D種のとき遮断条件トグルを表示
    var showsFastBreakToggle: Bool { type.allowsFastBreakRelief }

    func calculate() {
        result = GroundingCalculator.calculate(
            type: type,
            measured: measuredText.asDouble ?? 0,
            groundFaultCurrent: groundFaultCurrentText.asDouble ?? 0,
            fastBreak: fastBreak
        )
    }
}
