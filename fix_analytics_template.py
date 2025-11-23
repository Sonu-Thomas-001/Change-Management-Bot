# Script to update the analytics.html template
import re

# Read the current template
with open('templates/analytics.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the table headers
content = content.replace(
    '<th>Time</th>\n                                <th>Reason</th>\n                                <th>Chat Snippet</th>',
    '<th>Time</th>\n                                <th>Reason</th>\n                                <th>User Query</th>\n                                <th>Bot Response</th>'
)

# Replace the table data cells
content = content.replace(
    '<td style="white-space:nowrap; color:#6b7280;">{{ row.Timestamp }}</td>\n                                <td>{{ row.Reason }}</td>\n                                <td style="font-size:0.85rem; color:#555;">{{ row.Chat_Snippet }}</td>',
    '<td style="white-space:nowrap; color:#6b7280;">{{ row.Timestamp }}</td>\n                                <td>{{ row.Reason }}</td>\n                                <td style="font-size:0.85rem; color:#555;">{{ row.User_Query }}</td>\n                                <td style="font-size:0.85rem; color:#555;">{{ row.Bot_Response }}</td>'
)

# Update the colspan
content = content.replace(
    '<td colspan="3">No escalations found.</td>',
    '<td colspan="4">No escalations found.</td>'
)

# Write back
with open('templates/analytics.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Successfully updated analytics.html")
