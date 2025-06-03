# 33娘智能助手系统重构说明

## 概述

这次重构将原本分离的33娘表情控制和对话气泡功能整合到了一个统一的系统中，实现了更好的代码组织和可维护性。

## 文件结构

### 新增文件
- `speech_data.json` - 台词数据文件，存储所有33娘的台词和配置
- `neko33_controller.js` - 统一的33娘控制器，整合表情和气泡功能
- `speech_editor.html` - 可视化台词编辑器，方便管理台词数据

### 移除的文件
- `get_33_expression.js` - 已整合到统一控制器中
- `speech_bubble_controller.js` - 已整合到统一控制器中

### 修改的文件
- `video_border.html` - 更新脚本引用

## 新系统特点

### 1. 数据分离
- 所有台词数据现在存储在独立的JSON文件中
- 可以通过可视化编辑器方便地管理台词
- 支持动态加载和配置修改

### 2. 功能整合
- 表情控制和对话气泡现在由同一个控制器管理
- 确保表情和台词的同步性
- 统一的状态管理和检查逻辑

### 3. 配置灵活性
- 音频路径可配置
- 台词触发概率可调整
- 重复间隔可自定义

## 使用方法

### 1. 基本使用
确保以下文件在项目目录中：
- `speech_data.json`
- `neko33_controller.js`
- `video_border.html`

在OBS中加载`video_border.html`即可使用。

### 2. 编辑台词
1. 在浏览器中打开`speech_editor.html`
2. 点击"加载数据"按钮加载现有台词
3. 编辑、添加或删除台词
4. 点击"保存数据"下载新的JSON文件
5. 将下载的文件替换项目目录中的`speech_data.json`

### 3. 手动控制
可以通过浏览器控制台调用以下函数：
```javascript
// 设置表情（1-7）
set33Expression('2');

// 显示气泡
showSpeechBubble('hello world', 3000);

// 隐藏气泡
hideSpeechBubble();

// 强制检查更新
checkAndUpdate33();
```

## 台词数据结构

```json
{
  "config": {
    "audio_path": "./audio33/",
    "efficient_chance": 0.05,
    "default_repeat_interval": 300000
  },
  "expressions_comments": {
    "DEFAULT": [...],
    "NORMAL": [...],
    "EFFICIENT": [...]
  },
  "learning_comments": {
    "START": [...],
    "LONG_SESSION": [...]
  },
  "study_duration_levels": [...],
  "duration_comments": {
    "C": [...],
    "CC": [...],
    // ...其他等级
  }
}
```

每个台词对象包含：
- `jp`: 日文台词
- `zh`: 中文台词  
- `audio_prefix`: 音频文件前缀

## 表情状态映射

| 状态 | 表情编号 | 说明 |
|------|----------|------|
| DEFAULT | 7 | 默认惊诧表情（未学习状态）|
| NORMAL | 1 | 生气表情（学习中但分心）|
| EFFICIENT | 2 | 开心表情（高效学习状态）|

## 触发逻辑

1. **未学习状态**: 显示默认表情，每5分钟或学习时长变化时触发DEFAULT台词
2. **开始学习**: 触发START台词，切换到对应表情
3. **学习中分心**: 显示生气表情，触发NORMAL台词
4. **高效学习**: 显示开心表情，5%概率触发EFFICIENT台词，95%概率触发对应等级台词

## 故障排除

### 台词不显示
- 检查`speech_data.json`是否存在且格式正确
- 查看浏览器控制台是否有错误信息
- 确认CSV文件和按钮数据文件是否可访问

### 表情不变化
- 检查是否有有效的学习状态数据
- 确认时间阈值设置是否合理
- 验证CSV文件格式是否正确

### 音频不播放
- 检查音频文件路径配置
- 确认音频文件是否存在
- 验证浏览器音频权限设置

## 扩展开发

如需添加新功能，可以：

1. 在`speech_data.json`中添加新的台词分类
2. 在`neko33_controller.js`中添加对应的处理逻辑
3. 通过`speech_editor.html`管理新的台词数据

系统设计为模块化，方便后续扩展和维护。 