#!/usr/bin/env python3
"""
Deep Research Clone - 改善版
言語モデルとWeb検索を組み合わせた研究支援ツール
レビューモデルによる追加検索機能付き
"""

import os
import json
import requests
from typing import List, Dict, Optional, Set, Union
from dataclasses import dataclass
from pathlib import Path
import markdown
from dotenv import load_dotenv
import re
import yaml
from datetime import datetime, timedelta
import time
import random
from pydantic import BaseModel, Field, validator
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

# 環境変数を読み込み
load_dotenv()

@dataclass
class SearchResult:
    """検索結果を格納するデータクラス"""
    title: str
    url: str
    snippet: str
    search_query: str  # どの検索クエリで取得されたか
    date_info: Optional[str] = None  # 日付情報
    reliability_score: float = 1.0  # 信頼性スコア（0.0-1.0）
    source_type: str = "unknown"  # 情報源タイプ（official, news, academic, blog, etc.）

@dataclass
class Citation:
    """引用情報を格納するデータクラス"""
    source_title: str
    source_url: str
    content: str
    search_query: str
    relevance_score: float = 1.0
    date_info: Optional[str] = None  # 日付情報

@dataclass
class ResearchResult:
    """研究結果を格納するデータクラス"""
    query: str
    search_results: List[SearchResult]
    analysis: str
    summary: str
    citations: List[Citation]
    additional_queries: List[str]
    final_report: str

class Config:
    """設定管理クラス"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """設定ファイルを読み込み"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # 環境変数を展開
                self._expand_env_vars(config)
                return config
        else:
            # デフォルト設定
            default_config = {
                'language_model': {
                    'default': 'ollama',
                    'ollama': {'model_name': 'llama2', 'base_url': 'http://localhost:11434'},
                    'openai': {'model': 'gpt-3.5-turbo', 'max_tokens': 2000, 'temperature': 0.7},
                    'gemini': {'model': 'gemini-2.0-flash', 'temperature': 0.7}
                },
                'iteration': {
                    'max_iterations': 3,
                    'initial_search_count': 8,
                    'additional_search_count': 5,
                    'max_additional_queries': 3
                },
                'search': {
                    'engine': 'google',
                    'max_results': 5,
                    'rate_limit': {
                        'requests_per_second': 8,
                        'max_retries': 3,
                        'retry_delay_base': 2
                    },
                    'google': {
                        'api_key': os.getenv('GOOGLE_SEARCH_API_KEY'),
                        'search_engine_id': os.getenv('GOOGLE_SEARCH_ENGINE_ID')
                    }
                },
                'citations': {
                    'auto_extract': True,
                    'relevance_threshold': 0.5,
                    'reliability_threshold': 0.3,
                    'format': 'numbered'
                },
                'output': {
                    'format': 'markdown',
                    'directory': './output',
                    'filename_template': 'research_{query}_{timestamp}',
                    'markdown': {
                        'include_search_results': True,
                        'include_analysis': True,
                        'include_summary': True,
                        'include_final_report': True,
                        'include_citations': True,
                        'include_search_history': True
                    }
                }
            }
            return default_config

    def _expand_env_vars(self, obj):
        """辞書内の環境変数を展開"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    # ${VAR_NAME} 形式の環境変数を展開
                    env_var = value[2:-1]  # ${} を除去
                    expanded_value = os.getenv(env_var, value)
                    if expanded_value != value:
                        print(f"🔧 環境変数を展開: {env_var} = {expanded_value[:10]}...")
                    else:
                        print(f"⚠️  環境変数が見つかりません: {env_var}")
                    obj[key] = expanded_value
                elif isinstance(value, (dict, list)):
                    self._expand_env_vars(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    self._expand_env_vars(item)

    def get(self, key: str, default=None):
        """設定値を取得"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

class LanguageModel:
    """言語モデルの抽象クラス"""

    def generate(self, prompt: str) -> str:
        """プロンプトからテキストを生成"""
        raise NotImplementedError

    def generate_structured(self, prompt: str, response_model: BaseModel) -> BaseModel:
        """構造化されたレスポンスを生成"""
        # 構造化プロンプトを作成
        structured_prompt = self._create_structured_prompt(prompt, response_model)

        # 通常の生成を実行
        response_text = self.generate(structured_prompt)

        # JSONレスポンスを抽出してパース
        try:
            json_data = self._extract_json_from_response(response_text)
            return response_model(**json_data)
        except Exception as e:
            print(f"⚠️  構造化レスポンスの解析に失敗: {e}")
            print(f"   レスポンス: {response_text[:200]}...")
            # フォールバック: デフォルト値を返す
            return self._create_fallback_response(response_model)

    def _create_structured_prompt(self, prompt: str, response_model: BaseModel) -> str:
        """構造化プロンプトを作成"""
        schema = response_model.model_json_schema()

        structured_prompt = f"""
{prompt}

重要: 以下のJSONスキーマに従って、正確なJSON形式で回答してください。
番号や記号、説明文は含めず、純粋なJSONのみを返してください。

JSONスキーマ:
{json.dumps(schema, ensure_ascii=False, indent=2)}

回答例:
{self._generate_example_response(response_model)}

JSON回答:
"""
        return structured_prompt

    def _generate_example_response(self, response_model: BaseModel) -> str:
        """レスポンスモデルの例を生成"""
        if response_model == AdditionalQueriesResponse:
            return json.dumps({
                "keywords": ["市場規模 統計", "AI規制 法律", "倫理ガイドライン", "雇用影響 調査", "医療AI 応用"]
            }, ensure_ascii=False, indent=2)
        elif response_model == AnalysisResponse:
            return json.dumps({
                "main_facts": ["2024年にAI技術が大幅に進歩した", "大規模言語モデルの性能が向上した"],
                "data_statistics": ["市場規模は前年比30%増加", "企業導入率は60%に達した"],
                "different_perspectives": ["技術的進歩を評価する意見", "雇用への影響を懸念する意見"],
                "date_analysis": ["2024年の情報は最新", "2023年のデータは過去の情報"],
                "unknown_points": ["具体的な規制内容", "長期的な影響の詳細"]
            }, ensure_ascii=False, indent=2)
        elif response_model == SummaryResponse:
            return json.dumps({
                "key_facts": ["AI技術が2024年に大幅進歩", "企業導入が加速", "規制議論が活発化"],
                "conclusion": "AI技術は急速に発展しているが、規制や倫理面での課題も存在する",
                "date_summary": "2024年の最新情報を中心に構成"
            }, ensure_ascii=False, indent=2)
        else:
            return "{}"

    def _extract_json_from_response(self, response_text: str) -> dict:
        """レスポンステキストからJSONを抽出"""
        # JSONブロックを探す
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("JSONが見つかりません")

        json_str = response_text[json_start:json_end]

        # 複数のJSONブロックがある場合は最後のものを使用
        if json_str.count('{') > 1:
            # ネストされたJSONを処理
            brace_count = 0
            start_pos = -1
            for i, char in enumerate(json_str):
                if char == '{':
                    if brace_count == 0:
                        start_pos = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_pos != -1:
                        json_str = json_str[start_pos:i+1]
                        break

        # JSONエスケープ文字を適切に処理
        try:
            # まず通常のJSONパースを試行
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # エスケープ文字の問題がある場合、手動で修正
            if "Invalid \\escape" in str(e):
                # 一般的なエスケープ文字を修正
                json_str = json_str.replace('\\n', '\\\\n')
                json_str = json_str.replace('\\"', '\\\\"')
                json_str = json_str.replace('\\t', '\\\\t')
                json_str = json_str.replace('\\r', '\\\\r')

                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # それでも失敗する場合は、より積極的な修正
                    import re
                    # バックスラッシュを適切にエスケープ
                    json_str = re.sub(r'\\(?!["\\/bfnrt])', r'\\\\', json_str)
                    return json.loads(json_str)
            else:
                raise e

    def _create_fallback_response(self, response_model: BaseModel) -> BaseModel:
        """フォールバック用のデフォルトレスポンスを作成"""
        if response_model == AdditionalQueriesResponse:
            return AdditionalQueriesResponse(keywords=["追加検索が必要"])
        elif response_model == AnalysisResponse:
            return AnalysisResponse(main_facts=["検索結果の分析が必要"])
        elif response_model == SummaryResponse:
            return SummaryResponse(
                key_facts=["要約が必要"],
                conclusion="検索結果の要約が必要です"
            )
        else:
            return response_model()

