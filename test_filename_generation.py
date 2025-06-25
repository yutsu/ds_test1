#!/usr/bin/env python3
"""
ファイル名生成機能のテストスクリプト
"""

import os
import tempfile
import shutil
from datetime import datetime
from main import DeepResearch

def test_filename_generation():
    """ファイル名生成機能をテスト"""
    print("🔬 ファイル名生成機能テスト")
    print("=" * 50)

    # 一時ディレクトリを作成
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)
        print(f"📁 テストディレクトリ: {temp_dir}")

        # テスト用の設定
        config = {
            'output.filename_generation.duplicate_handling': 'both',
            'output.filename_generation.timestamp_format': 'YYYYMMDD_HHMMSS',
            'output.filename_generation.version_prefix': 'v'
        }

        # DeepResearchインスタンスを作成（設定のみ）
        researcher = DeepResearch.__new__(DeepResearch)
        researcher.config = config

        # テストケース1: 新しいファイル名
        base_filename = "test_research.md"
        unique_filename = researcher._get_unique_filename(base_filename)
        print(f"✅ 新しいファイル: {base_filename} -> {unique_filename}")

        # テストファイルを作成
        with open(unique_filename, 'w') as f:
            f.write("test content")

        # テストケース2: 重複ファイル名（タイムスタンプ付き）
        unique_filename2 = researcher._get_unique_filename(base_filename)
        print(f"✅ 重複時（タイムスタンプ）: {base_filename} -> {unique_filename2}")

        # テストケース3: さらに重複（バージョン番号付き）
        with open(unique_filename2, 'w') as f:
            f.write("test content 2")

        unique_filename3 = researcher._get_unique_filename(base_filename)
        print(f"✅ さらに重複時（バージョン）: {base_filename} -> {unique_filename3}")

        # テストケース4: タイムスタンプのみの設定
        config_timestamp = {
            'output.filename_generation.duplicate_handling': 'timestamp',
            'output.filename_generation.timestamp_format': 'YYYY-MM-DD_HH-MM-SS',
            'output.filename_generation.version_prefix': 'v'
        }
        researcher.config = config_timestamp

        unique_filename4 = researcher._get_unique_filename("another_test.md")
        print(f"✅ タイムスタンプ形式変更: another_test.md -> {unique_filename4}")

        # テストケース5: バージョン番号のみの設定
        config_version = {
            'output.filename_generation.duplicate_handling': 'version',
            'output.filename_generation.timestamp_format': 'YYYYMMDD_HHMMSS',
            'output.filename_generation.version_prefix': 'ver'
        }
        researcher.config = config_version

        # 複数のバージョンファイルを作成
        for i in range(1, 4):
            version_filename = f"version_test_ver{i}.md"
            with open(version_filename, 'w') as f:
                f.write(f"version {i}")

        unique_filename5 = researcher._get_unique_filename("version_test.md")
        print(f"✅ バージョン番号のみ: version_test.md -> {unique_filename5}")

        print("\n📋 生成されたファイル一覧:")
        for file in sorted(os.listdir('.')):
            if file.endswith('.md'):
                print(f"  - {file}")

        print("\n✅ ファイル名生成機能テスト完了")

    finally:
        # 一時ディレクトリを削除
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
        print(f"🗑️  テストディレクトリを削除: {temp_dir}")

if __name__ == "__main__":
    test_filename_generation()
