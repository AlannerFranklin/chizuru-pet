# 水原千鶴 · 二次元桌宠 + 自主生活循环

一个本地运行的「水原千鶴」（《出租女友》）角色项目：性格、声音、B 站活动、自主生活，全部跑在自己电脑上。

## 它能做什么

| 模块 | 能力 |
|---|---|
| **性格** | 四种语气（素 / 営業 / 衝突 / 软肋），台词语料 + LLM 生成，人格卡见 `card_v0_4.md` |
| **声音** | GPT-SoVITS 音色克隆（日语），气泡显示中日双语 |
| **桌宠** | PySide6 透明窗口，60fps 呼吸动画、置顶、可拖动、`Ctrl+Alt+Z` 唤起输入 |
| **B 站** | 自己搜索 / 挑视频 / 发评论 / 点赞 / 收藏；`bili_auto.py` 定时运营 |
| **工具** | 联网搜索、抓网页、读写文件、跑 PowerShell / Python、子代理 |
| **记忆** | E 盘持久化 + 自动压缩摘要（`memory.json`） |
| **自主生活** | `life_core.py`：定时醒来 → 自己决定做什么（逛 B 站 / 写日记 / 练台词 / 主动发微信） |
| **做视频** | 网页动画（HTML/CSS/JS）+ Playwright 逐帧渲染 + ffmpeg 合成，见 `tools/make_web_video2.py` |

## 目录结构

```
pet/            桌宠本体（GUI、大脑、声音、工具、生活循环）
tools/          B站脚本、生图、做视频、抓素材、LoRA 训练
review/         语音标注页（历史）
review_img/     图片审核页
card_v0_4.md    人格卡
启动桌宠.bat     一键启动（WMI 方式，脱离父进程）
```

## 快速开始

1. 安装依赖（Python 3.12）：
   ```bash
   pip install PySide6 requests soundfile lameenc numpy pillow
   ```
2. 复制 `pet/config.example.json` 为 `pet/config.json`，填入你的 DeepSeek API Key。
3. 双击 `启动桌宠.bat`（或 `pythonw pet/pet.py`）。

## 依赖的本地服务（可选）

- **GPT-SoVITS**：提供她的声音，`pet/voice.py` 会启动 `gsv_worker.py`
- **Chrome + CDP**：B 站自动化用独立配置目录，脚本会自动拉起
- **ComfyUI**：AI 生图 / LoRA 训练（`tools/gen_bg.py`、`tools/train_lora2.py`）

## 说明

- 语料、模型权重、图片素材都**不**在本仓库内（体积与版权原因）
- 角色版权归原作者；本项目仅为个人本地实验，不做分发
