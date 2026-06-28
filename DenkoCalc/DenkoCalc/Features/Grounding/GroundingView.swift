import SwiftUI

/// 3. 接地計算画面
struct GroundingView: View {
    @StateObject private var vm = GroundingViewModel()

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
            .navigationTitle("接地計算")
            .scrollDismissesKeyboard(.interactively)
        }
    }

    private var inputCard: some View {
        SectionCard("入力") {
            VStack(alignment: .leading, spacing: 6) {
                Text("接地種別").font(AppTheme.inputLabelFont).foregroundStyle(.secondary)
                Picker("接地種別", selection: $vm.type) {
                    ForEach(GroundingType.allCases) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)
            }

            NumberInputField(label: "測定値", unit: "Ω", text: $vm.measuredText)

            if vm.showsGroundFaultCurrent {
                NumberInputField(label: "1線地絡電流 Ig", unit: "A", text: $vm.groundFaultCurrentText)
                CautionText(message: "B種接地抵抗値は電力会社回答の1線地絡電流を確認してください。")
            }

            if vm.showsFastBreakToggle {
                Toggle(isOn: $vm.fastBreak) {
                    Text("0.5秒以内遮断あり").font(AppTheme.inputLabelFont)
                }
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
                ResultValueRow(label: "必要接地抵抗値", value: r.requiredResistance.formatted(decimals: 1), unit: "Ω", emphasized: true)
                Divider()
                ResultValueRow(label: "測定値", value: r.measuredResistance.formatted(decimals: 1), unit: "Ω")

                // 根拠メモ
                Text(r.basis)
                    .font(.system(size: 14))
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                CautionText(message: "法令・内線規程・電力会社協議を必ず確認してください。")
            }
        }
    }
}

#Preview {
    GroundingView()
}
