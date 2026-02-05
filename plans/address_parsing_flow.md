graph TD
    A[開始: 住所文字列] --> B{住所の正規化と全角化}
    B --> C{都道府県の抽出}
    C --> D{都道府県以下の住所を分離}
    D --> E{丁目部分の抽出}
    E --> F{地番・家屋番号部分の抽出}
    F --> G{地番・家屋番号のフォーマット変換<br/>例: 13番1号 -> 13-1, 13番地 -> 13}
    G --> H[結果: 所在欄]
    G --> I[結果: 地番・家屋番号欄]
    H --> J[終了]
    I --> J

    subgraph 住所解析ロジック
        C
        D
        E
        F
        G
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style J fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#bbf,stroke:#333,stroke-width:2px
    style I fill:#bbf,stroke:#333,stroke-width:2px
```
