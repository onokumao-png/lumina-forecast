# 電工電卓 (DenkoCalc)

電気工事の現場で使う計算を、スマホで素早く行うための iOS アプリ（MVP）。

- iPhone 向け / SwiftUI / オフライン動作
- ダークモード対応・大きい文字・大きいボタン
- 結果は OK（緑）/ NG（赤）で色分け、注意は黄色系
- 全角数字入力にも対応（入力確定時に半角へ正規化）

## 開く方法

`DenkoCalc.xcodeproj` を Xcode 16 以降で開いてそのままビルド・実行できます。
（プロジェクトは File System Synchronized Group を使用しているため、
`DenkoCalc/` 配下に追加した Swift ファイルは自動的にターゲットへ含まれます。）

- 最小デプロイ：iOS 17.0
- 署名：Automatic（実機実行時はご自身の Team を設定してください）

## 画面（下部タブ 5 つ）

1. **電力** … 単相/三相の kW・kVA・A を計算（A→kW / kW→A の逆算対応）
2. **電圧降下** … 35.6 / 30.8 係数で電圧降下・降下率・末端電圧、OK/NG 判定
3. **接地** … A/B/C/D 種の基準値と測定値の OK/NG 判定、根拠メモ
4. **管占積** … 管内径・ケーブル外径（仮データ）から最小管サイズを推奨
5. **早見表** … CV 各サイズの許容電流（仮データ）

## ディレクトリ構成（MVVM に近い構造）

```
DenkoCalc/
├── DenkoCalcApp.swift        # エントリポイント
├── ContentView.swift         # 下部タブ
├── Assets.xcassets           # AccentColor / AppIcon
├── Models/                   # 共通モデル（相線式・判定）
├── Shared/
│   ├── Theme/                # 色・フォント・レイアウト定義
│   ├── Utils/                # 全角→半角正規化など
│   └── Components/           # カード・数値入力・OK/NG バッジ等
└── Features/                 # 機能ごとに分割（計算ロジックは別ファイル）
    ├── Power/                # Calculator / ViewModel / View
    ├── VoltageDrop/
    ├── Grounding/
    ├── Conduit/              # + ConduitData（管・ケーブルデータ）
    └── Ampacity/             # + AmpacityData（許容電流表）
```

## 仮データについて

以下は **仮データ**（コメントに「仮データ」と明記）です。後から正確な規格値・
メーカー資料へ差し替えやすいよう、データはテーブルとして分離しています。

- 電線管の内径（`ConduitData.swift`）
- ケーブル外径（`ConduitData.swift`）
- CV 許容電流（`AmpacityData.swift`）

## 将来の Pro 版を見据えた設計

機能ごとにフォルダ／ファイルを分離しているため、以下の追加が容易です。
PDF 出力 / 計算履歴 / お気に入り / AI 相談 / 太陽光 PCS 計算 /
高圧受変電計算 / 圧着端子選定 / 端子締付トルク表 / ブレーカー選定。

## 注意

> 本アプリの計算結果は参考値です。実施工・設計・申請では、最新の法令、
> 内線規程、メーカー資料、電力会社協議内容を必ず確認してください。