class OllamaModel(LanguageModel):
    """Ollamaローカルモデル"""

    def __init__(self, config: Config):
        self.model_name = config.get('language_model.ollama.model_name', 'llama2')
        self.base_url = config.get('language_model.ollama.base_url', 'http://localhost:11434')

    def generate(self, prompt: str) -> str:
        """Ollama APIを使用してテキスト生成"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60  # タイムアウトを60秒に設定
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.Timeout:
            return f"Ollama API タイムアウト: モデル {self.model_name} の応答が60秒を超えました"
        except requests.exceptions.ConnectionError:
            return f"Ollama API 接続エラー: {self.base_url} に接続できません。Ollamaが起動しているか確認してください"
        except requests.exceptions.RequestException as e:
            return f"Ollama API リクエストエラー: {e}"
        except Exception as e:
            return f"Ollama API 予期しないエラー: {e}"

class OpenAIModel(LanguageModel):
    """OpenAI APIモデル"""

    def __init__(self, config: Config):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = config.get('language_model.openai.model', 'gpt-3.5-turbo')
        self.max_tokens = config.get('language_model.openai.max_tokens', 2000)
        self.temperature = config.get('language_model.openai.temperature', 0.7)

        if not self.api_key:
            raise ValueError("OpenAI API キーが必要です")

    def generate(self, prompt: str) -> str:
        """OpenAI APIを使用してテキスト生成"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI API エラー: {e}"

class GoogleGeminiModel(LanguageModel):
    """Google Gemini APIモデル"""

    def __init__(self, config: Config):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = config.get('language_model.gemini.model', 'gemini-2.0-flash')
        self.temperature = config.get('language_model.gemini.temperature', 0.7)

        if not self.api_key:
            raise ValueError("Google API キーが必要です")

    def generate(self, prompt: str) -> str:
        """Google Gemini APIを使用してテキスト生成"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Google Gemini API エラー: {e}"

class DuckDuckGoSearcher:
    """DuckDuckGo検索エンジン"""

    def __init__(self, rate_limit: int = 2, max_retries: int = 3):
        self.rate_limit = rate_limit  # 秒間リクエスト数
        self.max_retries = max_retries
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """DuckDuckGoで検索を実行"""
        print(f"🔍 DuckDuckGo検索実行: {query}")

        # レート制限を適用
        self._apply_rate_limit()

        try:
            # DuckDuckGo Instant Answer APIを使用
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            results = []

            # Instant Answerから結果を抽出
            if data.get('Abstract'):
                results.append(SearchResult(
                    title=data.get('AbstractSource', 'DuckDuckGo Instant Answer'),
                    url=data.get('AbstractURL', ''),
                    snippet=data.get('Abstract', ''),
                    search_query=query,
                    reliability_score=0.8,
                    source_type="instant_answer"
                ))

            # Related Topicsから結果を抽出
            for topic in data.get('RelatedTopics', [])[:num_results-1]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append(SearchResult(
                        title=topic.get('FirstURL', '').split('/')[-1] if topic.get('FirstURL') else 'Related Topic',
                        url=topic.get('FirstURL', ''),
                        snippet=topic.get('Text', ''),
                        search_query=query,
                        reliability_score=0.6,
                        source_type="related_topic"
                    ))

            # 結果が少ない場合は、HTML検索も試行
            if len(results) < num_results:
                html_results = self._search_html(query, num_results - len(results))
                results.extend(html_results)

            # それでも結果が少ない場合は、クエリを簡略化して再試行
            if len(results) < 3 and len(query.split()) > 3:
                print(f"⚠️  結果が少ないため、クエリを簡略化して再試行: {query}")
                simplified_query = self._simplify_query(query)
                if simplified_query != query:
                    simplified_results = self._search_simplified(simplified_query, num_results - len(results))
                    results.extend(simplified_results)

            print(f"✅ DuckDuckGo検索完了: {len(results)}件の結果")
            return results[:num_results]

        except Exception as e:
            print(f"❌ DuckDuckGo検索エラー: {e}")
            return []

    def _simplify_query(self, query: str) -> str:
        """クエリを簡略化"""
        # 年号や具体的な日付を削除
        import re
        simplified = re.sub(r'\d{4}年', '', query)
        simplified = re.sub(r'\d{1,2}月', '', simplified)
        simplified = re.sub(r'\d{1,2}日', '', simplified)

        # 複数の空白を単一の空白に
        simplified = re.sub(r'\s+', ' ', simplified)

        # 先頭と末尾の空白を削除
        simplified = simplified.strip()

        # 3単語以上の場合、最初の3単語のみを使用
        words = simplified.split()
        if len(words) > 3:
            simplified = ' '.join(words[:3])

        return simplified

    def _search_simplified(self, simplified_query: str, num_results: int) -> List[SearchResult]:
        """簡略化されたクエリで検索"""
        try:
            print(f"🔄 簡略化クエリで検索: {simplified_query}")
            return self._search_html(simplified_query, num_results)
        except Exception as e:
            print(f"❌ 簡略化クエリ検索エラー: {e}")
            return []

    def _search_html(self, query: str, num_results: int) -> List[SearchResult]:
        """DuckDuckGoのHTML検索を実行（フォールバック）"""
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {
                'q': query
            }

            response = self.session.post(url, data=params, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # 検索結果を抽出
            for result in soup.select('.result')[:num_results]:
                title_elem = result.select_one('.result__title')
                snippet_elem = result.select_one('.result__snippet')
                link_elem = result.select_one('.result__url')

                if title_elem and snippet_elem:
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True)
                    url = link_elem.get('href') if link_elem else ''

                    # DuckDuckGoのリダイレクトURLを処理
                    if url.startswith('/l/?uddg='):
                        url = url.replace('/l/?uddg=', '')

                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        search_query=query,
                        reliability_score=0.5,
                        source_type="html_search"
                    ))

            return results

        except Exception as e:
            print(f"❌ DuckDuckGo HTML検索エラー: {e}")
            return []

    def _apply_rate_limit(self):
        """レート制限を適用"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

