#!/usr/bin/env bash
cd "$(dirname "$0")/AccessibleBeautyAgent" || exit 1
./install-portable.sh
result=$?
[ "$result" -eq 0 ] || echo '安装未完成，请保留上面的错误信息。'
read -r -p '按回车关闭窗口。' _
exit "$result"
