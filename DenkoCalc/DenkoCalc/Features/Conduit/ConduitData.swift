import Foundation

/// 管種
enum ConduitType: String, CaseIterable, Identifiable {
    case ve = "VE"
    case fep = "FEP"
    case g = "G管"
    var id: String { rawValue }
}

/// ケーブル種類
enum CableType: String, CaseIterable, Identifiable {
    case cv = "CV"
    case cvt = "CVT"
    case vvf = "VVF"
    var id: String { rawValue }
}

/// 1つの管サイズ（呼び径と内径）
struct ConduitSize: Identifiable {
    let nominal: Int       // 呼び（16, 22 など）
    let innerDiameterMM: Double  // 内径 mm
    var id: Int { nominal }

    /// 管内の有効断面積 mm²
    var innerAreaMM2: Double {
        let r = innerDiameterMM / 2.0
        return Double.pi * r * r
    }
}

/// 管種別データ。
/// ※内径は仮データ（代表値）。後から正確な規格値へ差し替えやすいよう、呼び→内径の表として保持する。
enum ConduitDatabase {

    /// 管種ごとの (呼び, 内径mm) 一覧。内径はいずれも仮データ。
    static func sizes(for type: ConduitType) -> [ConduitSize] {
        switch type {
        case .ve:
            // VE：仮データ（内径は呼びにおおよそ対応させた代表値）
            return [
                ConduitSize(nominal: 16, innerDiameterMM: 14.0),
                ConduitSize(nominal: 22, innerDiameterMM: 20.0),
                ConduitSize(nominal: 28, innerDiameterMM: 26.0),
                ConduitSize(nominal: 36, innerDiameterMM: 34.0),
                ConduitSize(nominal: 42, innerDiameterMM: 40.0),
                ConduitSize(nominal: 54, innerDiameterMM: 51.0),
                ConduitSize(nominal: 70, innerDiameterMM: 67.0),
                ConduitSize(nominal: 82, innerDiameterMM: 78.0)
            ]
        case .fep:
            // FEP：仮データ
            return [
                ConduitSize(nominal: 30, innerDiameterMM: 30.0),
                ConduitSize(nominal: 40, innerDiameterMM: 40.0),
                ConduitSize(nominal: 50, innerDiameterMM: 50.0),
                ConduitSize(nominal: 65, innerDiameterMM: 65.0),
                ConduitSize(nominal: 80, innerDiameterMM: 80.0),
                ConduitSize(nominal: 100, innerDiameterMM: 100.0)
            ]
        case .g:
            // G管（鋼製電線管）：仮データ
            return [
                ConduitSize(nominal: 16, innerDiameterMM: 16.5),
                ConduitSize(nominal: 22, innerDiameterMM: 21.6),
                ConduitSize(nominal: 28, innerDiameterMM: 27.6),
                ConduitSize(nominal: 36, innerDiameterMM: 35.7),
                ConduitSize(nominal: 42, innerDiameterMM: 41.9),
                ConduitSize(nominal: 54, innerDiameterMM: 53.9),
                ConduitSize(nominal: 70, innerDiameterMM: 69.9),
                ConduitSize(nominal: 82, innerDiameterMM: 81.9),
                ConduitSize(nominal: 92, innerDiameterMM: 91.9),
                ConduitSize(nominal: 104, innerDiameterMM: 103.9)
            ]
        }
    }

    /// ケーブル種類×サイズ(sq) → 仕上り外径 mm（仮データ）。
    /// ※すべて仮データ。実際はメーカーカタログの仕上り外径へ差し替えること。
    static func cableOuterDiameterMM(type: CableType, sizeSq: Double) -> Double? {
        let table: [Double: Double]
        switch type {
        case .cv:
            // CV（単心）仮データ
            table = [
                2: 7.0, 3.5: 8.0, 5.5: 9.0, 8: 10.5, 14: 12.5,
                22: 14.5, 38: 17.5, 60: 21.0, 100: 26.0, 150: 31.0, 200: 35.0
            ]
        case .cvt:
            // CVT（トリプレックス）仮データ：3本一括の外接円相当
            table = [
                2: 15.0, 3.5: 17.0, 5.5: 19.0, 8: 22.0, 14: 27.0,
                22: 31.0, 38: 38.0, 60: 45.0, 100: 56.0, 150: 67.0, 200: 76.0
            ]
        case .vvf:
            // VVF（平形・2心相当）仮データ：短径×長径の代表外径
            table = [
                1.6: 6.0, 2.0: 6.6, 2.6: 7.9
            ]
        }
        return table[sizeSq]
    }

    /// 各ケーブル種類で選択可能なサイズ一覧（仮データに対応）
    static func availableSizes(for type: CableType) -> [Double] {
        switch type {
        case .cv:  return [2, 3.5, 5.5, 8, 14, 22, 38, 60, 100, 150, 200]
        case .cvt: return [2, 3.5, 5.5, 8, 14, 22, 38, 60, 100, 150, 200]
        case .vvf: return [1.6, 2.0, 2.6]
        }
    }
}
