import SwiftUI

/// 1. 電力計算画面
struct PowerView: View {
    @StateObject private var vm = PowerViewModel()

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
            .navigationTitle("電力計算")
            .scrollDismissesKeyboard(.interactively)
        }
    }

    // MARK: - 入力

    private var inputCard: some View {
        SectionCard("入力") {
            // 相線式
            VStack(alignment: .leading, spacing: 6) {
                Text("相線式").font(AppTheme.inputLabelFont).foregroundStyle(.secondary)
                Picker("相線式", selection: $vm.system) {
                    ForEach(PhaseSystem.allCases) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)
            }

            // モード
            VStack(alignment: .leading, spacing: 6) {
                Text("計算モード").font(AppTheme.inputLabelFont).foregroundStyle(.secondary)
                Picker("モード", selection: $vm.mode) {
                    ForEach(PowerViewModel.Mode.allCases) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)
            }

            NumberInputField(label: "電圧", unit: "V", text: $vm.voltageText)

            // モードに応じて入力欄を切替
            if vm.mode == .powerFromCurrent {
                NumberInputField(label: "電流", unit: "A", text: $vm.currentText)
            } else {
                NumberInputField(label: "電力", unit: "kW", text: $vm.powerKWText)
            }

            NumberInputField(label: "力率 cosφ", unit: "", text: $vm.powerFactorText)

            Button(action: vm.calculate) {
                Text("計算する")
                    .font(.system(size: 20, weight: .bold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
            }
            .buttonStyle(.borderedProminent)
        }
    }

    // MARK: - 結果

    @ViewBuilder
    private var resultCard: some View {
        if let r = vm.result {
            SectionCard("結果") {
                ResultValueRow(label: "電力", value: r.kW.formatted(decimals: 2), unit: "kW", emphasized: true)
                Divider()
                ResultValueRow(label: "皮相電力", value: r.kVA.formatted(decimals: 2), unit: "kVA")
                Divider()
                ResultValueRow(label: "電流", value: r.current.formatted(decimals: 1), unit: "A")
            }
        }
    }
}

#Preview {
    PowerView()
}
