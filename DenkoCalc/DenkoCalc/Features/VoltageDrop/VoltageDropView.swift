import SwiftUI

/// 2. 電圧降下計算画面
struct VoltageDropView: View {
    @StateObject private var vm = VoltageDropViewModel()

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
            .navigationTitle("電圧降下")
            .scrollDismissesKeyboard(.interactively)
        }
    }

    private var inputCard: some View {
        SectionCard("入力") {
            VStack(alignment: .leading, spacing: 6) {
                Text("相線式").font(AppTheme.inputLabelFont).foregroundStyle(.secondary)
                Picker("相線式", selection: $vm.system) {
                    ForEach(PhaseSystem.allCases) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)
            }

            if vm.showsSinglePhase3Note {
                CautionText(message: "単相3線は簡易計算として単相2線の式（係数35.6）を使用しています。実設計では中性線条件を確認してください。")
            }

            NumberInputField(label: "電圧", unit: "V", text: $vm.voltageText)
            NumberInputField(label: "電流", unit: "A", text: $vm.currentText)
            NumberInputField(label: "こう長", unit: "m", text: $vm.lengthText)
            NumberInputField(label: "ケーブルサイズ", unit: "sq", text: $vm.sizeText)

            // 材質（現状は銅固定）
            HStack {
                Text("材質").font(AppTheme.inputLabelFont).foregroundStyle(.secondary)
                Spacer()
                Text(vm.conductorMaterial).font(.system(size: 18, weight: .semibold))
            }

            NumberInputField(label: "許容電圧降下率", unit: "%", text: $vm.allowableRateText)

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
                ResultValueRow(label: "電圧降下", value: r.dropVoltage.formatted(decimals: 2), unit: "V", emphasized: true)
                Divider()
                ResultValueRow(label: "電圧降下率", value: r.dropRate.formatted(decimals: 2), unit: "%")
                Divider()
                ResultValueRow(label: "末端電圧", value: r.endVoltage.formatted(decimals: 1), unit: "V")

                CautionText(message: "実設計では負荷条件、配線方式、電線温度、内線規程等を確認してください。")
            }
        }
    }
}

#Preview {
    VoltageDropView()
}
