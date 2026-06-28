import SwiftUI

/// 4. 電線管占積率画面
struct ConduitView: View {
    @StateObject private var vm = ConduitViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    inputCard
                    resultCard
                    DisclaimerText()
                }
                .padding(16)
            }
            .background(AppTheme.screenBackground)
            .navigationTitle("電線管占積率")
            .scrollDismissesKeyboard(.interactively)
        }
    }

    private var inputCard: some View {
        SectionCard("入力") {
            // 管種
            labeledPicker("管種", selection: $vm.conduitType) {
                ForEach(ConduitType.allCases) { Text($0.rawValue).tag($0) }
            }

            // ケーブル種類
            labeledPicker("ケーブル種類", selection: $vm.cableType) {
                ForEach(CableType.allCases) { Text($0.rawValue).tag($0) }
            }

            // サイズ（一覧から選択）
            VStack(alignment: .leading, spacing: 6) {
                Text("サイズ").font(AppTheme.inputLabelFont).foregroundStyle(.secondary)
                Picker("サイズ", selection: $vm.cableSizeSq) {
                    ForEach(vm.availableSizes, id: \.self) { size in
                        Text("\(size.sqString) sq").tag(size)
                    }
                }
                .pickerStyle(.menu)
                .frame(maxWidth: .infinity, alignment: .leading)
            }

            NumberInputField(label: "本数", unit: "本", text: $vm.countText)

            // 占積率
            VStack(alignment: .leading, spacing: 6) {
                Text("占積率").font(AppTheme.inputLabelFont).foregroundStyle(.secondary)
                Picker("占積率", selection: $vm.fillRate) {
                    Text("32%").tag(0.32)
                    Text("48%").tag(0.48)
                }
                .pickerStyle(.segmented)
            }

            Button(action: vm.calculate) {
                Text("計算する")
                    .font(.system(size: 20, weight: .bold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
            }
            .buttonStyle(.borderedProminent)
        }
    }

    @ViewBuilder
    private var resultCard: some View {
        if let r = vm.result {
            SectionCard("結果") {
                JudgmentBadge(judgment: r.judgment)

                if let size = r.recommendedSize {
                    ResultValueRow(label: "推奨管サイズ", value: "\(size.nominal)", unit: vm.conduitType.rawValue, emphasized: true)
                    Divider()
                    ResultValueRow(label: "占積率", value: r.fillRatePercent.formatted(decimals: 1), unit: "%")
                } else {
                    Text("選択した管種では収まりません。サイズ・本数・占積率を見直してください。")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundStyle(AppTheme.ng)
                }

                Divider()
                ResultValueRow(label: "ケーブル合計断面積", value: r.totalCableAreaMM2.formatted(decimals: 1), unit: "mm²")

                CautionText(message: "管内径・ケーブル外径はいずれも仮データです。実設計ではメーカー資料・規格値を確認してください。")
            }
        }
    }

    // 共通の見出し付きセグメントPicker
    private func labeledPicker<SelectionValue: Hashable, Content: View>(
        _ title: String,
        selection: Binding<SelectionValue>,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title).font(AppTheme.inputLabelFont).foregroundStyle(.secondary)
            Picker(title, selection: selection, content: content)
                .pickerStyle(.segmented)
        }
    }
}

#Preview {
    ConduitView()
}
