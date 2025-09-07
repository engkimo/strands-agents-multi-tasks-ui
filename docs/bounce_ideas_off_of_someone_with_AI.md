あなた:
difyやgithub actionsで、claude code、codex cli、gemini cli、spec kitなどをワークフロー形式で並列で実行させている人たちがいる。私はこれらをそれぞれのcliの強みを活かし、airflowやargoなど、かつて存在してきていたワークフローツールで繋いで、それぞれのcliを連携させたい。それにはairflowはpythonのoperater、argoはyamlの設定が必要だ。おそらく上記を達成するには、タスクのinputやoutputによって動的にフローを観察し、変更できるリアルタイム性が、必要だと思う。それらを達成しうるソリューションはあるか？
ChatGPT:
4 秒で完了しました

ご要望ありがとうございます。確認ですが、DifyやGitHub Actionsで複数のCLI（Claude Code、Codex CLI、Gemini CLIなど）をワークフローに連携させ、AirflowやArgoのような既存のワークフローツールを利用して動的にタスクを管理できるソリューションを探している、という理解でよろしいでしょうか？最適な情報を探すため、こちらで最新の情報を収集し、リアルタイムでフローの変更が可能なソリューションが存在するかリサーチいたします。

あなた:
自動回答
続行
ChatGPT:
4 分で完了しました

以下では、Claude Code／Codex CLI／Gemini CLI／Spec KitなどのAI用CLIをワークフローとして連携させる方法と、タスクの入力・出力に応じて動的にフローを変えたい場合に使えるツールをまとめます。

Airflow／Argoでの「動的」タスク生成は限定的

Airflow 3.x には「Dynamic Task Mapping」という仕組みがあり、前のタスクの出力に基づいてタスク数を動的に増やすことができます。ドキュメントでは、動的タスクマッピングにより「DAG作者が何個必要か事前に知らなくても、ランタイムのデータに基づいてn個のタスクを生成できる」ことが示されています
airflow.apache.org
。この機能で map–reduce のように複数CLI実行を並列化できますが、タスクの追加やDAG構造自体は実行開始後に変更できません。条件分岐は @task.branch や BranchPythonOperator で可能ですが、ブランチに配置するタスクは事前定義が必要です。

Argo Workflows もYAMLでDAGを定義します。記事では、start‑dt と end‑dt を受け取り、Pythonスクリプトで日付リストを生成するタスク date‑generator を挟み、その出力JSON配列を withParam に渡して後続タスク（CLI呼び出し）を動的に分岐させる例が紹介されています
medium.com
。並列実行数は parallelism キーで制御できます。ただしこれも「定義済みのテンプレート内でループを展開する」方法であり、実行中にDAGを変更する機能ではありません。

上記のように、AirflowやArgoはCLI呼び出しをバッチ処理やMap‑Reduce形式で並列化するには向いていますが、リアルタイムに「次にどのCLIを呼び出すか」を決めるエージェント的なワークフローには向きません。

動的な意思決定・リアルタイム性が必要なら
Prefect

Prefect 3.xは「動的ランタイム」を標榜し、実行中にデータや条件に応じてタスクや分岐を生成することができます。公式ページでは「実行中に実データや条件に基づいてタスクを動的に作成し、新しいタスクや分岐を容易に生成できる」と説明されています
docs.prefect.io
。また、Prefect 2.0以降は静的DAGの制約を撤廃し、if/elseやwhileなどのPython制御構造をそのまま使えるようになったと記されています
docs.prefect.io
。PythonコードでCLIを呼び出し、結果に応じて次のタスクを動的に生成するようなエージェント型フローを構築できます。

Burr（DAGWorks）

Burrはエージェント向けのワークフレームで、状態を持つアプリケーションを記述する「アクション」と「遷移」で構成されています。遷移は現在の状態を評価して次のアクションを決定し、「どのモデルを呼び出すか」「会話を終了するか」などの判断を行えると説明されています
burr.dagworks.io
。条件は when・expr・default などで定義し、状態変数に基づいて遷移先を決められます
burr.dagworks.io
。さらにBurrはマップリデュース型の並列実行を高レベルAPIで提供し、複数のアクションを並列に実行して結果を統合する機能（MapStates、MapActions など）を備えています
burr.dagworks.io
。例えば「ClaudeとCodexとGeminiを並列で呼び出し、結果を比較して次の処理を決める」といった使い方が容易です。

