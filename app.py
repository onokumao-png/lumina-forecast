"""
LuminaTech 受注予測モデル
電気工事・太陽光パネル設置の受注確率を予測するStreamlitアプリ
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# 会社所在地（横浜本社）
# ─────────────────────────────────────────
COMPANY_LAT = 35.4437
COMPANY_LON = 139.6380
COMPANY_NAME = "LuminaTech 横浜本社"

# ─────────────────────────────────────────
# ページ設定
# ─────────────────────────────────────────
st.set_page_config(
    page_title="LuminaTech 受注予測モデル",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ LuminaTech 受注予測モデル")
st.caption("電気工事・太陽光パネル設置の受注確率・売上予測ダッシュボード")

# ─────────────────────────────────────────
# サンプルデータ生成
# ─────────────────────────────────────────

def generate_sample_data(n: int = 300) -> pd.DataFrame:
    """
    電気工事・太陽光案件らしいリアルなサンプルデータを生成する。
    実際のCSVがない場合の代替データとして使用。
    """
    np.random.seed(42)

    # 見積提出日（2022年1月〜2024年12月）
    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")
    dates = pd.to_datetime(
        np.random.randint(start.value, end.value, size=n)
    )

    # 工事種別
    categories = np.random.choice(
        ["電気工事", "太陽光", "その他"],
        size=n,
        p=[0.45, 0.40, 0.15],
    )

    # エリア
    areas = np.random.choice(
        ["東京", "神奈川", "その他"],
        size=n,
        p=[0.40, 0.35, 0.25],
    )

    # 見積金額（カテゴリ別に現実的な金額レンジを設定）
    amounts = []
    for cat in categories:
        if cat == "電気工事":
            amounts.append(int(np.random.lognormal(13.5, 0.6)))  # 50万〜500万円程度
        elif cat == "太陽光":
            amounts.append(int(np.random.lognormal(14.2, 0.5)))  # 100万〜800万円程度
        else:
            amounts.append(int(np.random.lognormal(12.8, 0.7)))  # 30万〜200万円程度

    # 受注確率のロジック（金額・カテゴリ・エリアに依存）
    results = []
    for cat, area, amt in zip(categories, areas, amounts):
        prob = 0.50  # ベース確率

        # カテゴリ補正
        if cat == "太陽光":
            prob += 0.10
        elif cat == "電気工事":
            prob += 0.05

        # エリア補正
        if area == "東京":
            prob += 0.08
        elif area == "神奈川":
            prob += 0.05

        # 金額補正（高すぎると失注しやすい）
        if amt > 5_000_000:
            prob -= 0.15
        elif amt < 500_000:
            prob -= 0.05

        prob = np.clip(prob, 0.1, 0.9)
        results.append(np.random.binomial(1, prob))

    # エリアごとの代表都市座標と都市名
    other_cities = [
        (35.6050, 140.1233, "千葉市"),
        (35.8617, 139.6455, "さいたま市"),
        (34.9757, 138.3827, "静岡市"),
        (35.3628, 138.7307, "甲府市"),
        (36.3912, 139.0608, "前橋市"),
        (36.5657, 136.6565, "金沢市"),
        (35.9056, 139.3797, "熊谷市"),
        (35.0116, 135.7681, "京都市"),
        (34.6937, 135.5023, "大阪市"),
        (35.1815, 136.9066, "名古屋市"),
    ]

    lats, lons, cities = [], [], []
    for area in areas:
        if area == "東京":
            lat = 35.6812 + np.random.normal(0, 0.06)
            lon = 139.7671 + np.random.normal(0, 0.07)
            cities.append("東京都")
        elif area == "神奈川":
            lat = 35.4478 + np.random.normal(0, 0.07)
            lon = 139.6425 + np.random.normal(0, 0.07)
            cities.append("神奈川県")
        else:
            city = other_cities[np.random.randint(len(other_cities))]
            lat = city[0] + np.random.normal(0, 0.12)
            lon = city[1] + np.random.normal(0, 0.12)
            cities.append(city[2])
        lats.append(lat)
        lons.append(lon)

    df = pd.DataFrame({
        "date": dates,
        "amount": amounts,
        "category": categories,
        "area": areas,
        "city": cities,
        "result": results,
        "lat": lats,
        "lon": lons,
    })
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ─────────────────────────────────────────
# 特徴量エンジニアリング
# ─────────────────────────────────────────

def prepare_features(df: pd.DataFrame):
    """
    モデル学習用の特徴量を作成する。
    カテゴリ変数をラベルエンコーディングし、数値特徴量と結合する。
    """
    df = df.copy()

    # カテゴリ・エリアをラベルエンコード
    le_cat = LabelEncoder()
    le_area = LabelEncoder()
    df["category_enc"] = le_cat.fit_transform(df["category"])
    df["area_enc"] = le_area.fit_transform(df["area"])

    # 月・四半期を特徴量として追加（季節性を捉える）
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter

    # 特徴量リスト
    feature_cols = ["amount", "category_enc", "area_enc", "month", "quarter"]
    X = df[feature_cols]
    y = df["result"]

    return X, y, le_cat, le_area, feature_cols


# ─────────────────────────────────────────
# モデル学習
# ─────────────────────────────────────────

@st.cache_resource
def train_model(df: pd.DataFrame, model_type: str):
    """
    受注予測モデルを学習し、評価指標とともに返す。
    st.cache_resource でキャッシュして再実行を抑制。
    """
    X, y, le_cat, le_area, feature_cols = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    if model_type == "ランダムフォレスト":
        model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
        scaler = None  # ランダムフォレストはスケーリング不要
        model.fit(X_train, y_train)
    else:
        # ロジスティック回帰はスケーリングが必要
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        model = LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
        model.fit(X_train_s, y_train)
        X_test = X_test_s  # 評価用に置き換え

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "auc": roc_auc_score(y_test, y_prob),
        "report": classification_report(y_test, y_pred, target_names=["失注", "受注"]),
    }

    return model, scaler, le_cat, le_area, feature_cols, metrics


# ─────────────────────────────────────────
# サイドバー：データ読み込み設定
# ─────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ 設定")

    # データソース選択
    data_source = st.radio(
        "データソース",
        ["サンプルデータを使用", "CSVをアップロード"],
    )

    if data_source == "CSVをアップロード":
        uploaded = st.file_uploader(
            "CSVファイルを選択",
            type=["csv"],
            help="date, amount, category, area, result の列が必要です",
        )
        if uploaded:
            df_raw = pd.read_csv(uploaded, parse_dates=["date"])
            st.success(f"✅ {len(df_raw)} 件読み込み完了")
        else:
            st.info("CSVがアップロードされるまでサンプルデータを表示します")
            df_raw = generate_sample_data()
    else:
        df_raw = generate_sample_data()
        st.info("サンプルデータ（300件）を使用中")

    st.divider()

    # モデル選択
    model_type = st.selectbox(
        "予測モデル",
        ["ランダムフォレスト", "ロジスティック回帰"],
        help="ランダムフォレストは精度重視、ロジスティック回帰は解釈性重視",
    )

    st.divider()
    st.caption("LuminaTech 受注予測システム v1.0")

# ─────────────────────────────────────────
# タブ構成
# ─────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 ダッシュボード",
    "🤖 モデル評価",
    "🔮 受注確率予測",
    "📋 データ確認",
    "🧠 エージェント",
    "🔬 ディープリサーチ",
])

# ─────────────────────────────────────────
# タブ1: ダッシュボード（グラフ表示）
# ─────────────────────────────────────────

with tab1:
    st.subheader("📊 受注データ概要")

    # KPI指標
    total = len(df_raw)
    won = df_raw["result"].sum()
    win_rate = won / total * 100
    total_revenue = df_raw[df_raw["result"] == 1]["amount"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総案件数", f"{total:,} 件")
    col2.metric("受注件数", f"{won:,} 件")
    col3.metric("受注率", f"{win_rate:.1f} %")
    col4.metric("受注総額", f"¥{total_revenue:,.0f}")

    st.divider()

    # ─── 地図: 会社 → 受注現場 アーク表示 ───────────────────────────
    st.subheader("🗾 受注マップ — 会社から現場への光線")

    map_filter = st.radio(
        "表示する案件",
        ["受注のみ", "失注のみ", "すべて"],
        horizontal=True,
    )

    df_map = df_raw.copy()
    if map_filter == "受注のみ":
        df_map = df_map[df_map["result"] == 1]
    elif map_filter == "失注のみ":
        df_map = df_map[df_map["result"] == 0]

    # 色設定（受注=青、失注=オレンジ）
    df_map["color"] = df_map["result"].map({1: "royalblue", 0: "orangered"})
    df_map["label"] = df_map["result"].map({1: "受注✅", 0: "失注❌"})
    df_map["tooltip"] = df_map.apply(
        lambda r: f"{r['label']}<br>{r['city']} / {r['category']}<br>¥{r['amount']:,}",
        axis=1,
    )

    fig_map = go.Figure()

    # 会社→現場のライン
    for _, row in df_map.iterrows():
        fig_map.add_trace(go.Scattermapbox(
            lon=[COMPANY_LON, row["lon"]],
            lat=[COMPANY_LAT, row["lat"]],
            mode="lines",
            line=dict(width=1.5, color=row["color"]),
            opacity=0.45,
            showlegend=False,
            hoverinfo="skip",
        ))

    # 現場マーカー
    fig_map.add_trace(go.Scattermapbox(
        lon=df_map["lon"],
        lat=df_map["lat"],
        mode="markers",
        marker=dict(size=8, color=df_map["color"], opacity=0.85),
        text=df_map["tooltip"],
        hovertemplate="%{text}<extra></extra>",
        showlegend=False,
    ))

    # 会社マーカー
    fig_map.add_trace(go.Scattermapbox(
        lon=[COMPANY_LON],
        lat=[COMPANY_LAT],
        mode="markers+text",
        marker=dict(size=18, color="gold"),
        text=["🏢 LuminaTech"],
        textposition="top right",
        hovertemplate="LuminaTech 横浜本社<extra></extra>",
        showlegend=False,
    ))

    fig_map.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=36.5, lon=138.5),
            zoom=5.2,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=520,
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig_map, use_container_width=True, config={"scrollZoom": True})

    col_leg1, col_leg2, col_leg3 = st.columns(3)
    col_leg1.info(f"🏢 会社: {COMPANY_NAME}")
    col_leg2.success(f"🔵 受注案件: {(df_raw['result']==1).sum()} 件")
    col_leg3.error(f"🟠 失注案件: {(df_raw['result']==0).sum()} 件")

    st.divider()

    # グラフ1: 月別受注額の推移
    st.subheader("📈 月別受注額の推移")

    df_won = df_raw[df_raw["result"] == 1].copy()
    df_won["year_month"] = df_won["date"].dt.to_period("M").astype(str)
    monthly = df_won.groupby("year_month")["amount"].sum().reset_index()
    monthly.columns = ["年月", "受注額"]

    fig_monthly = px.bar(
        monthly,
        x="年月",
        y="受注額",
        title="月別受注額（円）",
        color_discrete_sequence=["#1f77b4"],
        labels={"受注額": "受注額（円）"},
    )
    fig_monthly.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig_monthly, use_container_width=True)

    col_left, col_right = st.columns(2)

    # グラフ2: 工事種別の受注率
    with col_left:
        st.subheader("🏗️ 工事種別の受注率")
        cat_stats = df_raw.groupby("category").agg(
            total=("result", "count"),
            won=("result", "sum"),
        ).reset_index()
        cat_stats["受注率(%)"] = (cat_stats["won"] / cat_stats["total"] * 100).round(1)

        fig_cat = px.bar(
            cat_stats,
            x="category",
            y="受注率(%)",
            color="category",
            text="受注率(%)",
            title="工事種別ごとの受注率",
            labels={"category": "工事種別"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_cat.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_cat.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig_cat, use_container_width=True)

        # 詳細テーブル
        st.dataframe(
            cat_stats.rename(columns={"category": "種別", "total": "総件数", "won": "受注件数"}),
            use_container_width=True,
            hide_index=True,
        )

    # グラフ3: エリア別の受注率
    with col_right:
        st.subheader("📍 エリア別の受注率")
        area_stats = df_raw.groupby("area").agg(
            total=("result", "count"),
            won=("result", "sum"),
        ).reset_index()
        area_stats["受注率(%)"] = (area_stats["won"] / area_stats["total"] * 100).round(1)

        fig_area = px.bar(
            area_stats,
            x="area",
            y="受注率(%)",
            color="area",
            text="受注率(%)",
            title="エリアごとの受注率",
            labels={"area": "エリア"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_area.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_area.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig_area, use_container_width=True)

        # 詳細テーブル
        st.dataframe(
            area_stats.rename(columns={"area": "エリア", "total": "総件数", "won": "受注件数"}),
            use_container_width=True,
            hide_index=True,
        )

    # グラフ4: 工事種別×エリアのヒートマップ
    st.subheader("🗺️ 工事種別 × エリア 受注率ヒートマップ")
    pivot = df_raw.groupby(["category", "area"])["result"].mean().unstack(fill_value=0) * 100
    fig_heat = px.imshow(
        pivot,
        text_auto=".1f",
        color_continuous_scale="Blues",
        title="受注率 (%) ヒートマップ",
        labels={"x": "エリア", "y": "工事種別", "color": "受注率(%)"},
        aspect="auto",
    )
    fig_heat.update_layout(height=350)
    st.plotly_chart(fig_heat, use_container_width=True)

    # グラフ5: 見積金額分布と受注/失注
    st.subheader("💰 見積金額の分布（受注 vs 失注）")
    df_plot = df_raw.copy()
    df_plot["結果"] = df_plot["result"].map({1: "受注", 0: "失注"})
    fig_box = px.box(
        df_plot,
        x="category",
        y="amount",
        color="結果",
        title="工事種別ごとの見積金額分布",
        labels={"category": "工事種別", "amount": "見積金額（円）"},
        color_discrete_map={"受注": "#2196F3", "失注": "#FF7043"},
    )
    fig_box.update_layout(height=400)
    st.plotly_chart(fig_box, use_container_width=True)


# ─────────────────────────────────────────
# タブ2: モデル評価
# ─────────────────────────────────────────

with tab2:
    st.subheader("🤖 予測モデルの評価")

    # モデル学習
    with st.spinner("モデルを学習中..."):
        model, scaler, le_cat, le_area, feature_cols, metrics = train_model(df_raw, model_type)

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("正解率 (Accuracy)", f"{metrics['accuracy']:.3f}")
    col_m2.metric("AUC スコア", f"{metrics['auc']:.3f}")

    st.subheader("分類レポート")
    st.code(metrics["report"], language="text")

    # 特徴量重要度（ランダムフォレストのみ）
    if model_type == "ランダムフォレスト":
        st.subheader("📌 特徴量重要度")
        importance_df = pd.DataFrame({
            "特徴量": ["見積金額", "工事種別", "エリア", "月", "四半期"],
            "重要度": model.feature_importances_,
        }).sort_values("重要度", ascending=True)

        fig_imp = px.bar(
            importance_df,
            x="重要度",
            y="特徴量",
            orientation="h",
            title="受注予測に影響する要因の重要度",
            color="重要度",
            color_continuous_scale="Blues",
        )
        fig_imp.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_imp, use_container_width=True)

    elif model_type == "ロジスティック回帰":
        # ロジスティック回帰の係数を可視化
        st.subheader("📌 各特徴量の係数（ロジスティック回帰）")
        coef_df = pd.DataFrame({
            "特徴量": ["見積金額", "工事種別", "エリア", "月", "四半期"],
            "係数": model.coef_[0],
        }).sort_values("係数", ascending=True)

        fig_coef = px.bar(
            coef_df,
            x="係数",
            y="特徴量",
            orientation="h",
            title="正の係数＝受注に有利、負の係数＝受注に不利",
            color="係数",
            color_continuous_scale="RdBu",
            color_continuous_midpoint=0,
        )
        fig_coef.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_coef, use_container_width=True)


# ─────────────────────────────────────────
# タブ3: 新規案件の受注確率予測フォーム
# ─────────────────────────────────────────

with tab3:
    st.subheader("🔮 新規案件の受注確率を予測する")
    st.caption("案件情報を入力すると、AIが受注確率を算出します。")

    # モデルが未学習なら学習する
    if "model" not in dir():
        with st.spinner("モデルを準備中..."):
            model, scaler, le_cat, le_area, feature_cols, metrics = train_model(df_raw, model_type)

    with st.form("prediction_form"):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            input_date = st.date_input(
                "見積提出日",
                value=pd.Timestamp.today(),
                help="見積を提出する（した）日付",
            )
            input_amount = st.number_input(
                "見積金額（円）",
                min_value=100_000,
                max_value=50_000_000,
                value=3_000_000,
                step=100_000,
                format="%d",
                help="税抜きの見積金額を入力してください",
            )

        with col_f2:
            input_category = st.selectbox(
                "工事種別",
                options=["電気工事", "太陽光", "その他"],
            )
            input_area = st.selectbox(
                "エリア",
                options=["東京", "神奈川", "その他"],
            )

        submitted = st.form_submit_button("🔍 受注確率を予測する", use_container_width=True)

    if submitted:
        try:
            # 入力値をモデル用に変換
            input_month = pd.Timestamp(input_date).month
            input_quarter = (input_month - 1) // 3 + 1

            # カテゴリをエンコード（学習済みラベルに存在しない値は最近傍として扱う）
            cat_classes = list(le_cat.classes_)
            area_classes = list(le_area.classes_)
            cat_enc = cat_classes.index(input_category) if input_category in cat_classes else 0
            area_enc = area_classes.index(input_area) if input_area in area_classes else 0

            X_input = pd.DataFrame([{
                "amount": input_amount,
                "category_enc": cat_enc,
                "area_enc": area_enc,
                "month": input_month,
                "quarter": input_quarter,
            }])

            # ロジスティック回帰はスケーリングが必要
            if model_type == "ロジスティック回帰" and scaler is not None:
                X_input_scaled = scaler.transform(X_input)
                prob = model.predict_proba(X_input_scaled)[0][1]
            else:
                prob = model.predict_proba(X_input)[0][1]

            # 結果表示
            st.divider()
            col_r1, col_r2 = st.columns([1, 2])

            with col_r1:
                # 受注確率のゲージ表示
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=prob * 100,
                    title={"text": "受注確率 (%)"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#1f77b4"},
                        "steps": [
                            {"range": [0, 33], "color": "#ffcccc"},
                            {"range": [33, 66], "color": "#fff3cd"},
                            {"range": [66, 100], "color": "#d4edda"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": 50,
                        },
                    },
                    number={"suffix": "%", "font": {"size": 40}},
                ))
                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)

            with col_r2:
                st.markdown("### 予測結果")

                if prob >= 0.70:
                    st.success(f"✅ **受注見込み大** — 受注確率: **{prob*100:.1f}%**")
                    st.markdown("この案件は受注の可能性が高いです。積極的にフォローアップしましょう。")
                elif prob >= 0.50:
                    st.warning(f"⚠️ **受注見込み中** — 受注確率: **{prob*100:.1f}%**")
                    st.markdown("受注の可能性はありますが、競合との差別化や価格調整が鍵になります。")
                else:
                    st.error(f"❌ **受注見込み小** — 受注確率: **{prob*100:.1f}%**")
                    st.markdown("失注リスクが高めです。追加の提案や価格見直しを検討してください。")

                st.markdown("---")
                st.markdown("**入力内容のまとめ**")
                st.dataframe(pd.DataFrame({
                    "項目": ["見積提出日", "見積金額", "工事種別", "エリア"],
                    "値": [
                        str(input_date),
                        f"¥{input_amount:,}",
                        input_category,
                        input_area,
                    ],
                }), hide_index=True, use_container_width=True)

        except Exception as e:
            st.error(f"予測エラーが発生しました: {e}")
            st.info("入力値を確認し、再度お試しください。")


# ─────────────────────────────────────────
# タブ4: データ確認
# ─────────────────────────────────────────

with tab4:
    st.subheader("📋 読み込みデータの確認")

    col_d1, col_d2 = st.columns(2)
    col_d1.metric("総レコード数", f"{len(df_raw):,} 件")
    col_d2.metric("期間", f"{df_raw['date'].min().date()} 〜 {df_raw['date'].max().date()}")

    # フィルタ
    filter_cat = st.multiselect(
        "工事種別でフィルタ",
        options=df_raw["category"].unique().tolist(),
        default=df_raw["category"].unique().tolist(),
    )
    df_filtered = df_raw[df_raw["category"].isin(filter_cat)]

    # 表示（lat/lon は表示しない）
    df_display = df_filtered[["date", "amount", "category", "area", "result"]].copy()
    df_display["result"] = df_display["result"].map({1: "✅ 受注", 0: "❌ 失注"})
    df_display["amount"] = df_display["amount"].apply(lambda x: f"¥{x:,}")
    df_display.columns = ["見積日", "見積金額", "工事種別", "エリア", "受注結果"]

    st.dataframe(df_display, use_container_width=True, height=400)

    # CSV ダウンロード
    csv_data = df_raw.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 データをCSVでダウンロード",
        data=csv_data,
        file_name="lumina_data.csv",
        mime="text/csv",
    )

    # データ統計
    st.subheader("📐 基本統計量")
    st.dataframe(
        df_raw[["amount"]].describe().map(lambda x: f"{x:,.0f}"),
        use_container_width=True,
    )


# ─────────────────────────────────────────
# タブ5: エージェント
# ─────────────────────────────────────────

with tab5:
    st.subheader("🧠 AIエージェント（受注分析アシスタント）")
    st.caption("データに基づいて受注傾向・改善提案を自然言語で質問できます。")

    # チャット履歴の初期化
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = [
            {"role": "assistant", "content": (
                "こんにちは！LuminaTech 受注分析アシスタントです。\n\n"
                "例えば以下のような質問ができます：\n"
                "- 受注率が高い工事種別を教えて\n"
                "- 今月の受注傾向は？\n"
                "- 見積金額と受注率の関係は？"
            )}
        ]

    # チャット履歴を表示
    for msg in st.session_state.agent_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ユーザー入力
    if prompt := st.chat_input("受注データについて質問してください..."):
        st.session_state.agent_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # データを要約してコンテキストを作成
        total = len(df_raw)
        win_rate = df_raw["result"].mean() * 100
        avg_amount = df_raw["amount"].mean()
        top_cat = df_raw.groupby("category")["result"].mean().idxmax()
        top_area = df_raw.groupby("area")["result"].mean().idxmax()

        context = (
            f"【現在のデータ概要】\n"
            f"- 総レコード数: {total:,}件\n"
            f"- 全体受注率: {win_rate:.1f}%\n"
            f"- 平均見積金額: ¥{avg_amount:,.0f}\n"
            f"- 受注率トップ工事種別: {top_cat}\n"
            f"- 受注率トップエリア: {top_area}\n"
        )

        # 簡易ルールベース回答（API不要）
        answer = _agent_answer(prompt, context, df_raw)

        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.agent_messages.append({"role": "assistant", "content": answer})

    # 会話リセット
    if st.button("🔄 会話をリセット", key="reset_chat"):
        st.session_state.agent_messages = []
        st.rerun()


def _agent_answer(prompt: str, context: str, df) -> str:
    """
    ルールベースの簡易エージェント回答。
    API連携なしでデータから直接回答を生成する。
    """
    p = prompt.lower()

    win_rate = df["result"].mean() * 100
    cat_rates = df.groupby("category")["result"].mean().sort_values(ascending=False)
    area_rates = df.groupby("area")["result"].mean().sort_values(ascending=False)
    monthly = df.groupby(df["date"].dt.to_period("M"))["result"].mean() * 100

    if any(k in p for k in ["工事種別", "種別", "カテゴリ", "category"]):
        lines = "\n".join([f"- {c}: {r*100:.1f}%" for c, r in cat_rates.items()])
        return f"**工事種別ごとの受注率**\n\n{lines}\n\n最も高いのは **{cat_rates.index[0]}** です。"

    if any(k in p for k in ["エリア", "地域", "area"]):
        lines = "\n".join([f"- {a}: {r*100:.1f}%" for a, r in area_rates.items()])
        return f"**エリアごとの受注率**\n\n{lines}\n\n最も高いのは **{area_rates.index[0]}** です。"

    if any(k in p for k in ["金額", "見積", "amount", "価格"]):
        low = df[df["amount"] < df["amount"].median()]["result"].mean() * 100
        high = df[df["amount"] >= df["amount"].median()]["result"].mean() * 100
        return (
            f"**見積金額と受注率の関係**\n\n"
            f"- 中央値未満: {low:.1f}%\n"
            f"- 中央値以上: {high:.1f}%\n\n"
            f"{'低価格帯' if low > high else '高価格帯'}の方が受注率が高い傾向にあります。"
        )

    if any(k in p for k in ["今月", "傾向", "最近", "トレンド"]):
        recent = monthly.tail(3)
        lines = "\n".join([f"- {str(p)}: {v:.1f}%" for p, v in recent.items()])
        return f"**直近3ヶ月の受注率推移**\n\n{lines}"

    if any(k in p for k in ["改善", "提案", "アドバイス", "おすすめ"]):
        best_cat = cat_rates.index[0]
        worst_cat = cat_rates.index[-1]
        best_area = area_rates.index[0]
        return (
            f"**受注率改善の提案**\n\n"
            f"1. **{best_cat}** への注力 — 受注率 {cat_rates.iloc[0]*100:.1f}% と最高です。\n"
            f"2. **{best_area}** エリアへの集中 — 受注率が高いエリアです。\n"
            f"3. **{worst_cat}** の見直し — 受注率 {cat_rates.iloc[-1]*100:.1f}% と改善余地があります。"
        )

    # デフォルト: 概要を返す
    return (
        f"現在のデータ概要をお伝えします。\n\n{context}\n\n"
        "もう少し具体的な質問（工事種別・エリア・金額・改善提案など）をいただけると詳しく回答できます。"
    )


# ─────────────────────────────────────────
# タブ6: ディープリサーチ（多次元深掘り分析）
# ─────────────────────────────────────────

def _amount_tier(amount: float) -> str:
    """見積金額を 5 段階のティアに分類する。"""
    if amount < 500_000:
        return "①〜50万"
    if amount < 1_500_000:
        return "②50〜150万"
    if amount < 3_500_000:
        return "③150〜350万"
    if amount < 7_000_000:
        return "④350〜700万"
    return "⑤700万〜"


def _generate_insights(df: pd.DataFrame) -> list[str]:
    """
    データから主要なインサイトを自動抽出する。
    エグゼクティブサマリーとして箇条書きで返す。
    """
    insights: list[str] = []

    overall = df["result"].mean() * 100

    # 1) 工事種別の勝ち負け
    cat_rates = df.groupby("category")["result"].mean() * 100
    cat_best, cat_worst = cat_rates.idxmax(), cat_rates.idxmin()
    gap = cat_rates.max() - cat_rates.min()
    insights.append(
        f"**工事種別の差は {gap:.1f}pt** — {cat_best} が {cat_rates.max():.1f}% で最高、"
        f"{cat_worst} が {cat_rates.min():.1f}% で最低。"
    )

    # 2) エリアの勝ち負け
    area_rates = df.groupby("area")["result"].mean() * 100
    area_best = area_rates.idxmax()
    insights.append(
        f"**エリア別では {area_best} が最強** — 受注率 {area_rates.max():.1f}% "
        f"(全体平均 {overall:.1f}% を {area_rates.max() - overall:+.1f}pt 上回る)。"
    )

    # 3) 金額帯による傾向
    tier_rates = df.assign(tier=df["amount"].map(_amount_tier)).groupby("tier")["result"].mean() * 100
    tier_best = tier_rates.idxmax()
    insights.append(
        f"**金額帯ベストは {tier_best}** — 受注率 {tier_rates.max():.1f}%。"
        f"案件規模と受注率の相関を考慮した戦略が有効。"
    )

    # 4) 直近トレンド（最新3ヶ月 vs その前3ヶ月）
    monthly = df.groupby(df["date"].dt.to_period("M"))["result"].mean() * 100
    if len(monthly) >= 6:
        recent = monthly.tail(3).mean()
        prev = monthly.tail(6).head(3).mean()
        delta = recent - prev
        arrow = "📈 上昇" if delta > 1 else ("📉 下降" if delta < -1 else "➡️ 横ばい")
        insights.append(
            f"**直近トレンドは {arrow}** — 最新3ヶ月平均 {recent:.1f}% / 前3ヶ月 {prev:.1f}% "
            f"({delta:+.1f}pt)。"
        )

    # 5) 受注額の集中度（パレート）
    df_won = df[df["result"] == 1].sort_values("amount", ascending=False)
    if len(df_won) > 0:
        total_rev = df_won["amount"].sum()
        top20_n = max(1, int(len(df_won) * 0.2))
        top20_share = df_won.head(top20_n)["amount"].sum() / total_rev * 100
        insights.append(
            f"**売上の集中度: 上位20%案件で全体の {top20_share:.1f}%** — "
            f"{'高集中型（大型案件依存）' if top20_share > 70 else '分散型（安定収益構造）'}。"
        )

    # 6) 高金額×高勝率の機会セグメント
    cross = df.assign(tier=df["amount"].map(_amount_tier)).groupby(
        ["category", "area", "tier"]
    ).agg(n=("result", "size"), rate=("result", "mean"))
    cross = cross[cross["n"] >= 5]
    if len(cross) > 0:
        opp = cross.sort_values("rate", ascending=False).iloc[0]
        cat, area, tier = cross.sort_values("rate", ascending=False).index[0]
        insights.append(
            f"**狙い目セグメント: {cat} × {area} × {tier}** — "
            f"受注率 {opp['rate']*100:.1f}% (n={int(opp['n'])})。営業リソースの集中投下を推奨。"
        )

    return insights


with tab6:
    st.subheader("🔬 ディープリサーチ — データの多角的深掘り")
    st.caption(
        "受注データを多次元で分析し、勝ちパターン・失注リスク・狙い目セグメントを自動抽出します。"
    )

    # ── エグゼクティブサマリー（自動インサイト）────────────────
    st.markdown("### 📌 エグゼクティブサマリー")
    insights = _generate_insights(df_raw)
    for i, ins in enumerate(insights, 1):
        st.markdown(f"**{i}.** {ins}")

    st.divider()

    # ── 金額帯別パフォーマンス ──────────────────────────────
    st.markdown("### 💴 金額帯別 受注率・売上貢献")

    df_tier = df_raw.copy()
    df_tier["金額帯"] = df_tier["amount"].map(_amount_tier)
    tier_order = ["①〜50万", "②50〜150万", "③150〜350万", "④350〜700万", "⑤700万〜"]

    tier_stats = df_tier.groupby("金額帯").agg(
        案件数=("result", "size"),
        受注件数=("result", "sum"),
        平均金額=("amount", "mean"),
    ).reindex(tier_order).fillna(0)
    tier_stats["受注率(%)"] = (tier_stats["受注件数"] / tier_stats["案件数"].replace(0, np.nan) * 100).round(1)
    tier_stats["受注売上"] = df_tier[df_tier["result"] == 1].groupby("金額帯")["amount"].sum().reindex(tier_order).fillna(0)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        fig_tier_rate = px.bar(
            tier_stats.reset_index(),
            x="金額帯",
            y="受注率(%)",
            text="受注率(%)",
            title="金額帯別の受注率",
            color="受注率(%)",
            color_continuous_scale="Viridis",
        )
        fig_tier_rate.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_tier_rate.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_tier_rate, use_container_width=True)
    with col_t2:
        fig_tier_rev = px.bar(
            tier_stats.reset_index(),
            x="金額帯",
            y="受注売上",
            title="金額帯別の受注売上（円）",
            color="受注売上",
            color_continuous_scale="Plasma",
        )
        fig_tier_rev.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_tier_rev, use_container_width=True)

    st.dataframe(
        tier_stats.reset_index().assign(
            平均金額=lambda d: d["平均金額"].apply(lambda x: f"¥{x:,.0f}"),
            受注売上=lambda d: d["受注売上"].apply(lambda x: f"¥{x:,.0f}"),
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ── 多次元クロス分析 ───────────────────────────────────
    st.markdown("### 🧩 多次元クロス分析（カテゴリ × エリア × 金額帯）")

    metric_choice = st.radio(
        "表示する指標",
        ["受注率", "案件数", "受注売上"],
        horizontal=True,
        key="dr_cross_metric",
    )

    df_cross = df_raw.copy()
    df_cross["金額帯"] = df_cross["amount"].map(_amount_tier)

    if metric_choice == "受注率":
        cross = df_cross.groupby(["category", "金額帯"])["result"].mean().unstack().reindex(columns=tier_order) * 100
        color_scale, fmt, title_suffix = "Blues", ".1f", "(%)"
    elif metric_choice == "案件数":
        cross = df_cross.groupby(["category", "金額帯"])["result"].size().unstack().reindex(columns=tier_order)
        color_scale, fmt, title_suffix = "Greens", ".0f", "(件)"
    else:
        cross = df_cross[df_cross["result"] == 1].groupby(["category", "金額帯"])["amount"].sum().unstack().reindex(columns=tier_order)
        color_scale, fmt, title_suffix = "Oranges", ".0f", "(円)"

    fig_cross = px.imshow(
        cross,
        text_auto=fmt,
        color_continuous_scale=color_scale,
        title=f"カテゴリ × 金額帯 {metric_choice} {title_suffix}",
        aspect="auto",
        labels={"x": "金額帯", "y": "工事種別", "color": metric_choice},
    )
    fig_cross.update_layout(height=380)
    st.plotly_chart(fig_cross, use_container_width=True)

    # サンキー図: カテゴリ → エリア → 結果
    st.markdown("#### 🌊 案件の流れ（カテゴリ → エリア → 結果）")
    sankey_df = df_raw.copy()
    sankey_df["結果"] = sankey_df["result"].map({1: "受注", 0: "失注"})

    cats = sankey_df["category"].unique().tolist()
    areas_list = sankey_df["area"].unique().tolist()
    results_list = ["受注", "失注"]
    nodes = cats + areas_list + results_list
    node_idx = {name: i for i, name in enumerate(nodes)}

    flow1 = sankey_df.groupby(["category", "area"]).size().reset_index(name="value")
    flow2 = sankey_df.groupby(["area", "結果"]).size().reset_index(name="value")

    sources = [node_idx[c] for c in flow1["category"]] + [node_idx[a] for a in flow2["area"]]
    targets = [node_idx[a] for a in flow1["area"]] + [node_idx[r] for r in flow2["結果"]]
    values = flow1["value"].tolist() + flow2["value"].tolist()

    fig_sankey = go.Figure(go.Sankey(
        node=dict(
            label=nodes,
            pad=15,
            thickness=18,
            color=["#4C78A8"] * len(cats) + ["#72B7B2"] * len(areas_list) + ["#54A24B", "#E45756"],
        ),
        link=dict(source=sources, target=targets, value=values),
    ))
    fig_sankey.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_sankey, use_container_width=True)

    st.divider()

    # ── 季節性分析 ─────────────────────────────────────────
    st.markdown("### 🗓️ 季節性ヒートマップ（年 × 月）")

    df_season = df_raw.copy()
    df_season["年"] = df_season["date"].dt.year
    df_season["月"] = df_season["date"].dt.month

    season_metric = st.radio(
        "指標を選択",
        ["受注率", "案件数"],
        horizontal=True,
        key="dr_season_metric",
    )
    if season_metric == "受注率":
        season_pivot = df_season.groupby(["年", "月"])["result"].mean().unstack(fill_value=np.nan) * 100
        season_scale, season_fmt = "RdYlGn", ".1f"
    else:
        season_pivot = df_season.groupby(["年", "月"])["result"].size().unstack(fill_value=0)
        season_scale, season_fmt = "Blues", ".0f"

    season_pivot = season_pivot.reindex(columns=range(1, 13))
    fig_season = px.imshow(
        season_pivot,
        text_auto=season_fmt,
        color_continuous_scale=season_scale,
        title=f"年 × 月の {season_metric}",
        aspect="auto",
        labels={"x": "月", "y": "年", "color": season_metric},
    )
    fig_season.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=[f"{m}月" for m in range(1, 13)])
    fig_season.update_layout(height=320)
    st.plotly_chart(fig_season, use_container_width=True)

    # 月次推移＋3ヶ月移動平均
    st.markdown("#### 📉 月次受注率の推移と3ヶ月移動平均")
    monthly_full = df_raw.groupby(df_raw["date"].dt.to_period("M")).agg(
        受注率=("result", lambda s: s.mean() * 100),
        案件数=("result", "size"),
    ).reset_index()
    monthly_full["年月"] = monthly_full["date"].astype(str)
    monthly_full["3MA"] = monthly_full["受注率"].rolling(3, min_periods=1).mean()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=monthly_full["年月"],
        y=monthly_full["案件数"],
        name="案件数",
        marker_color="lightsteelblue",
        yaxis="y2",
        opacity=0.6,
    ))
    fig_trend.add_trace(go.Scatter(
        x=monthly_full["年月"],
        y=monthly_full["受注率"],
        name="月次受注率(%)",
        mode="lines+markers",
        line=dict(color="#1f77b4", width=2),
    ))
    fig_trend.add_trace(go.Scatter(
        x=monthly_full["年月"],
        y=monthly_full["3MA"],
        name="3ヶ月移動平均",
        mode="lines",
        line=dict(color="crimson", width=3, dash="dash"),
    ))
    fig_trend.update_layout(
        yaxis=dict(title="受注率 (%)"),
        yaxis2=dict(title="案件数", overlaying="y", side="right", showgrid=False),
        xaxis=dict(tickangle=-45),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # ── 失注リスク要因分析 ──────────────────────────────────
    st.markdown("### ⚠️ 失注リスク要因の分析")

    lost = df_raw[df_raw["result"] == 0]
    won = df_raw[df_raw["result"] == 1]

    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("失注件数", f"{len(lost):,} 件")
    col_r2.metric(
        "失注平均金額",
        f"¥{lost['amount'].mean():,.0f}" if len(lost) else "—",
        delta=f"{(lost['amount'].mean() - won['amount'].mean()):+,.0f} 円 vs 受注" if len(lost) and len(won) else None,
    )
    col_r3.metric(
        "想定逸失売上",
        f"¥{lost['amount'].sum():,.0f}" if len(lost) else "—",
        help="失注した案件の見積金額合計（仮に全件受注した場合の理論上の上限）",
    )

    # セグメント別の失注率ランキング
    seg = df_raw.copy()
    seg["金額帯"] = seg["amount"].map(_amount_tier)
    seg_stats = seg.groupby(["category", "area", "金額帯"]).agg(
        n=("result", "size"),
        loss_rate=("result", lambda s: (1 - s.mean()) * 100),
    ).reset_index()
    seg_stats = seg_stats[seg_stats["n"] >= 5].sort_values("loss_rate", ascending=False)

    st.markdown("#### 🚨 失注率が高いセグメント TOP10（n≥5）")
    if len(seg_stats) > 0:
        top_loss = seg_stats.head(10).copy()
        top_loss["失注率"] = top_loss["loss_rate"].map(lambda x: f"{x:.1f}%")
        st.dataframe(
            top_loss.rename(columns={
                "category": "工事種別",
                "area": "エリア",
                "n": "案件数",
            })[["工事種別", "エリア", "金額帯", "案件数", "失注率"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("サンプル数が足りないため、セグメント別の集計をスキップしました。")

    # 受注 vs 失注 の金額分布
    st.markdown("#### 💵 受注 vs 失注 の金額分布")
    df_dist = df_raw.copy()
    df_dist["結果"] = df_dist["result"].map({1: "受注", 0: "失注"})
    fig_dist = px.violin(
        df_dist,
        x="結果",
        y="amount",
        color="結果",
        box=True,
        points="all",
        title="受注／失注ごとの見積金額分布（バイオリン図）",
        labels={"amount": "見積金額（円）"},
        color_discrete_map={"受注": "#2196F3", "失注": "#FF7043"},
    )
    fig_dist.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig_dist, use_container_width=True)

    st.divider()

    # ── アクションレコメンド ────────────────────────────────
    st.markdown("### 🎯 データドリブンなアクション提案")

    cat_rates_full = df_raw.groupby("category")["result"].mean() * 100
    area_rates_full = df_raw.groupby("area")["result"].mean() * 100
    tier_rates_full = df_raw.assign(t=df_raw["amount"].map(_amount_tier)).groupby("t")["result"].mean() * 100

    rec_best_cat = cat_rates_full.idxmax()
    rec_worst_cat = cat_rates_full.idxmin()
    rec_best_area = area_rates_full.idxmax()
    rec_best_tier = tier_rates_full.idxmax()

    # 機会金額の試算: 最良セグメントの受注率を全体に適用した場合の追加売上
    best_rate = cat_rates_full.max() / 100
    current_rate = df_raw["result"].mean()
    avg_amount = df_raw["amount"].mean()
    uplift_potential = (best_rate - current_rate) * len(df_raw) * avg_amount

    st.success(
        f"#### 💡 重点施策\n\n"
        f"1. **{rec_best_cat}** を主力商材として営業ポートフォリオを再構成 "
        f"(受注率 {cat_rates_full.max():.1f}%)\n"
        f"2. **{rec_best_area}** エリアの案件発掘を強化 "
        f"(受注率 {area_rates_full.max():.1f}%)\n"
        f"3. **{rec_best_tier}** の価格帯にスイートスポットあり — 提案金額の最適化を検討\n"
        f"4. **{rec_worst_cat}** は受注率 {cat_rates_full.min():.1f}% — 撤退 or 抜本的見直しを判断\n"
    )

    st.info(
        f"#### 📊 機会試算\n\n"
        f"現在の全体受注率 **{current_rate*100:.1f}%** を最良カテゴリ水準 **{best_rate*100:.1f}%** まで引き上げた場合、"
        f"理論上の追加売上ポテンシャル: **¥{uplift_potential:,.0f}**\n\n"
        f"※ 平均見積金額 ¥{avg_amount:,.0f} × 全案件 {len(df_raw):,} 件 × 受注率改善幅で算出した参考値。"
    )
