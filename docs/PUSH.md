# 推送到 GitHub

## 当前状态

- remote：`https://github.com/CHADAO1/Ai-motion-comic.git`
- credential helper：`manager`（Git Credential Manager 2.9.1，随 Git for Windows 安装）
- 本地有若干 commit 未 push（`git status -sb` 会显示 `ahead N`）
- **没有缓存凭据**，首次 push 需要一次交互式登录

## 方式 A：GCM 浏览器登录（推荐）

在你自己的终端（PowerShell / Git Bash）执行：

```powershell
cd F:\工作区\Ai-motion-comic
git push origin main
```

GCM 弹出登录窗口 → 选择浏览器登录 GitHub → 授权。
凭据由 Windows 凭据管理器安全保存，之后 push 无需再登录。

> 这一步**必须在有界面的终端完成**。无界面 / 自动化 shell 里 GCM 会一直等待并超时。

## 方式 B：Fine-grained PAT

1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token
2. Repository access → Only select repositories → `Ai-motion-comic`
3. Permissions → Repository permissions → **Contents: Read and Write**
4. 执行 `git push origin main`，用户名填 `CHADAO1`，密码粘贴 token（GCM 会保存）

> 不要把 token 写进 remote URL、`.git/config`，或任何会提交进仓库的文件。

## 方式 C：SSH

```powershell
ssh-keygen -t ed25519 -C "CHADAO1" -f "$env:USERPROFILE\.ssh\id_ed25519"
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"   # 贴到 GitHub → SSH and GPG keys
git remote set-url origin git@github.com:CHADAO1/Ai-motion-comic.git
git push origin main
```

SSH 走 22 端口，本环境未验证连通性；若被网络限制请回退方式 A / B。

## 验证

```powershell
git status -sb                      # 应不再显示 ahead
git log --oneline origin/main..HEAD  # 应为空
```