Laminar Flow（Flow by lmnr‑ai）

FlowはAIエージェント用に開発されたタスクエンジンで、静的なDAGではなく「動的タスクキュー」方式を採用しています。開発者による紹介では、Flowは「並列実行」「動的スケジューリング」「スマート依存関係」という３つの原則で設計され、タスクがランタイムに新しいタスクをスケジュールできると説明されています
news.ycombinator.com
。共有コンテキストで状態を管理し、Map‑Reduceやストリーミング結果、ループ、自己修正ワークフローなどを簡単に表現できるため、AIエージェントが「次にどのCLIを呼ぶか」を自己判断して計画を更新するような用途に適しています。

まとめと提案

Airflow/Argoで構築する場合：

各CLI（Claude Code, Codex CLI, Gemini CLI, Spec Kit）をPython/Bash Operator（Airflow）やscript/containerタスク（Argo）にラップし、環境変数やXCom/パラメータ経由で結果を次のタスクに受け渡します。

動的な分岐や並列実行が必要なら、Airflowの動的タスクマッピング
airflow.apache.org
やArgoのwithParam／whenでファンアウト/条件分岐
medium.com
を利用します。ただし、実行開始後にタスク構造を変更することはできません。

よりリアルタイム性が欲しい場合：

PrefectでCLI呼び出しをタスクとして実装し、データに応じてif/elseやループを使って動的に次のタスクを生成します。

BurrやLaminar Flowといったエージェント特化フレームワークを使うと、状態に基づく遷移や動的タスク生成が標準で提供され、複数CLIの並列実行や結果統合が容易です
burr.dagworks.io
burr.dagworks.io
news.ycombinator.com
。AIモデルの出力に合わせて次のアクション（CLI呼び出し）を決定するなど、リアルタイムにワークフローを変更できます。

その他の選択肢：

Dagster、TemporalなどもPythonベースで動的タスク生成や複雑な条件分岐をサポートしており、CLI連携を拡張できます。

AIエージェント向けのLangGraphやStrands AgentsはLLMが自律的に計画を生成し、Pydanticスキーマで出力を検証して外部ツールを呼び出す仕組みを持っているため、AIによる動的オーケストレーションが可能です
medium.com
。

以上のように、単にCLIを並列で実行するだけならAirflowやArgoで十分ですが、タスクの結果に応じてフローをリアルタイムに変えたい場合は、PrefectやBurr、Laminar Flowなど動的なワークフローエンジンを検討すると良いでしょう。

情報源
あなた:
airflowとargoはだめですね。以下が良さそう。

よりリアルタイム性が欲しい場合：

PrefectでCLI呼び出しをタスクとして実装し、データに応じてif/elseやループを使って動的に次のタスクを生成します。

BurrやLaminar Flowといったエージェント特化フレームワークを使うと、状態に基づく遷移や動的タスク生成が標準で提供され、複数CLIの並列実行や結果統合が容易です
burr.dagworks.io
burr.dagworks.io
news.ycombinator.com
。AIモデルの出力に合わせて次のアクション（CLI呼び出し）を決定するなど、リアルタイムにワークフローを変更できます。

その他の選択肢：

Dagster、TemporalなどもPythonベースで動的タスク生成や複雑な条件分岐をサポートしており、CLI連携を拡張できます。

AIエージェント向けのLangGraphやStrands AgentsはLLMが自律的に計画を生成し、Pydanticスキーマで出力を検証して外部ツールを呼び出す仕組みを持っているため、AIによる動的オーケストレーションが可能です
medium.com
。
ChatGPT:
4 分で完了しました

これまでの調査から、CLI（Claude Code／Codex CLI／Gemini CLI／Spec Kit等）の連携にリアルタイム性や動的なタスク生成が必要な場合、静的DAGベースのAirflowやArgoでは難しいことが分かりました。その代わり、以下のような動的ワークフローエンジンやAIエージェント向けフレームワークが適しています。

