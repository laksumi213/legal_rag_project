# src/legal_system/ui/utils/scroll_helper.py

import streamlit.components.v1 as components

def maintain_scroll_position():
    """
    Injects JavaScript to maintain scroll position across Streamlit reruns.
    Saves the scroll position to sessionStorage before a rerun and restores it after.
    """
    js_code = """
    <script>
        (function() {
            // Save scroll position before the page unloads (which happens on a Streamlit rerun)
            window.addEventListener("beforeunload", function() {
                sessionStorage.setItem("scrollPosition", window.scrollY);
            });

            // Restore scroll position after the page loads.
            // A small delay is used to ensure all elements are rendered before scrolling.
            window.addEventListener("load", function() {
                setTimeout(function() {
                    const scrollPosition = sessionStorage.getItem("scrollPosition");
                    if (scrollPosition) {
                        window.scrollTo(0, parseInt(scrollPosition, 10));
                        sessionStorage.removeItem("scrollPosition"); // Clean up
                    }
                }, 100); // 100ms delay
            });
        })();
    </script>
    """
    components.html(js_code, height=0)
