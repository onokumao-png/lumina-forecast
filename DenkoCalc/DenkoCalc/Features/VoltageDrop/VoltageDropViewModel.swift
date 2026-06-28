import Foundation
import SwiftUI

/// 電圧降下画面のViewModel。
@MainActor
final class VoltageDropViewModel: ObservableObject {

    // MARK: - 入力
    @Published var system: PhaseSystem = .singlePhase2
    @Published var voltageText: String = ""
    @Published var currentText: String = ""
    @Published var lengthText: String = ""
    @Published var sizeText: String = ""
    @Published var allowableRateText: String = "2"  // 一般的な許容値の一例

    // 材質は現状「銅」固定（将来アルミ対応を見据えてプロパティ化）
    let conductorMaterial = "銅"

    // MARK: - 結果
    @Published var result: VoltageDropCalculator.Result?

    /// 単相3線のときに表示する注記が必要か
    var showsSinglePhase3Note: Bool {
        system == .singlePhase3
    }

    func calculate() {
        result = VoltageDropCalculator.calculate(
            system: system,
            voltage: voltageText.asDouble ?? 0,
            current: currentText.asDouble ?? 0,
            lengthM: lengthText.asDouble ?? 0,
            sizeSq: sizeText.asDouble ?? 0,
            allowableRate: allowableRateText.asDouble ?? 0
        )
    }
}
