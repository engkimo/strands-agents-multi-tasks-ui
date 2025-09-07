# PR パッケージングと CodeRabbit 評価（計画）

## 背景
- ベスト出力（best_tool）を PR 案としてまとめ、GitHub 上に Pull Request を作成。
- CodeRabbit（GitHub App）が自動でレビューを実行し、結果をPR上で確認する。

## オフライン・パッケージ（先行実装）
- Backend: `POST /runs/{id}/package_pr`
  - 入力: `tool?`（任意: 採用するツール）, `title?`
  - 動作: Runの `tool`（指定がなければ `best_tool` → 最初の成功ノード）を採用。
  - 出力: `var/data/runs/<id>/pr/` に以下を生成
    - `summary.md`（タイトル/説明/採用理由/スコア/プロポーザル全文）
    - `patch.txt`（出力内に unified diff が含まれていれば抽出して保存）
    - `review.md`（簡易ヒューリスティックレビュー: 情報量/コード/差分/テスト語）
- UI: Run詳細の差分ビュー直下に「PRパッケージ作成（左を採用）」ボタン。作成後はプレビューを表示（summary/review/patch）

## GitHub 連携（任意）
- 設定: `.env` に `GITHUB_TOKEN`, `GITHUB_REPO=owner/name`, `GITHUB_BASE=main`
- Backend: `POST /runs/{id}/create_pr`
  - GitHub REST API でブランチ作成/コミット/PR作成（差分の適用方法はステージングディレクトリで実施）
  - レスポンス: 作成された PR の URL
- UI: 作成結果URLを表示、PRへ遷移

## CodeRabbit 連携（任意）
- 手順: 対象リポジトリに CodeRabbit App をインストール
- 挙動: PR 作成後、自動でレビューが実行され、PR タイムラインにコメントが生成
- UI（将来）: レビュー結果の要約をUIで参照

## 安全性・権限
- PAT/アプリ権限は最小限に（PR 作成/ブランチ作成）
- 外部送信はUIで明示/同意（MVPでは明示の操作時のみ）

---
- 本計画はMVP後の拡張。まずはオフライン・パッケージで体験を確認し、次にGitHub連携を加える。
