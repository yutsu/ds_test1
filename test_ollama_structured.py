#!/usr/bin/env python3
"""
実際のOllamaモデルで構造化レスポンスをテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import DeepResearch

def test_ollama_structured():
    """実際のOllamaモデルで構造化レスポンスをテスト"""
    print("🧪 実際のOllamaモデルで構造化レスポンステスト")
    print("=" * 60)

    try:
        # DeepResearchインスタンスを作成
        researcher = DeepResearch("ollama")

        print(f"使用モデル: {researcher.model.model_name}")
        print(f"接続先: {researcher.model.base_url}")
        print()

        # テストデータ
        original_query = "人工知能の最新動向"
        analysis = """
        2024年にAI技術が大幅に進歩した。大規模言語モデルの性能が向上し、企業導入が加速している。
        特に、生成AIの実用化が進み、多くの企業で業務効率化に活用されている。
        しかし、プライバシーやセキュリティの課題も指摘されている。
        """
        summary = "AI技術は急速に発展しているが、規制や倫理面での課題も存在する。"

        print(f"元のクエリ: {original_query}")
        print(f"分析結果: {analysis[:100]}...")
        print(f"要約: {summary}")
        print()

        # 構造化レスポンスで追加検索キーワードを生成
        print("🔍 追加検索キーワード生成中...")
        additional_queries = researcher._generate_additional_queries(
            original_query, analysis, summary
        )

        print("生成された追加検索キーワード:")
        for i, query in enumerate(additional_queries, 1):
            print(f"  {i}. {query}")

        if additional_queries:
            print(f"\n✅ 追加検索キーワードが {len(additional_queries)} 個生成されました")

            # キーワードの品質チェック
            valid_keywords = [q for q in additional_queries if len(q) >= 2]
            print(f"有効なキーワード: {len(valid_keywords)}/{len(additional_queries)}")

            # 無効なキーワードのチェック
            invalid_keywords = [q for q in additional_queries if any(invalid in q.lower() for invalid in [
                'キーワード', '追加', '提案', '以下の', '各キーワード', '番号や記号'
            ])]
            if not invalid_keywords:
                print("✅ 無効なキーワードが含まれていません")
            else:
                print(f"⚠️  無効なキーワードが含まれています: {invalid_keywords}")
        else:
            print("\n❌ 追加検索キーワードが生成されませんでした")

        # 構造化分析のテスト
        print("\n📊 構造化分析テスト...")
        from main import SearchResult

        # ダミーの検索結果を作成
        search_results = [
            SearchResult(
                title="2024年AI技術の進歩",
                url="https://example.com/ai-2024",
                snippet="2024年にAI技術が大幅に進歩した。大規模言語モデルの性能が向上し、企業導入が加速している。",
                search_query="AI技術",
                date_info="2024年",
                reliability_score=0.9,
                source_type="news"
            ),
            SearchResult(
                title="企業のAI導入状況",
                url="https://example.com/ai-adoption",
                snippet="企業導入率は60%に達し、特に製造業での活用が進んでいる。",
                search_query="AI技術",
                date_info="2024年",
                reliability_score=0.8,
                source_type="research"
            )
        ]

        analysis_result = researcher._analyze_results(original_query, search_results)
        print("生成された分析（一部）:")
        print(analysis_result[:300] + "..." if len(analysis_result) > 300 else analysis_result)

        if analysis_result:
            print(f"\n✅ 分析が正常に生成されました（{len(analysis_result)}文字）")

            # 分析内容の検証
            if "主要な事実" in analysis_result or "main_facts" in analysis_result.lower():
                print("✅ 構造化された分析形式が検出されました")
            else:
                print("⚠️  従来のテキスト形式で分析が生成されました")
        else:
            print("\n❌ 分析が生成されませんでした")

        # 構造化要約のテスト
        print("\n📝 構造化要約テスト...")
        summary_result = researcher._create_summary(original_query, analysis_result)
        print("生成された要約（一部）:")
        print(summary_result[:200] + "..." if len(summary_result) > 200 else summary_result)

        if summary_result:
            print(f"\n✅ 要約が正常に生成されました（{len(summary_result)}文字）")

            # 要約内容の検証
            if "重要な事実" in summary_result or "key_facts" in summary_result.lower():
                print("✅ 構造化された要約形式が検出されました")
            else:
                print("⚠️  従来のテキスト形式で要約が生成されました")
        else:
            print("\n❌ 要約が生成されませんでした")

        print("\n🎉 実際のOllamaモデルでのテストが完了しました！")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    print("🧪 実際のOllamaモデルで構造化レスポンステスト")
    print("=" * 60)

    # Ollamaサーバーの状態確認
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollamaサーバーが起動しています")
            models = response.json().get('models', [])
            if models:
                print(f"利用可能なモデル: {[m['name'] for m in models]}")
            else:
                print("⚠️  利用可能なモデルがありません")
        else:
            print("❌ Ollamaサーバーに接続できません")
            return
    except Exception as e:
        print(f"❌ Ollamaサーバーに接続できません: {e}")
        print("対処法: ollama serve を実行してください")
        return

    # 構造化レスポンステスト
    test_ollama_structured()

if __name__ == "__main__":
    main()
