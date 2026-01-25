#!/bin/bash
# 自动更新 README.md 活跃状态
# 用于阿里云定时函数，防止 GitHub Actions 失活

# 1. 克隆仓库到临时目录（使用浅克隆加速）
REPO_URL="https://github.com/PPsteven/shanghai-view-tourist-realtime.git"
TMP_DIR="/tmp/shanghai-view-tourist-realtime-$$"
git clone --depth=1 "$REPO_URL" "$TMP_DIR"
cd "$TMP_DIR"

# 2. 运行活跃状态更新逻辑
README="README.md"
ACTIVE_MARK="当前项目在"
DATE=$(date '+%Y-%m-%d')
ACTIVE_LINE="当前项目在 $DATE 时还活跃"

# 检查 README.md 是否存在
if [ ! -f "$README" ]; then
  echo "README.md 不存在，脚本终止。"
  exit 1
fi

# 如果已存在活跃行，则替换，否则追加到文件末尾
if grep -q "$ACTIVE_MARK" "$README"; then
  # 用 Linux 版 sed 替换首个匹配行
  sed -i "/^$ACTIVE_MARK.*$/c$ACTIVE_LINE" "$README"
else
  # 替换占位符（如果有）
  if grep -q "<!-- 活跃状态自动更新标记" "$README"; then
    sed -i "/<!-- 活跃状态自动更新标记/ {n;s/.*/$ACTIVE_LINE/;}" "$README"
  else
    # 追加到文件末尾
    echo -e "\n$ACTIVE_LINE" >> "$README"
  fi
fi

# 3. git 操作：自动提交并推送
if git diff --quiet "$README"; then
  echo "README.md 无需更新，未做 git 提交。"
else
  git add "$README"
  git commit -m "chore: 自动更新活跃状态 $DATE"
  git push
  echo "已自动提交并推送到远程仓库。"
fi

echo "README.md 已更新：$ACTIVE_LINE"

# 4. 清理临时目录
cd /
rm -rf "$TMP_DIR"
