import Foundation

extension String {
    /// 全角数字・全角記号を半角へ正規化する。
    /// 現場では全角入力されがちなので、計算前に必ず通す。
    var normalizedNumber: String {
        let mapping: [Character: Character] = [
            "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
            "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
            "．": ".", "。": ".", "、": ".", "，": ".",
            "－": "-", "ー": "-", "−": "-",
            "　": " " // 全角スペース
        ]
        return String(map { mapping[$0] ?? $0 })
            .trimmingCharacters(in: .whitespaces)
    }

    /// 全角を考慮して Double へ変換する。変換できなければ nil。
    var asDouble: Double? {
        let normalized = normalizedNumber
        guard !normalized.isEmpty else { return nil }
        return Double(normalized)
    }
}

extension Double {
    /// 小数点以下の桁数を指定して文字列化（末尾の不要なゼロは整える）。
    func formatted(decimals: Int) -> String {
        String(format: "%.\(decimals)f", self)
    }

    /// サイズ表示用。整数なら小数点なし、端数があれば小数1桁。
    var sqString: String {
        truncatingRemainder(dividingBy: 1) == 0 ? formatted(decimals: 0) : formatted(decimals: 1)
    }
}
