# LeanAgent

Lean 4 项目，用于 Gauss 的形式化验证。

## 概述 | Overview

此目录包含 Lean 4 项目配置，用于：
- 引入 Mathlib 数学库依赖
- 提供 Lean 4 编译环境供 `lean_env.py` 调用
- 存放经 Gauss 系统验证过的定理

## 配置 | Configuration

- **Lean 版本**: v4.29.0-rc4（见 `lean-toolchain`）
- **构建工具**: Lake（见 `lakefile.toml`）
- **依赖**: Mathlib

## 使用 | Usage

```bash
# 构建项目（首次需要下载 Mathlib，耗时较长）
cd lean_project
lake build

# 检查单个文件
lake env lean LeanAgent/Basic.lean
```

## 结构 | Structure

```
lean_project/
├── lakefile.toml           # Lake 构建配置
├── lean-toolchain          # Lean 版本指定
├── lake-manifest.json      # 依赖锁文件
├── LeanAgent.lean          # 根模块（导入 Basic）
└── LeanAgent/
    └── Basic.lean          # 基础定义
```