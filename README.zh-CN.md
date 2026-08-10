<div align="center">

# 🧭 智途 Career+ · ZhituCareer+

**AI 驱动的职业规划与求职智能助手**

基于 **Flask + 多 Agent 协作（LLM + Playwright 实时市场分析）** 打造的一站式职业分析平台，
提供职业路径分析、职位智能匹配与课程学习推荐。

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)
![ModelScope](https://img.shields.io/badge/LLM-ModelScope%20%2F%20SiliconFlow-4B32C3?style=flat-square)
![Playwright](https://img.shields.io/badge/Playwright-Automation-2EAD33?style=flat-square&logo=playwright&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)

<br>

**⭐ 如果这个项目对你有帮助，欢迎 Star 支持！**

</div>

---

## ✨ 特性一览

| 特性 | 说明 |
| --- | --- |
| 🎯 **职业路径分析** | 基于个人画像与实时市场数据，生成专属职业发展方向 |
| 💼 **职位智能匹配** | 结合技能与搜索偏好，从职位库中匹配最合适的工作 |
| 📊 **市场趋势洞察** | Playwright 实时抓取就业市场动态，AI 汇总行业风向 |
| 📚 **课程学习推荐** | 围绕职业目标推荐匹配的课程与学习路径 |
| 🔐 **角色权限控制** | 用户 / 管理员双角色，独立管理后台 |
| 🚀 **开箱即用** | 内置演示账号与示例数据，分钟级完成部署 |

---

## 📸 界面预览

### 登录页

![登录页](docs/screenshots/login.png)

### 用户职业分析仪表盘

![用户仪表盘](docs/screenshots/dashboard.png)

### 管理后台

![管理后台](docs/screenshots/admin.png)

---

## 🧠 核心概念：多 Agent 协作架构

ZhiTuCareer+ 采用模块化的 **Agent 协作架构**，多个智能体各司其职、串联协作：

- **User Profile Agent**：解析用户学历 / 专业 / 技能 / 经验 / 目标，输出个人能力画像
- **Market Analysis Agent**：基于 Playwright 实时抓取就业市场动态，结合 LLM 输出行业趋势
- **Job Recommendation Agent**：融合个人画像与市场分析，生成结构化求职建议
- **Job Matching Agent**：从职位库中按匹配度筛选最适合用户的岗位
- **Course Matching Agent**：结合职业目标推荐最匹配的学习课程

```
用户画像 Agent ──► 市场分析 Agent ──► 职位推荐 Agent ──► 推荐结果
                        │                    │
                        ▼                    ▼
                Playwright 实时抓取     职位匹配 Agent / 课程匹配 Agent
```

<div align="center">
  <img src="agent/agent_structure.jpeg" width="360px">
</div>

---

## 🚀 快速开始

### 环境要求

- Python 3.9+（推荐使用 [Anaconda](https://www.anaconda.com/download) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)）
- 一个 [ModelScope](https://www.modelscope.cn/) 或 [SiliconFlow](https://siliconflow.cn/) 的 API Key

### 安装

```bash
# 1. 创建并激活虚拟环境
conda create -n zhitu_career python=3.9
conda activate zhitu_career

# 2. 克隆仓库
git clone https://github.com/NoahIsARider/ZhituCareer.git
cd ZhituCareer

# 3. 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
cp .env.example .env
```

```env
# 必填：ModelScope / SiliconFlow 的 API Key
OPENAI_API_KEY=your_api_key_here

# 可选：自定义模型与接口地址
# LLM_BASE_URL=https://api-inference.modelscope.cn/v1/
# LLM_MODEL=LLM-Research/Meta-Llama-3.1-8B-Instruct

# 可选：生产环境建议修改会话密钥
# SECRET_KEY=your-secret-key
```

> 💡 所有模型名、接口地址均可通过环境变量覆盖，无需修改任何代码。
> 未配置 API Key 时应用仍可正常启动，AI 分析功能会在调用时给出清晰提示。

### 启动应用

```bash
python app.py
```

访问 **http://localhost:5000**，使用演示账号登录：

| 角色 | 手机号 | 密码 |
| --- | --- | --- |
| 👑 管理员 | `13800000000` | `admin123` |
| 👤 普通用户 | `13900000000` | `user123` |

---

## 📖 使用指南

### 普通用户

1. 登录后在仪表盘填写 **教育背景 / 专业 / 技能 / 经验 / 职业目标**
2. 点击「获取职业分析」，AI 将生成 **职业方向、求职建议、能力提升清单与推荐职位**
3. 使用「职位搜索」按关键词与城市匹配岗位
4. 使用「课程推荐」获取与职业目标匹配的学习路径

### 管理员

1. 登录后在「管理后台」查看课程与职位的实时统计
2. 通过卡片操作 **添加 / 编辑 / 删除** 课程与职位数据
3. 数据保存至 `data/course.json` 与 `data/jobs.json`

---

## 🗂️ 项目结构

```
ZhituCareer/
├── app.py                  # Flask 主应用（路由、鉴权、会话管理）
├── career_model.py         # 职业分析编排（多 Agent 串联）
├── job_matching.py         # 职位匹配服务
├── course_matching.py      # 课程匹配服务
├── agent/                  # 多 Agent 协作层
│   ├── llm_client.py       # LLM 客户端与统一响应处理
│   ├── user_profile_agent.py
│   ├── market_analysis_agent.py   # Playwright 市场抓取
│   ├── job_recommendation_agent.py
│   ├── job_matching_agent.py
│   └── course_matching_agent.py
├── data/                   # 数据存储（JSON）
│   ├── users.json          # 用户与角色
│   ├── jobs.json           # 职位数据
│   └── course.json         # 课程数据
├── templates/              # 前端页面（Bootstrap 5）
│   ├── login.html          # 登录页
│   ├── index.html          # 用户仪表盘
│   └── admin.html          # 管理后台
└── requirements.txt
```

---

## 🛠️ 技术栈

| 层次 | 技术 |
| --- | --- |
| 后端 | Flask 3 · Python 3.9+ |
| AI 引擎 | OpenAI 兼容接口（ModelScope / SiliconFlow）· Meta-Llama-3.1-8B-Instruct |
| 数据采集 | Playwright（Chromium 无头浏览器） |
| 前端 | Bootstrap 5 · Bootstrap Icons · 原生 ES6 |
| 数据存储 | JSON 文件（可无缝迁移至 SQLite / MySQL，见 [data_base 分支](https://github.com/NoahIsARider/ZhituCareer/tree/data_base)） |

---

## 🔧 自定义配置

系统高度可配置，全部通过环境变量完成：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OPENAI_API_KEY` | 空 | **必填**，ModelScope / SiliconFlow API Key |
| `LLM_BASE_URL` | ModelScope v1 | 自定义 LLM 接口地址 |
| `LLM_MODEL` | Llama-3.1-8B | 自定义推理模型 |
| `SECRET_KEY` | dev 占位符 | Flask 会话密钥，生产必改 |
| `HOST` / `PORT` | `0.0.0.0` / `5000` | 服务监听地址 |
| `FLASK_DEBUG` | `0` | 是否开启调试模式 |

---

## 🤝 参与贡献

欢迎任何形式的贡献！

- 🐛 发现 Bug → 提交 [Issue](https://github.com/NoahIsARider/ZhituCareer/issues)
- ✨ 新功能 / 改进 → Fork 后提交 Pull Request
- 📖 完善文档 → 帮助更多人快速上手

> 在提交 PR 前，请确保代码通过基础检查，并遵循现有代码风格。

---

## 📄 License

本项目基于 **MIT License** 开源，详见 [LICENSE](LICENSE) 文件。
