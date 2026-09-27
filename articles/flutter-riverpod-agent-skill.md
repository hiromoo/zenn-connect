---
title: "自分の理想のFlutterアーキテクチャをAgent Skillにして公開する"
emoji: "📚"
type: "tech"
topics: ["flutter", "riverpod", "ai"]
published: true
---

## はじめに

Flutterでアプリを作るなら、こんな設計にしたい。状態管理にはRiverpodを使い、Widgetの中だけで完結する状態はHooksに任せる。APIとの境界はRepositoryで分けて、見た目と言語はアプリ全体で揃える。

これまで、こうした考えをひとつの設計方針としてきちんと整理したことはありませんでした。今回は自分が理想とするFlutterアプリの構成を言葉にして、AIエージェントが開発時に参照できるAgent Skillにまとめました。

目的は、これを唯一の正解として勧めることではありません。自分が大切にしたい設計を、ほかの人にも試してもらえる形にすることです。方針だけで終わらないよう、Reading Shelfというサンプルアプリも作って、実際のコードに落とし込んでいます。

この記事では、どのようなアプリを目指したのか、設計判断をどうSkillにまとめたのか、サンプルで確認できることを紹介します。

## どんなFlutterアプリを作りたいか

自分は責務を必要に応じて分けながら、最初から過剰に層を増やさない構成にしたいと思っています。

重視しているのは、機能を追加するときに「どこへ書くか」を判断しやすく、変更したときの影響も追いやすいことです。処理を別の層へ渡すだけのクラスを増やすと、小さな機能でも複数のファイルを行き来することになります。そこで、独立した責務があるか、変更の影響を閉じ込められるかを基準に、分ける場所を決めたいと考えました。

### Riverpodを画面状態の中心にする

状態の読み取りにはProviderを使い、画面の操作や更新にはNotifierやAsyncNotifierを使います。画面ごとに必ずViewModelクラスを作るのではなく、Notifier自身が画面状態と操作を表現できるなら、それをコントローラーとして使います。

この場合、さらにViewModelを置いても、Notifierの状態やメソッドを受け渡すだけになりがちです。自分は、画面の操作から状態が変わるまでを追いやすくするために、まずNotifierへ責務をまとめ、別の責務が見えてきたときに分割を考える方針にしています。

データを読み取るだけなら、操作用のNotifierを用意せず、Providerで表現します。たとえば書籍検索では、検索語とページ番号を受け取り、Repositoryから結果を取得します。

```dart
@riverpod
Future<BookSearchPage> bookSearch(
  Ref ref, {
  required String query,
  required int page,
}) =>
    ref.watch(booksRepositoryProvider).search(query: query, page: page);
```

UIはこのProviderの非同期状態を監視し、読み込み・結果・エラーを表示します。検索画面にDioや生成APIクライアントを持ち込まず、データ取得の実装はRepository側に置きます。

テキストコントローラーやフォーカス、一時的な選択など、そのWidgetが破棄されれば一緒に消えてよい状態は`flutter_hooks`に置きます。共有したい状態やアプリの振る舞いまでHooksに詰め込まず、状態の寿命に応じてRiverpodと使い分けます。

画面状態の中心をRiverpodにしても、入力欄のフォーカスのようなWidget固有の都合までNotifierへ持たせる必要はないと考えています。そのWidgetだけで使う状態は近くに置くことで、Notifierが扱う状態と操作の範囲を明確にしたいからです。

### Repositoryを境界にする

画面やNotifierは、APIのDTOではなくアプリ側のモデルとRepositoryの契約を扱います。APIをOpenAPIで定義できる場合はOpenAPI Generatorの`dart-dio`でクライアントを生成し、Data層のRepository実装で生成DTOをドメインモデルへ変換します。

```dart
abstract interface class BooksRepository {
  Future<BookSearchPage> search({required String query, required int page});
  Future<Book?> getById(String id);
}
```

この契約をfeature側に置くことで、WidgetやNotifierは通信方式を意識せずに済みます。認証情報や接続先もcomposition rootで組み立て、生成クライアントをData層の外へ漏らしません。

層を増やしすぎない方針でも、この境界は設けたいと考えています。APIのレスポンス形式や通信方式が変わったときに、アプリ側の契約を保てる変更ならRepository実装で吸収し、画面への影響を抑えたいからです。

