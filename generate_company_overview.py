"""
株式会社LuminaTech 会社概要書 PDF ジェネレーター

reportlab の組み込み日本語CIDフォント（HeiseiKakuGo-W5 / HeiseiMin-W3）を使用し、
外部フォントファイルなしで日本語PDFを生成する。

実行:
    python generate_company_overview.py
出力:
    company_overview.pdf
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ─────────────────────────────────────────
# フォント登録（組み込みCIDフォント。外部ファイル不要）
# ─────────────────────────────────────────
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))  # ゴシック
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))     # 明朝

GOTHIC = "HeiseiKakuGo-W5"
MINCHO = "HeiseiMin-W3"

# ブランドカラー
NAVY = colors.HexColor("#0B2A4A")
BLUE = colors.HexColor("#1f77b4")
GOLD = colors.HexColor("#E0A800")
LIGHT = colors.HexColor("#EAF2FA")
GRAY = colors.HexColor("#5A6B7B")

COMPANY = "株式会社LuminaTech"
OUTPUT = "company_overview.pdf"


# ─────────────────────────────────────────
# スタイル定義
# ─────────────────────────────────────────
def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "CoverTitle", fontName=GOTHIC, fontSize=34, leading=44,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "CoverSub", fontName=MINCHO, fontSize=15, leading=22,
        textColor=GRAY, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "CoverDoc", fontName=GOTHIC, fontSize=20, leading=28,
        textColor=GOLD, alignment=TA_CENTER, spaceBefore=30,
    ))
    styles.add(ParagraphStyle(
        "SectionHead", fontName=GOTHIC, fontSize=15, leading=20,
        textColor=colors.white, leftIndent=4,
    ))
    styles.add(ParagraphStyle(
        "Body", fontName=MINCHO, fontSize=10.5, leading=18,
        textColor=colors.HexColor("#1a1a1a"),
    ))
    styles.add(ParagraphStyle(
        "BodyG", fontName=GOTHIC, fontSize=10.5, leading=18,
        textColor=colors.HexColor("#1a1a1a"),
    ))
    styles.add(ParagraphStyle(
        "Cell", fontName=MINCHO, fontSize=10, leading=15,
        textColor=colors.HexColor("#1a1a1a"),
    ))
    styles.add(ParagraphStyle(
        "CellHead", fontName=GOTHIC, fontSize=10, leading=15,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        "KpiNum", fontName=GOTHIC, fontSize=22, leading=24,
        textColor=BLUE, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "KpiLabel", fontName=GOTHIC, fontSize=9, leading=12,
        textColor=GRAY, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "Footer", fontName=MINCHO, fontSize=8, leading=10,
        textColor=GRAY, alignment=TA_CENTER,
    ))
    return styles


# ─────────────────────────────────────────
# セクション見出し（帯）
# ─────────────────────────────────────────
def section(title, styles):
    t = Table([[Paragraph(title, styles["SectionHead"])]],
              colWidths=[170 * mm], rowHeights=[9 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBEFORE", (0, 0), (0, 0), 4, GOLD),
    ]))
    return t


# ─────────────────────────────────────────
# ページ装飾（ヘッダ/フッタ）
# ─────────────────────────────────────────
def cover_bg(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 70 * mm, w, 70 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, h - 72 * mm, w, 2 * mm, fill=1, stroke=0)
    # 下部の光のモチーフ
    canvas.setFillColor(LIGHT)
    canvas.rect(0, 0, w, 28 * mm, fill=1, stroke=0)
    # 上部ネイビー帯の中央にロゴ的なテキストマーク
    canvas.setFillColor(GOLD)
    canvas.setFont(GOTHIC, 22)
    canvas.drawCentredString(w / 2, h - 42 * mm, "L U M I N A T E C H")
    canvas.setFillColor(colors.HexColor("#9DB6CE"))
    canvas.setFont(MINCHO, 11)
    canvas.drawCentredString(w / 2, h - 52 * mm,
                             "Electrical  /  Solar  /  AI Forecast")
    canvas.restoreState()


def content_bg(canvas, doc):
    canvas.saveState()
    w, h = A4
    # ヘッダライン
    canvas.setFillColor(NAVY)
    canvas.setFont(GOTHIC, 9)
    canvas.drawString(20 * mm, h - 12 * mm, COMPANY)
    canvas.setFillColor(GOLD)
    canvas.setLineWidth(1)
    canvas.setStrokeColor(GOLD)
    canvas.line(20 * mm, h - 14 * mm, w - 20 * mm, h - 14 * mm)
    # フッタ
    canvas.setStrokeColor(colors.HexColor("#cccccc"))
    canvas.line(20 * mm, 15 * mm, w - 20 * mm, 15 * mm)
    canvas.setFillColor(GRAY)
    canvas.setFont(MINCHO, 8)
    canvas.drawString(20 * mm, 10 * mm, f"{COMPANY}  会社概要書")
    canvas.drawRightString(w - 20 * mm, 10 * mm, f"- {doc.page} -")
    canvas.restoreState()


# ─────────────────────────────────────────
# コンテンツ生成
# ─────────────────────────────────────────
def build_story(styles):
    story = []

    # ===== 表紙 =====
    story.append(Spacer(1, 78 * mm))
    story.append(Paragraph("LuminaTech", styles["CoverTitle"]))
    story.append(Paragraph("株式会社ルミナテック", styles["CoverSub"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "電気工事・太陽光発電 &times; AIで、地域の未来を照らす。",
        styles["CoverSub"]))
    story.append(Paragraph("会社概要書", styles["CoverDoc"]))
    story.append(Spacer(1, 24 * mm))
    story.append(Paragraph("COMPANY PROFILE", ParagraphStyle(
        "cp", parent=styles["CoverSub"], fontName=GOTHIC, fontSize=11,
        textColor=GRAY)))
    story.append(Paragraph("2026", ParagraphStyle(
        "yr", parent=styles["CoverSub"], fontSize=12, textColor=NAVY)))

    story.append(NextPageTemplate("content"))
    story.append(PageBreak())

    # ===== 経営理念 =====
    story.append(section("経営理念 &mdash; Our Mission", styles))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(
        "「ひかりで、暮らしと産業をつなぐ。」", ParagraphStyle(
            "mission", parent=styles["BodyG"], fontSize=15, leading=24,
            textColor=NAVY, alignment=TA_CENTER)))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "私たちLuminaTechは、確かな電気工事の技術と再生可能エネルギーの普及を通じて、"
        "安全で持続可能な社会の実現に貢献します。さらに、長年の現場で蓄積した受注・施工データを"
        "AIで解析し、データドリブンな経営判断と高品質なサービスの両立を追求しています。",
        styles["Body"]))
    story.append(Spacer(1, 7 * mm))

    # ===== 会社概要 =====
    story.append(section("会社概要 &mdash; Company Profile", styles))
    story.append(Spacer(1, 5 * mm))

    def row(k, v):
        return [Paragraph(k, styles["CellHead"]), Paragraph(v, styles["Cell"])]

    profile = [
        row("商号", "株式会社LuminaTech（ルミナテック）"),
        row("英文社名", "LuminaTech Inc."),
        row("設立", "2015年4月"),
        row("資本金", "5,000万円"),
        row("代表者", "代表取締役社長　小野 熊男"),
        row("従業員数", "48名（2026年6月現在）"),
        row("本社所在地", "〒220-0011　神奈川県横浜市西区高島2丁目（横浜本社）"),
        row("事業所", "横浜本社／東京オフィス"),
        row("主要エリア", "東京都・神奈川県を中心とした関東一円"),
        row("事業内容", "電気工事業／太陽光発電システムの設計・施工・保守／"
                      "AI受注予測システムの開発・運用"),
        row("許認可", "電気工事業者登録／建設業許可（電気工事業）"),
        row("取引銀行", "横浜銀行／みずほ銀行"),
    ]
    pt = Table(profile, colWidths=[38 * mm, 132 * mm])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8e3")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(pt)
    story.append(Spacer(1, 7 * mm))

    # ===== 事業内容 =====
    def biz(title, desc):
        head = Paragraph(title, ParagraphStyle(
            "bh", parent=styles["BodyG"], fontSize=11.5, textColor=NAVY))
        body = Paragraph(desc, styles["Body"])
        cell = Table([[head], [body]], colWidths=[80 * mm])
        cell.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (0, 0), 8),
            ("BOTTOMPADDING", (0, 1), (0, 1), 8),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFD")),
            ("LINEABOVE", (0, 0), (-1, 0), 3, GOLD),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8e3")),
        ]))
        return cell

    b1 = biz("01　電気工事事業",
             "住宅・店舗・工場・公共施設における屋内外電気設備の設計・施工・保守を行います。"
             "受配電設備、照明・コンセント工事、LED化改修まで幅広く対応します。")
    b2 = biz("02　太陽光発電事業",
             "戸建住宅から産業用まで、太陽光発電システムの設計・施工・メンテナンスをワンストップで提供。"
             "蓄電池連携やZEH対応など、脱炭素ニーズにお応えします。")
    b3 = biz("03　AI受注予測事業",
             "自社開発の受注予測ダッシュボード「Lumina Forecast」を活用し、見積案件の受注確率を"
             "機械学習で算定。営業戦略の最適化と高い受注率を実現します。")
    b4 = biz("04　保守・アフターサービス",
             "施工後の定期点検・遠隔監視・緊急対応まで、長期にわたり設備の安定稼働を支援します。"
             "お客様の安心を第一に、継続的なサポートを提供します。")

    biz_table = Table([[b1, b2], [b3, b4]], colWidths=[85 * mm, 85 * mm])
    biz_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 5),
        ("TOPPADDING", (0, 0), (-1, 0), 0),
        ("TOPPADDING", (0, 1), (-1, 1), 6),
    ]))
    story.append(KeepTogether([
        section("事業内容 &mdash; Our Business", styles),
        Spacer(1, 5 * mm),
        biz_table,
    ]))

    story.append(PageBreak())

    # ===== 強み・テクノロジー =====
    story.append(section("私たちの強み &mdash; Strengths", styles))
    story.append(Spacer(1, 5 * mm))
    strengths = [
        ("確かな施工品質", "有資格者を中心とした技術者集団。電気工事から太陽光まで一貫対応。"),
        ("データドリブン経営", "受注・施工データをAIで解析し、精度の高い受注予測と営業最適化を実現。"),
        ("地域密着", "横浜本社を起点に、東京・神奈川を中心とした迅速なフットワーク。"),
        ("脱炭素への貢献", "再生可能エネルギーの普及を通じ、地域のカーボンニュートラルを推進。"),
    ]
    for title, desc in strengths:
        story.append(Paragraph(
            f"&#9679; <b>{title}</b>　{desc}", styles["Body"]))
        story.append(Spacer(1, 2 * mm))
    story.append(Spacer(1, 5 * mm))

    # ===== 実績データ =====
    story.append(section("実績ハイライト &mdash; Performance", styles))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(
        "自社受注予測システム「Lumina Forecast」で管理する案件データに基づく主要指標（一例）。",
        styles["Body"]))
    story.append(Spacer(1, 4 * mm))

    def kpi(num, label):
        c = Table([[Paragraph(num, styles["KpiNum"])],
                   [Paragraph(label, styles["KpiLabel"])]],
                  colWidths=[40 * mm], rowHeights=[14 * mm, 9 * mm])
        c.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8e3")),
            ("LINEABOVE", (0, 0), (-1, 0), 3, BLUE),
        ]))
        return c

    kpis = Table([[
        kpi("300+", "年間管理案件数"),
        kpi("60%+", "平均受注率"),
        kpi("3 領域", "電気・太陽光・他"),
        kpi("2 拠点", "横浜・東京"),
    ]], colWidths=[42.5 * mm] * 4)
    kpis.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(kpis)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "※ 上記は社内サンプルデータに基づく参考値であり、実績を保証するものではありません。",
        ParagraphStyle("note", parent=styles["Body"], fontSize=8,
                       textColor=GRAY)))
    story.append(Spacer(1, 6 * mm))

    # ===== 沿革 =====
    story.append(section("沿革 &mdash; History", styles))
    story.append(Spacer(1, 5 * mm))
    history = [
        [Paragraph("2015年", styles["CellHead"]),
         Paragraph("横浜市にて株式会社LuminaTechを設立。電気工事業を開始。", styles["Cell"])],
        [Paragraph("2018年", styles["CellHead"]),
         Paragraph("太陽光発電システム事業に本格参入。", styles["Cell"])],
        [Paragraph("2021年", styles["CellHead"]),
         Paragraph("東京オフィスを開設し、関東一円へ事業エリアを拡大。", styles["Cell"])],
        [Paragraph("2024年", styles["CellHead"]),
         Paragraph("AI受注予測システム「Lumina Forecast」を自社開発・運用開始。", styles["Cell"])],
        [Paragraph("2026年", styles["CellHead"]),
         Paragraph("データ活用を軸とした次世代エネルギーソリューションへ進化中。", styles["Cell"])],
    ]
    ht = Table(history, colWidths=[24 * mm, 146 * mm])
    ht.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe6ee")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (0, 0), (0, -1), BLUE),
    ]))
    story.append(ht)
    story.append(Spacer(1, 6 * mm))

    # ===== お問い合わせ =====
    story.append(section("お問い合わせ &mdash; Contact", styles))
    story.append(Spacer(1, 5 * mm))
    contact = Table([[Paragraph(
        f"<b>{COMPANY}</b><br/>"
        "〒220-0011　神奈川県横浜市西区高島2丁目（横浜本社）<br/>"
        "TEL: 045-XXX-XXXX　／　FAX: 045-XXX-XXXX<br/>"
        "Email: info@luminatech.example.jp<br/>"
        "Web: https://www.luminatech.example.jp",
        ParagraphStyle("contact", parent=styles["Body"], leading=20))]],
        colWidths=[170 * mm])
    contact.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8e3")),
        ("LINEBEFORE", (0, 0), (0, 0), 4, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(contact)
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "本書に記載の情報は本資料作成時点のものです。社名・所在地・連絡先等は"
        "サンプル値を含みます。", styles["Footer"]))

    return story


def main():
    styles = build_styles()
    doc = BaseDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=22 * mm,
        title=f"{COMPANY} 会社概要書", author=COMPANY,
    )
    frame_cover = Frame(0, 0, A4[0], A4[1], id="cover",
                        leftPadding=20 * mm, rightPadding=20 * mm,
                        topPadding=20 * mm, bottomPadding=20 * mm)
    frame_content = Frame(doc.leftMargin, doc.bottomMargin,
                          doc.width, doc.height, id="content")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame_cover], onPage=cover_bg),
        PageTemplate(id="content", frames=[frame_content], onPage=content_bg),
    ])
    doc.build(build_story(styles))
    print(f"✅ {OUTPUT} を生成しました。")


if __name__ == "__main__":
    main()