方式/ツール	特徴（参考情報）	備考
Prefect 2.x/Orion	Prefectの新エンジンは「静的なDAGを捨てた」ことが特徴で、ネイティブな if/for/while などの制御構造をそのまま使用し、実行時のデータに応じてタスクやフローを生成できます
prefect.io
。
具体的には、runtimeのデータを見てタスクを動的に作成したり、複雑な条件分岐や再試行を if 文で書けるため、CLIの出力に応じて次のステップを決めることが容易です
prefect.io
。	Python製で、CLI呼び出しをtask関数にラップすればよい。動的な分岐やストリーミング処理にも対応。
Burr（DagWorks）	Burrは状態遷移によるオーケストレーションを基本とし、when・expr・default 条件で次のアクション（例えばどのCLIを呼び出すか）を決定します
burr.dagworks.io
。また、MapStatesやMapActions などのAPIにより複数のアクションを並列に実行し、出力を結合する機能があり
burr.dagworks.io
、複数CLIの並列実行や結果統合に向いています。	YAML/JSONで遷移図を記述し、状態に基づき次のタスクを動的に選択可能。
Laminar Flow（lmnr-ai）	Flowは静的なDAGではなく動的タスクキュー方式で、タスクが実行中に新しいタスクをスケジュールできるのが特徴です。開発者による紹介では、並列実行・動的スケジューリング・スマート依存関係の3原則により、マップリデュースや自己修正ワークフロー、ループ、ストリーミングなどを自然に表現できると述べています
news.ycombinator.com
。	スレッドセーフな共有コンテキストで状態を管理し、AIエージェントが次のタスクを決めながら計画を更新する用途に適しています。
Dagster	Dagsterは動的出力（DynamicOut / DynamicOutput）と map／collect APIにより、実行時にデータを見てタスク数を決定し、同じopを複数回複製して処理することができます
docs.dagster.io
。また、多値出力を利用した条件分岐の例では、branching_op が2つの出力のうちどちらかを返し、未解決の入力を持つ下流のopは自動的にスキップされるため、簡単にブランチ処理を実装できます
docs.dagster.io
。	Pythonでops（タスク）を定義し、グラフで組み合わせる方式。完全なリアルタイム変更は難しいが、実行中のデータに基づくループやブランチが可能。
Temporal	Temporalはワークフローが通常のコードとして記述されるので、分岐や条件判定は標準言語の if や switch で実装します。コミュニティでは「Go SDKなら if condition { ... } else { ... } や switch を使う」と説明しており、動的ディスパッチ用にmapやインタフェースを使う方法も示されています
community.temporal.io
。名前が不明なWorkflowやActivityを実行する場合は「Dynamic Handler」を用いますが、これは名前を事前に知らない場合のフォールバックであり、乱用は推奨されていません
docs.temporal.io
。	Go/Java/TypeScriptなど多言語対応。ワークフローがコードそのものなので自由度は高いが、非決定的な操作に注意が必要。
LangGraph	LangGraphはLangChainチームが開発した状態管理フレームワークで、ツール・関数・LLM・サブグラフをノードとし、エッジにはループや条件ルートを置けるため、複雑なエージェント間インタラクションをグラフとして表現します
xenoss.io
。主な機能は、永続的なチェックポイントと“タイムトラベル”デバッグ、Human-in-the-Loop（HITL）制御、ノード単位のタイムアウトやガードなどで、複数エージェントの状態管理に強みがあります
xenoss.io
。LangChainのドキュメントでも「複雑な状態管理や分岐、ループ、多数のエージェントを必要とする場合はLangGraphを使うべき」と推奨されています
xenoss.io
。	Python専用（2025年時点）。ReAct AgentやToolNodeなどのテンプレートを提供し、マルチエージェント実装の敷居を下げています
xenoss.io
。
Strands Agents	Strands Agentsはマルチエージェント・オーケストレーションのSDKで、multiagent.graph モジュールが「エージェントやSwarm/Graphなどのインスタンスをノードとしてグラフに配置し、依存関係に従って決定論的に実行する」仕組みを提供します
strandsagents.com
。出力はエッジを伝って次のノードに渡され、フィードバックループやサイクル、ネストされたグラフもサポートします
strandsagents.com
。	MCP（Model Context Protocol）やHooksなどの概念が統合されており、ツール呼び出しや安全性管理も一体化。公式ガイドには、複数エージェントが共同でタスクをこなすグラフやスワームの例が多数あります。
選択のポイント

