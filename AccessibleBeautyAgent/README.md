# TRACE-Next 本地运行

面向盲人和低视力用户的语音优先美妆陪伴项目。它独立于化妆品公司、支付平台和比赛，不限定品牌；当前默认 mock。

## 安装与启动

Python 3.12.x、Node.js 26.10.0。双击外层首次安装入口后再双击启动入口。Mac使用.command，Windows使用.bat。终端可运行本目录install-portable.sh，然后用应用Python运行launch-portable.py。Mac应用Python为.venv-portable/bin/python，Windows为.venv-portable/Scripts/python.exe。

默认网页 http://127.0.0.1:5280/ ，API8112，语音8113。配置见runtime.json。保留窗口，Control+C停止。可用launch-portable.py的--frontend-port、--backend-port、--voice-port指定空闲端口，--doctor查看状态，--no-browser不自动开网页。缺模型仍可文字交互。

## 配置与模型

没有复制旧版.env、密钥、用户SQLite、录音或下载权重。需要远程AI时从.env.example创建自己的.env，明确配置ALLOW_REMOTE_AI和供应商。数据库默认data/users/beauty.sqlite，属于新目录；Cookie仅做本机匿名隔离，不是付费账号。

应用Python执行voice/setup_local_voice_models.py核验语音资产，加--download下载；scripts/setup_local_landmarks.py --check核验视觉资产，去掉--check安装。固定来源与哈希见原有模型清单。可选硬件用pip install -e hardware单独安装，缺包时核心正常降级。

## 验证和开发

应用Python运行：-m pytest -ra；scripts/validate_kb.py；scripts/verify_runtime.py --missing-voice（缺模型时）；-m unittest discover -s voice -p test_bounded.py。前端目录运行npm test、npm run build。

新集成导入app.factory.create_app不会创建默认应用和数据库；app.main:app保留兼容启动。ExtensionSpec接入命名路由/api/extensions/{name}，各扩展须另做对象所有权、身份及业务验证。

旧目录保持原位。回退时停止新目录并启动旧版，不把新库覆盖旧库。用户数据迁移不在本次范围。行为及证据见仓库根级 SPEC.md 和 docs 目录。尚未完成 Windows 实机、实体音视频/读屏、真实远程 AI、专业审核和目标用户试用验收。
