import SwiftUI

/// 注意文（黄色系）。各画面の補足注意に使う。
struct CautionText: View {
    let message: String

    var body: some View {
        HStack(alignment: .top, spacing: 6) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(AppTheme.warning)
            Text(message)
                .font(.system(size: 13))
                .foregroundStyle(.primary)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AppTheme.warning.opacity(0.15))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

/// 全画面共通の免責注意文（小さく表示）。
struct DisclaimerText: View {
    var body: some View {
        Text(AppText.disclaimer)
            .font(AppTheme.cautionFont)
            .foregroundStyle(.secondary)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.top, 4)
    }
}