CLIコマンドを関数としてラップし、結果に応じて次のステップを変えたい場合は、PrefectやDagsterの動的マッピング／条件分岐で十分です。特にPrefect 2.x（Orion）は「コード＝ワークフロー」という思想で、実行中にタスクを生成したりループを回したりできます
prefect.io
。

AIエージェントが複数CLIの結果を比較しながら意思決定するような用途には、BurrやLaminar Flowのようなエージェント向けフレームワークが適しており、状態に基づく遷移や並列処理が簡単に書けます
burr.dagworks.io
burr.dagworks.io
news.ycombinator.com
。

マルチエージェントや複雑なループ・分岐・ヒューマンインザループが必要なら、LangGraphやStrands Agentsのようなグラフ型エージェントフレームワークが有力です。これらは状態管理とデバッグ機能が充実しており、エッジに条件を持たせたり周期的なグラフを構築できます
xenoss.io
strandsagents.com
。

Temporalはワークフロー全体をコードで記述するアプローチであり、if/switch文で条件分岐が可能
community.temporal.io
ですが、動的ハンドラはフォールバック用途に留めるべきとの注意があります
docs.temporal.io
。

これらを踏まえ、目的に応じて適切なフレームワークを選択することで、複数のCLIを動的かつリアルタイムに連携させるワークフローを実現できます。

情報源
あなた:
UIがあり、常にinput/outputや設定などを確認したいですね。どれがいいかな。ワークフロー自体もLLMが操作していきます。
ChatGPT:
5 分で完了しました

LLM によるワークフローの制御を前提にする場合、単にタスクを自動化するだけではなく、「今どのステップで何が起きているのか」「入力・出力や設定を把握できるか」を可視化する UI が重要になります。各候補について UI・リアルタイム性を中心に比較しました。

UI と監視機能のあるツール
ツール	UI／監視機能	LLM 向けの適合性	考慮点
Prefect 2/3 (Orion)	公式ドキュメントの「Essential features」では、Prefect にモダン UIがあり「リアルタイムのフロー実行監視・ログ取得・状態追跡ができる。依存グラフや DAG は自動で表示される」と説明されています
docs.prefect.io
。UI から各タスクの実行状況やログを確認でき、入力パラメータや出力も記録されます。	Python ベースなので CLI をタスクとしてラップしやすく、データや条件に応じて if/else で動的にタスクを生成できる
docs.prefect.io
。	ワークフローは LLM による計画更新には対応しているが、UI はデータパイプライン向けで LLM 特有の構造化デバッグ機能はない。
Dagster (Dagit UI)	Dagster の Ops ガイドでは、イベントストリームを Dagster UI で視覚化でき、デバッグや実行中のジョブのリアルタイム監視を助けると記述されています
docs.dagster.io
。またセンサー設定では、UI からセンサーの開始・停止や評価状況、エラー理由を確認できる
docs.dagster.io
。	Ops 入力／出力に型や I/O マネージャを設定できるため CLI の入出力管理に向く。	パイプライン志向のため、LLM が自律的にフローを変更する用途には向かない。
Temporal	Temporal Web UI には「Input and Results セクション」があり、各ワークフロー実行の関数引数と戻り値を表示し、デバッグに利用できると説明されています
docs.temporal.io
。他にもイベント履歴やアクティビティの状態を詳細に閲覧できます。	マルチランゲージ対応でワークフローを普通のコードとして記述するため自由度は高い。	UI は汎用ワークフロー向けで、LLM 特有のチャット履歴やトークン数などは管理しない。
Burr (DagWorks)	Burr は AI エージェント向けのステートフルフレームワークで、ブログ記事によると「状態管理・可視性・永続化が重要なので、Burr ではOpenTelemetry互換のスパンや任意の属性を記録できる
blog.dagworks.io
」「Burr にはモニタリング／テレメトリ用のユーザーインターフェースが同梱されており、実行中のアプリをリアルタイムに観察できる」と説明されています
blog.dagworks.io
。UI ではウォーターフォールビューで各アクションのタイミングと状態を見られ、スパンを展開するとプロンプトやチャット履歴などの属性が表示される
blog.dagworks.io
。	状態遷移ベースの設計で、LLM の出力に応じて次のアクションを動的に決めることができる。UI はLLMアプリ向けに特化し、各ステップの入力プロンプト・出力・トークン数まで可視化できる。	OSS UI は 2024 年8月公開で発展途上。OpenTelemetry を使うため環境構築が必要。
LangGraph Studio	LangChain が提供する LangGraph Studio は「エージェント用 IDE」であり、グラフ構造を視覚化し、エージェントの実行をインタラクティブにデバッグできると説明されています
docs.langchain.com
。特徴として「グラフアーキテクチャの可視化」「エージェントの実行結果との対話」「アシスタントやスレッドの管理」「プロンプトの反復改善」「時刻を遡ってデバッグ（タイムトラベル）」などが挙げられています
docs.langchain.com
。Graph mode ではノードの traversed 状況や中間状態を表示し、Chat mode ではチャット主体の UI を提供します
docs.langchain.com
。	LangGraph は LLM エージェントの状態管理やヒューマン・イン・ザ・ループに対応しており、LLM が自律的にタスクを決めるようなワークフローを構築しやすい。Studio の UI で入力プロンプトや生成結果、メモリ状態を確認できる。	LangGraph Platform 上でホストするかローカルサーバーを立てる必要がある。
Strands Agents	Strands Agents SDK は「AI エージェント向けの観測機能」を提供し、OpenTelemetryベースのトレース、メトリクス、ログを取得する仕組みがあります
strandsagents.com
。トレースではモデル呼び出しやツール実行の入力・出力、トークン使用量などを記録できる
strandsagents.com
。	SDK 内に計量・トレース API はあるが、専用 UI は用意されていません。Langfuse や Datadog など外部ツールに送って可視化する必要があります。	独自 UI を開発するか外部サービスを組み合わせる手間が掛かる。
LLM が操作するワークフロー向けの推奨