Use Caseはすべての処理に一律で用意するものではありません。Repositoryの呼び出しをそのまま中継するだけなら追加せず、複雑な業務処理や複数featureで再利用する処理が必要になったときに追加します。APIとの境界はRepositoryで確保し、業務処理を独立させる必要があるかは別に判断する、という分け方です。

### 見た目・言語・ルートをアプリ全体で揃える

色や文字スタイルを各画面に直接書き散らさず、`MaterialApp.router`にライト・ダークテーマとテーマ設定を集約します。Material 3の`ColorScheme`や`TextTheme`、Component Themeを基準にすれば、後から全体のトーンを調整しやすくなります。

多言語対応にはFlutterの`gen_l10n`とARBを使います。Widgetでは生成されたローカライズを`context.l`から参照します。

```dart
extension AppLocalizationsContext on BuildContext {
  AppLocalizations get l => AppLocalizations.of(this)!;
}
```

```dart
Text(context.l.search)
```

利用者に見せる文言をWidgetやNotifierに直接埋め込まず、APIエラーなども表示用の状態へ変換してから翻訳します。言語切替はアプリの設定として保持し、レイアウトは長い文言や文字サイズ変更にも耐えるようにします。

画面遷移には`go_router`と`go_router_builder`を使い、ルートを型付きで定義します。検索語やページ番号のように共有・復元したい値はURLに含め、直接アクセスや再読み込みでも同じ画面を開ける形を目指します。

## 設計方針をAgent Skillにする

「RiverpodとRepositoryを使う」と伝えるだけでは、ViewModelを別に作るか、Widget内の状態をどこまでProviderへ移すかまでは決まりません。AIエージェントに機能追加を依頼するときにも同じ基準で判断してほしいので、採用する技術に加えて、責務の置き方と分割の条件をSkillとして残すことにしました。

設計をAIエージェントが実装時に参照できる指示へ変換します。`SKILL.md`では適用範囲、必須規約、基本ワークフローを説明し、細かな判断基準は`references/`以下に分けました。

