import SwiftUI

/// アプリ共通のデザイン定義。
/// 現場向けに「大きい文字・大きいボタン・OK/NGを色で明示」を一元管理する。
/// 色や数値はここを変えるだけで全画面に反映される。
enum AppTheme {

    // MARK: - カラー（ライト/ダーク両対応。systemColorを基準にする）

    /// 強調色（AccentColorと揃える）
    static let accent = Color.accentColor

    /// OK（適合）= 緑
    static let ok = Color.green
    /// NG（不適合）= 赤
    static let ng = Color.red
    /// 注意 = 黄色系
    static let warning = Color.orange

    /// 結果カードの背景
    static let cardBackground = Color(.secondarySystemBackground)
    /// 画面全体の背景
    static let screenBackground = Color(.systemBackground)

    // MARK: - フォント（大きめ）

    /// 結果の主役となる特大数値
    static let resultValueFont = Font.system(size: 44, weight: .bold, design: .rounded)
    /// 結果の副次的な数値
    static let resultSubValueFont = Font.system(size: 28, weight: .semibold, design: .rounded)
    /// セクション見出し
    static let sectionTitleFont = Font.system(size: 18, weight: .bold)
    /// 入力ラベル
    static let inputLabelFont = Font.system(size: 17, weight: .medium)
    /// 注意文（小さめ）
    static let cautionFont = Font.system(size: 12, weight: .regular)

    // MARK: - レイアウト

    static let cornerRadius: CGFloat = 14
    static let cardPadding: CGFloat = 16
    static let fieldHeight: CGFloat = 52
}

/// 共通の注意文（全結果画面に小さく表示する）
enum AppText {
    static let disclaimer =
    "本アプリの計算結果は参考値です。実施工・設計・申請では、最新の法令、内線規程、メーカー資料、電力会社協議内容を必ず確認してください。"
}
