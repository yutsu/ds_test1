# Google Custom Search Engine 作成手順

## 404エラーの解決方法

### 1. Google Custom Search Engine の作成

1. **Google Programmable Search Engine** にアクセス
   - https://programmablesearchengine.google.com/

2. **新しい検索エンジンを作成**
   - 「新しい検索エンジンを作成」をクリック
   - サイトを指定: `www.google.com` （全Web検索の場合）
   - または特定のサイトを指定

3. **検索エンジンIDを取得**
   - 作成後、「検索エンジンID」をコピー
   - 形式: `012345678901234567890:abcdefghijk`

### 2. 設定ファイルの更新

`.env`ファイルを更新:
```env
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_new_search_engine_id_here
```

### 3. 検証

```bash
# 新しいIDでテスト
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_NEW_ENGINE_ID&q=test&num=1"
```

## よくある問題

### 1. 検索エンジンIDが無効
- 404エラーの主な原因
- 新しい検索エンジンを作成する必要があります

### 2. APIキーの問題
- 403エラーが発生する場合
- Google Cloud ConsoleでAPIが有効になっているか確認

### 3. クォータ制限
- 429エラーが発生する場合
- 1日100クエリの無料枠を超えている可能性

## トラブルシューティング

### 1. 現在の設定確認
```bash
# 環境変数の確認
echo $GOOGLE_SEARCH_API_KEY
echo $GOOGLE_SEARCH_ENGINE_ID
```

### 2. API接続テスト
```bash
# 簡単なテスト
python -c "
import requests
import os
api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
url = f'https://www.googleapis.com/customsearch/v1?key={api_key}&cx={engine_id}&q=test&num=1'
response = requests.get(url)
print(f'Status: {response.status_code}')
print(response.json() if response.status_code == 200 else response.text)
"
```