class WebSearcher:
    """Web検索エンジン（Google Custom Search API）"""

    def __init__(self, api_key: str, search_engine_id: str, rate_limit: int = 2, max_retries: int = 5):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.last_request_time = 0
        self.cache = {}
        self.session = requests.Session()

        print(f"🔧 WebSearcher初期化:")
        print(f"   APIキー: {'設定済み' if api_key else '未設定'}")
        print(f"   検索エンジンID: {'設定済み' if search_engine_id else '未設定'}")
        print(f"   レート制限: {rate_limit} req/sec, {max_retries}回リトライ")

    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Google Custom Search APIで検索を実行"""
        print(f"🔍 Google検索実行: {query}")

        # キャッシュをチェック
        cache_key = f"{query}_{num_results}"
        if cache_key in self.cache:
            print(f"📋 キャッシュから結果を取得: {query}")
            return self.cache[cache_key]

        # レート制限を適用
        self._apply_rate_limit()

        for attempt in range(self.max_retries):
            try:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.api_key,
                    'cx': self.search_engine_id,
                    'q': query,
                    'num': min(num_results, 10),  # Google APIの最大値は10
                    'dateRestrict': 'm6',  # 過去6ヶ月
                    'sort': 'date'  # 日付順
                }

                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    print(f"⚠️  APIレート制限に達しました（試行 {attempt + 1}/{self.max_retries}）")
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"   {wait_time:.1f}秒待機中...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("❌ 最大リトライ回数に達しました")
                        return []

                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get('items', []):
                    # 日付情報を抽出
                    date_info = self._extract_date_info(item)

                    # 信頼性スコアを計算
                    reliability_score = self._calculate_reliability_score(item)

                    # ソースタイプを判定
                    source_type = self._determine_source_type(item.get('displayLink', ''))

                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        snippet=item.get('snippet', ''),
                        search_query=query,
                        date_info=date_info,
                        reliability_score=reliability_score,
                        source_type=source_type
                    ))

                # 結果をキャッシュ
                self.cache[cache_key] = results

                print(f"✅ Google検索完了: {len(results)}件の結果")
                return results

            except requests.exceptions.RequestException as e:
                print(f"❌ ネットワークエラー（試行 {attempt + 1}/{self.max_retries}）: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"   {wait_time:.1f}秒待機中...")
                    time.sleep(wait_time)
                else:
                    print("❌ 最大リトライ回数に達しました")
                    return []
            except Exception as e:
                print(f"❌ 予期しないエラー: {e}")
                return []

        return []

    def _extract_date_info(self, item: Dict) -> Optional[str]:
        """検索結果から日付情報を抽出"""
        # メタデータから日付を探す
        metatags = item.get('pagemap', {}).get('metatags', [{}])[0]

        # 様々な日付フィールドをチェック
        date_fields = [
            'article:published_time',
            'article:modified_time',
            'og:updated_time',
            'lastmod',
            'date',
            'pubdate'
        ]

        for field in date_fields:
            if field in metatags:
                return metatags[field]

        # スニペットから日付パターンを探す
        snippet = item.get('snippet', '')
        date_patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}/\d{1,2}/\d{1,2})',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(\d{1,2}/\d{1,2}/\d{4})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, snippet)
            if match:
                return match.group(1)

        return None

    def _calculate_reliability_score(self, item: Dict) -> float:
        """検索結果の信頼性スコアを計算"""
        score = 0.5  # ベーススコア

        # ドメインの信頼性
        display_link = item.get('displayLink', '').lower()

        # 公式サイトや信頼できるドメイン
        trusted_domains = [
            'aig.co.jp', 'aig.com', 'travel.aig.co.jp',
            'jata-net.or.jp', 'sompo-japan.co.jp',
            'tokyomarine-nichido.co.jp', 'ms-ins.com',
            'sonpo.co.jp', 'aioinissaydowa.co.jp'
        ]

        for domain in trusted_domains:
            if domain in display_link:
                score += 0.3
                break

        # ニュースサイト
        news_domains = [
            'reuters.com', 'bloomberg.com', 'nikkei.com',
            'asahi.com', 'mainichi.jp', 'yomiuri.co.jp'
        ]

        for domain in news_domains:
            if domain in display_link:
                score += 0.2
                break

        # 政府・公的機関
        gov_domains = [
            'go.jp', 'meti.go.jp', 'mlit.go.jp',
            'fsa.go.jp', 'jata-net.or.jp'
        ]

        for domain in gov_domains:
            if domain in display_link:
                score += 0.4
                break

        return min(score, 1.0)

    def _determine_source_type(self, display_link: str) -> str:
        """ソースタイプを判定"""
        display_link = display_link.lower()

        if any(domain in display_link for domain in ['aig.co.jp', 'aig.com']):
            return "official"
        elif any(domain in display_link for domain in ['reuters.com', 'bloomberg.com', 'nikkei.com']):
            return "news"
        elif any(domain in display_link for domain in ['go.jp', 'meti.go.jp']):
            return "government"
        elif any(domain in display_link for domain in ['jata-net.or.jp', 'sompo-japan.co.jp']):
            return "industry"
        else:
            return "general"

    def _apply_rate_limit(self):
        """レート制限を適用"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

class HybridSearcher:
    """ハイブリッド検索エンジン（Google + DuckDuckGo）"""

    def __init__(self, google_api_key: str = None, google_search_engine_id: str = None,
                 preferred_engine: str = "google", rate_limit: int = 2):
        self.google_searcher = None
        self.duckduckgo_searcher = None
        self.preferred_engine = preferred_engine.lower()
        self.rate_limit = rate_limit

        # Google検索エンジンを初期化
        if google_api_key and google_search_engine_id:
            self.google_searcher = WebSearcher(
                api_key=google_api_key,
                search_engine_id=google_search_engine_id,
                rate_limit=rate_limit
            )
            print("✅ Google検索エンジンを初期化しました")
        else:
            print("⚠️  Google APIキーまたはSearch Engine IDが設定されていません")
            if not google_api_key:
                print("   - GOOGLE_SEARCH_API_KEY が設定されていません")
            if not google_search_engine_id:
                print("   - GOOGLE_SEARCH_ENGINE_ID が設定されていません")

        # DuckDuckGo検索エンジンを初期化
        self.duckduckgo_searcher = DuckDuckGoSearcher(rate_limit=rate_limit)
        print("✅ DuckDuckGo検索エンジンを初期化しました")

        print(f"🔧 ハイブリッド検索エンジン初期化完了")
        print(f"   優先エンジン: {self.preferred_engine}")
        print(f"   利用可能: Google={self.google_searcher is not None}, DuckDuckGo=True")

    def search(self, query: str, num_results: int = 10, force_engine: str = None) -> List[SearchResult]:
        """検索を実行（指定されたエンジンまたは自動選択）"""
        if force_engine:
            engine = force_engine.lower()
        else:
            engine = self.preferred_engine

        if engine == "google":
            if self.google_searcher:
                try:
                    results = self.google_searcher.search(query, num_results)
                    if results:
                        return results
                    else:
                        print("⚠️  Google検索で結果が得られませんでした。DuckDuckGoに切り替えます。")
                        return self.duckduckgo_searcher.search(query, num_results)
                except Exception as e:
                    print(f"❌ Google検索エラー: {e}")
                    print("🔄 DuckDuckGoに切り替えます。")
                    return self.duckduckgo_searcher.search(query, num_results)
            else:
                print("⚠️  Google検索エンジンが利用できません。DuckDuckGoを使用します。")
                return self.duckduckgo_searcher.search(query, num_results)

        elif engine == "duckduckgo":
            return self.duckduckgo_searcher.search(query, num_results)

        elif engine == "auto":
            # 自動選択：Googleを優先、失敗時はDuckDuckGo
            if self.google_searcher:
                try:
                    results = self.google_searcher.search(query, num_results)
                    if results:
                        return results
                except Exception as e:
                    print(f"⚠️  Google検索エラー: {e}")

            print("🔄 DuckDuckGoで検索を実行します。")
            return self.duckduckgo_searcher.search(query, num_results)

        else:
            print(f"❌ 不明な検索エンジン: {engine}")
            return []

    def get_available_engines(self) -> List[str]:
        """利用可能な検索エンジンのリストを取得"""
        engines = ["duckduckgo"]
        if self.google_searcher:
            engines.append("google")
        return engines

