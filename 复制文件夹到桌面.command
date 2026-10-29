#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd "$(dirname "$0")" && pwd)"
destination="$HOME/Desktop/欧莱雅Demo_最新版_20261020"
if [ "$source_dir" = "$destination" ]; then open "$destination"; exit 0; fi
if [ -e "$destination" ]; then destination="$destination-$(date +%H%M%S)"; fi
if ! ditto "$source_dir" "$destination"; then
 echo '复制未完成，请将这个完整文件夹手动拖到桌面。'
 read -r -p '按回车关闭。' _
 exit 1
fi
echo "已完整复制到：$destination"
open "$destination"
