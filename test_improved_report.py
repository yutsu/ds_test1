#!/usr/bin/env python3
"""
改善されたレポート生成機能のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import DeepResearch, SearchResult

def test_improved_report_generation():
    """改善されたレポート生成機能をテスト"""
    print("🧪 改善されたレポート生成機能テスト")
    print("=" * 60)

    try:
        # DeepResearchインスタンスを作成
        researcher = DeepResearch("ollama")

        print(f"使用モデル: {researcher.model.model_name}")
        print(f"接続先: {researcher.model.base_url}")
        print()

        # テスト用のダミー検索結果を作成
        search_results = [
            SearchResult(
                title="AIG損保の海外旅行保険商品概要",
                url="https://travel.aig.co.jp/",
                snippet="AIG損保は海外旅行保険・海外留学保険を提供。インターネットでの契約や出発当日の加入も可能。24時間365日の損害サービスを提供。",
                search_query="AIG損保 海外旅行保険",
                date_info="2024年",
                reliability_score=0.9,
                source_type="official"
            ),
            SearchResult(
                title="海外旅行保険の市場動向2024",
                url="https://example.com/market-trends",
                snippet="2023年の調査では約8割が海外旅行保険への加入意向を示していた。2022年の日本人海外旅行費用は平均36.7万円。",
                search_query="海外旅行保険 市場動向",
                date_info="2023年",
                reliability_score=0.8,
                source_type="research"
            ),
            SearchResult(
                title="AIG損保の顧客満足度調査",
                url="https://example.com/customer-satisfaction",
                snippet="AIG損保の海外旅行保険は、現地の医療機関への連絡や支払い対応がスムーズという評価がある。",
                search_query="AIG損保 顧客満足度",
                date_info="2024年",
                reliability_score=0.7,
                source_type="review"
            )
        ]

        # テストクエリ
        query = "AIG損保の海外旅行保険の現状と課題"

        print(f"テストクエリ: {query}")
        print(f"検索結果数: {len(search_results)}")
        print()

        # 分析を生成
        print("📊 構造化分析生成中...")
        analysis = researcher._analyze_results(query, search_results)
        print("生成された分析（一部）:")
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        print()

        # 要約を生成
        print("📝 構造化要約生成中...")
        summary = researcher._create_summary(query, analysis)
        print("生成された要約:")
        print(summary)
        print()

        # 最終レポートを生成
        print("📋 最終レポート生成中...")
        final_report = researcher._create_final_report(query, analysis, summary)
        print("生成された最終レポート（一部）:")
        print(final_report[:800] + "..." if len(final_report) > 800 else final_report)
        print()

        # レポートの品質評価
        print("🔍 レポート品質評価")
        print("=" * 40)

        # 1. 重複チェック
        if "エグゼクティブサマリー" in final_report and final_report.count("エグゼクティブサマリー") == 1:
            print("✅ エグゼクティブサマリーの重複なし")
        else:
            print("❌ エグゼクティブサマリーが重複している可能性")

        # 2. 構造チェック
        required_sections = [
            "エグゼクティブサマリー", "研究背景", "主要な発見",
            "市場分析", "課題と機会", "結論"
        ]

        found_sections = []
        for section in required_sections:
            if section in final_report:
                found_sections.append(section)

        print(f"✅ 必要なセクション: {len(found_sections)}/{len(required_sections)}")
        for section in found_sections:
            print(f"   - {section}")

        # 3. 具体的なデータの確認
        if any(word in final_report for word in ["8割", "36.7万円", "24時間", "365日"]):
            print("✅ 具体的な数値データが含まれている")
        else:
            print("⚠️  具体的な数値データが不足している可能性")

        # 4. 長さの確認
        if len(final_report) > 1000:
            print(f"✅ レポートの長さ: {len(final_report)}文字（十分な内容）")
        else:
            print(f"⚠️  レポートの長さ: {len(final_report)}文字（短すぎる可能性）")

        # 5. 構造化の確認
        if "###" in final_report or "##" in final_report:
            print("✅ 適切な見出し構造が使用されている")
        else:
            print("⚠️  見出し構造が不十分")

        print(f"\n🎉 改善されたレポート生成テストが完了しました！")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def test_prompt_improvements():
    """プロンプト改善の効果をテスト"""
    print("\n🔧 プロンプト改善効果テスト")
    print("=" * 60)

    try:
        # 設定ファイルからプロンプトを確認
        from main import Config
        config = Config()

        # 分析プロンプトの確認
        analysis_prompt = config.get('prompts.analysis', '')
        if "構造化された分析" in analysis_prompt:
            print("✅ 分析プロンプトが改善されている")
        else:
            print("❌ 分析プロンプトの改善が必要")

        # 要約プロンプトの確認
        summary_prompt = config.get('prompts.summary', '')
        if "簡潔で実用的" in summary_prompt:
            print("✅ 要約プロンプトが改善されている")
        else:
            print("❌ 要約プロンプトの改善が必要")

        # 最終レポートプロンプトの確認
        final_report_prompt = config.get('prompts.final_report', '')
        if "重複を避ける" in final_report_prompt:
            print("✅ 最終レポートプロンプトが改善されている")
        else:
            print("❌ 最終レポートプロンプトの改善が必要")

        print(f"\n📋 プロンプト改善状況:")
        print(f"   分析プロンプト: {len(analysis_prompt)}文字")
        print(f"   要約プロンプト: {len(summary_prompt)}文字")
        print(f"   最終レポートプロンプト: {len(final_report_prompt)}文字")

    except Exception as e:
        print(f"❌ プロンプト確認でエラーが発生しました: {e}")

def main():
    """メイン関数"""
    print("🧪 改善されたレポート生成機能テスト")
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

    # プロンプト改善効果のテスト
    test_prompt_improvements()

    # 改善されたレポート生成のテスト
    test_improved_report_generation()

if __name__ == "__main__":
    main()
