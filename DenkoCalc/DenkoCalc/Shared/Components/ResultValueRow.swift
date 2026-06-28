import SwiftUI

/// 結果の数値を大きく表示する行。主役（大）と副次（中）でサイズを切り替える。
struct ResultValueRow: View {
    let label: String
    let value: String
    let unit: String
    var emphasized: Bool = false

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(label)
                .font(.system(size: 17, weight: .medium))
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .font(emphasized ? AppTheme.resultValueFont : AppTheme.resultSubValueFont)
                .foregroundStyle(.primary)
                .monospacedDigit()
                .minimumScaleFactor(0.5)
                .lineLimit(1)
            Text(unit)
                .font(.system(size: 18, weight: .medium))
                .foregroundStyle(.secondary)
        }
    }
}
