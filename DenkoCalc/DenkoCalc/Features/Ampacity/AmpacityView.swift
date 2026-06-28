import SwiftUI

/// 5. 許容電流早見表画面
struct AmpacityView: View {
    private let rows = AmpacityDatabase.cvTable

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    SectionCard("CV 許容電流（仮データ）") {
                        // ヘッダ
                        HStack {
                            Text("サイズ")
                                .font(.system(size: 16, weight: .bold))
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text("許容電流")
                                .font(.system(size: 16, weight: .bold))
                                .foregroundStyle(.secondary)
                        }

                        ForEach(rows) { row in
                            Divider()
                            HStack {
                                Text(row.sizeLabel)
                                    .font(.system(size: 20, weight: .semibold))
                                Spacer()
                                Text(row.ampacityA.formatted(decimals: 0))
                                    .font(.system(size: 24, weight: .bold, design: .rounded))
                                    .monospacedDigit()
                                Text("A")
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundStyle(.secondary)
                            }
                            .padding(.vertical, 2)
                        }
                    }

                    CautionText(message: "許容電流値はすべて仮データです。施工条件（周囲温度・布設方法・条数等）により変わります。")
                    DisclaimerText()
                }
                .padding(16)
            }
            .background(AppTheme.screenBackground)
            .navigationTitle("許容電流早見表")
        }
    }
}

#Preview {
    AmpacityView()
}
