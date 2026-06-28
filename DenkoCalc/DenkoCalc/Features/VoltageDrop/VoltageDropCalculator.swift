import Foundation

/// 電圧降下計算ロジック（銅電線）。
///
/// 単相2線：e = 35.6 × L × I ÷ (1000 × A)
/// 三相3線：e = 30.8 × L × I ÷ (1000 × A)
/// 単相3線：簡易計算として単相2線と同じ式を使用（画面側で注記を表示する）
///
/// L: こう長 m / I: 電流 A / A: ケーブル断面積 sq(mm²)
enum VoltageDropCalculator {

    struct Result {
        let dropVoltage: Double   // 電圧降下 V
        let dropRate: Double      // 電圧降下率 %
        let endVoltage: Double    // 末端電圧 V
        let judgment: Judgment    // 許容率との判定
    }

    /// 相線式ごとの係数
    private static func coefficient(for system: PhaseSystem) -> Double {
        switch system {
        case .singlePhase2: return 35.6
        case .singlePhase3: return 35.6   // 簡易：単相2線と同式（注記表示）
        case .threePhase3:  return 30.8
        }
    }

    /// 電圧降下を計算する。
    /// - Parameters:
    ///   - allowableRate: 許容電圧降下率 %
    static func calculate(
        system: PhaseSystem,
        voltage: Double,
        current: Double,
        lengthM: Double,
        sizeSq: Double,
        allowableRate: Double
    ) -> Result {
        let k = coefficient(for: system)
        // 0除算ガード（断面積0なら降下0扱い）
        let drop = sizeSq == 0 ? 0 : (k * lengthM * current) / (1000.0 * sizeSq)
        let rate = voltage == 0 ? 0 : drop / voltage * 100.0
        let endVoltage = voltage - drop
        // 許容率以下ならOK、超えたらNG
        let judgment: Judgment = (rate <= allowableRate) ? .ok : .ng
        return Result(dropVoltage: drop, dropRate: rate, endVoltage: endVoltage, judgment: judgment)
    }
}
