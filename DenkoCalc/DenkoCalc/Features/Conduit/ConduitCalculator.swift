import Foundation

/// 電線管占積率の計算ロジック。
///
/// 1. ケーブル合計断面積 = 本数 × π × (外径 ÷ 2)²
/// 2. 各管サイズの「内断面積 × 占積率」がケーブル合計断面積以上なら収まる
/// 3. 収まる最小の管サイズを推奨として返す
enum ConduitCalculator {

    struct Result {
        let recommendedSize: ConduitSize?  // 推奨管サイズ（収まらなければ nil）
        let fillRatePercent: Double        // 推奨サイズでの実占積率 %
        let totalCableAreaMM2: Double      // ケーブル合計断面積
        let judgment: Judgment             // 収まれば OK、なければ NG
    }

    /// - Parameters:
    ///   - allowableFillRate: 占積率（0.32 や 0.48）
    static func calculate(
        conduitType: ConduitType,
        cableType: CableType,
        cableSizeSq: Double,
        count: Int,
        allowableFillRate: Double
    ) -> Result {
        // ケーブル1本の外径（仮データ）
        guard let outer = ConduitDatabase.cableOuterDiameterMM(type: cableType, sizeSq: cableSizeSq),
              count > 0 else {
            return Result(recommendedSize: nil, fillRatePercent: 0, totalCableAreaMM2: 0, judgment: .ng)
        }

        // ケーブル合計断面積
        let r = outer / 2.0
        let oneArea = Double.pi * r * r
        let totalArea = oneArea * Double(count)

        // 収まる最小サイズを探索（呼びの昇順）
        let sizes = ConduitDatabase.sizes(for: conduitType).sorted { $0.nominal < $1.nominal }
        for size in sizes {
            let usable = size.innerAreaMM2 * allowableFillRate
            if usable >= totalArea {
                let fill = size.innerAreaMM2 == 0 ? 0 : totalArea / size.innerAreaMM2 * 100.0
                return Result(
                    recommendedSize: size,
                    fillRatePercent: fill,
                    totalCableAreaMM2: totalArea,
                    judgment: .ok
                )
            }
        }

        // どの管にも収まらない
        return Result(recommendedSize: nil, fillRatePercent: 0, totalCableAreaMM2: totalArea, judgment: .ng)
    }
}
