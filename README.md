# 用 AI 从零安装 Kindle 微信读书

把「确认型号 → 备份 → 越狱 → 清理 → 安装微信读书 → 实机验证」整理成可供 AI 执行的 Skill。面向 Windows 用户，也提供可在 Python 3.10+ 上运行的文件工具。

**这不是一键刷机包。** 电脑负责文件备份、校验和官方工具准备；飞行模式、重启、打开商店、扫码登录等步骤仍需要本人在 Kindle 上完成。

## 已验证范围

本流程来自一次 Kindle Paperwhite 4（2018／第 10 代）、固件 **5.18.1.1.1** 的实操。使用 SpringBreak v1.2，随后安装用户提供的微信读书 **0.3.6-rc.4**。

已验证：备份文件哈希、越狱完成记录、临时目录清理、安装文件校验，以及用户反馈应用可以打开。没有验证长期稳定性、全部书籍、休眠行为或所有账号。其他型号／固件必须重新查开发者支持表，不要套用本例升级或降级。

## 让 AI 帮你安装

下载本仓库或 Release 工具包，解压到电脑。把下面这段话连同实际安装包路径交给能访问本机文件和终端的 AI：

```text
请读取 skills/kindle-weread-setup/SKILL.md，协助我从未越狱状态安装 Kindle 微信读书。
先核实连接设备、型号和固件，再做可校验的备份。只使用当前明确支持的越狱方案。
我会完成 Kindle 屏幕上的操作。微信读书安装包路径是：<填写电脑上的 ZIP 路径>。
每一步区分准备完成、越狱成功、安装完成和实际运行成功，不要混为一谈。
```

也可将 `skills/kindle-weread-setup/` 文件夹安装到所用 AI 的 skills 目录，随后调用 `$kindle-weread-setup`。具体目录取决于 AI 客户端，仓库不会自动修改客户端设置。

## 完整流程

1. 确认设备型号、300 ppi 等软件要求、固件版本、是否已越狱，以及 USB 文件读写能力。
2. 备份 USB 可读取的文件并校验 SHA-256；备份完成前不执行越狱。
3. 重新核对官方越狱支持范围；本例使用 SpringBreak。
4. 飞行模式、重启、连接 USB；电脑运行官方工具准备文件。
5. 安全弹出拔线，在 Kindle 打开商店并按需联网，等待执行结果及自动重启。
6. 回到主页后开启飞行模式并重连；确认成功记录，再用官方工具清理临时目录。
7. 阅读微信读书安装包说明，复制适用文件并逐个校验。
8. 安全弹出拔线，运行「微信读书兼容性检查」；重连读取报告后判断下一步。
9. 正常打开微信读书，联网扫码登录，验证阅读、退出、休眠和唤醒。

逐步操作、失败处理和恢复边界见 [完整安装教程](skills/kindle-weread-setup/references/guide.md)。

## 附带工具

命令示例中的 `F:\` 只是示例；**先确认真实 Kindle 盘符**，不要直接照抄。

```powershell
# USB 文件备份；将备份放在电脑上，不放在 Kindle 上
python skills/kindle-weread-setup/scripts/kindle_tools.py backup --device F:\ --out backups/before-jailbreak

# 检查并校验现有备份
python skills/kindle-weread-setup/scripts/kindle_tools.py verify-backup --backup backups/before-jailbreak

# 下载固定版本的官方 SpringBreak，并核对已登记的 SHA-256；不会执行它
python skills/kindle-weread-setup/scripts/download_springbreak.py --out downloads/springbreak.zip

# 微信读书安装预览（不写设备）
python skills/kindle-weread-setup/scripts/kindle_tools.py install --device F:\ --package "微信读书安装包.zip"

# 使用通过校验的备份记录，实际安装；安装记录另存电脑
python skills/kindle-weread-setup/scripts/kindle_tools.py install --device F:\ --package "微信读书安装包.zip" --backup backups/before-jailbreak --record private/install-record --apply
```

安装器只复制 `weread/`、`documents/`、`extensions/`、`fonts/`。同名且内容不同的文件默认拒绝覆盖；更新时先正常退出应用、重新备份，再使用 `--allow-update`。保留原账号目录、缓存、共享字体和无关文档。

## 工具包与第三方安装包

- Release ZIP 包含本教程、Skill、Python 工具、测试和官方来源清单。
- **不包含 Kindle 固件、SpringBreak 二进制、微信读书二进制或字体。** SpringBreak 通过固定官方链接按需下载；微信读书 ZIP 由用户从作者渠道自行取得。
- 用户提供的微信读书 ZIP 未附可确认的再分发许可证，因此不会公开重打包。本仓库的 MIT 许可证不覆盖它。
- 不收集或上传设备序列号、书籍、笔记、账号、Cookie 或令牌。备份和日志保存在用户电脑，不应上传 GitHub。

普通 USB 文件备份不是完整系统镜像，无法保证恢复全部进度或一键撤销越狱。卸载越狱应另行遵循开发者流程，不能把恢复出厂设置当作通用撤销按钮。

## 开发与验证

```powershell
python -m unittest discover -s tests -v
python scripts/build_release.py
```

项目只需要 Python 标准库。工具包通过固定文件清单构建，不递归收集用户目录；生成 SHA-256 校验文件。源代码和教程采用 MIT 许可证，第三方项目保持其原有权利归属。
