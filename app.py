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
    st.divider()
    st.caption("🪪 古物商許可")
    st.caption("東京都公安委員会")
    st.caption("第301032618963号")

# ─────────────────────────────────────────
# タブ構成
# ─────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 ダッシュボード",
    "🤖 モデル評価",
    "🔮 受注確率予測",
    "📋 データ確認",
    "🧠 エージェント",
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