Burr…状態遷移に基づき LLM の出力で次のステップを決める設計が標準であり、付属の UI で各アクションの入力・出力・トークン数などをリアルタイムに確認できる
blog.dagworks.io
blog.dagworks.io
。エージェントアプリを作るなら最適候補です。

LangGraph Studio…LangGraph によるエージェントワークフローをグラフィカルに可視化・操作でき、アシスタントの追加やプロンプトの改善、タイムトラベルデバッグなど LLM アプリ向け機能が豊富
docs.langchain.com
。LangChain 生態系を利用する場合に有力です。

Prefect や Dagster (Dagit)…CLI 呼び出しをタスクとして登録し、実行状況を一般的なワークフロー UI で監視する用途には適します
docs.prefect.io
docs.dagster.io
。しかし、フローを LLM が動的に更新するようなエージェント的シナリオには適応が必要で、LLM 固有の情報（プロンプト内容やトークン数など）は自前でログを収集する必要があります。

Temporal…Web UI で各ワークフローの入力引数と戻り値を表示し、履歴を詳細に確認できます
docs.temporal.io
。汎用ワークフロー管理に強みがありますが、LLM 特有のインタラクションを可視化するにはカスタム実装が必要です。

このように、LLM 主導のワークフローを可視化したいのであれば、エージェント向けに特化した Burr や LangGraph Studio が最も適しています。これらはプロンプトや出力、トークン数といった AI 特有の情報を UI で追跡でき、状態遷移を理解しながら LLM がフローを操作する様子を確認できます。一般的なワークフローエンジンの UI も有用ですが、AI アプリケーションには専用の可視化ツールを選ぶと効果的です。

情報源
あなた:
LangGraphはないかな。それ以外でcommitやスターが多いものは？
ChatGPT:
2 分で完了しました

以下では、LangGraph を除いた候補について、GitHub 上のスター数やコミット頻度から活発度を比較します。コミット数の厳密な合計は GitHub API で取得できなかったものの、更新日時やプッシュ頻度からどの程度活発に開発されているかを判断できます。

