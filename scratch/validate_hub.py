with open(r'c:\Users\yasha\Desktop\My Projects\scout\Furniture\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

print('Contains raw graph TD in code-box:', '<pre class="code-box"><code>graph TD' in text)
print('Count of graph TD:', text.count('graph TD'))
print('Count of <pre:', text.count('<pre'))
print('Count of dash-ul:', text.count('dash-ul'))
print('Count of segment-cell:', text.count('segment-cell'))
print('Count of badge-ultra:', text.count('badge-ultra'))
print('Count of badge-rich:', text.count('badge-rich'))
print('Count of badge-upper-mid:', text.count('badge-upper-mid'))
print('Count of badge-mid:', text.count('badge-mid'))
print('Count of badge-budget:', text.count('badge-budget'))
