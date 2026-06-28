import Foundation

/// 電力計算ロジック。
/// 単相：kW = V × A × 力率 ÷ 1000
/// 三相：kW = √3 × V × A × 力率 ÷ 1000
/// kVA は力率を掛けない皮相電力。
enum PowerCalculator {

    /// 計算結果（kW / kVA / A をまとめて返す）
    struct Result {
        let kW: Double
        let kVA: Double
        let current: Double  // A
    }

    /// 相線式に応じた係数（三相は√3、単相は1）
    private static func coefficient(for system: PhaseSystem) -> Double {
        system.isThreePhase ? 3.0.squareRoot() : 1.0
    }

    /// 順算：電圧・電流・力率 → kW / kVA を求める。
    /// - Parameters:
    ///   - voltage: 電圧 V
    ///   - current: 電流 A
    ///   - powerFactor: 力率 cosφ（0〜1）
    static func powerFromCurrent(
        system: PhaseSystem,
        voltage: Double,
        current: Double,
        powerFactor: Double
    ) -> Result {
        let k = coefficient(for: system)
        // 皮相電力 kVA = 係数 × V × A ÷ 1000
        let kVA = k * voltage * current / 1000.0
        // 有効電力 kW = kVA × 力率
        let kW = kVA * powerFactor
        return Result(kW: kW, kVA: kVA, current: current)
    }

    /// 逆算：kW・電圧・力率 → 電流 A を求める。
    /// A = kW × 1000 ÷ (係数 × V × 力率)
    static func currentFromPower(
        system: PhaseSystem,
        powerKW: Double,
        voltage: Double,
        powerFactor: Double
    ) -> Result {
        let k = coefficient(for: system)
        let denominator = k * voltage * powerFactor
        // 0除算ガード
        let current = denominator == 0 ? 0 : powerKW * 1000.0 / denominator
        // kVA = kW ÷ 力率（力率0は0扱い）
        let kVA = powerFactor == 0 ? 0 : powerKW / powerFactor
        return Result(kW: powerKW, kVA: kVA, current: current)
    }
}