アーキテクチャの基本線はFlutter公式の[Architecture Best Practices Skill](https://github.com/flutter/agent-plugins/blob/main/skills/flutter-apply-architecture-best-practices/SKILL.md)を参照します。その内容を複製するのではなく、Riverpodを前提にしたときの差分を追加しています。外部APIにはOpenAPI GeneratorのDioクライアントを使う、ローカル状態にはHooksを使う、画面遷移は型安全なルートにする、といった方針です。

作業内容に応じて[Flutter公式agent-pluginsのSkills](https://github.com/flutter/agent-plugins/tree/main/skills)も補助的に参照します。多言語設定やルーティング、Widget testなどの公式Skillはコピーせず、リンクで案内します。

Skillに書いた指示は、設計や実装の一貫性を目指すためのガイドです。それだけで品質が保証されるわけではありません。対象リポジトリの規約を確認し、コード生成・解析・テストを行うところまでを開発手順に含めています。

たとえば、Skillには次のような判断基準を書いています。

> ViewModelクラスは必須にしない。RiverpodのNotifierが画面状態と操作を表現できる場合は、そのNotifierをpresentation controllerとして使う。

ライブラリの一覧だけでなく、どんな場合に追加のクラスを作るかまで示すことで、実装時の判断に使える指示を目指しています。

## Reading Shelfで試す

方針を試すために、読書記録アプリのReading Shelfを用意しました。書籍検索とページ送り、詳細、本棚、読書記録の編集、言語とテーマの切替ができます。架空の書籍データを使い、Shelf製のローカルAPIが読書記録をJSONへ保存します。

![Reading Shelfの本棚画面](/images/reading-shelf-shelf.png)

*本棚画面。読書中の本と、これから読みたい本を一覧できます。*

構成は`catalog`、`reading`、`settings`に分けています。検索Providerは`catalog/application`、Repositoryの契約は`catalog/domain`、生成APIクライアントを呼ぶ実装は`catalog/data`に置きます。composition rootがRepositoryを生成し、ProviderScopeのoverrideで注入します。([Provider](https://github.com/hiromoo/flutter-riverpod-skill/blob/main/examples/reading_shelf/lib/features/catalog/application/catalog_providers.dart)、[Repository実装](https://github.com/hiromoo/flutter-riverpod-skill/blob/main/examples/reading_shelf/lib/features/catalog/data/api_books_repository.dart))

検索と記録編集は`HookConsumerWidget`で、入力Controllerや編集中フラグはHooks、検索結果や保存状態はRiverpodで管理します。状態を寿命に応じて分ける例です。

サンプルには、検索画面のWidget test、APIクライアントのserializer test、Shelf APIのテストと、解析・生成・Web buildを行うGitHub Actionsのworkflowがあります。ここで確認できるテストは限定的です。すべての画面状態や実機ブラウザーでの一連の操作を自動テスト済みという意味ではありません。

### 読書記録の保存をAsyncNotifierで実装する

読書記録の保存では、AsyncNotifierに操作とその実行状態を持たせています。サンプルの[ReadingEntryActions](https://github.com/hiromoo/flutter-riverpod-skill/blob/main/examples/reading_shelf/lib/features/reading/application/reading_providers.dart)から保存部分を抜粋しました。import・part宣言と削除処理は省略しています。

```dart
@riverpod
class ReadingEntryActions extends _$ReadingEntryActions {
  late String _bookId;

  @override
  FutureOr<void> build(String bookId) {
    _bookId = bookId;
  }

  Future<bool> save(ReadingEntry entry) async {
    if (state.isLoading) return false;
    state = const AsyncLoading<void>();
    try {
      await ref.read(readingRepositoryProvider).save(entry);
      state = const AsyncData<void>(null);
      ref.invalidate(readingEntriesProvider);
      ref.invalidate(readingEntryProvider(_bookId));
      return true;
    } catch (error, stackTrace) {
      state = AsyncError<void>(error, stackTrace);
      return false;
    }
  }
}
```

`build`が`FutureOr<void>`を返すため、コード生成によってAsyncNotifierとして扱われ、`state`は`AsyncValue<void>`になります。ここで保持するのは読書記録そのものではなく、保存などの操作の実行状態です。保存中は`AsyncLoading`、成功時は`AsyncData`、失敗時は`AsyncError`へ更新し、成功したら一覧と対象書籍の読書記録をinvalidateして、監視中のデータを再取得します。

Widget側では、入力ControllerをHooksで管理し、保存状態を`ref.watch`で監視します。[編集画面](https://github.com/hiromoo/flutter-riverpod-skill/blob/main/examples/reading_shelf/lib/features/reading/presentation/reading_editor_screen.dart)を、既存の読書記録のメモだけを編集する例に簡略化すると、次の形です。コードは`HookConsumerWidget`の`build`内に置き、`entry`は読み込み済みの`ReadingEntry`、`bookId`はその書籍IDとします。

```dart
final noteController = useTextEditingController(text: entry.note);
final action = ref.watch(readingEntryActionsProvider(bookId));

return Column(
  children: [
    TextField(
      controller: noteController,
      enabled: !action.isLoading,
      maxLength: 2000,
      decoration: InputDecoration(labelText: context.l.note),
    ),
    if (action.hasError) Text(context.l.saveFailed),
    FilledButton(
      onPressed: action.isLoading
          ? null
          : () async {
              await ref
                  .read(readingEntryActionsProvider(bookId).notifier)
                  .save(entry.copyWith(note: noteController.text.trim()));
            },
      child: Text(action.isLoading ? context.l.saving : context.l.save),
    ),
  ],
);
```

入力中のメモは`noteController`が保持し、保存ボタンを押した時点で`copyWith`により保存用のモデルへ反映します。Controllerの生成と破棄は`useTextEditingController`がWidgetの寿命に合わせて管理し、保存中・失敗などの実行状態はAsyncNotifierが管理します。なお、`text: entry.note`はController生成時の初期値なので、この簡略例は同じ記録を編集する間の処理を示しています。

Widgetは保存中の表示や入力・ボタンの無効化、エラーメッセージの表示を受け持ちます。保存先のRepositoryを呼び出し、関連データの更新を促す処理はNotifierが受け持つので、この例ではその間をつなぐViewModelを別に設けていません。

### サンプルを作ってSkillに戻したこと

実際に組み合わせてみると、ライブラリ名を並べるだけでは足りないことが分かりました。RiverpodのruntimeとgeneratorはメジャーバージョンによってAPIが異なるため、複数featureの実装に進む前に、小さなProviderのコード生成と解析で互換性を確かめる手順をSkillへ加えました。

OpenAPI Generatorは生成先のファイルを置き換えることがあります。そのため、手管理する設定を`.openapi-generator-ignore`で保護し、生成コードと手書きの設定が共存するようにしています。また、このクライアントの`Optional<T>`はフィールドの省略と明示的なnullを区別します。値を読む前に`isPresent`を確認する、といった生成DTOの扱いも記録しました。

また、FlutterアプリとDartサーバーが同じサンプルディレクトリ配下にあるため、アプリの解析対象を`lib`と`test`に明示しています。パッケージ単位で依存関係を解決し、それぞれの責務に応じて解析・テストすることも、再利用できる開発上の知見になりました。

このように、Skillは最初に書いた方針を固定する文書ではなく、サンプルの実装で気付いたことを反映しながら育てるものとして扱っています。

## 使い方

リポジトリは[GitHubで公開しています](https://github.com/hiromoo/flutter-riverpod-skill)。Codexでは、Skillを`$CODEX_HOME/skills`（通常は`~/.codex/skills`）に配置して利用できます。たとえば、リポジトリ全体をSkillとして置く場合は次のようにcloneします。

```sh
git clone https://github.com/hiromoo/flutter-riverpod-skill.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/flutter-riverpod-skill"
cd "${CODEX_HOME:-$HOME/.codex}/skills/flutter-riverpod-skill"
```

CodexにSkillを認識させたら、明示的に名前を指定して依頼できます。Skillの名前は`SKILL.md`のfrontmatterにある`flutter-riverpod-skill`です。

```text
$flutter-riverpod-skill を使って、このアプリに設定画面を追加してください。
既存の構成を確認し、設定の永続化、Riverpodの状態管理、l10n、型安全なルートまで含めて実装してください。
```

新規プロジェクトなら、たとえば次のように依頼できます。

```text
$flutter-riverpod-skill の方針を使って、Flutterで蔵書管理アプリの土台を作ってください。
まず現在のSDK・依存関係・生成コードの互換性を確認し、構成案と実装手順を提示してください。
```

Skillは既存プロジェクトの規約を確認し、差分を小さく進めることも求めています。プロジェクト固有の要件があれば、依頼時に明示してください。設計方針は状況に合わせて調整するものです。

Reading Shelfを動かす場合、必要なのは[FVM](https://fvm.app/)です。Flutter 3.47.5を`.fvmrc`で固定しており、外部APIキーは不要です。FVMが未導入の場合は[公式手順](https://fvm.app/documentation/getting-started/installation)に従って導入してください。初回はリポジトリルートからアプリのSDKを準備します。

```sh
cd examples/reading_shelf
fvm use 3.47.5
cd ../..
```

その後、リポジトリルートからAPIサーバーとWebアプリを別々のターミナルで起動します。

```sh
cd examples/reading_shelf/server
fvm dart pub get
fvm dart run bin/server.dart
```

```sh
cd examples/reading_shelf
fvm flutter pub get
fvm dart run build_runner build
fvm flutter gen-l10n
fvm flutter run -d chrome --web-port 3000 \
  --dart-define=API_BASE_URL=http://localhost:8080
```

詳しい前提条件や生成手順は[サンプルのREADME](https://github.com/hiromoo/flutter-riverpod-skill/blob/main/examples/reading_shelf/README.md)にあります。

## おわりに

今回は、自分がFlutterアプリで大切にしたい設計を整理し、AIエージェントにも共有できるAgent Skillとして公開しました。技術の選択だけでなく、それらをどう組み合わせ、どの層に責務を置くかを明文化できました。

Reading Shelfは、その設計を試すための小さなサンプルです。これがあらゆるFlutterアプリにそのまま合うとは限りませんが、似た考え方を持つ方が土台として使ったり、自分の方針に合わせて調整したりできればうれしいです。

試して気付いた点や、こういう判断も明文化するとよさそう、といったフィードバックがあれば、ぜひリポジトリのIssueなどで教えてください。今後は別のアプリにも適用しながら、どのルールが汎用的で、どこを選択肢として残すべきかを考えていきたいです。
