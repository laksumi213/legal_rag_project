# Legal System Database Schema (PostgreSQL/SQLAlchemy)

## 1. 案件管理 (Case Management)

### cases (案件テーブル)
- **case_id** (PK, Int): 内部ID
- **case_number** (String, Unique): 案件番号 (例: G1024)
- **client_name** (String): 依頼者（相続人代表）氏名
- **client_name_kana** (String): 依頼者カナ
- **sol_case_number** (String): SOL案件番号（日興証券連携用）
- **kintone_record_id** (Int): Kintone側のレコードID
- **folder_path** (String): ファイルサーバーのパス
- **manager_id** (FK -> users.id): 進捗担当者
- **operator_id** (FK -> users.id): 実務担当者
- **status** (FK -> case_statuses.id): ステータス
- **referral_sec_phone** (String): 紹介元電話番号 (Ver 2.0追加)

### deceased (被相続人)
- **id** (PK, Int)
- **case_id** (FK -> cases.case_id): 1対1リレーション
- **name_last**, **name_first**: 氏名
- **name_last_kana**, **name_first_kana**: カナ
- **date_of_death** (Date): 相続開始日
- **date_of_birth** (Date): 生年月日
- **last_address_id** (FK -> address.id): 最後の住所

### heirs (相続人)
- **id** (PK, Int)
- **deceased_id** (FK -> deceased.id): 1対多リレーション
- **name_last**, **name_first**: 氏名
- **relationship_type**: 続柄 (妻, 長男, 二女 等)
- **is_contracting_party** (Bool): 契約者（依頼主）かどうか
- **address_links**: 住所履歴 (H_AddressHistory経由)
- **contact_links**: 連絡先 (H_ContactLink経由)

## 2. 資産管理 (Assets)

### financial_asset (預貯金)
- **id** (PK, Int)
- **case_id** (FK -> cases.case_id)
- **bank_id** (FK -> bank_master.id)
- **branch_id** (FK -> branch_master.id)
- **account_number** (String): 口座番号
- **balance** (Float): 残高
- **status** (String): 手続き状況

## 3. マスタデータ (Master Data)

### bank_master (銀行マスタ)
- **id** (PK, Int)
- **bank_name** (String): 銀行名 (例: 三菱UFJ銀行)
- **bank_code** (String): 銀行コード
- **seal_cert_limit** (String): 印鑑証明期限ルール
- **id_verify_rule** (String): 本人確認書類ルール
- **remarks** (Text): RAG用特記事項

### users (ユーザー)
- **id** (PK, Int)
- **windows_id** (String): WindowsログインID
- **name** (String): 表示名

### address (住所マスタ)
- **id** (PK, Int)
- **zip_code**, **prefecture**, **city_ward_town**, **street_address**, **building_name**

## 4. RAG・ファイル管理 (Agentic Features)

### file_registry (ファイル管理)
- **file_hash** (PK, String): MD5ハッシュ
- **filename** (String): ファイル名
- **case_id** (FK -> cases.case_id): 紐付け案件
- **doc_type** (String): 書類種別 (戸籍謄本, 残高証明書, 委任状, etc.)
- **registered_at** (DateTime)

### audit_logs (監査ログ)
- **id** (PK, Int)
- **action_type**: "AI_REASONING", "PII_CHECK", etc.
- **target**: 対象ファイル名やデータ
- **details**: AIの思考プロセスやJSON出力