import SwiftUI

/// OK/NG を大きく色分け表示するバッジ。NGは赤で強調。
struct JudgmentBadge: View {
    let judgment: Judgment

    var body: some View {
        Text(judgment.text)
            .font(.system(size: 30, weight: .heavy, design: .rounded))
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(judgment.isOK ? AppTheme.ok : AppTheme.ng)
            .clipShape(RoundedRectangle(cornerRadius: AppTheme.cornerRadius, style: .continuous))
    }
}
