import os
import re

# 匹配 <pre lang="xxx"...> 形式
PRE_LANG_PATTERN = re.compile(r'<pre\s+[^>]*lang="([^"]+)"[^>]*>', re.IGNORECASE)

# 匹配 <pre class="lang:xxx ..."> 形式
PRE_CLASS_LANG_PATTERN = re.compile(r'<pre\s+[^>]*class="[^"]*lang:([^ "\']+)[^"]*"[^>]*>', re.IGNORECASE)

# 匹配完整 <pre>...</pre> 块
FULL_PRE_BLOCK_PATTERN = re.compile(r'<pre[^>]*>.*?</pre>', re.DOTALL | re.IGNORECASE)

def process_md_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    def replacer(match):
        block = match.group(0)

        # 先尝试匹配 lang="xxx"
        lang_match = PRE_LANG_PATTERN.search(block)
        if lang_match:
            lang = lang_match.group(1).strip().lower()
        else:
            # 尝试匹配 class="lang:xxx"
            class_match = PRE_CLASS_LANG_PATTERN.search(block)
            if class_match:
                lang = class_match.group(1).strip().lower()
            else:
                # 找不到语言，跳过处理
                return block

        # 构建替换块
        # 替换开头的 <pre ...> 为 <pre><code class="language-xxx">
        new_block = re.sub(r'<pre[^>]*>', f'<pre><code class="language-{lang}">', block, count=1, flags=re.IGNORECASE)
        # 替换结尾的 </pre> 为 </code></pre>
        new_block = new_block.replace('</pre>', '</code></pre>')

        return new_block

    new_content = FULL_PRE_BLOCK_PATTERN.sub(replacer, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Processed: {filepath}")
    else:
        print(f"⏭️  Skipped (no matches): {filepath}")

def process_all_md_files(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.md'):
                process_md_file(os.path.join(root, filename))

if __name__ == '__main__':
    target_directory = '.\\_posts'  # 修改为你的 md 文件目录
    process_all_md_files(target_directory)
