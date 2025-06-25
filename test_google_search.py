#!/usr/bin/env python3
"""
Google検索機能のテストスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def test_environment_variables():
    """環境変数の設定をテスト"""
    print("🔧 環境変数テスト")
    print("=" * 50)

    api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

    print(f"GOOGLE_SEARCH_API_KEY: {'設定済み' if api_key else '未設定'}")
    if api_key:
        print(f"  APIキー: {api_key[:10]}...")

    print(f"GOOGLE_SEARCH_ENGINE_ID: {'設定済み' if search_engine_id else '未設定'}")
    if search_engine_id:
        print(f"  検索エンジンID: {search_engine_id}")

    return api_key and search_engine_id

def test_config_loading():
    """設定ファイルの読み込みをテスト"""
    print("\n📋 設定ファイルテスト")
    print("=" * 50)

    try:
        from main import Config
        config = Config()

        api_key = config.get('search.google.api_key')
        search_engine_id = config.get('search.google.search_engine_id')

        print(f"設定ファイルから読み込み:")
        print(f"  APIキー: {'設定済み' if api_key else '未設定'}")
        print(f"  検索エンジンID: {'設定済み' if search_engine_id else '未設定'}")

        return api_key and search_engine_id
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        return False

def test_web_searcher():
    """WebSearcherクラスのテスト"""
    print("\n🔍 WebSearcherテスト")
    print("=" * 50)

    try:
        from main import WebSearcher, Config
        config = Config()
        searcher = WebSearcher(config)

        # 簡単な検索テスト
        print("簡単な検索テストを実行中...")
        results = searcher.search("テスト", num_results=2)

        if results:
            print(f"✅ 検索成功: {len(results)}件の結果を取得")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.title}")
                print(f"     URL: {result.url}")
                print(f"     信頼性: {result.reliability_score:.2f} ({result.source_type})")

            # キャッシュ機能のテスト
            print("\n📋 キャッシュ機能テスト")
            cached_results = searcher.search("テスト", num_results=2)
            if cached_results == results:
                print("✅ キャッシュ機能が正常に動作しています")
            else:
                print("❌ キャッシュ機能に問題があります")
        else:
            print("❌ 検索結果が取得できませんでした")

        return len(results) > 0
    except Exception as e:
        print(f"❌ WebSearcherテストエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🧪 Google検索機能テスト")
    print("=" * 50)

    # 環境変数テスト
    env_ok = test_environment_variables()

    # 設定ファイルテスト
    config_ok = test_config_loading()

    # WebSearcherテスト
    searcher_ok = test_web_searcher()

    # 結果まとめ
    print("\n📊 テスト結果まとめ")
    print("=" * 50)
    print(f"環境変数: {'✅ OK' if env_ok else '❌ NG'}")
    print(f"設定ファイル: {'✅ OK' if config_ok else '❌ NG'}")
    print(f"WebSearcher: {'✅ OK' if searcher_ok else '❌ NG'}")

    if all([env_ok, config_ok, searcher_ok]):
        print("\n🎉 全てのテストが成功しました！")
    else:
        print("\n⚠️  一部のテストが失敗しました。設定を確認してください。")

if __name__ == "__main__":
    main()
