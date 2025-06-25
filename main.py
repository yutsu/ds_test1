#!/usr/bin/env python3
"""
Deep Research Clone - 改善版
言語モデルとWeb検索を組み合わせた研究支援ツール
レビューモデルによる追加検索機能付き
"""

import os
import json
import requests
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import markdown
from dotenv import load_dotenv
import re
import yaml
from datetime import datetime
import time
import random

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
            return {
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
                    'google': {
                        'api_key': os.getenv('GOOGLE_SEARCH_API_KEY'),
                        'search_engine_id': os.getenv('GOOGLE_SEARCH_ENGINE_ID')
                    }
                },
                'citations': {
                    'auto_extract': True,
                    'relevance_threshold': 0.5,
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

    def _expand_env_vars(self, obj):
        """辞書内の環境変数を展開"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    # ${VAR_NAME} 形式の環境変数を展開
                    env_var = value[2:-1]  # ${} を除去
                    obj[key] = os.getenv(env_var, value)
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

class WebSearcher:
    """Web検索クラス（改善版）"""

    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.get('search.google.api_key')
        self.search_engine_id = config.get('search.google.search_engine_id')
        self.max_results = config.get('search.max_results', 5)

        # レート制限設定（設定ファイルから読み込み）
        self.requests_per_second = config.get('search.rate_limit.requests_per_second', 8)
        self.max_retries = config.get('search.rate_limit.max_retries', 3)
        self.retry_delay_base = config.get('search.rate_limit.retry_delay_base', 2)
        self.last_request_time = 0

    def _extract_date_info(self, title: str, snippet: str) -> Optional[str]:
        """タイトルとスニペットから日付情報を抽出"""
        # 既存の日付抽出ロジック
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
            r'(\d{1,2})月(\d{1,2})日',
            r'(\d{4})年(\d{1,2})月',
            r'(\d{4})年',
            r'(\d{1,2})時間前',
            r'(\d{1,2})日前',
            r'(\d{1,2})週間前',
            r'(\d{1,2})ヶ月前',
            r'(\d{1,2})年前',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, title + " " + snippet)
            if match:
                return match.group(0)

        return None

    def _evaluate_source_reliability(self, url: str, title: str, snippet: str) -> Dict[str, any]:
        """情報源の信頼性を評価"""
        reliability_score = 1.0
        source_type = "unknown"

        # URLベースの評価
        url_lower = url.lower()

        # 公式サイト・政府機関
        official_domains = [
            'gov.jp', 'go.jp', 'pref.', 'city.', 'town.', 'village.',
            'ac.jp', 'edu.', 'university.', 'college.',
            'org', 'association.', 'foundation.'
        ]

        # 主要メディア
        news_domains = [
            'nhk.', 'asahi.', 'mainichi.', 'yomiuri.', 'sankei.',
            'nikkei.', 'reuters.', 'bloomberg.', 'cnn.', 'bbc.'
        ]

        # 学術・研究機関
        academic_domains = [
            'research.', 'study.', 'journal.', 'paper.', 'arxiv.',
            'pubmed.', 'scholar.google.', 'jstor.'
        ]

        # ブログ・個人サイト
        blog_indicators = [
            'blog.', 'note.com', 'hatena.', 'ameblo.', 'fc2.',
            'wordpress.', 'tumblr.', 'medium.'
        ]

        # 信頼性評価
        if any(domain in url_lower for domain in official_domains):
            reliability_score = 0.9
            source_type = "official"
        elif any(domain in url_lower for domain in news_domains):
            reliability_score = 0.8
            source_type = "news"
        elif any(domain in url_lower for domain in academic_domains):
            reliability_score = 0.85
            source_type = "academic"
        elif any(indicator in url_lower for indicator in blog_indicators):
            reliability_score = 0.5
            source_type = "blog"
        else:
            reliability_score = 0.6
            source_type = "general"

        # タイトル・スニペットベースの調整
        content_lower = (title + " " + snippet).lower()

        # 信頼性を下げる要素
        if any(word in content_lower for word in ['噂', 'デマ', '未確認', '推測', '憶測']):
            reliability_score *= 0.7

        # 信頼性を上げる要素
        if any(word in content_lower for word in ['発表', '公式', '確認', '調査結果', 'データ']):
            reliability_score *= 1.1

        # スコアを0.0-1.0の範囲に制限
        reliability_score = max(0.0, min(1.0, reliability_score))

        return {
            "reliability_score": reliability_score,
            "source_type": source_type
        }

    def search(self, query: str, num_results: int = None) -> List[SearchResult]:
        """Web検索を実行（レート制限・リトライ機能付き）"""
        if num_results is None:
            num_results = self.config.get('search.max_results', 5)

        # レート制限の適用
        self._apply_rate_limit()

        for attempt in range(self.max_retries):
            try:
                # Google Custom Search APIを使用
                api_key = self.config.get('search.google.api_key')
                search_engine_id = self.config.get('search.google.search_engine_id')

                if not api_key or not search_engine_id:
                    raise ValueError("Google Custom Search API キーと検索エンジンIDが必要です")

                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': api_key,
                    'cx': search_engine_id,
                    'q': query,
                    'num': min(num_results, 10)  # Google APIの最大値は10
                }

                response = requests.get(url, params=params)

                # レスポンスの処理
                if response.status_code == 429:
                    # Too Many Requests - リトライ
                    wait_time = self.retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                    print(f"⚠️  レート制限に達しました。{wait_time:.1f}秒待機してリトライします...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 403:
                    # Forbidden - APIキーエラー
                    raise ValueError("APIキーが無効です。Google Cloud Consoleで設定を確認してください。")
                else:
                    response.raise_for_status()

                data = response.json()

                results = []
                if 'items' in data:
                    for item in data['items']:
                        title = item.get('title', '')
                        url = item.get('link', '')
                        snippet = item.get('snippet', '')

                        # 日付情報を抽出
                        date_info = self._extract_date_info(title, snippet)

                        # 信頼性評価を実行
                        reliability_info = self._evaluate_source_reliability(url, title, snippet)

                        result = SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            search_query=query,
                            date_info=date_info,
                            reliability_score=reliability_info["reliability_score"],
                            source_type=reliability_info["source_type"]
                        )
                        results.append(result)

                return results

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                    print(f"⚠️  ネットワークエラー: {e}. {wait_time:.1f}秒待機してリトライします...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 検索エラー: {e}")
                    return []
            except Exception as e:
                print(f"❌ 予期しないエラー: {e}")
                return []

        print("❌ 最大リトライ回数に達しました")
        return []

    def _apply_rate_limit(self):
        """レート制限を適用"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < 1.0 / self.requests_per_second:
            sleep_time = (1.0 / self.requests_per_second) - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

class CitationManager:
    """引用管理を行うクラス"""

    def __init__(self, config: Config):
        self.config = config
        self.citations: List[Citation] = []
        self.citation_counter = 1
        self.auto_extract = config.get('citations.auto_extract', True)
        self.relevance_threshold = config.get('citations.relevance_threshold', 0.5)

    def add_citation(self, source: SearchResult, content: str, relevance_score: float = 1.0) -> int:
        """引用を追加"""
        if relevance_score >= self.relevance_threshold:
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
        return 0

    def get_citation_text(self, citation_index: int) -> str:
        """引用テキストを取得"""
        if 0 <= citation_index - 1 < len(self.citations):
            citation = self.citations[citation_index - 1]
            return f"[{citation_index}] {citation.source_title} ({citation.source_url})"
        return f"[{citation_index}] 引用が見つかりません"

    def get_all_citations(self) -> List[Citation]:
        """全ての引用を取得"""
        return self.citations

class DeepResearch:
    """Deep Researchのメインクラス（改善版）"""

    def __init__(self, model_type: str = None, config_path: str = "config.yaml"):
        self.config = Config(config_path)
        self.model_type = model_type or self.config.get('language_model.default', 'ollama')
        self.model = self._create_model(self.model_type)
        self.review_model = self._create_model(self.model_type)  # レビュー用の別モデル
        self.searcher = WebSearcher(self.config)
        self.citation_manager = CitationManager(self.config)
        self.all_search_results: List[SearchResult] = []

        # 設定から値を取得
        self.max_iterations = self.config.get('iteration.max_iterations', 3)
        self.initial_search_count = self.config.get('iteration.initial_search_count', 8)
        self.additional_search_count = self.config.get('iteration.additional_search_count', 5)
        self.max_additional_queries = self.config.get('iteration.max_additional_queries', 3)

        # 今日の日付を取得
        self.today_date = datetime.now().strftime("%Y年%m月%d日")
        self.today_year = datetime.now().year
        self.today_month = datetime.now().month
        self.today_day = datetime.now().day

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

    def research(self, query: str, max_iterations: int = None) -> ResearchResult:
        """指定されたクエリでDeep Researchを実行（反復改善版）"""
        if max_iterations is None:
            max_iterations = self.max_iterations

        print(f"🔍 初期検索中: {query}")

        # 初期検索
        initial_results = self.searcher.search(query, num_results=self.initial_search_count)

        # 検索結果が空の場合の処理
        if not initial_results:
            print("❌ 検索結果が取得できませんでした。以下の原因が考えられます：")
            print("   - Google Custom Search APIのレート制限に達した")
            print("   - APIキーまたは検索エンジンIDが無効")
            print("   - ネットワーク接続の問題")
            print("   - 検索クエリに問題がある")
            print("\n対処法：")
            print("   - しばらく待ってから再実行してください")
            print("   - .envファイルのAPI設定を確認してください")
            print("   - 検索クエリを変更してみてください")
            return None

        # 信頼性に基づいて並び替え
        initial_results = self._sort_results_by_reliability(initial_results)

        # 信頼性の低い結果をフィルタリング（オプション）
        reliability_threshold = self.config.get('citations.reliability_threshold', 0.3)
        initial_results = self._filter_results_by_reliability(initial_results, reliability_threshold)

        self.all_search_results.extend(initial_results)

        # 初期分析
        analysis = self._analyze_results(query, initial_results)
        summary = self._create_summary(query, analysis)

        additional_queries = []

        # 反復改善
        for iteration in range(max_iterations - 1):
            print(f"🔄 反復 {iteration + 1}: レポートレビュー中...")

            # レビューモデルで追加検索キーワードを生成
            new_queries = self._generate_additional_queries(query, analysis, summary)

            # 既存のクエリと重複を避ける
            new_queries = [q for q in new_queries if q not in additional_queries and q != query]

            if not new_queries:
                print("追加の検索キーワードが見つかりませんでした")
                break

            additional_queries.extend(new_queries[:self.max_additional_queries])

            # 追加検索を実行
            for additional_query in new_queries[:self.max_additional_queries]:
                print(f"🔍 追加検索: {additional_query}")
                additional_results = self.searcher.search(additional_query, num_results=self.additional_search_count)
                self.all_search_results.extend(additional_results)

            # 全結果で再分析
            analysis = self._analyze_all_results(query, self.all_search_results)
            summary = self._create_summary(query, analysis)

            print(f"📊 累積検索結果: {len(self.all_search_results)}件")

        # 最終レポート生成
        final_report = self._create_final_report(query, analysis, summary)

        # 引用を整理
        if self.citation_manager.auto_extract:
            self._organize_citations(analysis, final_report)

        return ResearchResult(
            query=query,
            search_results=self.all_search_results,
            analysis=analysis,
            summary=summary,
            citations=self.citation_manager.get_all_citations(),
            additional_queries=additional_queries,
            final_report=final_report
        )

    def _analyze_results(self, query: str, search_results: List[SearchResult]) -> str:
        """検索結果を分析"""
        # 今日の日付情報を準備
        today_info = f"今日の日付: {self.today_date}"

        # 各検索結果に相対的な日付情報を追加
        results_with_date_info = []
        for result in search_results:
            date_analysis = self._parse_date_info(result.date_info)
            relative_date = date_analysis.get("relative_info", "日付不明")
            is_future = date_analysis.get("is_future", False)
            is_recent = date_analysis.get("is_recent", False)

            date_status = ""
            if is_future:
                date_status = "（将来の予定）"
            elif is_recent:
                date_status = "（最近の情報）"
            elif date_analysis.get("is_valid", False):
                date_status = "（過去の情報）"

            # 信頼性情報を追加
            reliability_info = f"信頼性: {result.reliability_score:.2f}（{result.source_type}）"

            results_with_date_info.append(
                f"タイトル: {result.title}\n"
                f"URL: {result.url}\n"
                f"内容: {result.snippet}\n"
                f"日付情報: {result.date_info or '不明'} → {relative_date}{date_status}\n"
                f"{reliability_info}"
            )

        results_text = "\n\n".join(results_with_date_info)

        # 設定ファイルからプロンプトを取得、なければデフォルトを使用
        prompt_template = self.config.get('prompts.analysis', """
今日の日付情報: {today_info}

以下の検索結果のみを基に、'{query}'について分析してください。検索結果に含まれていない情報は推測せず、事実のみを記載してください。

検索結果:
{results_text}

分析では以下の点を含めてください：
- 検索結果から得られる主要な事実（重要度順）
- 検索結果に含まれる具体的なデータや統計
- 検索結果から読み取れる異なる視点や意見
- 各情報の日付（検索結果に含まれる場合）と今日との関係
- 将来の予定や過去の情報の区別
- 検索結果からは不明な点や追加で調べるべき点

重要：検索結果に含まれていない情報は記載せず、事実のみを記載してください。
分析結果を日本語で詳しく記述してください。
""")

        prompt = prompt_template.format(
            query=query,
            results_text=results_text,
            today_info=today_info
        )
        return self.model.generate(prompt)

    def _analyze_all_results(self, query: str, all_results: List[SearchResult]) -> str:
        """全検索結果を分析"""
        # 今日の日付情報を準備
        today_info = f"今日の日付: {self.today_date}"

        # 各検索結果に相対的な日付情報を追加
        results_with_date_info = []
        for result in all_results:
            date_analysis = self._parse_date_info(result.date_info)
            relative_date = date_analysis.get("relative_info", "日付不明")
            is_future = date_analysis.get("is_future", False)
            is_recent = date_analysis.get("is_recent", False)

            date_status = ""
            if is_future:
                date_status = "（将来の予定）"
            elif is_recent:
                date_status = "（最近の情報）"
            elif date_analysis.get("is_valid", False):
                date_status = "（過去の情報）"

            results_with_date_info.append(
                f"タイトル: {result.title}\n"
                f"URL: {result.url}\n"
                f"内容: {result.snippet}\n"
                f"検索クエリ: {result.search_query}\n"
                f"日付情報: {result.date_info or '不明'} → {relative_date}{date_status}"
            )

        results_text = "\n\n".join(results_with_date_info)

        # 設定ファイルからプロンプトを取得、なければデフォルトを使用
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
            today_info=today_info
        )
        return self.model.generate(prompt)

    def _create_summary(self, query: str, analysis: str) -> str:
        """要約を生成"""
        # 設定ファイルからプロンプトを取得、なければデフォルトを使用
        prompt_template = self.config.get('prompts.summary', """
以下の分析結果のみを基に、'{query}'について簡潔な要約を作成してください。分析結果に含まれていない情報は推測せず、事実のみを記載してください。

分析結果:
{analysis}

要約では以下の点を含めてください：
- 検索結果から得られる最も重要な事実（3-5点）
- 各事実の日付（分析結果に含まれる場合）
- 結論（検索結果から読み取れる範囲で）

重要：分析結果に含まれていない情報は記載せず、事実のみを記載してください。
要約を日本語で簡潔に記述してください。
""")

        prompt = prompt_template.format(query=query, analysis=analysis)
        return self.model.generate(prompt)

    def _generate_additional_queries(self, original_query: str, analysis: str, summary: str) -> List[str]:
        """レビューモデルで追加検索キーワードを生成"""
        # 今日の日付情報を準備
        today_info = f"今日の日付: {self.today_date}"

        # 設定ファイルからプロンプトを取得、なければデフォルトを使用
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
6. 古い情報（過去の予定や発売日）について最新状況を確認すべき項目
7. 将来の予定について最新の進捗状況を確認すべき項目

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
            today_info=today_info
        )
        response = self.review_model.generate(prompt)

        # レスポンスからキーワードを抽出（改善版）
        lines = response.strip().split('\n')
        queries = []
        for line in lines:
            line = line.strip()
            # 空行、番号、記号、説明文を除外
            if (line and
                not line.startswith(('#', '-', '*', '1.', '2.', '3.', '4.', '5.', 'キーワード', '追加', '提案')) and
                len(line) > 2 and  # 短すぎる行を除外
                not line.endswith(':') and  # 説明文を除外
                not line.startswith('以下の') and  # 説明文を除外
                not line.startswith('各キーワード') and  # 説明文を除外
                not line.startswith('番号や記号') and  # 説明文を除外
                not line.startswith('重要') and  # 説明文を除外
                not line.startswith('分析で言及') and  # 説明文を除外
                not line.startswith('関連する') and  # 説明文を除外
                not line.startswith('比較対象') and  # 説明文を除外
                not line.startswith('最新の') and  # 説明文を除外
                not line.startswith('反対意見') and  # 説明文を除外
                not line.startswith('特に') and  # 説明文を除外
                not line.startswith('また') and  # 説明文を除外
                not line.startswith('各キーワード')):  # 説明文を除外
                queries.append(line)

        print(f"生成された追加クエリ: {queries}")
        return queries[:5]  # 最大5つまで

    def _create_final_report(self, query: str, analysis: str, summary: str) -> str:
        """最終レポートを生成（統合版）"""
        # 今日の日付情報を準備
        today_info = f"今日の日付: {self.today_date}"

        # 引用情報を準備
        citation_texts = []
        for i, result in enumerate(self.all_search_results, 1):
            date_analysis = self._parse_date_info(result.date_info)
            relative_date = date_analysis.get("relative_info", "日付不明")
            date_info = f"（{result.date_info}）" if result.date_info else ""
            citation_texts.append(f"[{i}] {result.title}{date_info} → {relative_date}: {result.url}")

        citations_section = "\n".join(citation_texts)

        # 設定ファイルからプロンプトを取得、なければデフォルトを使用
        prompt_template = self.config.get('prompts.final_report', """
今日の日付情報: {today_info}

以下の分析結果のみを基に、'{query}'について学術的な品質の統合レポートを作成してください。検索結果に含まれていない情報は推測せず、事実のみを記載してください。

分析結果:
{analysis}

要約:
{summary}

利用可能な情報源:
{citations_section}

レポートでは以下の構成で作成してください：
1. エグゼクティブサマリー（検索結果から得られる最も重要な事実）
2. 背景と目的
3. 主要な発見事項（検索結果に基づく詳細な分析）
4. データと統計（検索結果に含まれる数値情報）
5. 異なる視点の比較（検索結果から読み取れる範囲で）
6. 結論と推奨事項（検索結果から導き出せる範囲で）
7. 今後の研究方向

各セクションで適切な引用を行い、信頼性の高い情報源を明記してください。
各情報の日付（検索結果に含まれる場合）と今日との関係も明記してください。
将来の予定や過去の情報を区別して記載してください。
引用は [1], [2] の形式で記載し、対応する情報源を明記してください。

重要：検索結果に含まれていない情報は記載せず、事実のみを記載してください。
""")

        prompt = prompt_template.format(
            query=query,
            analysis=analysis,
            summary=summary,
            citations_section=citations_section,
            today_info=today_info
        )

        return self.model.generate(prompt)

    def _organize_citations(self, analysis: str, final_report: str):
        """分析結果とレポートから引用を整理"""
        # 分析結果から重要な情報を抽出して引用を作成
        for result in self.all_search_results:
            # 結果の内容が分析やレポートで言及されているかチェック
            if result.title in analysis or result.title in final_report:
                self.citation_manager.add_citation(result, result.snippet, relevance_score=1.0)

    def save_to_markdown(self, result: ResearchResult, filename: str = None) -> str:
        """結果をマークダウンファイルに保存（改善版）"""
        if not filename:
            filename = f"research_{result.query.replace(' ', '_')}.md"

        # 引用リンクの辞書を作成
        citation_links = {}
        for i, citation in enumerate(result.citations, 1):
            citation_links[f"[{i}]"] = f"[{i}]({citation.source_url})"

        # 最終レポートに引用リンクを差し込み
        final_report_with_links = result.final_report
        for citation_ref, link in citation_links.items():
            final_report_with_links = final_report_with_links.replace(citation_ref, link)

        content = f"""# Deep Research: {result.query}

## エグゼクティブサマリー
{result.summary}

## 統合レポート
{final_report_with_links}

## 詳細分析
{result.analysis}

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

    try:
        # Deep Researchインスタンスを作成
        researcher = DeepResearch(model_type, config_path)

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
