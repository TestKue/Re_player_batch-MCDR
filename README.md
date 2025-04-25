# PlayerBatch - MCDR假人批量操作插件

![License](https://img.shields.io/badge/License-GPLv3-blue)
![MCDR](https://img.shields.io/badge/MCDR-2.1.0%2B-blue)

一个用于MCDReforged的假人批量操作插件，支持快速生成/控制多个假人，适配Carpet Mod等主流假人系统。

## 功能特性

- 🚀 **批量生成** - 通过简单指令快速生成连续编号的假人
- ⚡ **动作执行** - 批量执行攻击/移动/移除等假人操作
- 🛠️ **灵活配置** - 自定义假人名称前缀和权限等级
- 📊 **智能反馈** - 实时显示操作结果和错误日志
- 🔒 **权限管理** - 支持多级OP权限控制

## 安装方法

1. 将 `player_batch.pyz` 放入MCDR的 `plugins` 目录
2. 重启MCDR服务端
3. 自动生成配置文件 `config/player_batch.json`

## 使用说明

### 基础命令格式
```text
基础命令:
!!plb <名称> <起始编号> <结束编号> <动作参数>
!!playerbatch <名称> <起始编号> <结束编号> <动作参数>
```

### 直线生成命令格式
```text
!!plb li <名称> <起始> <结束> <方向> <间隔> <动作>
!!playerbatch li <名称> <起始> <结束> <方向> <间隔> <动作>
```

### 方形阵列命令格式
```text
!!plb re <名称> <起始> <结束> <方向1> <方向2> <间隔> <动作>
!!playerbatch re <名称> <起始> <结束> <方向1> <方向2> <间隔> <动作>
