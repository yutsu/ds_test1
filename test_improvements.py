#!/usr/bin/env python3
"""
改善された機能のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import DeepResearch, DuckDuckGoSearcher

def test_json_escape_fix():
    """JSONエスケープ修正のテスト"""
    print("🔧 JSONエスケープ修正テスト")
    print("=" * 50)

    try:
        from main import LanguageModel
        import json

        # テスト用のモッククラス
        class MockLanguageModel(LanguageModel):
            def generate(self, prompt: str) -> str:
                # エスケープ文字を含むJSONレスポンスを返す
                return '''
{
  "analysis_text": "{\n \"1. 主要な事実\": [\n \"Switch2の発表直後、株価は一時6～7%下落し9006円まで値を下げた (2025年1月16日, 検索結果1)\",\n \"2024年後半から株価は急激な上昇トレンドに入り、一時12,000円台まで上昇した (検索結果4)\",\n \"現在の株価は11,000円台で推移しており、PERは約20倍と高値圏にある\"\n ],\n \"2. 具体的なデータ・統計\": [\n \"Switch 2の発売価格は49,980円～（2025年6月5日発売）\",\n \"初動販売台数は4日間で350万台を記録\",\n \"2025年3月期の連結経常利益は前年同期比減益\"\n ]\n}"
}
'''

        model = MockLanguageModel()

        # 構造化レスポンスのテスト
        from main import AnalysisResponse

        try:
            response = model.generate_structured("テストプロンプト", AnalysisResponse)
            print("✅ JSONエスケープ修正が正常に動作しました")
            print(f"   レスポンス: {response.analysis_text[:100]}...")
        except Exception as e:
            print(f"❌ JSONエスケープ修正が失敗: {e}")

    except Exception as e:
        print(f"❌ テストエラー: {e}")

def test_duckduckgo_improvements():
    """DuckDuckGo改善機能のテスト"""
    print("\n🦆 DuckDuckGo改善機能テスト")
    print("=" * 50)

    try:
        searcher = DuckDuckGoSearcher(rate_limit=1)

        # 長いクエリでテスト
        long_query = "任天堂 今後のゲームソフトラインナップ 2025年 最新情報"
        print(f"長いクエリテスト: {long_query}")

        results = searcher.search(long_query, num_results=5)
        print(f"結果数: {len(results)}")

        if results:
            print("✅ 長いクエリでも結果が得られました")
            for i, result in enumerate(results[:2], 1):
                print(f"  {i}. {result.title}")
        else:
            print("⚠️  長いクエリでは結果が得られませんでした")

        # 簡略化クエリのテスト
        simplified = searcher._simplify_query(long_query)
        print(f"\nクエリ簡略化テスト:")
        print(f"  元のクエリ: {long_query}")
        print(f"  簡略化後: {simplified}")

        if simplified != long_query:
            print("✅ クエリ簡略化が正常に動作しました")
        else:
            print("⚠️  クエリ簡略化が適用されませんでした")

    except Exception as e:
        print(f"❌ DuckDuckGo改善テストエラー: {e}")

def test_query_validation():
    """クエリ検証・改善機能のテスト"""
    print("\n🔍 クエリ検証・改善機能テスト")
    print("=" * 50)

    try:
        researcher = DeepResearch("ollama")

        # テスト用のクエリ
        original_query = "任天堂 Switch 2"
        test_queries = [
            "キーワード1",  # 無効
            "追加提案",     # 無効
            "Switch",       # 短すぎる
            "Switch 2 スペック 価格 最新情報",  # 有効
            "任天堂 株価 最新",  # 有効
            "分析結果",     # 無効
        ]

        print(f"元のクエリ: {original_query}")
        print("テストクエリ:")
        for i, query in enumerate(test_queries, 1):
            print(f"  {i}. {query}")

        # クエリ検証・改善をテスト
        validated_queries = researcher._validate_and_improve_queries(test_queries, original_query)

        print(f"\n検証・改善後のクエリ:")
        for i, query in enumerate(validated_queries, 1):
            print(f"  {i}. {query}")

        # 結果の検証
        invalid_queries = [q for q in test_queries if any(pattern in q.lower() for pattern in [
            'キーワード', '追加', '提案', '分析'
        ])]

        if not any(invalid in validated_queries for invalid in invalid_queries):
            print("✅ 無効なクエリが適切に除外されました")
        else:
            print("❌ 無効なクエリが残っています")

        if len(validated_queries) >= 3:
            print("✅ 十分な数の有効なクエリが生成されました")
        else:
            print("⚠️  有効なクエリが少なすぎます")

    except Exception as e:
        print(f"❌ クエリ検証テストエラー: {e}")

def test_full_improvement():
    """全体的な改善のテスト"""
    print("\n🧪 全体的な改善テスト")
    print("=" * 50)

    try:
        researcher = DeepResearch("ollama")

        # テストクエリ
        query = "任天堂 Switch 2 最新情報"
        print(f"テストクエリ: {query}")

        # 初期検索
        print("\n🔍 初期検索中...")
        initial_results = researcher.searcher.search(query, num_results=5)
        print(f"初期検索結果: {len(initial_results)}件")

        if initial_results:
            # 分析
            print("\n📊 分析中...")
            analysis = researcher._analyze_results(query, initial_results)
            print(f"分析完了: {len(analysis)}文字")

            # 要約
            print("\n📝 要約生成中...")
            summary = researcher._create_summary(query, analysis)
            print(f"要約完了: {len(summary)}文字")

            # 追加クエリ生成
            print("\n🔍 追加クエリ生成中...")
            additional_queries = researcher._generate_additional_queries(query, analysis, summary)
            print(f"追加クエリ: {len(additional_queries)}個")
            for i, q in enumerate(additional_queries, 1):
                print(f"  {i}. {q}")

            print("\n✅ 全体的な改善テストが成功しました")
        else:
            print("❌ 初期検索で結果が得られませんでした")

    except Exception as e:
        print(f"❌ 全体的な改善テストエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    print("🧪 改善された機能のテスト")
    print("=" * 60)

    # 1. JSONエスケープ修正テスト
    test_json_escape_fix()

    # 2. DuckDuckGo改善機能テスト
    test_duckduckgo_improvements()

    # 3. クエリ検証・改善機能テスト
    test_query_validation()

    # 4. 全体的な改善テスト
    test_full_improvement()

    print(f"\n🎉 改善された機能のテストが完了しました！")

if __name__ == "__main__":
    main()
