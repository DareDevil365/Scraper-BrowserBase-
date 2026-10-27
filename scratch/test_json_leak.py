import re
import json

text = "**[Arttd'inox Official Brand Portal](https://arttdinox.com/)**"
t1 = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer" class="dash-link">\1</a>', text)
print("t1:", repr(t1))
t2 = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t1)
print("t2:", repr(t2))

j = json.dumps({"html": t2})
print("json:", repr(j))