GitHub スター数と更新状況
フレームワーク	主なレポジトリ	スター数	更新状況・備考
Prefect	PrefectHQ/prefect	約 20,274 stars
api.github.com
	2018 年公開。最新 push が 2025‑09‑07 と直近で、週次コミットも継続中
api.github.com
。Python 製オーケストレーション基盤の中では最もコミュニティが大きく、Issue や PR も活発。
Temporal	temporalio/temporal	約 15,575 stars
api.github.com
	2019 年開始。最新 push は 2025‑09‑05
api.github.com
。バックエンドサービスが Go で書かれており、SDK は複数言語に分かれている。更新頻度・コミット数ともに高い。
Dagster (Dagit)	dagster-io/dagster	約 13,961 stars
api.github.com
	2018 年公開。最新 push も 2025‑09‑06
api.github.com
。週あたり 50〜150 コミットがあるなど、データパイプライン界隈で非常に活発
api.github.com
。
Strands Agents SDK	strands-agents/sdk-python	約 3,170 stars
api.github.com
	2025 年 5 月に公開された新興プロジェクト。最新 push は 2025‑09‑05
api.github.com
。リリースから間もないが AWS 製エージェント SDK として注目を集め、星が急速に増加中。
Burr (DagWorks)	apache/burr	約 1,782 stars
api.github.com
	2024 年 1 月にオープンソース化されたばかり。最新 push は 2025‑09‑02
api.github.com
で、Apache 財団のリポジトリに移行後も開発は継続中。コミュニティはまだ小さいものの、エージェント向け機能に特化している。
総合評価

スター数が多いのは Prefect で、20k以上の stars と 2018 年からの長い開発歴があります
api.github.com
。ワークフロー管理全般に関心を持つユーザが多く、コミットも安定しており、成熟したエコシステムといえます。

Temporal と Dagster も 13k–16k stars と人気が高く、直近まで活発に更新されています
api.github.com
api.github.com
。特に Dagster は 1 週間で百件規模のコミットがあり
api.github.com
、データパイプライン領域で勢いがあります。

Strands Agents は2025年公開の若いプロジェクトながら 3k 星以上を獲得
api.github.com
しており、AWS 製エージェントフレームワークとして急速に伸びています。

Burr は 2024 年公開でまだ星は少ないものの（1.7k）
api.github.com
、LLM アプリ向けの UI や状態遷移管理など独自の強みがあり、今後の成長が期待されます。

以上から、LangGraph を除いた候補の中でコミュニティ規模や開発活性度が最も高いのは Prefect、次いで Temporal と Dagster です。新しいエージェント特化型のプロジェクトとしては Strands Agents と Burr があり、急速にユーザー数を伸ばしています。どれを選ぶかは用途（一般的なワークフローかエージェント特化か）によって変わりますが、成熟度やコミュニティ規模を重視するなら Prefect や Temporal が有力でしょう。

情報源
あなた:
Strands AgentsはUIを確認できますか？プで何が起きているのか」「入力・出力や設定を把握できるか」を可視化する UI がありますか？CLI（Claude Code／Codex CLI／Gemini CLI／Spec Kit等）の連携にリアルタイム性や動的なタスク生成ができますか？
ChatGPT:
3 分で完了しました

Strands AgentsはAWSが公開している「エージェント用SDK」であり、複数のエージェント（LLMやツール）を連携させてタスクをこなすためのモデル駆動アーキテクチャを提供します。主な特徴と制約は次の通りです。

専用のUIはまだ存在しない

Strands AgentsにはPrefectやDagsterのような公式のダッシュボードは付属していません。Observability機能はOpenTelemetry準拠のトレース・メトリクス・ログの収集に限定されています。トレースではシステムプロンプト、モデルパラメータ、入出力メッセージ、トークン使用量、ツールの入出力などAI固有の情報も含めて収集でき
strandsagents.com
、メトリクスでは各ツールの実行回数やレイテンシ、エラー率などを記録します
strandsagents.com
。これらのデータは外部の可視化ツール（Langfuse、Datadogなど）やダッシュボードに送信することで監視します。

