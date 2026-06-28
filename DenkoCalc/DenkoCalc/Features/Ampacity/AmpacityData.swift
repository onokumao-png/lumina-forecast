import Foundation

/// 許容電流早見表の1行。
struct AmpacityRow: Identifiable {
    let cableType: String   // 例：CV
    let sizeSq: Double       // 例：5.5
    let ampacityA: Double    // 許容電流 A（仮データ）
    var id: String { "\(cableType)-\(sizeSq)" }

    var sizeLabel: String {
        "\(cableType) \(sizeSq.sqString) sq"
    }
}

/// 許容電流データ。
/// ※許容電流値はすべて仮データ。後から正確な許容電流表（内線規程等）へ差し替えること。
enum AmpacityDatabase {
    static let cvTable: [AmpacityRow] = [
        AmpacityRow(cableType: "CV", sizeSq: 2,   ampacityA: 27),   // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 3.5, ampacityA: 37),   // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 5.5, ampacityA: 49),   // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 8,   ampacityA: 61),   // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 14,  ampacityA: 88),   // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 22,  ampacityA: 115),  // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 38,  ampacityA: 162),  // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 60,  ampacityA: 217),  // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 100, ampacityA: 298),  // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 150, ampacityA: 395),  // 仮データ
        AmpacityRow(cableType: "CV", sizeSq: 200, ampacityA: 469)   // 仮データ
    ]
}
