import Foundation
import SwiftUI

/// 電線管占積率画面のViewModel。
@MainActor
final class ConduitViewModel: ObservableObject {

    // MARK: - 入力
    @Published var conduitType: ConduitType = .ve
    @Published var cableType: CableType = .cv {
        didSet { syncSizeForCableType() }
    }
    @Published var cableSizeSq: Double = 5.5
    @Published var countText: String = "3"
    @Published var fillRate: Double = 0.48  // 0.32 / 0.48

    // MARK: - 結果
    @Published var result: ConduitCalculator.Result?

    /// 現在のケーブル種類で選べるサイズ一覧
    var availableSizes: [Double] {
        ConduitDatabase.availableSizes(for: cableType)
    }

    /// ケーブル種類を変えたとき、サイズが一覧に無ければ先頭に合わせる
    private func syncSizeForCableType() {
        let sizes = availableSizes
        if !sizes.contains(cableSizeSq), let first = sizes.first {
            cableSizeSq = first
        }
    }

    func calculate() {
        let count = Int(countText.normalizedNumber) ?? 0
        result = ConduitCalculator.calculate(
            conduitType: conduitType,
            cableType: cableType,
            cableSizeSq: cableSizeSq,
            count: count,
            allowableFillRate: fillRate
        )
    }
}
