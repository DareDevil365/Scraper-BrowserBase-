from html.parser import HTMLParser

class HTMLTagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
        self.void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def handle_starttag(self, tag, attrs):
        if tag not in self.void_tags:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in self.void_tags:
            return
        if not self.stack:
            self.errors.append(f"Error: Closing tag </{tag}> at line {self.getpos()[0]}, col {self.getpos()[1]} has no matching opening tag.")
            return
        
        open_tag, (open_line, open_col) = self.stack.pop()
        if open_tag != tag:
            self.errors.append(f"Error: Mismatched tag </{tag}> at line {self.getpos()[0]}. Expected </{open_tag}> (opened at line {open_line}).")
            # Push the open tag back to try to recover
            self.stack.append((open_tag, (open_line, open_col)))

    def check_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        self.feed(content)
        
        for err in self.errors:
            print(err)
            
        while self.stack:
            tag, (line, col) = self.stack.pop()
            print(f"Error: Unclosed tag <{tag}> opened at line {line}, col {col}.")

if __name__ == '__main__':
    checker = HTMLTagChecker()
    checker.check_file(r'c:\Users\yasha\Desktop\scout\templates\index.html')
