import Foundation
import SwiftUI

/// 電力画面のViewModel（MVVM）。
/// 入力（文字列）→ 正規化 → 計算 → 結果 を担う。
@MainActor
final class PowerViewModel: ObservableObject {

    /// 計算モード（順算 / 逆算）
    enum Mode: String, CaseIterable, Identifiable {
        case powerFromCurrent = "A → kW"   // 電流から電力
        case currentFromPower = "kW → A"   // 電力から電流
        var id: String { rawValue }
    }

    // MARK: - 入力
    @Published var system: PhaseSystem = .singlePhase2
    @Published var mode: Mode = .powerFromCurrent
    @Published var voltageText: String = ""
    @Published var currentText: String = ""
    @Published var powerKWText: String = ""
    @Published var powerFactorText: String = "1.0"

    // MARK: - 結果
    @Published var result: PowerCalculator.Result?

    /// 計算実行
    func calculate() {
        let voltage = voltageText.asDouble ?? 0
        let powerFactor = powerFactorText.asDouble ?? 1.0

        switch mode {
        case .powerFromCurrent:
            let current = currentText.asDouble ?? 0
            result = PowerCalculator.powerFromCurrent(
                system: system,
                voltage: voltage,
                current: current,
                powerFactor: powerFactor
            )
        case .currentFromPower:
            let powerKW = powerKWText.asDouble ?? 0
            result = PowerCalculator.currentFromPower(
                system: system,
                powerKW: powerKW,
                voltage: voltage,
                powerFactor: powerFactor
            )
        }
    }
}