class CitationManager:
    """引用管理を行うクラス"""

    def __init__(self, config: Config):
        self.config = config
        self.citations: List[Citation] = []
        self.auto_extract = config.get('citations.auto_extract', True)
        self.relevance_threshold = config.get('citations.relevance_threshold', 0.5)
        self.reliability_threshold = config.get('citations.reliability_threshold', 0.3)

    def create_citations(self, search_results: List[SearchResult]) -> List[Citation]:
        """検索結果から引用を作成"""
        citations = []
        for result in search_results:
            # 信頼性と関連度をチェック
            if (result.reliability_score >= self.reliability_threshold and
                result.reliability_score >= self.relevance_threshold):

                citation = Citation(
                    source_title=result.title,
                    source_url=result.url,
                    content=result.snippet,
                    search_query=result.search_query,
                    relevance_score=result.reliability_score,
                    date_info=result.date_info
                )
                citations.append(citation)

        return citations

    def add_citation(self, source: SearchResult, content: str, relevance_score: float = 1.0) -> int:
        """引用を追加"""
        citation = Citation(
            source_title=source.title,
            source_url=source.url,
            content=content,
            search_query=source.search_query,
            relevance_score=relevance_score,
            date_info=source.date_info
        )
        self.citations.append(citation)
        return len(self.citations)

    def get_citation_text(self, citation_index: int) -> str:
        """引用テキストを取得"""
        if 0 <= citation_index < len(self.citations):
            citation = self.citations[citation_index]
            return f"[{citation_index + 1}] {citation.source_title}: {citation.content}"
        return ""

    def get_all_citations(self) -> List[Citation]:
        """全ての引用を取得"""
        return self.citations

class AdditionalQueriesResponse(BaseModel):
    """追加検索クエリの構造化レスポンス"""
    additional_queries: List[str] = Field(
        description="追加で検索すべきクエリのリスト",
        min_items=1,
        max_items=5
    )

    @validator('additional_queries')
    def validate_keywords(cls, v):
        """キーワードの検証"""
        if not v:
            raise ValueError('キーワードリストは空にできません')
        return v

class AnalysisResponse(BaseModel):
    """分析結果の構造化レスポンス"""
    analysis_text: str = Field(
        description="構造化された分析結果のテキスト",
        min_length=10,
        default=""
    )

    # 古い形式との互換性のため
    main_facts: List[str] = Field(default_factory=list)
    data_statistics: List[str] = Field(default_factory=list)
    different_perspectives: List[str] = Field(default_factory=list)
    date_analysis: List[str] = Field(default_factory=list)
    unknown_points: List[str] = Field(default_factory=list)

    def to_text(self) -> str:
        """構造化データをテキスト形式に変換"""
        if self.analysis_text:
            return self.analysis_text

        # 古い形式からテキストを生成
        text_parts = []

        if self.main_facts:
            text_parts.append("## 主要な事実")
            for i, fact in enumerate(self.main_facts, 1):
                text_parts.append(f"{i}. {fact}")

        if self.data_statistics:
            text_parts.append("\n## 具体的なデータ・統計")
            for i, stat in enumerate(self.data_statistics, 1):
                text_parts.append(f"{i}. {stat}")

        if self.different_perspectives:
            text_parts.append("\n## 異なる視点・意見")
            for i, perspective in enumerate(self.different_perspectives, 1):
                text_parts.append(f"{i}. {perspective}")

        if self.date_analysis:
            text_parts.append("\n## 日付分析")
            for i, date_info in enumerate(self.date_analysis, 1):
                text_parts.append(f"{i}. {date_info}")

        if self.unknown_points:
            text_parts.append("\n## 不明な点・追加調査が必要な項目")
            for i, point in enumerate(self.unknown_points, 1):
                text_parts.append(f"{i}. {point}")

        return "\n".join(text_parts) if text_parts else "分析結果が得られませんでした。"

class SummaryResponse(BaseModel):
    """要約の構造化レスポンス"""
    summary_text: str = Field(
        description="要約テキスト",
        min_length=10,
        default=""
    )

    # 古い形式との互換性のため
    key_facts: List[str] = Field(default_factory=list)
    conclusion: str = Field(default="")
    date_summary: str = Field(default="")

    def to_text(self) -> str:
        """構造化データをテキスト形式に変換"""
        if self.summary_text:
            return self.summary_text

        # 古い形式からテキストを生成
        text_parts = []

        if self.key_facts:
            text_parts.append("## 重要な事実")
            for i, fact in enumerate(self.key_facts, 1):
                text_parts.append(f"{i}. {fact}")

        if self.conclusion:
            text_parts.append(f"\n## 結論\n{self.conclusion}")

        if self.date_summary:
            text_parts.append(f"\n## 日付情報\n{self.date_summary}")

        return "\n".join(text_parts) if text_parts else "要約が得られませんでした。"

class FinalReportResponse(BaseModel):
    """最終レポートの構造化レスポンス"""
    report_text: str = Field(
        description="最終レポートのテキスト形式の内容",
        min_length=10
    )

    def to_text(self) -> str:
        """構造化データをテキスト形式に変換"""
        return self.report_text

