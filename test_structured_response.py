#!/usr/bin/env python3
"""
構造化レスポンスのテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import DeepResearch, AdditionalQueriesResponse, AnalysisResponse, SummaryResponse
import json

class MockStructuredLanguageModel:
    """テスト用のモック構造化言語モデル"""

    def generate(self, prompt: str) -> str:
        """テスト用のダミーレスポンスを返す"""
        if "追加検索キーワード" in prompt or "keywords" in prompt:
            return '''
{
  "keywords": [
    "市場規模 統計",
    "AI規制 法律",
    "倫理ガイドライン",
    "雇用影響 調査",
    "医療AI 応用"
  ]
}
'''
        elif "分析" in prompt or "main_facts" in prompt:
            return '''
{
  "main_facts": [
    "2024年にAI技術が大幅に進歩した",
    "大規模言語モデルの性能が向上した",
    "企業導入が加速している"
  ],
  "data_statistics": [
    "市場規模は前年比30%増加",
    "企業導入率は60%に達した"
  ],
  "different_perspectives": [
    "技術的進歩を評価する意見",
    "雇用への影響を懸念する意見"
  ],
  "date_analysis": [
    "2024年の情報は最新",
    "2023年のデータは過去の情報"
  ],
  "unknown_points": [
    "具体的な規制内容",
    "長期的な影響の詳細"
  ]
}
'''
        elif "要約" in prompt or "key_facts" in prompt:
            return '''
{
  "key_facts": [
    "AI技術が2024年に大幅進歩",
    "企業導入が加速",
    "規制議論が活発化"
  ],
  "conclusion": "AI技術は急速に発展しているが、規制や倫理面での課題も存在する。長期的な影響については継続的な調査が必要である。",
  "date_summary": "2024年の最新情報を中心に構成"
}
'''
        else:
            return "これはテスト用のレスポンスです。"

    def generate_structured(self, prompt: str, response_model):
        """構造化レスポンスを生成"""
        response_text = self.generate(prompt)

        # JSONレスポンスを抽出してパース
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            json_data = json.loads(json_str)
            return response_model(**json_data)
        except Exception as e:
            print(f"JSON解析エラー: {e}")
            # フォールバック
            if response_model == AdditionalQueriesResponse:
                return AdditionalQueriesResponse(keywords=["テストキーワード"])
            elif response_model == AnalysisResponse:
                return AnalysisResponse(main_facts=["テスト分析"])
            elif response_model == SummaryResponse:
                return SummaryResponse(
                    key_facts=["テスト要約"],
                    conclusion="これはテスト用の結論です。十分な長さを持つ結論文です。"
                )

def test_structured_additional_queries():
    """構造化追加検索キーワード生成のテスト"""
    print("🧪 構造化追加検索キーワード生成テスト")
    print("=" * 60)

    try:
        # DeepResearchインスタンスを作成
        researcher = DeepResearch("ollama")

        # モックモデルに置き換え
        researcher.review_model = MockStructuredLanguageModel()

        # テストデータ
        original_query = "人工知能の最新動向"
        analysis = "2024年にAI技術が大幅に進歩した。大規模言語モデルの性能が向上し、企業導入が加速している。"
        summary = "AI技術は急速に発展しているが、規制や倫理面での課題も存在する。"

        print(f"元のクエリ: {original_query}")
        print(f"分析結果: {analysis}")
        print(f"要約: {summary}")
        print()

        # 構造化レスポンスで追加検索キーワードを生成
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

            # 構造化レスポンスの検証
            if len(additional_queries) <= 5:
                print("✅ キーワード数が制限内（最大5個）")
            else:
                print("❌ キーワード数が制限を超えています")

            # 無効なキーワードのチェック
            invalid_keywords = [q for q in additional_queries if any(invalid in q.lower() for invalid in [
                'キーワード', '追加', '提案', '以下の', '各キーワード'
            ])]
            if not invalid_keywords:
                print("✅ 無効なキーワードが含まれていません")
            else:
                print(f"❌ 無効なキーワードが含まれています: {invalid_keywords}")

        else:
            print("\n❌ 追加検索キーワードが生成されませんでした")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def test_structured_analysis():
    """構造化分析のテスト"""
    print("\n📊 構造化分析テスト")
    print("=" * 60)

    try:
        # DeepResearchインスタンスを作成
        researcher = DeepResearch("ollama")

        # モックモデルに置き換え
        researcher.model = MockStructuredLanguageModel()

        # テストデータ
        query = "AI技術の最新動向"
        search_results = [
            type('SearchResult', (), {
                'title': '2024年AI技術の進歩',
                'url': 'https://example.com/ai-2024',
                'snippet': '2024年にAI技術が大幅に進歩した',
                'date_info': '2024年',
                'reliability_score': 0.9,
                'source_type': 'news'
            })(),
            type('SearchResult', (), {
                'title': '企業のAI導入状況',
                'url': 'https://example.com/ai-adoption',
                'snippet': '企業導入率は60%に達した',
                'date_info': '2024年',
                'reliability_score': 0.8,
                'source_type': 'research'
            })()
        ]

        print(f"クエリ: {query}")
        print(f"検索結果数: {len(search_results)}")
        print()

        # 構造化レスポンスで分析を生成
        analysis = researcher._analyze_results(query, search_results)

        print("生成された分析:")
        print(analysis)

        if analysis:
            print(f"\n✅ 分析が正常に生成されました")

            # 分析内容の検証
            if "主要な事実" in analysis:
                print("✅ 主要な事実セクションが含まれています")
            else:
                print("❌ 主要な事実セクションが含まれていません")

            if "具体的なデータ・統計" in analysis:
                print("✅ データ・統計セクションが含まれています")
            else:
                print("❌ データ・統計セクションが含まれていません")

        else:
            print("\n❌ 分析が生成されませんでした")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def test_structured_summary():
    """構造化要約のテスト"""
    print("\n📝 構造化要約テスト")
    print("=" * 60)

    try:
        # DeepResearchインスタンスを作成
        researcher = DeepResearch("ollama")

        # モックモデルに置き換え
        researcher.model = MockStructuredLanguageModel()

        # テストデータ
        query = "AI技術の最新動向"
        analysis = """
