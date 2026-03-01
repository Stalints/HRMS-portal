import os
import re

directories = [
    r'c:\Users\stali\OneDrive\Documents\Desktop\HRMS\hr\templates\hr',
    r'c:\Users\stali\OneDrive\Documents\Desktop\HRMS\core\templates\core'
]

js_snippet = """
    <!-- Notification System JS -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
            const notifySocket = new WebSocket(wsProtocol + window.location.host + '/ws/notifications/');

            function updateBadge(count) {
                const badges = document.querySelectorAll('.global-chat-badge');
                badges.forEach(b => {
                    if(count > 0) {
                        b.textContent = count;
                        b.style.display = 'inline-block';
                    } else {
                        b.style.display = 'none';
                    }
                });
            }

            function showToast(sender, preview) {
                const toast = document.createElement('div');
                toast.style.position = 'fixed';
                toast.style.bottom = '20px';
                toast.style.right = '20px';
                toast.style.background = '#4f46e5';
                toast.style.color = 'white';
                toast.style.padding = '12px 20px';
                toast.style.borderRadius = '12px';
                toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)';
                toast.style.zIndex = '9999';
                toast.style.transition = 'opacity 0.3s';
                toast.style.fontFamily = 'system-ui, sans-serif';
                toast.innerHTML = `<div style="font-weight:bold; margin-bottom:4px;">New Message from ${sender} <span style="font-size:16px;">💬</span></div><div style="font-size:0.9em; opacity:0.9;">${preview}</div>`;
                document.body.appendChild(toast);
                
                setTimeout(() => {
                    toast.style.opacity = '0';
                    setTimeout(() => toast.remove(), 300);
                }, 5000);
            }

            notifySocket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                if (data.type === 'unread_count_init') {
                    updateBadge(data.unread_count);
                } else if (data.type === 'chat_notification') {
                    updateBadge(data.unread_count);
                    if (!window.location.pathname.includes('/chat/') && !window.location.pathname.includes('/messages/')) {
                        showToast(data.sender_name, data.message_preview);
                    }
                }
            };
        });
    </script>
</body>
"""

for directory in directories:
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if "<!-- Notification System JS -->" not in content and "</body>" in content:
                # Add JS before </body>
                content = content.replace("</body>", js_snippet, 1)

                # Add badge to HR template sidebar Chat links
                if directory.endswith('hr'):
                    content = content.replace(
                        '<span class="me-2" aria-hidden="true">&#128172;</span> Chat',
                        '<span class="me-2" aria-hidden="true">&#128172;</span> Chat <span class="global-chat-badge badge bg-danger ms-2" style="display:none;">0</span>'
                    )

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Patched {filename}')
