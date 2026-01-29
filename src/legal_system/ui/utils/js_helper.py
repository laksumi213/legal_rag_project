# src/legal_system/ui/utils/js_helper.py

import uuid
import streamlit.components.v1 as components

def enable_keyboard_shortcuts(search_keyword="案件番号"):
    """
    指定されたキーワード（プレースホルダー等）を持つ入力フィールドに
    強制的にフォーカスを当てるJavaScriptを埋め込む。
    
    Ver 12.0: Recursive Deep DOM Traversal (Final Solution)
    - Shadow DOMやIframeの階層に関わらず、全要素を再帰的に探索してターゲットを特定する。
    - 物理キーコード(KeyS)による判定でIMEの影響を排除。
    """
    
    # 検索バーのプレースホルダーに含まれるキーワード
    TARGET_KW = "案件番号" 
    
    # 強制リロード用のID埋め込み
    unique_id = str(uuid.uuid4())
    
    js_code = f"""
    <script>
        /* Force Reload ID: {unique_id} */
        (function() {{
            const SEARCH_KW = "{TARGET_KW}";
            const OPEN_KEYWORDS = ["📂 開く", "フォルダを開く"]; 
            const KINTONE_KEYWORDS = ["🔗 Kintone", "Kintoneで開く"];
            
            console.log("🚀 LegalApp JS Helper v12 (Deep Traversal) loaded.");

            // ============================================================
            // 1. 深層再帰探索ロジック (Shadow DOM & Iframe を貫通)
            // ============================================================
            function findInputRecursive(node) {{
                if (!node) return null;

                // 1. inputタグかつキーワード一致なら発見
                if (node.tagName === 'INPUT') {{
                    const txt = (node.placeholder || "") + (node.getAttribute('aria-label') || "");
                    if (txt.includes(SEARCH_KW) && node.type !== 'hidden' && node.style.display !== 'none') {{
                        return node;
                    }}
                }}

                // 2. Shadow Root があれば内部へ潜る
                if (node.shadowRoot) {{
                    const found = findInputRecursive(node.shadowRoot);
                    if (found) return found;
                }}

                // 3. Iframe があれば内部ドキュメントへ潜る
                if (node.tagName === 'IFRAME') {{
                    try {{
                        const innerDoc = node.contentDocument || node.contentWindow.document;
                        if (innerDoc) {{
                            // iframe内のbodyから再帰探索
                            const found = findInputRecursive(innerDoc.body);
                            if (found) return found;
                        }}
                    }} catch(e) {{
                        // Cross-origin制限などは無視
                    }}
                }}

                // 4. 子要素を再帰探索
                if (node.children) {{
                    for (let i = 0; i < node.children.length; i++) {{
                        const found = findInputRecursive(node.children[i]);
                        if (found) return found;
                    }}
                }}

                return null;
            }}

            // ============================================================
            // 2. アクション (フォーカス & クリック)
            // ============================================================
            function doFocus() {{
                // 親ウィンドウのドキュメント全体から再帰探索開始
                const input = findInputRecursive(window.parent.document.body);
                
                if (input) {{
                    // フォーカス処理 (念入りに実行)
                    input.focus();
                    setTimeout(() => input.focus(), 50);
                    
                    try {{ input.select(); }} catch(e) {{}}
                    
                    // 視覚エフェクト (マゼンタ枠線)
                    const originalBorder = input.style.border;
                    const originalShadow = input.style.boxShadow;
                    
                    input.style.transition = "all 0.2s";
                    input.style.border = "3px solid #d33682"; // マゼンタ色
                    input.style.boxShadow = "0 0 15px rgba(211, 54, 130, 0.6)";
                    
                    setTimeout(() => {{
                        input.style.border = originalBorder;
                        input.style.boxShadow = originalShadow;
                    }}, 1200);
                    
                    return true;
                }}
                return false;
            }}

            function triggerButton(keywords) {{
                const doc = window.parent.document;
                // ボタン類はShadowDOMの深い場所にはあまりないため、querySelectorで探索
                const elements = doc.querySelectorAll('button, a, div[role="button"]');
                for (const el of elements) {{
                    const text = (el.innerText || el.textContent || "").trim();
                    if (!text) continue;
                    if (keywords.some(kw => text.includes(kw))) {{
                        el.click();
                        return true;
                    }}
                }}
                return false;
            }}

            // ============================================================
            // 3. イベントリスナー (ショートカット)
            // ============================================================
            const doc = window.parent.document;
            const HANDLER_NAME = '_legalAppKeyHandler_v12';

            // 既存リスナーの完全削除
            if (window.parent[HANDLER_NAME]) {{
                doc.removeEventListener('keydown', window.parent[HANDLER_NAME], true);
            }}

            window.parent[HANDLER_NAME] = function(e) {{
                // Altキー必須
                if (!e.altKey) return;

                // 物理キーコードで判定 (IMEの影響を受けない 'KeyS')
                const code = e.code; 
                let handled = false;

                // [Alt+S] 検索
                if (code === 'KeyS') {{
                    // デフォルト動作(ブラウザメニュー等)を完全停止
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    if (doFocus()) {{
                        console.log("LegalApp: Focused via Alt+S");
                    }} else {{
                        console.log("LegalApp: Search Input Not Found via Alt+S");
                    }}
                    handled = true;
                }}
                
                // [Alt+O] フォルダ
                else if (code === 'KeyO') {{
                    if (triggerButton(OPEN_KEYWORDS)) {{
                        e.preventDefault(); 
                        handled = true;
                    }}
                }}

                // [Alt+K] Kintone
                else if (code === 'KeyK') {{
                    if (triggerButton(KINTONE_KEYWORDS)) {{
                        e.preventDefault(); 
                        handled = true;
                    }}
                }}
            }};

            // Captureフェーズ(true)で最優先でイベントを奪取
            doc.addEventListener('keydown', window.parent[HANDLER_NAME], true);


            // ============================================================
            // 4. 自動フォーカス (MutationObserverによる監視)
            // ============================================================
            let hasFocused = false;

            // 初回トライ
            if (doFocus()) hasFocused = true;

            // 画面描画の遅延に対応するため、DOM変化を監視して出現した瞬間にフォーカス
            const observer = new MutationObserver((mutations) => {{
                if (hasFocused) {{
                    observer.disconnect();
                    return;
                }}
                
                // 変更があるたびにトライ (負荷軽減のためシンプルに呼ぶ)
                if (doFocus()) {{
                    console.log("LegalApp: Auto-focused by Observer");
                    hasFocused = true;
                    observer.disconnect();
                }}
            }});

            observer.observe(window.parent.document.body, {{
                childList: true, 
                subtree: true
            }});
            
            // 安全策: 3秒後まで定期的にリトライ (Observerで見逃した場合用)
            let retryCount = 0;
            const interval = setInterval(() => {{
                if (hasFocused || retryCount > 15) {{
                    clearInterval(interval);
                    return;
                }}
                if (doFocus()) {{
                    hasFocused = true;
                }}
                retryCount++;
            }}, 200); // 0.2秒ごとにチェック

        }})();
    </script>
    """
    
    # key引数を使わず、HTML内の unique_id でリロードを強制する
    components.html(js_code, height=0)