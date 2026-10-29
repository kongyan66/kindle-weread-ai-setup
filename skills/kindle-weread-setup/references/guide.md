# 从未越狱到微信读书可用：操作教程

## 1. 准备与设备检查

需要 Kindle、可传数据的 USB 线、电脑、Wi-Fi、本人手机微信，以及从作者渠道获取的 Kindle 微信读书 ZIP。它不是手机安卓 APK。

本教程实操样本：Paperwhite 4／2018 款／第 10 代，300 ppi，固件 5.18.1.1.1。不要把 Paperwhite 第 10 代和入门款 Kindle 第 10 代混为一谈。

在 Kindle「设置 → 设备选项 → 设备信息」核实型号、固件。菜单名称可能随版本变化。电脑应能打开 Kindle USB 存储；Windows 可使用 `pnputil /enum-devices /connected /class DiskDrive` 只读确认当前连接。仅存在盘符或注册表旧记录不够。

若电脑资源管理器能读取、AI 的终端却提示拒绝访问，优先处理工具权限，不要据此断言设备故障。

## 2. 备份与恢复边界

把 Kindle USB 可读取的文件备份到电脑，包含隐藏文件、`documents`、`.sdr`、`My Clippings.txt`。跳过 Windows 的 `System Volume Information`。使用附带工具逐个校验 SHA-256，完成后生成 `manifest.json`。`verify-backup` 必须通过，才进入越狱。

备份保存好，不上传。普通 USB 备份不是固件／系统分区镜像。通常可以拷回个人文件，但登录状态、全部笔记和进度不保证完整恢复；`My Clippings.txt` 是文本记录，拷回不等于重建书内标注。不要在不同固件上盲目覆盖 `system`。

## 3. 选择当前支持的越狱

以开发者当前文档为准：

- [KindleModding 入口](https://kindlemodding.org/jailbreaking/)
- [SpringBreak 源项目](https://github.com/KindleModding/SpringBreak)
- [SpringBreak 操作步骤](https://kindlemodding.org/jailbreaking/SpringBreak/)

本例 PW4／5.18.1.1.1 使用 SpringBreak v1.2。仓库的 `sources.json` 登记该官方 ZIP 和已核对的 SHA-256。固定下载用于重现本例；版本改变应重新审查兼容范围和哈希，而非把清单当成永久最新结论。

本教程不打包第三方越狱二进制，也不自动升级、降级或恢复出厂设置。

## 4. SpringBreak 电脑准备

确认已备份且已登录亚马逊账号。安全弹出 Kindle 并拔线，开启飞行模式，重启；回到主页后再连接电脑。

下载、校验并解压官方包。`.active_content_sandbox` 必须与 `springbreak.exe` 保持包内的相对位置。在解压目录运行官方工具，看到设备列表后选择已确认的 Kindle 盘。

工具会替换商店缓存并创建约 5,000 层临时目录，Windows 上可能需要几分钟。不要拔线，不要自行添加其他教程的填充文件，也不要对深目录执行普通递归删除命令。

仅当工具明确显示 `SpringBreak Preparation Complete` 后才进入下一步。这仍不是越狱成功。

## 5. Kindle 上触发

安全弹出、拔线，回到主页打开商店／购物车图标。提示联网时关闭飞行模式并连接 Wi-Fi，等待 SpringBreak 页面和执行文字。

短暂加载可等待；持续加载不等于成功。如果没有执行文字，先记录等待时间、当前屏幕和联网状态。不要反复强制重启或恢复出厂设置。若已经执行到 `Done`、`Restarting Kindle…` 并自动重启，等待回到主页。

如果出现 `Application Error`，开发者的排查建议包含一次或几次重新插拔连接；先保存具体错误再选择后续步骤，不要无目的循环尝试。

## 6. 清理与验证

回到主页后开启飞行模式，重连电脑。检查 `documents/JAILBROKEN.txt` 等实际生成的完成记录。不要因某个固定文件不存在就直接断言失败，结合屏幕及日志判断。

在原解压目录重新运行官方 SpringBreak 工具并选择相同设备，执行 `Post-Jailbreak Cleanup`。这个操作会删除先前的临时商店缓存；核实目标限定在正确 Kindle 的 `.active_content_sandbox`。

清理结束应显示 `Done`。核对临时目录已移除，确认无待安装的根目录 `update*.bin`／`update.bin.tmp.partial`。若发现，先核对文件用途；不得泛化为删除所有 `.bin`。必要时保留到电脑再处理。

未清理的深目录可能使后续启动非常慢。清理完成前不要把整个流程宣布结束。

## 7. 安装 Kindle 微信读书

本例安装包为 0.3.6-rc.4，作者标注候选测试版。实操样本成功不表示全部机型或书籍已验证。

读取安装说明，确认当前已支持 Scriptlets／SH_Integration 文档入口，或符合包要求的其他启动器。现代越狱可能已配置所需组件，不要重复混装旧 KUAL／hotfix。

先执行安装预览。仅合并复制这四个目录到 USB 根目录：`weread`、`documents`、`extensions`、`fonts`。不要把 ZIP 外层目录一起复制，也不要替换整个 `documents`／`fonts` 文件夹。

附带安装器拒绝越界、符号链接和重复冲突路径，按 SHA-256 校验复制结果。遇到不同内容的同名文件会停下；更新需先正常退出应用并做新备份，再明确选择 `--allow-update`。不要删除原账号目录、书籍缓存或共享字体。

## 8. 兼容性检查

安全弹出并拔线，在图书馆打开「微信读书兼容性检查」。找不到时切换为全部／文档，等待索引更新。只生成报告是正常行为；重连后读取 `documents/微信读书兼容性报告.txt`。

本例报告显示：PW4、1072×1448、`hardware_preflight=pass`、`portable_probe=ready`，同时 `firmware_contract=blocked`、`hardware_validation=not-tested`。因此不能宣布完全兼容；正常启动后实际观察，不修改二进制或绕过检查。

## 9. 登录、阅读与退出

安全弹出拔线，打开「微信读书」，连接 Wi-Fi；本人用手机微信扫码并确认。AI 不需要获取登录二维码、Cookie 或令牌。

验证：应用首屏、扫码登录、开书、翻页、退出、休眠后唤醒。分别记录哪些已实际通过。退出到 Kindle 原生主页用「退出应用」；「退出登录」会退出微信读书账号，不是关闭应用。按钮位置随版本变化，看不到时提供当前屏幕让 AI 定位，不猜坐标。

## 10. 故障与卸载

先保存实际存在的 `weread/launch.log` 和对应会话 `app.log`、`session.log`，再决定是否重启或恢复。不要反复重现卡死。日志也可能含个人信息，分享前检查并脱敏，不上传整个缓存或账号目录。

应用提供「微信读书恢复」文档入口；按本包说明，在系统主页可操作时使用。卸载应用只处理其明确拥有的文件和目录，保留共享 `fonts`、书籍和其他应用。卸载越狱是另一项操作，遵循 [官方撤销指南](https://kindlemodding.org/jailbreaking/unjailbreaking.html)，不要把普通恢复出厂设置当作通用撤销。
