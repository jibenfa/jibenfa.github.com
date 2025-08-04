import os
import re
import yaml

# 你可以扩展关键词词典
rules = {
    "openwrt": ["openwrt", "lede", "路由器", "固件","MT7621","tp-link"],
    "科学上网": ["v2ray", "shadowsocks", "vpn"],
    "linux": ["linux", "kernel", "shell","debian"],
    "编程": ["python", "perl", "脚本"],
    "虚拟化": ["esxi", "虚拟机", "hypervisor"],
}

post_dir = "_posts"

def match_keywords(text):
    found = []
    txt = text.lower()
    for cat, kws in rules.items():
        if any(kw.lower() in txt for kw in kws):
            found.append(cat)
    return sorted(set(found))

for fname in os.listdir(post_dir):
    if not fname.endswith(".md"):
        continue
    filepath = os.path.join(post_dir, fname)
    with open(filepath, encoding="utf-8") as f:
        lines = f.read().splitlines()

    # 拆分 front matter 和正文
    if not lines or lines[0] != "---":
        print(f"跳过（不是标准 front matter）: {fname}")
        continue
    try:
        idx = lines[1:].index("---") + 1
    except ValueError:
        print(f"跳过（找不到闭合分隔符）: {fname}")
        continue

    fm_lines = lines[1:idx]
    body_lines = lines[idx+1:]
    meta = yaml.safe_load("\n".join(fm_lines)) or {}

    title = meta.get("title", "")
    if not title:
        print(f"{fname} 没有 title，跳过分类")
        continue

    matched = match_keywords(title)
    if not matched:
        print(f"{fname} 未匹配到关键词")
        continue

    changed = False
    if not meta.get("categories"):
        meta["categories"] = matched
        changed = True
    if "tags" not in meta or not meta["tags"]:
        meta["tags"] = matched
        changed = True

    if changed:
        new_fm = yaml.dump(meta, allow_unicode=True, sort_keys=False)
        new_content = ["---"] + new_fm.splitlines() + ["---"] + body_lines
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(new_content))
        print(f"✅ 更新: {fname} → categories, tags: {matched}")
    else:
        print("")
        #print(f"{fname} 已有分类/标签，无需更新")