公式の GitHub では「AG‑UI Protocol」というフロントエンド連携用プロトコルを検討中で、これは「AIエージェントがフロントエンドアプリケーションに接続するための軽量なイベントベースプロトコル」だと説明されています
github.com
。提案では「StrandsのイベントをAG‑UI形式にマッピングし、エージェントとUI間で状態情報を管理できるラッパー」を想定しており、将来的にはWebアプリとエージェントを結ぶ標準になる可能性が示唆されています
github.com
。しかし現時点ではこの機能は未実装で、UIは自作か外部ツールに頼る必要があります。

リアルタイム性と動的タスク生成

Strands Agentsはマルチエージェント連携を目的としており、以下の仕組みで動的ワークフローや並列実行をサポートします。

機能	説明
Graph パターン	複数のエージェントをDAGとして構成し、ノード間の依存関係に従って実行します。GraphBuilderでノードとエッジを組み立て、エッジに条件関数を設定することで結果に応じた条件分岐（ブランチ）を実現します
strandsagents.com
。invoke_async を使えば各ノードを非同期に実行でき、タスクの結果やトークン使用量などを取得できます
strandsagents.com
。また graph ツールを使うと、エージェントが実行時に新しいグラフを自動生成して実行し、結果を分析して次のグラフを作る、といった自己計画も可能です
strandsagents.com
。
Swarm パターン	専門性の異なるエージェントが共有メモリにアクセスしながら協調する仕組みで、各エージェントが必要に応じて他のエージェントに「ハンドオフ」することでタスクを分担します。Swarm は動的タスク分配と並列性を前提としており、共有コンテキストを持ち、非同期 (invoke_async) 実行にも対応しています
strandsagents.com
strandsagents.com
。
Workflow ツール	Strands Agentsにはタスク依存関係や優先度を定義しておくと、依存関係を解決しながらタスクを生成・実行し、並列化可能な部分は自動で並列処理してくれるWorkflowツールがあります
strandsagents.com
。タスクの一時停止・再開、リトライやステータス取得をサポートし、状態・実行時間・依存タスクなどのメタデータを返します
strandsagents.com
。
CLI連携の可否

Strands Agents自体はPython SDKであり、「ツール」と呼ばれる外部機能をPython関数として実装します。従って：

Claude Code／Codex CLI／Gemini CLI／Spec KitなどをPythonラッパーの形でツール登録すれば、GraphやSwarmのノードとして呼び出し、並列実行することができます。

ワークフローやSwarmが非同期実行と条件分岐に対応しているため、結果に応じて次にどのCLIを呼ぶかを動的に決定することが可能です
strandsagents.com
strandsagents.com
。

しかし専用のUIはまだないため、実行状況やCLIの入力・出力を確認するには外部の観測サービスを利用する必要があります。Observabilityで収集したトレース・メトリクスをLangfuseやOpenTelemetry対応のダッシュボードに送ると、CLIの呼び出し内容や結果、トークン消費量まで可視化できます
strandsagents.com
。

結論

Strands Agentsはマルチエージェント構築のための強力なフレームワークで、Graph／Swarm／Workflowツールによりリアルタイムな並列処理や動的なワークフロー生成を実現します。一方で、PrefectやDagsterのような標準UIは備えておらず、観測データはOpenTelemetry互換のトレースやメトリクスとして外部ダッシュボードに送る設計です。将来的にはAG‑UIプロトコルへの対応が検討されています
github.com
が、現状では独自のUIを構築するかLangfuseなどを組み合わせて可視化する必要があります。

情報源
あなた:
Claude Code／Codex CLI／Gemini CLI／Spec KitなどをPythonラッパーの形でツール登録すれば、GraphやSwarmのノードとして呼び出し、並列実行することができます
これ本当？どうやってやるの？プラクティスはある？
ChatGPT:
2 分で完了しました

Strands Agentsの「ツール」は、エージェントが外部システムと対話するための拡張ポイントで、Python関数やクラス、モジュールをラップするだけで簡単に定義できます
strandsagents.com
。@tool デコレータを使えば通常の関数をそのままツール化でき、ドキュメントによるとドックストリングや型注釈から自動的に入力パラメータや説明が生成されます
strandsagents.com
。以下に、外部のCLIを呼び出すツールを作成してGraph／Swarmのノードとして利用する手順を示します。

