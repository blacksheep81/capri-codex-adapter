# Capri Codex Adapter

Capri 桌宠到 Codex 自定义宠物的适配准备工具。**当前不是可直接安装的成品宠物。**

2026-10-26 更新：已另外完成一份本地生成的 v2 宠物包（73 帧）。结构预检及质量检查通过，三个独立盲测的主方向通过，部分斜向仍有识别歧义。由于原角色再分发许可未确认，图片和完整包未发布到此仓库；这里仍然只提供工具，不声称可以从仓库直接下载成品。

本仓库仅发布转换代码与说明，不分发 Capri 原始图片或生成后的角色图片，不包含 Windows 可执行程序、语音或聊天服务。

## 已完成与边界

- 从固定上游提交下载七种原始动画，验证 Git blob 哈希，拆帧并生成本地 GIF 预览。
- 将另行制作并审核的 11 行帧打包为 Codex v2 候选包。
- 缺少状态、尺寸错误或目标目录已存在时拒绝打包，不静默重复动画填空。
- 几何检查不等于动作、方向、身份一致性、透明边缘和视觉质量审核通过。
- 原始 Capri 没有完整的 Codex 工作、检查、挥手、左右移动及 16 个注视方向，仍需补充美术与人工预览。

## 精确文件预览

需要 Python 的 Pillow 和系统可用的 FFmpeg。从已打包的 v2 图集生成各状态 GIF、综合 MP4、跳跃衔接、注视循环与四张静帧，不重新绘制角色：

```sh
python preview.py dist/capri/spritesheet.webp --output work/preview
```

此工具只是预览导出，不代替独立视觉审核或应用内测试。

## 运行

Python 3.10 或更新版本：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python adapter.py prepare --output work/source
python -m unittest -v
```

Windows 使用 `.venv\Scripts\activate`。`prepare` 仅访问上游 GitHub 原始素材，不执行上游代码、不安装原应用、不设置自启动。

生成内容位于被 Git 忽略的 `work/` 中。查看 GIF 与 `report.json`。请勿将本地素材目录提交到公共仓库。

## 打包候选

另行准备以下目录，每帧为透明的 192x208 PNG，名称用 `00.png`、`01.png` 等排序。所有行保持同一缩放与基线，跳跃保留真实的垂直位移。

| 行目录 | 帧数 |
| --- | --- |
| idle | 6 |
| running-right | 8 |
| running-left | 8 |
| waving | 4 |
| jumping | 5 |
| failed | 8 |
| waiting | 6 |
| running | 6 |
| review | 6 |
| look-first | 8 |
| look-second | 8 |

`running` 是工作状态，不是跑步。注视方向按屏幕坐标顺时针，第一行为 000 到 157.5 度，第二行为 180 到 337.5 度，间隔 22.5 度；000 朝上。

```sh
python adapter.py pack --frames work/approved --output dist/capri
```

输出 `pet.json` 与 1536x2288 的 `spritesheet.webp`。这是待审核候选，脚本不会安装或切换宠物。完整检查各状态、方向和动画衔接之后，才可将目录放到 `${CODEX_HOME:-$HOME/.codex}/pets/capri/`，并在应用的宠物选择器中尝试选择。尚未进行 Codex 内加载测试。

## 来源与许可

- 上游：[lachydotmcg/capri-desktop](https://github.com/lachydotmcg/capri-desktop)。固定提交 `d2876694bce524e37d89ea1bb043f34e431486e5`，帧数与速度来自该提交的 `app/Capri.cs`。
- 格式参考：[OpenAI Codex pet contract](https://github.com/openai/skills/blob/main/skills/.curated/hatch-pet/references/codex-pet-contract.md)，以及本机现有 v2 manifest 与 Pets v2 布局说明。官方链接目前描述九行旧布局，11 行方向扩展按 v2 合同处理；应用版本兼容性仍需验证。
- 2026-10-26 检查时，上游未提供覆盖角色图像的明确再分发许可。署名不代替授权；发布角色素材或完整宠物包前，需另行确认适用权利。
- 此项目是非官方适配工具，与 OpenAI 和原作者无隶属或背书关系。暂未为整个仓库附加统一许可证；不改变上游或角色素材的权利归属。