主要な事実:
1. 2024年にAI技術が大幅に進歩した
2. 大規模言語モデルの性能が向上した
3. 企業導入が加速している

具体的なデータ・統計:
1. 市場規模は前年比30%増加
2. 企業導入率は60%に達した

結論: AI技術は急速に発展しているが、規制や倫理面での課題も存在する
"""

        print(f"クエリ: {query}")
        print(f"分析結果: {analysis[:100]}...")
        print()

        # 構造化レスポンスで要約を生成
        summary = researcher._create_summary(query, analysis)

        print("生成された要約:")
        print(summary)

        if summary:
            print(f"\n✅ 要約が正常に生成されました")

            # 要約内容の検証
            if "重要な事実" in summary:
                print("✅ 重要な事実セクションが含まれています")
            else:
                print("❌ 重要な事実セクションが含まれていません")

            if "結論" in summary:
                print("✅ 結論セクションが含まれています")
            else:
                print("❌ 結論セクションが含まれていません")

        else:
            print("\n❌ 要約が生成されませんでした")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def test_pydantic_models():
    """Pydanticモデルのテスト"""
    print("\n🔧 Pydanticモデルテスト")
    print("=" * 60)

    try:
        # AdditionalQueriesResponseのテスト
        print("1. AdditionalQueriesResponseテスト")
        valid_keywords = ["市場規模", "AI規制", "倫理ガイドライン"]
        response = AdditionalQueriesResponse(keywords=valid_keywords)
        print(f"   ✅ 有効なキーワード: {response.keywords}")

        # 無効なキーワードのテスト
        try:
            invalid_keywords = ["キーワード1", "追加提案", "以下の内容"]
            response = AdditionalQueriesResponse(keywords=invalid_keywords)
            print(f"   ❌ 無効なキーワードが受け入れられました: {response.keywords}")
        except Exception as e:
            print(f"   ✅ 無効なキーワードが適切に拒否されました: {e}")

        # AnalysisResponseのテスト
        print("\n2. AnalysisResponseテスト")
        analysis_data = {
            "main_facts": ["事実1", "事実2"],
            "data_statistics": ["統計1"],
            "different_perspectives": ["視点1"],
            "date_analysis": ["日付分析1"],
            "unknown_points": ["不明点1"]
        }
        analysis = AnalysisResponse(**analysis_data)
        print(f"   ✅ 分析レスポンス: {len(analysis.main_facts)}個の主要事実")

        # テキスト変換のテスト
        text = analysis.to_text()
        print(f"   ✅ テキスト変換: {len(text)}文字")

        # SummaryResponseのテスト
        print("\n3. SummaryResponseテスト")
        summary_data = {
            "key_facts": ["重要事実1", "重要事実2", "重要事実3"],
            "conclusion": "これはテスト結論です",
            "date_summary": "2024年の情報"
        }
        summary = SummaryResponse(**summary_data)
        print(f"   ✅ 要約レスポンス: {len(summary.key_facts)}個の重要事実")

        # テキスト変換のテスト
        text = summary.to_text()
        print(f"   ✅ テキスト変換: {len(text)}文字")

        print("\n🎉 全てのPydanticモデルテストが成功しました！")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    print("🧪 構造化レスポンステスト")
    print("=" * 60)

    # Pydanticモデルのテスト
    test_pydantic_models()

    # 構造化レスポンスのテスト
    test_structured_additional_queries()
    test_structured_analysis()
    test_structured_summary()

    print("\n🎉 全てのテストが完了しました！")

if __name__ == "__main__":
    main()