1. Pythonラッパーを作成する
関数として登録する方法

from strands import tool をインポートします。

任意のPython関数に @tool デコレータを付けます。関数のドックストリングでツールの説明と引数説明を記述し、引数に型注釈を付けます
strandsagents.com
。

関数内で subprocess.run() などを使って外部 CLI を実行します。戻り値はテキストや辞書を返せます。辞書を返す場合は {"status":"success","content":[{"text": ... }]} の形式にすると、エージェントがそのまま応答として利用できます
strandsagents.com
strandsagents.com
。

例外をキャッチしてエラー時のレスポンスを返します
strandsagents.com
。

import subprocess
from strands import Agent, tool

@tool
async def run_codex_cli(prompt: str) -> dict:
    """Run Codex CLI with a prompt.
    Args:
        prompt: The input text for the CLI.
    """
    try:
        # 非同期プロセスの起動
        proc = await asyncio.create_subprocess_shell(
            f"codex-cli '{prompt}'",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return {
                "status": "success",
                "content": [{"text": stdout.decode()}],
            }
        else:
            return {
                "status": "error",
                "content": [{"text": stderr.decode()}],
            }
    except Exception as e:
        return {"status": "error", "content": [{"text": f"Exception: {e}"}]}


このように async 定義にすると、Strands Agentsは非同期ツールを自動で並列実行します
strandsagents.com
。同様のラッパーをClaude CodeやGemini CLI、Spec Kit用に作成すれば、複数のCLIをPython経由で使えるようになります。

モジュールとして登録する方法

ツールを独立したファイルにしたい場合は、TOOL_SPEC 変数と同名の関数を含む Python モジュールを作成します
strandsagents.com
。TOOL_SPEC にはツール名・説明・入力スキーマを記述し、関数ではCLIを呼び出して結果をフォーマットします
strandsagents.com
。このモジュールを tools=["./weather_forecast.py"] のようにパスで登録すれば読み込まれます
strandsagents.com
。

2. エージェントにツールを登録する

作成したツール関数（やモジュール）をエージェント初期化時の tools 引数として渡します
strandsagents.com
。例えば：

agent = Agent(tools=[run_codex_cli, run_claude_code, run_gemini_cli])


これでエージェントは必要に応じて適切なツールを選んで実行します。

3. Graph/Swarmで並列実行する

Graph：複数ツール呼び出しをノードとして配置し、エッジに条件関数を設定することで結果に基づく分岐が可能です。invoke_async を用いれば各ノードの実行を並列化できます
strandsagents.com
strandsagents.com
。

Swarm：異なるエージェント（各CLIラッパーを使うエージェント）を共有コンテキストで協調させる仕組みで、invoke_async により複数エージェントが同時にタスクを処理します
strandsagents.com
。結果が返ってきたら後続の作業者が受け継ぎます。

Graph/Swarmとも、非同期ツールが含まれていればエージェントはCLI呼び出しを並列で実行し、各結果をまとめたり条件分岐に活用できます。

ベストプラクティス

入力スキーマとドキュメントを丁寧に記述：@tool デコレータはドックストリングと型注釈から自動的にツール仕様を生成します
strandsagents.com
。プロンプトの意図や引数の意味を明確に記載するとLLMが適切にツールを選択します。

非同期実装を利用する：外部CLIはI/O待ちが多いため、async ツールにして asyncio.create_subprocess_shell などを使うと並列性が高まります
strandsagents.com
。

エラー処理を統一する：CLIが失敗した場合でも status="error" としてメッセージを返すようにし、LLMにエラー内容を伝えます
strandsagents.com
。

Context を利用する：必要に応じて context=True を指定し ToolContext を引数にすると、ツール実行中にエージェント名やツール使用IDなどの情報にアクセスできます
strandsagents.com
。

依存を隔離する：複数CLIを使う場合は個別のモジュールに分け、TOOL_SPEC と関数をそれぞれ定義するとインポートやデプロイが容易になります
strandsagents.com
。

このように、Strands Agentsでは外部CLIをPythonから呼び出すラッパーを用意し、ツールとして登録することでGraphやSwarmに組み込み、並列実行や条件分岐を含む動的ワークフローを構築できます。

情報源