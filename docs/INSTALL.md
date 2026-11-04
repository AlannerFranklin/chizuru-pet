# 安装文档

本项目的核心（桌宠 + 大脑 + 工具 + 生活循环）只需要 Python；
**声音**和**生图/训练**是可选的本地服务，按需接入。

---

## 1. 基础环境（必须）

- **Python 3.12**（作者使用 uv 管理的独立环境，普通 venv 也可以）
- **Windows 10/11**（桌宠窗口、快捷键、WMI 启动都是 Windows API）

```bash
pip install PySide6 requests soundfile lameenc numpy pillow
```

可选（做视频 / B站 / 训练时才需要）：

```bash
pip install playwright open_clip_torch diffusers peft accelerate transformers==4.51.3
python -m playwright install chromium   # 或用本机已装的 Chrome
```

## 2. 配置 API Key

```bash
copy pet\config.example.json pet\config.json
```

编辑 `pet/config.json`：

```json
{
  "base_url": "https://api.deepseek.com/v1",
  "api_key": "sk-你的key",
  "model": "deepseek-chat",
  "temperature": 0.8,
  "timeout": 40
}
```

> `pet/config.json` 已在 `.gitignore` 中，不会被提交。

## 3. 启动桌宠

```bash
pythonw pet\pet.py
```

或双击 `启动桌宠.bat`（用 WMI 启动，脱离父进程，关掉终端也不影响）。

- `Ctrl + Alt + Z`：打开/关闭聊天输入框
- 双击立绘：输入框
- 右键：说一句 / 逛 B 站 / 静音 / 动画 / 帧率 / 打开工作区 / 退出

---

## 4. 接入声音：GPT-SoVITS（可选）

桌宠用 **GPT-SoVITS v2** 复刻她的音色，通过一个常驻 worker 进程提供 TTS。

### 4.1 装 GPT-SoVITS

```bash
git clone https://github.com/RVC-Boss/GPT-SoVITS
cd GPT-SoVITS
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

已知坑（本项目踩过）：

| 现象 | 处理 |
|---|---|
| `ModuleNotFoundError: text/tools` | `PYTHONPATH` 同时包含 `repo` 和 `repo\GPT_SoVITS` |
| gradio 版本冲突 | 固定 `gradio==4.4.1`、`gradio_client==1.3.0` |
| transformers 要求 torch≥2.6 | 降级 `transformers==4.51.3` |
| `torchvision::nms does not exist` | 装 `torchvision==0.20.1+cu121` |
| `2-name2text.txt` 缺失 | 训练前把各分片的 name2text 合并 |

### 4.2 放模型权重

```
GPT-SoVITS/repo/GPT_weights_v2/<你的>.ckpt
GPT-SoVITS/repo/SoVITS_weights_v2/<你的>.pth
GPT-SoVITS/dataset6/raw/<参考音频>.wav   # 3~7 秒、干净、无 BGM
```

### 4.3 配置 worker

`gsv_worker.py` 通过环境变量指定权重与参考音频：

| 变量 | 含义 |
|---|---|
| `GSV_GPT` | GPT 权重路径（相对 `repo/`） |
| `GSV_SOVITS` | SoVITS 权重路径 |
| `GSV_REF` | 参考音频绝对路径 |
| `GSV_REF_TXT` | 参考音频对应的日文文本 |

桌宠 `pet/voice.py` 第一次说话时会自动拉起 worker（`pythonw`，无窗口），
单句合成 **1~2 秒**；模型加载约 13 秒，所以桌宠启动时会**预热**。

### 4.4 经验（很重要）

- **参考音频必须是原声、不要降噪、不要分离**：重降噪会毁掉音色，人声分离会让相似度掉一半
- 参考文本必须和音频**逐字对应**，否则合成会截断
- 情绪来自**参考音频**，不是重新训练：想让她凶一点，就换一段凶的参考
- 别用重度处理过的参考（谱质心会从 2200Hz 掉到 1600Hz，听起来就“糊”）

---

## 5. 接入生图：ComfyUI（可选）

用于生成场景图、素材，以及训练角色 LoRA。

### 5.1 安装

```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
python -m venv venv
venv\Scripts\pip install torch==2.7.1 torchvision==0.22.1 --index-url https://mirror.nju.edu.cn/pytorch/whl/cu126
venv\Scripts\pip install -r requirements.txt
```

> 本机实测：ComfyUI 0.43 的 `comfy_kitchen` 需要 **torch ≥ 2.7**，
> 用 torch 2.5/2.6 会在 `infer_schema` 处直接崩。
> 国内用南京大学镜像下载 torch，比官方源快很多。

### 5.2 放模型

```
ComfyUI/models/checkpoints/Counterfeit-V2.5_fp16.safetensors   # 二次元底模
```

### 5.3 启动（无窗口）

```bash
venv\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188
```

想完全隐藏控制台，用 `.vbs` 包一层（`wscript start_hidden.vbs`）。

本项目通过 HTTP API 提交工作流，见 `tools/gen_bg.py`、`tools/gen_char.py`。

### 5.4 LoRA 训练（角色一致性）

`tools/train_lora2.py`：UNet + TextEncoder 双 LoRA，自写训练循环，不依赖 kohya。

```bash
python tools/train_lora2.py --data <数据集目录> --steps 2400 --lr 1e-4 --te_lr 1e-4
```

**经验**：
- 数据要**同画风、脸占比大、干净**，混画风会训成“泛二次元脸”
- 文本编码器 LoRA 会给风格带来明显漂移，效果不对时先关掉它
- 生成时用 `512×768` 竖版 + `full body, standing` 能出全身

---

## 6. 接入 B 站（可选）

需要一个**专用 Chrome 配置**（独立目录），脚本会自动拉起，不用手动开。

```bash
python tools/bili_login.py     # 第一次：窗口里扫码登录
python tools/bili_auto.py --once --post   # 跑一次：逛 → 点赞收藏 → 发评论
```

原理：Chrome 带 `--remote-debugging-port=9222` + 独立 `--user-data-dir`，
Playwright 用 CDP 连接，登录态持久保存在那个目录里。

> Chrome 136 以后**禁止**对默认配置开调试端口，所以必须用独立配置目录。
> 自动化操作有账号风险，`bili_auto.py` 默认限频（每天 ≤3 次）。

---

## 7. 做视频（可选）

`tools/make_web_video2.py`：**网页动画 → 逐帧截图 → ffmpeg 合成**，比 AI 生图可控。

```bash
python tools/script_v2.py            # 生成配音 + 字幕（需要 GPT-SoVITS）
python tools/make_web_video2.py --fps 60
```

- 动画由 JS 按时间轴计算，所以不会掉帧、不会和音频错位
- 人声用 `adelay` 对齐片头，输出强制 CFR
- 封面：`tools/make_cover.py`（1146×717）

---

## 8. 自主生活循环（核心特性）

`pet/life_core.py` 由桌宠内置调度：

- 白天每 22~45 分钟醒一次，凌晨 1~7 点基本睡觉
- 每次醒来读状态 + 记忆，自己决定做 0~2 件事：
  逛 B 站 / 发评论 / 写日记 / 练台词 / **主动发微信** / 什么都做
- 状态（精力、心情、最近行动）存在 `memory/life_state.json`
- 主动发消息限频：8:00~23:00、每天 ≤2 条、间隔 ≥6 小时

想单独跑（无界面）：

```bash
python tools/life.py --once     # 醒一次
python tools/life.py            # 常驻
```
