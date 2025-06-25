#!/usr/bin/env python3
"""
追加検索機能のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import DeepResearch

class MockLanguageModel:
    """テスト用のモック言語モデル"""

    def generate(self, prompt: str) -> str:
        """テスト用のダミーレスポンスを返す"""
        if "追加検索キーワード" in prompt:
            return """
市場規模 統計
AI規制 法律
倫理ガイドライン
雇用影響 調査
医療AI 応用
"""
        elif "分析" in prompt:
            return "これはテスト用の分析結果です。"
        elif "要約" in prompt:
            return "これはテスト用の要約です。"
        else:
            return "これはテスト用のレスポンスです。"

def test_additional_queries():
    """追加検索キーワード生成のテスト"""
    print("🧪 追加検索機能テスト")
    print("=" * 50)

    # テスト用のダミーデータ
    original_query = "人工知能の最新動向"
    analysis = """
    検索結果から以下の事実が確認されました：

    1. 2024年における人工知能の主要な進展
    - 大規模言語モデルの性能向上
    - マルチモーダルAIの実用化
    - 生成AIの企業導入が加速

    2. 技術的な課題
    - ハルシネーション問題
    - プライバシーとセキュリティの懸念
    - 計算リソースの大量消費

    3. 社会的影響
    - 雇用への影響
    - 教育分野での活用
    - 医療分野での応用

    検索結果からは不明な点：
    - 具体的な市場規模の数値
    - 各国の規制動向
    - 倫理的ガイドラインの詳細
    """

    summary = """
    人工知能は2024年に大きな進展を遂げ、特に大規模言語モデルと生成AIの実用化が加速しています。
    しかし、ハルシネーションやプライバシー問題などの技術的課題も存在します。
    社会的影響としては雇用への影響が懸念されていますが、教育や医療分野での活用も進んでいます。
    """

    try:
        # DeepResearchインスタンスを作成
        researcher = DeepResearch("ollama")

        # モックモデルに置き換え
        researcher.review_model = MockLanguageModel()

        print(f"元のクエリ: {original_query}")
        print(f"分析結果: {analysis[:200]}...")
        print(f"要約: {summary[:200]}...")
        print()

        # 追加検索キーワードを生成
        additional_queries = researcher._generate_additional_queries(
            original_query, analysis, summary
        )

        print("生成された追加検索キーワード:")
        for i, query in enumerate(additional_queries, 1):
            print(f"  {i}. {query}")

        if additional_queries:
            print(f"\n✅ 追加検索キーワードが {len(additional_queries)} 個生成されました")

            # 期待されるキーワードとの比較
            expected_keywords = ["市場規模", "AI規制", "倫理ガイドライン", "雇用影響", "医療AI"]
            matched = [q for q in additional_queries if any(exp in q for exp in expected_keywords)]
            print(f"期待されるキーワードとの一致: {len(matched)}/{len(expected_keywords)}")

        else:
            print("\n❌ 追加検索キーワードが生成されませんでした")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def test_date_extraction():
    """日付抽出機能のテスト"""
    print("\n📅 日付抽出機能テスト")
    print("=" * 50)

    from main import WebSearcher, Config

    config = Config()
    searcher = WebSearcher(config)

    test_cases = [
        ("2024年最新のAI技術", "2024年における人工知能の最新動向について"),
        ("2023年12月の市場動向", "2023年12月に発表された市場調査結果"),
        ("2024-01-15の発表", "2024年1月15日に開催された会議での発表内容"),
        ("2024/02/20の記事", "2024年2月20日に公開された技術記事"),
        ("3月15日のニュース", "3月15日に報道された最新ニュース"),
        ("2023年の統計", "2023年の統計データ"),
        ("日付なしのタイトル", "日付情報が含まれていないタイトル"),
    ]

    success_count = 0
    for title, snippet in test_cases:
        date_info = searcher._extract_date_info(title, snippet)
        print(f"タイトル: {title}")
        print(f"スニペット: {snippet}")
        print(f"抽出された日付: {date_info or 'なし'}")

        # 期待される結果との比較
        expected = None
        if "2024年最新" in title:
            expected = "2024年"
        elif "2023年12月" in title:
            expected = "2023年12月"
        elif "2024-01-15" in title:
            expected = "2024年1月15日"
        elif "2024/02/20" in title:
            expected = "2024年2月20日"
        elif "3月15日" in title:
            expected = "3月15日"
        elif "2023年" in title:
            expected = "2023年"

        if date_info == expected:
            print("✅ 正しく抽出されました")
            success_count += 1
        else:
            print(f"❌ 期待値: {expected}")

        print("-" * 30)

    print(f"日付抽出成功率: {success_count}/{len(test_cases)}")

def test_hallucination_prevention():
    """ハルシネーション防止機能のテスト"""
    print("\n🛡️ ハルシネーション防止機能テスト")
    print("=" * 50)

    # プロンプトにハルシネーション防止の文言が含まれているかチェック
    from main import DeepResearch

    researcher = DeepResearch("ollama")

    # 分析プロンプトのチェック
    analysis_prompt = researcher._analyze_results("テスト", [])
    if "検索結果に含まれていない情報は推測せず" in analysis_prompt:
        print("✅ 分析プロンプトにハルシネーション防止文言が含まれています")
    else:
        print("❌ 分析プロンプトにハルシネーション防止文言が含まれていません")

    # 要約プロンプトのチェック
    summary_prompt = researcher._create_summary("テスト", "テスト分析")
    if "事実のみを記載してください" in summary_prompt:
        print("✅ 要約プロンプトにハルシネーション防止文言が含まれています")
    else:
        print("❌ 要約プロンプトにハルシネーション防止文言が含まれていません")

    # 最終レポートプロンプトのチェック
    final_prompt = researcher._create_final_report("テスト", "テスト分析", "テスト要約")
    if "事実のみを記載してください" in final_prompt:
        print("✅ 最終レポートプロンプトにハルシネーション防止文言が含まれています")
    else:
        print("❌ 最終レポートプロンプトにハルシネーション防止文言が含まれていません")

def test_markdown_links():
    """マークダウンリンク機能のテスト"""
    print("\n🔗 マークダウンリンク機能テスト")
    print("=" * 50)

    from main import SearchResult, Citation, ResearchResult, DeepResearch

    # テスト用のダミーデータ
    search_results = [
        SearchResult(
            title="テスト記事1",
            url="https://example.com/article1",
            snippet="これはテスト記事1の内容です。",
            search_query="テスト",
            date_info="2024年"
        ),
        SearchResult(
            title="テスト記事2",
            url="https://example.com/article2",
            snippet="これはテスト記事2の内容です。",
            search_query="テスト",
            date_info="2023年"
        )
    ]

    citations = [
        Citation(
            source_title="テスト記事1",
            source_url="https://example.com/article1",
            content="テスト記事1の内容",
            search_query="テスト",
            relevance_score=1.0,
            date_info="2024年"
        ),
        Citation(
            source_title="テスト記事2",
            source_url="https://example.com/article2",
            content="テスト記事2の内容",
            search_query="テスト",
            relevance_score=0.8,
            date_info="2023年"
        )
    ]

    result = ResearchResult(
        query="テストクエリ",
        search_results=search_results,
        analysis="テスト分析",
        summary="テスト要約",
        citations=citations,
        additional_queries=["追加クエリ1", "追加クエリ2"],
        final_report="これは[1]に基づくテストレポートです。[2]も参考にしました。"
    )

    # DeepResearchインスタンスを作成
    researcher = DeepResearch("gemini")

    # マークダウンファイルを保存
    filename = researcher.save_to_markdown(result, "test_output.md")

    # ファイルの内容を確認
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # マークダウンリンクが正しく生成されているかチェック
    if "[テスト記事1](https://example.com/article1)" in content:
        print("✅ 検索結果のマークダウンリンクが正しく生成されています")
    else:
        print("❌ 検索結果のマークダウンリンクが生成されていません")

    if "[テスト記事1](https://example.com/article1)（2024年）" in content:
        print("✅ 引用文献のマークダウンリンクが正しく生成されています")
    else:
        print("❌ 引用文献のマークダウンリンクが生成されていません")

    if "[1](https://example.com/article1)" in content:
        print("✅ レポート内の引用リンクが正しく生成されています")
    else:
        print("❌ レポート内の引用リンクが生成されていません")

    # テストファイルを削除
    os.remove(filename)
    print("✅ テストファイルを削除しました")

def test_integrated_report():
    """統合レポート機能のテスト"""
    print("\n📋 統合レポート機能テスト")
    print("=" * 50)

    from main import DeepResearch

    researcher = DeepResearch("gemini")

    # 最終レポート生成のプロンプトをチェック
    final_prompt = researcher._create_final_report("テスト", "テスト分析", "テスト要約")

    if "統合レポート" in final_prompt:
        print("✅ 統合レポートの生成指示が含まれています")
    else:
        print("❌ 統合レポートの生成指示が含まれていません")

    if "利用可能な情報源" in final_prompt:
        print("✅ 情報源の明示が含まれています")
    else:
        print("❌ 情報源の明示が含まれていません")

    if "[1], [2] の形式" in final_prompt:
        print("✅ 引用形式の指定が含まれています")
    else:
        print("❌ 引用形式の指定が含まれていません")

def test_date_relative_analysis():
    """相対的な日付分析機能のテスト"""
    print("\n📅 相対的日付分析機能テスト")
    print("=" * 50)

    from main import DeepResearch

    researcher = DeepResearch("gemini")

    # 今日の日付を確認
    print(f"今日の日付: {researcher.today_date}")

    # 様々な日付パターンをテスト
    test_dates = [
        ("2024年1月15日", "過去の日付"),
        ("2024年12月31日", "将来の日付"),
        ("2024年", "年のみ"),
        ("3月15日", "月日のみ"),
        ("2023年12月", "年月のみ"),
        ("2024-01-15", "ハイフン区切り"),
        ("2024/01/15", "スラッシュ区切り"),
        ("", "日付なし"),
        ("不明な形式", "不明な形式"),
    ]

    for date_str, description in test_dates:
        result = researcher._parse_date_info(date_str)
        print(f"{description}: {date_str} → {result.get('relative_info', '解析失敗')}")

        if result.get('is_valid', False):
            if result.get('is_future', False):
                print(f"  → 将来の予定")
            elif result.get('is_recent', False):
                print(f"  → 最近の情報")
            else:
                print(f"  → 過去の情報")

    print("✅ 相対的日付分析機能のテスト完了")

def test_date_integration():
    """日付情報の統合テスト"""
    print("\n🔄 日付情報統合テスト")
    print("=" * 50)

    from main import DeepResearch, SearchResult

    researcher = DeepResearch("gemini")

    # テスト用の検索結果を作成
    test_results = [
        SearchResult(
            title="2024年1月発売予定の製品",
            url="https://example.com/product1",
            snippet="2024年1月に発売予定の新製品について",
            search_query="テスト",
            date_info="2024年1月15日"
        ),
        SearchResult(
            title="2024年12月の発表",
            url="https://example.com/announcement",
            snippet="2024年12月に発表予定の新技術",
            search_query="テスト",
            date_info="2024年12月31日"
        ),
        SearchResult(
            title="2023年の統計",
            url="https://example.com/stats",
            snippet="2023年の市場統計データ",
            search_query="テスト",
            date_info="2023年"
        )
    ]

    # 分析プロンプトを生成
    analysis_prompt = researcher._analyze_results("テストクエリ", test_results)

    # 今日の日付情報が含まれているかチェック
    if "今日の日付" in analysis_prompt:
        print("✅ 今日の日付情報がプロンプトに含まれています")
    else:
        print("❌ 今日の日付情報がプロンプトに含まれていません")

    # 相対的な日付情報が含まれているかチェック
    if "→" in analysis_prompt and ("日前" in analysis_prompt or "日後" in analysis_prompt or "過去の情報" in analysis_prompt or "将来の予定" in analysis_prompt):
        print("✅ 相対的な日付情報がプロンプトに含まれています")
    else:
        print("❌ 相対的な日付情報がプロンプトに含まれていません")

    # 追加検索クエリ生成のテスト
    additional_prompt = researcher._generate_additional_queries("テストクエリ", "テスト分析", "テスト要約")

    if "今日の日付" in additional_prompt:
        print("✅ 追加検索クエリ生成に今日の日付情報が含まれています")
    else:
        print("❌ 追加検索クエリ生成に今日の日付情報が含まれていません")

    if "発売予定日" in additional_prompt or "最新状況" in additional_prompt:
        print("✅ 古い情報の最新状況確認指示が含まれています")
    else:
        print("❌ 古い情報の最新状況確認指示が含まれていません")

def test_enhanced_date_extraction():
    """強化された日付抽出機能のテスト"""
    print("\n📅 強化された日付抽出機能テスト")
    print("=" * 50)

    from main import WebSearcher, Config

    searcher = WebSearcher(Config())

    test_cases = [
        # 英語形式
        ("Jan 15, 2024", "January 15, 2024の記事"),
        ("Feb 20, 2023", "February 20, 2023のニュース"),
        ("15 Mar 2024", "March 15, 2024の発表"),

        # 相対的な日付表現
        ("今日のニュース", "今日発表された最新ニュース"),
        ("昨日の記事", "昨日公開された記事"),
        ("明日の会議", "明日開催される会議"),
        ("今週の発表", "今週予定されている発表"),
        ("先週の統計", "先週発表された統計データ"),
        ("来週のイベント", "来週開催されるイベント"),
        ("今月の動向", "今月の市場動向"),
        ("先月の結果", "先月の業績結果"),
        ("来月の予定", "来月の予定"),
        ("今年の目標", "今年の目標"),
        ("去年の実績", "去年の実績"),
        ("来年の計画", "来年の計画"),
        ("3日前の発表", "3日前に発表された内容"),
        ("2週間前の記事", "2週間前に公開された記事"),
        ("1ヶ月前の統計", "1ヶ月前に発表された統計"),
        ("5年前の調査", "5年前に実施された調査"),

        # 複雑な形式
        ("2024-01-15の発表", "2024年1月15日に開催された会議での発表内容"),
        ("2024/02/20の記事", "2024年2月20日に公開された技術記事"),
        ("03-15-2024のニュース", "3月15日に報道された最新ニュース"),
        ("12/25/2023の統計", "2023年12月25日の統計データ"),
    ]

    success_count = 0
    for title, snippet in test_cases:
        extracted_date = searcher._extract_date_info(title, snippet)
        print(f"タイトル: {title}")
        print(f"スニペット: {snippet}")
        print(f"抽出された日付: {extracted_date}")
        if extracted_date:
            print("✅ 正しく抽出されました")
            success_count += 1
        else:
            print("❌ 抽出されませんでした")
        print("-" * 30)

    print(f"日付抽出成功率: {success_count}/{len(test_cases)}")

def test_academic_quality_prompts():
    """学術的品質プロンプトのテスト"""
    print("\n🎓 学術的品質プロンプトテスト")
    print("=" * 50)

    from main import DeepResearch

    researcher = DeepResearch("gemini")

    # 最終レポート生成のプロンプトをチェック
    final_prompt = researcher._create_final_report("テスト", "テスト分析", "テスト要約")

    academic_elements = [
        "時系列の正確な理解",
        "情報源の信頼性評価",
        "批判的思考と多角的分析",
        "学術的厳密性",
        "過去の事実、現在の状況、将来の予定を区別",
        "一次情報と二次情報を区別",
        "情報の偏りや限界を明記",
        "反対意見や異論も含めて検討",
        "情報の矛盾点や不確実性を明記",
        "事実と推測を明確に区別",
        "適切な引用と出典の明記",
        "論理的な構成と客観的な記述"
    ]

    found_elements = 0
    for element in academic_elements:
        if element in final_prompt:
            print(f"✅ {element} が含まれています")
            found_elements += 1
        else:
            print(f"❌ {element} が含まれていません")

    print(f"\n学術的要素の包含率: {found_elements}/{len(academic_elements)}")

def test_reliability_evaluation():
    """信頼性評価機能のテスト"""
    print("\n🔍 信頼性評価機能テスト")
    print("=" * 50)

    from main import WebSearcher, Config

    # 設定を読み込み
    config = Config()
    searcher = WebSearcher(config)

    # テストケース
    test_cases = [
        {
            "url": "https://www.nhk.or.jp/news/article1.html",
            "title": "NHKニュース: 公式発表",
            "snippet": "政府が公式に発表した内容",
            "expected_type": "news",
            "expected_min_score": 0.7
        },
        {
            "url": "https://www.gov.jp/press/2024/01/01.html",
            "title": "政府発表",
            "snippet": "政府の公式発表",
            "expected_type": "official",
            "expected_min_score": 0.8
        },
        {
            "url": "https://example.blog.com/rumor.html",
            "title": "噂話",
            "snippet": "未確認の噂話",
            "expected_type": "blog",
            "expected_min_score": 0.0
        }
    ]

    for i, case in enumerate(test_cases, 1):
        result = searcher._evaluate_source_reliability(
            case["url"], case["title"], case["snippet"]
        )

        print(f"\nテストケース {i}:")
        print(f"URL: {case['url']}")
        print(f"期待されるタイプ: {case['expected_type']}")
        print(f"実際のタイプ: {result['source_type']}")
        print(f"期待される最小スコア: {case['expected_min_score']}")
        print(f"実際のスコア: {result['reliability_score']:.2f}")

        if result['source_type'] == case['expected_type']:
            print("✅ タイプ判定: 成功")
        else:
            print("❌ タイプ判定: 失敗")

        if result['reliability_score'] >= case['expected_min_score']:
            print("✅ スコア判定: 成功")
        else:
            print("❌ スコア判定: 失敗")

def test_reliability_sorting():
    """信頼性による並び替え機能のテスト"""
    print("\n📊 信頼性並び替え機能テスト")
    print("=" * 50)

    from main import SearchResult, DeepResearch

    # テスト用の検索結果を作成
    test_results = [
        SearchResult(
            title="低信頼性記事",
            url="https://blog.example.com/low.html",
            snippet="低信頼性の内容",
            search_query="テスト",
            reliability_score=0.3,
            source_type="blog"
        ),
        SearchResult(
            title="高信頼性記事",
            url="https://www.gov.jp/high.html",
            snippet="高信頼性の内容",
            search_query="テスト",
            reliability_score=0.9,
            source_type="official"
        ),
        SearchResult(
            title="中信頼性記事",
            url="https://news.example.com/medium.html",
            snippet="中信頼性の内容",
            search_query="テスト",
            reliability_score=0.6,
            source_type="news"
        )
    ]

    # DeepResearchインスタンスを作成
    researcher = DeepResearch("gemini")

    # 並び替え前
    print("並び替え前:")
    for i, result in enumerate(test_results, 1):
        print(f"{i}. {result.title} (信頼性: {result.reliability_score:.2f})")

    # 並び替え後
    sorted_results = researcher._sort_results_by_reliability(test_results)
    print("\n並び替え後:")
    for i, result in enumerate(sorted_results, 1):
        print(f"{i}. {result.title} (信頼性: {result.reliability_score:.2f})")

    # フィルタリングテスト
    filtered_results = researcher._filter_results_by_reliability(test_results, threshold=0.5)
    print(f"\nフィルタリング後 (閾値: 0.5): {len(filtered_results)}件")
    for i, result in enumerate(filtered_results, 1):
        print(f"{i}. {result.title} (信頼性: {result.reliability_score:.2f})")

    # 検証
    if sorted_results[0].reliability_score == 0.9:
        print("✅ 並び替え機能: 成功")
    else:
        print("❌ 並び替え機能: 失敗")

    if len(filtered_results) == 2:
        print("✅ フィルタリング機能: 成功")
    else:
        print("❌ フィルタリング機能: 失敗")

if __name__ == "__main__":
    test_additional_queries()
    test_date_extraction()
    test_hallucination_prevention()
    test_markdown_links()
    test_integrated_report()
    test_date_relative_analysis()
    test_date_integration()
    test_enhanced_date_extraction()
    test_academic_quality_prompts()
    test_reliability_evaluation()
    test_reliability_sorting()
