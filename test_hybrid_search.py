#!/usr/bin/env python3
"""
ハイブリッド検索エンジン（Google + DuckDuckGo）のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import HybridSearcher, DuckDuckGoSearcher, WebSearcher, SearchResult

def test_duckduckgo_search():
    """DuckDuckGo検索のテスト"""
    print("🦆 DuckDuckGo検索テスト")
    print("=" * 40)

    try:
        searcher = DuckDuckGoSearcher(rate_limit=1)

        # テストクエリ
        query = "AIG損保 海外旅行保険"
        print(f"検索クエリ: {query}")

        results = searcher.search(query, num_results=5)

        if results:
            print(f"✅ 検索成功: {len(results)}件の結果")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.title}")
                print(f"   URL: {result.url}")
                print(f"   信頼性: {result.reliability_score:.2f} ({result.source_type})")
                print(f"   内容: {result.snippet[:100]}...")
        else:
            print("❌ 検索結果が得られませんでした")

    except Exception as e:
        print(f"❌ DuckDuckGo検索エラー: {e}")
        import traceback
        traceback.print_exc()

def test_hybrid_searcher():
    """ハイブリッド検索エンジンのテスト"""
    print("\n🔧 ハイブリッド検索エンジンテスト")
    print("=" * 40)

    try:
        # 環境変数からGoogle API設定を取得
        from main import Config
        config = Config()

        google_api_key = config.get('search.google.api_key')
        google_search_engine_id = config.get('search.google.search_engine_id')

        print(f"Google API設定:")
        print(f"  APIキー: {'設定済み' if google_api_key else '未設定'}")
        print(f"  検索エンジンID: {'設定済み' if google_search_engine_id else '未設定'}")

        # ハイブリッド検索エンジンを初期化
        hybrid_searcher = HybridSearcher(
            google_api_key=google_api_key,
            google_search_engine_id=google_search_engine_id,
            preferred_engine="auto",
            rate_limit=1
        )

        print(f"\n利用可能な検索エンジン: {hybrid_searcher.get_available_engines()}")

        # テストクエリ
        query = "AIG損保 海外旅行保険 2024"
        print(f"\nテストクエリ: {query}")

        # 自動選択で検索
        print("\n🔄 自動選択で検索中...")
        results = hybrid_searcher.search(query, num_results=5)

        if results:
            print(f"✅ 検索成功: {len(results)}件の結果")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.title}")
                print(f"   URL: {result.url}")
                print(f"   信頼性: {result.reliability_score:.2f} ({result.source_type})")
                print(f"   内容: {result.snippet[:100]}...")
        else:
            print("❌ 検索結果が得られませんでした")

        # DuckDuckGoのみで検索
        print("\n🦆 DuckDuckGoのみで検索中...")
        results_dd = hybrid_searcher.search(query, num_results=3, force_engine="duckduckgo")

        if results_dd:
            print(f"✅ DuckDuckGo検索成功: {len(results_dd)}件の結果")
        else:
            print("❌ DuckDuckGo検索で結果が得られませんでした")

        # Googleのみで検索（利用可能な場合）
        if google_api_key and google_search_engine_id:
            print("\n🔍 Googleのみで検索中...")
            results_google = hybrid_searcher.search(query, num_results=3, force_engine="google")

            if results_google:
                print(f"✅ Google検索成功: {len(results_google)}件の結果")
            else:
                print("❌ Google検索で結果が得られませんでした")
        else:
            print("\n⚠️  Google検索は設定されていないためスキップ")

    except Exception as e:
        print(f"❌ ハイブリッド検索エラー: {e}")
        import traceback
        traceback.print_exc()

def test_search_engine_fallback():
    """検索エンジンのフォールバック機能テスト"""
    print("\n🔄 フォールバック機能テスト")
    print("=" * 40)

    try:
        # 無効なGoogle設定でハイブリッド検索エンジンを初期化
        hybrid_searcher = HybridSearcher(
            google_api_key="invalid_key",
            google_search_engine_id="invalid_id",
            preferred_engine="google",  # Googleを優先に設定
            rate_limit=1
        )

        print("無効なGoogle設定でハイブリッド検索エンジンを初期化")
        print(f"利用可能な検索エンジン: {hybrid_searcher.get_available_engines()}")

        # テストクエリ
        query = "AIG損保 海外旅行保険"
        print(f"\nテストクエリ: {query}")

        # Googleを優先に設定しているが、無効な設定のためDuckDuckGoにフォールバック
        print("\n🔄 Google優先で検索中（フォールバックテスト）...")
        results = hybrid_searcher.search(query, num_results=3)

        if results:
            print(f"✅ フォールバック成功: {len(results)}件の結果")
            print("DuckDuckGoに正常にフォールバックされました")
        else:
            print("❌ フォールバックでも結果が得られませんでした")

    except Exception as e:
        print(f"❌ フォールバックテストエラー: {e}")
        import traceback
        traceback.print_exc()

def test_search_engine_comparison():
    """検索エンジンの比較テスト"""
    print("\n📊 検索エンジン比較テスト")
    print("=" * 40)

    try:
        from main import Config
        config = Config()

        google_api_key = config.get('search.google.api_key')
        google_search_engine_id = config.get('search.google.search_engine_id')

        # 各検索エンジンを初期化
        duckduckgo_searcher = DuckDuckGoSearcher(rate_limit=1)

        google_searcher = None
        if google_api_key and google_search_engine_id:
            google_searcher = WebSearcher(
                api_key=google_api_key,
                search_engine_id=google_search_engine_id,
                rate_limit=1
            )

        # テストクエリ
        query = "AIG損保 海外旅行保険"
        print(f"テストクエリ: {query}")

        results_comparison = {}

        # DuckDuckGo検索
        print("\n🦆 DuckDuckGo検索中...")
        try:
            dd_results = duckduckgo_searcher.search(query, num_results=3)
            results_comparison["DuckDuckGo"] = {
                "count": len(dd_results),
                "success": True,
                "results": dd_results
            }
            print(f"✅ DuckDuckGo: {len(dd_results)}件")
        except Exception as e:
            results_comparison["DuckDuckGo"] = {
                "count": 0,
                "success": False,
                "error": str(e)
            }
            print(f"❌ DuckDuckGo: エラー - {e}")

        # Google検索
        if google_searcher:
            print("\n🔍 Google検索中...")
            try:
                google_results = google_searcher.search(query, num_results=3)
                results_comparison["Google"] = {
                    "count": len(google_results),
                    "success": True,
                    "results": google_results
                }
                print(f"✅ Google: {len(google_results)}件")
            except Exception as e:
                results_comparison["Google"] = {
                    "count": 0,
                    "success": False,
                    "error": str(e)
                }
                print(f"❌ Google: エラー - {e}")
        else:
            print("\n⚠️  Google検索は設定されていないためスキップ")
            results_comparison["Google"] = {
                "count": 0,
                "success": False,
                "error": "設定されていない"
            }

        # 比較結果を表示
        print(f"\n📊 比較結果:")
        print(f"{'検索エンジン':<12} {'結果数':<6} {'状態':<8}")
        print("-" * 30)

        for engine, data in results_comparison.items():
            status = "成功" if data["success"] else "失敗"
            print(f"{engine:<12} {data['count']:<6} {status:<8}")

        # 成功した検索エンジンの結果を表示
        print(f"\n📋 詳細結果:")
        for engine, data in results_comparison.items():
            if data["success"] and data["results"]:
                print(f"\n{engine}の結果:")
                for i, result in enumerate(data["results"][:2], 1):  # 最初の2件のみ表示
                    print(f"  {i}. {result.title}")
                    print(f"     信頼性: {result.reliability_score:.2f} ({result.source_type})")

    except Exception as e:
        print(f"❌ 比較テストエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    print("🧪 ハイブリッド検索エンジンテスト")
    print("=" * 60)

    # 1. DuckDuckGo検索テスト
    test_duckduckgo_search()

    # 2. ハイブリッド検索エンジンテスト
    test_hybrid_searcher()

    # 3. フォールバック機能テスト
    test_search_engine_fallback()

    # 4. 検索エンジン比較テスト
    test_search_engine_comparison()

    print(f"\n🎉 ハイブリッド検索エンジンテストが完了しました！")

if __name__ == "__main__":
    main()
