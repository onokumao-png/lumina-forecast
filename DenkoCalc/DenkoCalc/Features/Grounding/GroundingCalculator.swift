import Foundation

/// 接地種別
enum GroundingType: String, CaseIterable, Identifiable {
    case typeA = "A種"
    case typeB = "B種"
    case typeC = "C種"
    case typeD = "D種"
    var id: String { rawValue }

    /// B種以外で、0.5秒以内遮断の緩和（500Ω）が適用されうるか
    var allowsFastBreakRelief: Bool {
        self == .typeC || self == .typeD
    }
}

/// 接地抵抗計算ロジック。
///
/// 基準値：
/// - A種：10Ω以下
/// - C種：10Ω以下（0.5秒以内遮断ありで500Ω以下）
/// - D種：100Ω以下（0.5秒以内遮断ありで500Ω以下）
/// - B種：150 ÷ Ig Ω以下
enum GroundingCalculator {

    struct Result {
        let requiredResistance: Double   // 必要接地抵抗値 Ω
        let measuredResistance: Double   // 測定値 Ω
        let judgment: Judgment           // OK/NG
        let basis: String                // 根拠メモ
    }

    /// - Parameters:
    ///   - measured: 測定値 Ω
    ///   - groundFaultCurrent: B種用 1線地絡電流 Ig (A)
    ///   - fastBreak: 0.5秒以内遮断ありか
    static func calculate(
        type: GroundingType,
        measured: Double,
        groundFaultCurrent: Double,
        fastBreak: Bool
    ) -> Result {
        let required: Double
        let basis: String

        switch type {
        case .typeA:
            required = 10
            basis = "A種：10Ω以下"
        case .typeB:
            // B種：150 ÷ 1線地絡電流
            if groundFaultCurrent > 0 {
                required = 150.0 / groundFaultCurrent
                basis = "B種：150 ÷ Ig(\(groundFaultCurrent.formatted(decimals: 1))A) = \(required.formatted(decimals: 1))Ω以下"
            } else {
                required = 0
                basis = "B種：1線地絡電流 Ig を入力してください。"
            }
        case .typeC:
            required = fastBreak ? 500 : 10
            basis = fastBreak ? "C種：0.5秒以内遮断あり → 500Ω以下" : "C種：10Ω以下"
        case .typeD:
            required = fastBreak ? 500 : 100
            basis = fastBreak ? "D種：0.5秒以内遮断あり → 500Ω以下" : "D種：100Ω以下"
        }

        // 測定値が必要値以下ならOK
        let judgment: Judgment = (required > 0 && measured <= required) ? .ok : .ng
        return Result(
            requiredResistance: required,
            measuredResistance: measured,
            judgment: judgment,
            basis: basis
        )
    }
}
