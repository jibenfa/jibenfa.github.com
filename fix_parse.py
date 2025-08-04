import os
import yaml

POSTS_DIR = "_posts"

for fname in os.listdir(POSTS_DIR):
    if not fname.endswith(".md"):
        continue

    filepath = os.path.join(POSTS_DIR, fname)
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        continue

    parts = content.split("---", 2)
    if len(parts) < 3:
        continue

    fm_text = parts[1]
    body = parts[2]

    try:
        # 使用 FullLoader 载入支持引用的 YAML
        meta = yaml.load(fm_text, Loader=yaml.FullLoader)
    except Exception as e:
        print(f"{fname} 解析失败：{e}")
        continue

    changed = False

    # 如果 tags 是一个引用对象
    if isinstance(meta.get("tags"), yaml.nodes.Node):
        print(f"{fname} 的 tags 是 YAML 引用，跳过")
        continue

    # 如果 tags 是引用 categories 的别名（如 *id001）
    if isinstance(meta.get("tags"), list) and meta.get("tags") == meta.get("categories"):
        meta["tags"] = meta["categories"].copy()
        changed = True

    # 如果存在锚点语法（从文本中判断）
    if "&id" in fm_text or "*id" in fm_text:
        changed = True

    if changed:
        new_yaml = yaml.dump(meta, allow_unicode=True, sort_keys=False)
        new_content = f"---\n{new_yaml}---{body}"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅ 修复完成: {fname}")
    else:
        print(f"跳过: {fname} 无需修复")