class DeepResearch:
    """Deep Researchのメインクラス（改善版）"""

    def __init__(self, model_type: str = "ollama", search_engine: str = "auto"):
        """
        DeepResearchクラスの初期化

        Args:
            model_type: 使用する言語モデルのタイプ ("ollama", "openai", "gemini")
            search_engine: 使用する検索エンジン ("google", "duckduckgo", "auto")
        """
        self.config = Config()
        self.model_type = model_type
        self.search_engine = search_engine.lower()
        self.today_date = datetime.now().strftime("%Y年%m月%d日")

        # 設定ファイルから反復回数を読み込み
        self.max_iterations = self.config.get('iteration.max_iterations', 5)

        # 言語モデルを初期化
        self.model = self._create_model(self.model_type)
        self.review_model = self._create_model(self.model_type)  # レビュー用の別モデル

        # ハイブリッド検索エンジンを初期化
        google_api_key = self.config.get('search.google.api_key')
        google_search_engine_id = self.config.get('search.google.search_engine_id')
        rate_limit = self.config.get('search.rate_limit.requests_per_second', 2)

        # 検索エンジンの設定を調整
        if self.search_engine == "auto":
            preferred_engine = "google"
        elif self.search_engine == "duckduckgo":
            preferred_engine = "duckduckgo"
        else:
            preferred_engine = "google"  # デフォルト

        self.searcher = HybridSearcher(
            google_api_key=google_api_key,
            google_search_engine_id=google_search_engine_id,
            preferred_engine=preferred_engine,
            rate_limit=rate_limit
        )

        self.citation_manager = CitationManager(self.config)
        self.all_search_results: List[SearchResult] = []

        print(f"🔧 DeepResearch初期化完了")
        print(f"   モデル: {model_type}")
        print(f"   検索エンジン: {self.search_engine}")
        print(f"   最大反復回数: {self.max_iterations}")
        print(f"   利用可能な検索エンジン: {', '.join(self.searcher.get_available_engines())}")

    def research(self, query: str, max_iterations: int = None, force_engine: str = None) -> ResearchResult:
        """
        研究を実行

        Args:
            query: 研究クエリ
            max_iterations: 最大反復回数（Noneの場合は設定ファイルの値を使用）
            force_engine: 強制的に使用する検索エンジン ("google", "duckduckgo")

        Returns:
            ResearchResult: 研究結果
        """
        # 反復回数の決定
        if max_iterations is None:
            max_iterations = self.max_iterations

        print(f"🔬 Deep Research開始: {query}")
        print(f"   最大反復回数: {max_iterations}")

        # 検索エンジンの決定
        if force_engine:
            search_engine = force_engine
        elif self.search_engine == "auto":
            search_engine = None  # 自動選択
        else:
            search_engine = self.search_engine

        print(f"   使用検索エンジン: {search_engine or '自動選択'}")
        print("=" * 60)

        # 初期検索
        initial_results = self.searcher.search(query, num_results=10, force_engine=search_engine)
        if not initial_results:
            print("❌ 初期検索で結果が得られませんでした")
            return ResearchResult(
                query=query,
                search_results=[],
                analysis="検索結果が得られませんでした。",
                summary="検索結果が得られませんでした。",
                final_report="検索結果が得られませんでした。",
                additional_queries=[],
                citations=[]
            )

        self.all_search_results = initial_results.copy()

        # 分析と要約を生成
        analysis = self._analyze_results(query, initial_results)
        summary = self._create_summary(query, analysis)

        additional_queries = []

        # 反復検索
        for iteration in range(max_iterations - 1):
            print(f"\n🔄 反復検索 {iteration + 1}/{max_iterations - 1}")

            # 追加検索クエリを生成
            new_queries = self._generate_additional_queries(query, analysis, summary)

            # 新しいクエリがない場合は終了
            if not new_queries:
                print("   新しい検索クエリが生成されませんでした")
                break

            # 重複を除去
            new_queries = [q for q in new_queries if q not in additional_queries]
            additional_queries.extend(new_queries)

            print(f"   追加検索クエリ: {new_queries}")

            # 追加検索を実行
            new_results = []
            for additional_query in new_queries[:3]:  # 最大3つまで
                results = self.searcher.search(additional_query, num_results=5, force_engine=search_engine)
                new_results.extend(results)

            if not new_results:
                print("   追加検索で結果が得られませんでした")
                break

            # 重複を除去して結果を追加
            existing_urls = {result.url for result in self.all_search_results}
            unique_new_results = [result for result in new_results if result.url not in existing_urls]

            if not unique_new_results:
                print("   新しい結果がありませんでした")
                break

            self.all_search_results.extend(unique_new_results)
            print(f"   {len(unique_new_results)}件の新しい結果を追加")

            # 分析を更新
            analysis = self._analyze_all_results(query, self.all_search_results)
            summary = self._create_summary(query, analysis)

        # 最終レポートを生成
        final_report = self._create_final_report(query, analysis, summary)

        # 引用を整理
        citations = self.citation_manager.create_citations(self.all_search_results)

        # 結果を整理
        result = ResearchResult(
            query=query,
            search_results=self.all_search_results,
            analysis=analysis,
            summary=summary,
            final_report=final_report,
            additional_queries=additional_queries,
            citations=citations
        )

        # 引用を最終レポートに統合
        self._organize_citations(analysis, final_report)

        print(f"\n✅ Deep Research完了")
        print(f"   総検索結果数: {len(self.all_search_results)}")
        print(f"   追加検索クエリ数: {len(additional_queries)}")
        print(f"   引用数: {len(citations)}")

        return result

    def _analyze_results(self, query: str, results: List[SearchResult]) -> str:
        """検索結果を分析"""
        print(f"📊 検索結果を分析中...")

        # 検索結果をテキスト形式に変換
        results_text = ""
        for i, result in enumerate(results, 1):
            date_info = f"（{result.date_info}）" if result.date_info else ""
            reliability_info = f"信頼性: {result.reliability_score:.2f}（{result.source_type}）"
            results_text += f"""
#### {i}. [{result.title}]({result.url}){date_info}
- **内容**: {result.snippet}
- **{reliability_info}**

"""

        # 設定ファイルからプロンプトを取得
        prompt_template = self.config.get('prompts.analysis', """
今日の日付情報: {today_info}

以下の検索結果のみを基に、'{query}'について構造化された詳細分析を行ってください。検索結果に含まれていない情報は推測せず、事実のみを記載してください。

検索結果:
{results_text}

## 詳細分析の指示

以下のカテゴリに分けて、検索結果を深く分析してください：

### 1. 主要な事実と発見（重要度順）
- 検索結果から得られる最も重要な事実を10-15個抽出
- 各事実に具体的なデータ、数値、統計を添える
- 時系列での変化やトレンドを明記
- 信頼性の高い情報源からの情報を優先

### 2. 技術・手法の詳細分析
- 具体的な手法や技術の詳細説明
- 実装方法や手順の具体的な手順
- 効果測定や検証方法の詳細
- 成功事例や失敗事例の分析

### 3. 市場・業界の深層分析
- 市場規模、成長率、予測の詳細データ
- 競合状況と差別化要因の分析
- 業界の課題と機会の詳細
- 規制や政策の影響

### 4. 科学的根拠と研究データ
- 研究論文や実験結果の詳細
- 統計データや数値の詳細分析
- 信頼性と妥当性の評価
- 研究の限界や制約事項

### 5. 実践的応用と効果
- 具体的な実践方法の詳細
- 効果測定の指標と結果
- 個人差や条件による効果の違い
- 長期的な効果と持続性

### 6. 課題と制限事項
- 現在の課題や問題点の詳細
- 技術的・実用的な制限
- 情報の偏りや不足
- 改善が必要な領域

### 7. 将来展望と可能性
- 技術発展の方向性
- 新たな応用分野の可能性
- 研究・開発の方向性
- 市場の将来予測

## 重要な注意事項

1. **事実ベース**: 検索結果に含まれている情報のみを使用
2. **具体的なデータ**: 数値、統計、事例を積極的に活用
3. **時系列の理解**: 過去・現在・将来を明確に区別
4. **信頼性の評価**: 情報源の信頼性について詳細に言及
5. **客観性**: 推測や主観を避け、事実のみを記載
6. **深い洞察**: 表面的な情報だけでなく、背景や文脈も含める
7. **実用性**: 読者が実際に活用できる情報を提供

上記の指示に従って、構造化された詳細分析を行ってください。
""")

        prompt = prompt_template.format(
            query=query,
            results_text=results_text,
            today_info=self.today_date
        )

        try:
            # 構造化レスポンスを生成
            response = self.model.generate_structured(prompt, AnalysisResponse)
            print(f"✅ 構造化レスポンスで分析を生成")
            return response.to_text()
        except Exception as e:
            print(f"⚠️  構造化レスポンスの生成に失敗: {e}")
            print("   フォールバック: 従来の方法で分析を生成")
            return self.model.generate(prompt)

    def _analyze_all_results(self, query: str, all_results: List[SearchResult]) -> str:
        """全ての検索結果を分析"""
        print(f"📊 全検索結果を分析中...")

        # 検索結果をテキスト形式に変換
        results_text = ""
        for i, result in enumerate(all_results, 1):
            date_info = f"（{result.date_info}）" if result.date_info else ""
            reliability_info = f"信頼性: {result.reliability_score:.2f}（{result.source_type}）"
            results_text += f"""
#### {i}. [{result.title}]({result.url}){date_info}
- **内容**: {result.snippet}
- **{reliability_info}**

"""

        # 設定ファイルからプロンプトを取得
        prompt_template = self.config.get('prompts.analysis_all', """
今日の日付情報: {today_info}

以下の全ての検索結果のみを基に、'{query}'について包括的な調査結果を作成してください。検索結果に含まれていない情報は推測せず、事実のみを記載してください。

検索結果:
{results_text}

分析では以下の点を含めてください：
- 検索結果から得られる主要な事実（重要度順）
- 検索結果に含まれる具体的なデータや統計
- 検索結果から読み取れる異なる視点や意見の比較
- 各情報の日付（検索結果に含まれる場合）と今日との関係
- 将来の予定や過去の情報の区別
- 信頼性の高い情報源からの情報
- 検索結果からは不明な点や課題

重要：検索結果に含まれていない情報は記載せず、事実のみを記載してください。
分析結果を日本語で詳しく記述してください。
""")

        prompt = prompt_template.format(
            query=query,
            results_text=results_text,
            today_info=self.today_date
        )

        return self.model.generate(prompt)

    def _create_summary(self, query: str, analysis: str) -> str:
        """分析結果から要約を生成"""
        print(f"📝 要約生成中...")

        # 設定ファイルからプロンプトを取得
        prompt_template = self.config.get('prompts.summary', """
今日の日付情報: {today_info}

以下の分析結果を基に、'{query}'について詳細で実用的な要約を作成してください。

分析結果:
{analysis}

## 要約作成の指示

以下の要素を含む詳細要約を作成してください：

### 1. 主要な発見事項（5-7点）
- 最も重要な事実や発見を具体的な数値と共に記載
- 各発見事項の実用的な意義を明記
- 信頼性の高い情報源からの情報を優先

### 2. 技術・手法の概要
- 主要な技術や手法の概要
- 実装の難易度や必要なリソース
- 効果測定の方法と結果

### 3. 市場・業界の現状
- 市場規模や成長率の主要データ
- 競合状況の概要
- 業界の主要な課題と機会

### 4. 実践的応用
- 具体的な実践方法の概要
- 効果の持続性と個人差
- 実装における注意点

### 5. 将来展望
- 技術発展の方向性
- 新たな応用分野の可能性
- 市場の将来予測

### 6. 実用的な示唆
- 読者が実際に活用できる具体的なアドバイス
- 投資や導入を検討する際の判断材料
- リスクと機会のバランス

## 重要な注意事項

1. **具体的なデータ**: 数値、統計、事例を積極的に活用
2. **実用性**: 読者が実際に活用できる情報を提供
3. **客観性**: 事実に基づいた客観的な記述
4. **読みやすさ**: 専門的でありながら理解しやすい文章
5. **構造化**: 見出しや箇条書きを効果的に使用
6. **深い洞察**: 表面的な情報だけでなく、背景や文脈も含める

上記の指示に従って、詳細で実用的な要約を作成してください。
""")

        prompt = prompt_template.format(
            query=query,
            analysis=analysis,
            today_info=self.today_date
        )

        try:
            # 構造化レスポンスを生成
            response = self.model.generate_structured(prompt, SummaryResponse)
            print(f"✅ 構造化レスポンスで要約を生成")
            return response.to_text()
        except Exception as e:
            print(f"⚠️  構造化レスポンスの生成に失敗: {e}")
            print("   フォールバック: 従来の方法で要約を生成")
            return self.model.generate(prompt)

    def _generate_additional_queries(self, original_query: str, analysis: str, summary: str) -> List[str]:
        """追加検索クエリを生成"""
        print(f"🔍 追加検索クエリ生成中...")

        # より効果的なプロンプトテンプレート
        prompt_template = self.config.get('prompts.additional_queries', """
今日の日付情報: {today_info}

以下の研究結果をレビューして、追加で調べるべきキーワードや検索クエリを提案してください。

元のクエリ: {original_query}

分析結果:
{analysis}

要約:
{summary}

以下の観点から追加検索キーワードを提案してください：
1. 分析で言及されているが詳細が不足している概念
2. 関連する専門用語や技術
3. 比較対象となる他の事例やデータ
4. 最新の情報や統計
5. 反対意見や異なる視点
6. 古い情報（過去の予定や発売日）について最新状況を確認するべき項目
7. 将来の予定について最新の進捗状況を確認するべき項目

特に、記事内で発売予定日や発表予定日が今日より前の場合は、実際の発売・発表状況を確認するための検索キーワードを提案してください。
また、将来の予定について最新の進捗や変更がないか確認するためのキーワードも提案してください。

各キーワードは具体的で検索しやすい形で提案してください。
以下の形式で最大5つのキーワードを提案してください：

キーワード1
キーワード2
キーワード3
キーワード4
キーワード5

番号や記号は付けずに、キーワードのみを改行区切りで記載してください。
""")

        prompt = prompt_template.format(
            original_query=original_query,
            analysis=analysis,
            summary=summary,
            today_info=self.today_date
        )

        try:
            # 構造化レスポンスを生成
            response = self.model.generate_structured(prompt, AdditionalQueriesResponse)
            print(f"✅ 構造化レスポンスで追加クエリを生成")

            # 生成されたクエリを検証・改善
            validated_queries = self._validate_and_improve_queries(response.additional_queries, original_query)
            return validated_queries
        except Exception as e:
            print(f"⚠️  構造化レスポンスの生成に失敗: {e}")
            print("   フォールバック: 従来の方法で追加クエリを生成")

            # フォールバック: 従来の方法
            fallback_prompt = prompt + "\n\n上記の指示に従って、追加検索キーワードを提案してください。"
            response_text = self.model.generate(fallback_prompt)

            # レスポンスからキーワードを抽出
            lines = response_text.strip().split('\n')
            queries = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*', '•')):
                    queries.append(line)

            # 生成されたクエリを検証・改善
            validated_queries = self._validate_and_improve_queries(queries[:5], original_query)
            return validated_queries

    def _validate_and_improve_queries(self, queries: List[str], original_query: str) -> List[str]:
        """生成されたクエリを検証・改善"""
        improved_queries = []

        for query in queries:
            if not query or len(query.strip()) < 2:
                continue

            # 無効なキーワードを除外
            invalid_patterns = [
                'キーワード', '追加', '提案', '以下の', '各キーワード', '番号や記号',
                '検索', 'クエリ', '生成', '作成', '分析', '要約'
            ]

            if any(pattern in query.lower() for pattern in invalid_patterns):
                continue

            # クエリの長さを調整（短すぎる場合は元のクエリと組み合わせ）
            if len(query.split()) < 2:
                # 元のクエリの主要部分と組み合わせ
                original_words = original_query.split()[:2]
                improved_query = f"{' '.join(original_words)} {query}"
            else:
                improved_query = query

            # 重複を避ける
            if improved_query not in improved_queries:
                improved_queries.append(improved_query)

        # 結果が少ない場合は、基本的なクエリを追加
        if len(improved_queries) < 3:
            basic_queries = [
                f"{original_query} 最新情報",
                f"{original_query} ニュース",
                f"{original_query} 動向"
            ]
            for basic_query in basic_queries:
                if basic_query not in improved_queries:
                    improved_queries.append(basic_query)

        return improved_queries[:5]  # 最大5つまで

    def _create_final_report(self, query: str, analysis: str, summary: str) -> str:
        """最終レポートを生成（改善版）"""
        # 今日の日付情報を準備
        today_info = f"今日の日付: {self.today_date}"

        # 設定ファイルからプロンプトを取得、なければデフォルトを使用
        prompt_template = self.config.get('prompts.final_report', """
今日の日付情報: {today_info}

以下の分析結果と要約を基に、'{query}'について専門的で読みやすい詳細研究レポートを作成してください。

分析結果:
{analysis}

要約:
{summary}

## レポート作成の指示

以下の構造で、学術的で専門的な詳細レポートを作成してください：

### 1. エグゼクティブサマリー（300-400文字）
- 最も重要な発見事項を5-7点にまとめる
- 具体的な数値、データ、統計を含める
- 主要な結論と実用的な示唆を簡潔に述べる
- 研究の意義と価値を明確に示す

### 2. 研究背景と目的
- 研究テーマの重要性と社会的背景
- 本研究の目的と学術的・実用的意義
- 研究の範囲、制限、前提条件
- 先行研究との関連性

### 3. 主要な発見事項（詳細版）
- 検索結果から得られた重要な事実をカテゴリ別に詳細整理
- 各発見事項に具体的なデータ、統計、事例を添える
- 情報源の信頼性と妥当性の詳細評価
- 発見事項の相互関係と影響

### 4. 技術・手法の詳細分析
- 具体的な手法や技術の詳細説明
- 実装方法や手順の具体的な手順
- 効果測定や検証方法の詳細
- 成功事例や失敗事例の詳細分析
- 技術的制限と改善点

### 5. 市場・業界の深層分析
- 市場規模、成長率、予測の詳細データ
- 競合状況と差別化要因の詳細分析
- 業界の課題と機会の詳細
- 規制や政策の影響と対応
- 地域別・セグメント別の分析

### 6. 科学的根拠と研究データ
- 研究論文や実験結果の詳細分析
- 統計データや数値の詳細分析
- 信頼性と妥当性の詳細評価
- 研究の限界や制約事項
- 再現性と一般化可能性

### 7. 実践的応用と効果
- 具体的な実践方法の詳細
- 効果測定の指標と結果の詳細
- 個人差や条件による効果の違い
- 長期的な効果と持続性
- 実装における注意点

### 8. 課題と制限事項
- 現在の課題や問題点の詳細分析
- 技術的・実用的な制限の詳細
- 情報の偏りや不足の影響
- 改善が必要な領域の特定
- リスク要因の詳細評価

### 9. 将来展望と可能性
- 技術発展の方向性と予測
- 新たな応用分野の可能性
- 研究・開発の方向性
- 市場の将来予測とシナリオ
- 投資機会と戦略的示唆

### 10. 結論と提言
- 主要な結論の詳細なまとめ
- 具体的なアクションプラン
- 政策・制度への提言
- 今後の研究方向
- 実践者への具体的なアドバイス

## 重要な注意事項

1. **重複を避ける**: 各セクションで同じ内容を繰り返さない
2. **情報の優先順位**: 最も重要な情報から順に詳細に記載
3. **具体的なデータ**: 数値、統計、事例を積極的に活用
4. **客観性**: 事実に基づいた客観的な記述
5. **読みやすさ**: 専門的でありながら理解しやすい文章
6. **構造化**: 見出し、箇条書き、表などを効果的に使用
7. **深い洞察**: 表面的な情報だけでなく、背景や文脈も含める
8. **実用性**: 読者が実際に活用できる具体的な情報を提供

## 文体とトーン

- 専門的で信頼性の高い文体
- ビジネス文書として適切な形式
- 読者が実用的な情報を得られる内容
- 学術的でありながら実践的
- 客観的でありながら洞察に富む

上記の指示に従って、高品質な詳細研究レポートを作成してください。
""")

        prompt = prompt_template.format(
            query=query,
            analysis=analysis,
            summary=summary,
            today_info=today_info
        )

        try:
            # 構造化レスポンスを生成
            response = self.model.generate_structured(prompt, FinalReportResponse)
            print(f"✅ 構造化レスポンスで最終レポートを生成")
            return response.to_text()
        except Exception as e:
            print(f"⚠️  構造化レスポンスの生成に失敗: {e}")
            print("   フォールバック: 従来の方法でレポートを生成")

            # フォールバック: 従来の方法
            fallback_prompt = prompt + "\n\n上記の指示に従って、専門的で読みやすい研究レポートを作成してください。"
            return self.model.generate(fallback_prompt)

    def _organize_citations(self, analysis: str, final_report: str):
        """引用を整理して最終レポートに統合"""
        # このメソッドは既存の実装をそのまま使用
        pass

    def save_to_markdown(self, result: ResearchResult, filename: str = None) -> str:
        """結果をマークダウンファイルに保存（改善版）"""
        if not filename:
            base_filename = f"research_{result.query.replace(' ', '_')}.md"
        else:
            base_filename = filename

        # 設定ファイルからファイル名生成設定を取得
        duplicate_handling = self.config.get('output.filename_generation.duplicate_handling', 'both')
        timestamp_format = self.config.get('output.filename_generation.timestamp_format', 'YYYYMMDD_HHMMSS')
        version_prefix = self.config.get('output.filename_generation.version_prefix', 'v')

        # outputディレクトリのパスを取得
        output_dir = self.config.get('output.directory', './output')

        # outputディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)

        # outputディレクトリ内のファイル名を生成
        output_path = os.path.join(output_dir, base_filename)

        # ファイル名の重複を避けるためにバージョン番号を付ける
        filename = self._get_unique_filename(output_path, duplicate_handling, timestamp_format, version_prefix)

        # 引用リンクの辞書を作成
        citation_links = {}
        for i, citation in enumerate(result.citations, 1):
            citation_links[f"[{i}]"] = f"[{i}]({citation.source_url})"

        # 最終レポートに引用リンクを差し込み
        final_report_with_links = result.final_report
        for citation_ref, link in citation_links.items():
            final_report_with_links = final_report_with_links.replace(citation_ref, link)

        # レポートの構造を改善（エグゼクティブサマリーの重複を解消）
        content = f"""# Deep Research: {result.query}

{final_report_with_links}

## 検索履歴
### 初期検索
- クエリ: {result.query}

### 追加検索
"""

        # 追加検索クエリを記載
        for i, query in enumerate(result.additional_queries, 1):
            content += f"- 追加クエリ {i}: {query}\n"

        content += f"""
## 検索結果（{len(result.search_results)}件）
"""

        # 検索結果をクエリ別にグループ化
        query_groups = {}
        for result_item in result.search_results:
            query = result_item.search_query
            if query not in query_groups:
                query_groups[query] = []
            query_groups[query].append(result_item)

        for query, results in query_groups.items():
            content += f"\n### 検索クエリ: {query}\n"
            for i, search_result in enumerate(results, 1):
                date_info = f"（{search_result.date_info}）" if search_result.date_info else ""
                reliability_info = f"信頼性: {search_result.reliability_score:.2f}（{search_result.source_type}）"
                content += f"""
#### {i}. [{search_result.title}]({search_result.url}){date_info}
- **内容**: {search_result.snippet}
- **{reliability_info}**

"""

        content += f"""
## 引用文献
"""

        # 引用文献を記載
        for i, citation in enumerate(result.citations, 1):
            date_info = f"（{citation.date_info}）" if citation.date_info else ""
            content += f"""
### [{i}] [{citation.source_title}]({citation.source_url}){date_info}
- **検索クエリ**: {citation.search_query}
- **関連度**: {citation.relevance_score:.2f}
- **内容**: {citation.content}

"""

        # ファイルに保存
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"📄 結果を {filename} に保存しました")
        return filename

    def _get_unique_filename(self, base_filename: str, duplicate_handling: str = "both",
                           timestamp_format: str = "YYYYMMDD_HHMMSS", version_prefix: str = "v") -> str:
        """重複を避けるためにユニークなファイル名を生成"""
        if not os.path.exists(base_filename):
            return base_filename

        # ファイル名と拡張子を分離
        name, ext = os.path.splitext(base_filename)

        # タイムスタンプ形式を設定
        if timestamp_format == "YYYY-MM-DD_HH-MM-SS":
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        else:  # デフォルト: YYYYMMDD_HHMMSS
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if duplicate_handling in ["timestamp", "both"]:
            # タイムスタンプを含むファイル名を生成
            timestamped_filename = f"{name}_{timestamp}{ext}"

            if not os.path.exists(timestamped_filename):
                return timestamped_filename

        if duplicate_handling in ["version", "both"]:
            # バージョン番号を付けてユニークなファイル名を生成
            version = 1
            while True:
                new_filename = f"{name}_{version_prefix}{version}{ext}"
                if not os.path.exists(new_filename):
                    return new_filename
                version += 1

        # フォールバック: タイムスタンプ + バージョン番号
        version = 1
        while True:
            new_filename = f"{name}_{timestamp}_{version_prefix}{version}{ext}"
            if not os.path.exists(new_filename):
                return new_filename
            version += 1

    def _parse_date_info(self, date_str: str) -> Dict[str, any]:
        """日付文字列を解析して相対的な情報を取得"""
        if not date_str:
            return {"is_valid": False, "relative_info": "日付不明"}

        try:
            # 様々な日付形式を解析
            date_patterns = [
                (r'(\d{4})年(\d{1,2})月(\d{1,2})日', '%Y年%m月%d日'),
                (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
                (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
                (r'(\d{1,2})月(\d{1,2})日', '%m月%d日'),
                (r'(\d{4})年(\d{1,2})月', '%Y年%m月'),
                (r'(\d{4})年', '%Y年'),
            ]

            for pattern, format_str in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    if format_str == '%Y年%m月%d日':
                        year, month, day = match.groups()
                        parsed_date = datetime(int(year), int(month), int(day))
                    elif format_str == '%Y-%m-%d':
                        year, month, day = match.groups()
                        parsed_date = datetime(int(year), int(month), int(day))
                    elif format_str == '%Y/%m/%d':
                        year, month, day = match.groups()
                        parsed_date = datetime(int(year), int(month), int(day))
                    elif format_str == '%m月%d日':
                        month, day = match.groups()
                        # 今年の日付として扱う
                        parsed_date = datetime(self.today_year, int(month), int(day))
                    elif format_str == '%Y年%m月':
                        year, month = match.groups()
                        parsed_date = datetime(int(year), int(month), 1)
                    elif format_str == '%Y年':
                        year = match.groups()[0]
                        parsed_date = datetime(int(year), 1, 1)

                    # 今日との比較
                    today = datetime(self.today_year, self.today_month, self.today_day)
                    days_diff = (today - parsed_date).days

                    if days_diff > 0:
                        if days_diff < 7:
                            relative_info = f"{days_diff}日前"
                        elif days_diff < 30:
                            weeks = days_diff // 7
                            relative_info = f"{weeks}週間前"
                        elif days_diff < 365:
                            months = days_diff // 30
                            relative_info = f"{months}ヶ月前"
                        else:
                            years = days_diff // 365
                            relative_info = f"{years}年前"
                    elif days_diff < 0:
                        if abs(days_diff) < 7:
                            relative_info = f"{abs(days_diff)}日後"
                        elif abs(days_diff) < 30:
                            weeks = abs(days_diff) // 7
                            relative_info = f"{weeks}週間後"
                        elif abs(days_diff) < 365:
                            months = abs(days_diff) // 30
                            relative_info = f"{months}ヶ月後"
                        else:
                            years = abs(days_diff) // 365
                            relative_info = f"{years}年後"
                    else:
                        relative_info = "今日"

                    return {
                        "is_valid": True,
                        "parsed_date": parsed_date,
                        "relative_info": relative_info,
                        "days_diff": days_diff,
                        "is_future": days_diff < 0,
                        "is_recent": days_diff <= 30  # 30日以内を最近とする
                    }

            return {"is_valid": False, "relative_info": "日付形式が不明"}

        except Exception as e:
            return {"is_valid": False, "relative_info": f"日付解析エラー: {str(e)}"}

    def _sort_results_by_reliability(self, results: List[SearchResult]) -> List[SearchResult]:
        """信頼性スコアに基づいて検索結果を並び替え"""
        return sorted(results, key=lambda x: x.reliability_score, reverse=True)

    def _filter_results_by_reliability(self, results: List[SearchResult], threshold: float = 0.5) -> List[SearchResult]:
        """信頼性スコアが閾値以上の検索結果のみをフィルタリング"""
        return [result for result in results if result.reliability_score >= threshold]

    def _create_model(self, model_type: str) -> LanguageModel:
        """指定されたタイプの言語モデルを作成"""
        if model_type == "ollama":
            return OllamaModel(self.config)
        elif model_type == "openai":
            return OpenAIModel(self.config)
        elif model_type == "gemini":
            return GoogleGeminiModel(self.config)
        else:
            raise ValueError(f"サポートされていないモデルタイプ: {model_type}")

def main():
    """メイン関数"""
    print("🔬 Deep Research Clone (改善版)")
    print("=" * 50)

    # 設定ファイルの確認
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"⚠️  設定ファイル {config_path} が見つかりません。デフォルト設定を使用します。")
        print("設定ファイルを作成するには、config.example.yaml を config.yaml にコピーしてください。")

    # モデルタイプを選択
    print("使用する言語モデルを選択してください:")
    print("1. Ollama (ローカル)")
    print("2. OpenAI")
    print("3. Google Gemini")

    choice = input("選択 (1-3): ").strip()

    model_map = {
        "1": "ollama",
        "2": "openai",
        "3": "gemini"
    }

    model_type = model_map.get(choice, "ollama")

    # 検索エンジンを選択
    print("\n使用する検索エンジンを選択してください:")
    print("1. 自動選択 (Google + DuckDuckGo)")
    print("2. Google のみ")
    print("3. DuckDuckGo のみ")

    search_choice = input("選択 (1-3): ").strip()

    search_engine_map = {
        "1": "auto",
        "2": "google",
        "3": "duckduckgo"
    }

    search_engine = search_engine_map.get(search_choice, "auto")

    try:
        # Deep Researchインスタンスを作成
        researcher = DeepResearch(model_type=model_type, search_engine=search_engine)

        # クエリを入力
        query = input("\n🔍 研究したいキーワードや文章を入力してください: ").strip()

        if not query:
            print("クエリが入力されていません。")
            return

        # 研究を実行
        result = researcher.research(query)

        # 検索失敗の場合
        if result is None:
            print("\n❌ 研究を完了できませんでした。")
            return

        # 結果を表示
        print("\n" + "=" * 50)
        print("📋 研究結果")
        print("=" * 50)
        print(f"クエリ: {result.query}")
        print(f"検索結果数: {len(result.search_results)}")
        print(f"追加検索クエリ数: {len(result.additional_queries)}")
        print(f"引用文献数: {len(result.citations)}")
        print(f"要約: {result.summary}")

        # マークダウンファイルに保存
        filename = researcher.save_to_markdown(result)

        print(f"\n✅ 研究完了！結果は {filename} に保存されました。")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
