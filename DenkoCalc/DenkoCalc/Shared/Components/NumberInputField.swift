import SwiftUI

/// 数字入力欄。
/// - 数字キーボードを優先（小数点入力可）
/// - 全角数字にも対応（フォーカスが外れたタイミングで半角へ正規化）
/// - ラベルと単位を大きく表示して片手操作しやすくする
struct NumberInputField: View {
    let label: String
    let unit: String
    @Binding var text: String

    @FocusState private var isFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(AppTheme.inputLabelFont)
                .foregroundStyle(.secondary)

            HStack(spacing: 8) {
                TextField("0", text: $text)
                    .keyboardType(.numbersAndPunctuation)
                    .font(.system(size: 24, weight: .semibold, design: .rounded))
                    .focused($isFocused)
                    .onChange(of: isFocused) { _, focused in
                        // 入力確定時に全角→半角へ正規化
                        if !focused {
                            text = text.normalizedNumber
                        }
                    }

                if !unit.isEmpty {
                    Text(unit)
                        .font(.system(size: 18, weight: .medium))
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal, 14)
            .frame(height: AppTheme.fieldHeight)
            .background(AppTheme.screenBackground)
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .stroke(isFocused ? AppTheme.accent : Color.secondary.opacity(0.3), lineWidth: 1.5)
            )
        }
    }
}
