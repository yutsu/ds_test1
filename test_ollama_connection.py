#!/usr/bin/env python3
"""
Ollama接続テストスクリプト
"""

import requests
import json
import sys

def test_ollama_connection():
    """Ollamaサーバーへの接続をテスト"""
    print("🔧 Ollama接続テスト")
    print("=" * 50)

    # 接続先URL
    base_url = "http://localhost:11434"

    try:
        # 1. サーバーの状態確認
        print("1. サーバー状態確認...")
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollamaサーバーが起動しています")
        else:
            print(f"❌ サーバーエラー: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Ollamaサーバーに接続できません")
        print("   対処法:")
        print("   1. ollama serve を実行してください")
        print("   2. ポート11434が使用可能か確認してください")
        return False
    except requests.exceptions.Timeout:
        print("❌ 接続がタイムアウトしました")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

    try:
        # 2. 利用可能なモデル確認
        print("\n2. 利用可能なモデル確認...")
        response = requests.get(f"{base_url}/api/tags")
        models = response.json().get('models', [])

        if models:
            print(f"✅ {len(models)}個のモデルが利用可能:")
            for model in models:
                print(f"   - {model['name']}")
        else:
            print("⚠️  利用可能なモデルがありません")
            print("   対処法: ollama pull llama3.1:8b を実行してください")

    except Exception as e:
        print(f"❌ モデル確認エラー: {e}")
        return False

    try:
        # 3. 簡単な生成テスト
        print("\n3. 生成テスト...")
        test_prompt = "こんにちは"

        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": "llama3.1:8b",
                "prompt": test_prompt,
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ 生成テスト成功")
            print(f"   レスポンス: {result.get('response', '')[:50]}...")
        else:
            print(f"❌ 生成テスト失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 生成テストがタイムアウトしました")
        return False
    except Exception as e:
        print(f"❌ 生成テストエラー: {e}")
        return False

    print("\n🎉 Ollama接続テストが成功しました！")
    return True

def main():
    """メイン関数"""
    print("🧪 Ollama接続テスト")
    print("=" * 50)

    success = test_ollama_connection()

    if not success:
        print("\n📋 トラブルシューティング")
        print("=" * 50)
        print("1. Ollamaがインストールされているか確認:")
        print("   which ollama")
        print()
        print("2. Ollamaサーバーを起動:")
        print("   ollama serve")
        print()
        print("3. モデルをダウンロード:")
        print("   ollama pull llama3.1:8b")
        print()
        print("4. 別のポートを使用している場合:")
        print("   config.yamlでbase_urlを変更")
        print()
        print("5. ファイアウォール設定を確認")
        sys.exit(1)
    else:
        print("\n✅ 全てのテストが成功しました！")

if __name__ == "__main__":
    main()
