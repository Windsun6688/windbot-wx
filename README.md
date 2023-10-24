# windbot-wx
![](https://img.shields.io/github/last-commit/Windsun6688/windbot-wx?style=for-the-badge)
![](https://img.shields.io/github/commit-activity/w/Windsun6688/windbot-wx?style=for-the-badge)


A chatbot that provides mainly rhythm-game-related features.
提供音乐游戏相关服务的聊天软件机器人。
> 还在开发中，写码能力不强，请见谅（

## :page_with_curl: 功能列表 Features List
WindBot主要提供 [Arcaea](https://arcaea.lowiro.com/) / [maimaiDX](https://maimai.sega.jp/) / [Project Sekai](https://pjsekai.sega.jp/) 相关的功能。
<details>
  <summary>主要功能 Main Features</summary>

- **Arcaea相关**: 查询歌曲信息，查询谱面信息，查询别名，获取指定定数所有曲目，定数表，随机曲目
- **maimaiDX相关**: 查询歌曲&谱面信息，查询别名，best50图片生成，随机曲目，新歌列表
- **pjsk相关**: 查询当前活动信息，查询个人FC/AP数据，查询皆传进度，查询别名
  
</details>

<details>
  <summary>其他功能 Other Features</summary>
  
  - 我想要五千兆系图片生成
  - 动画截图溯源
  - 拍一拍反馈
  - RSS订阅推送
  
</details>

## :card_file_box: 开发日志 Develop Log

<details>
  <summary>点我展开 Click To Expand</summary>

  - 2023.9.14
    - 修复rss推送会重复推送，动态删除导致不再判断刷新的问题
  - 2023.9.11
    - 增加rss推送功能
    - 新增randmai函数 随机抽取maimai歌曲
    - 新增mnew函数 显示当前maimai版本所有歌曲
    - 修复拍一拍相关
  - 2023.08.20
    - 适配wxAPI更新，wx版本更新至至3.9.2.23
  
</details>

## :gift_heart: 特别感谢 Thanks

本机器人以这个库为基础开发 This chatbot is developed based on [cixingguangming55555's Wechat API](https://github.com/cixingguangming55555/wechat-bot).

使用来自这里的歌曲数据库 Using song database from [ArcaeaSongDataBase](https://github.com/Arcaea-Infinity/ArcaeaSongDatabase)

5000兆生成器参考 Reference of 5000choyen style image generation [pcrbot/5000choyen](https://github.com/pcrbot/5000choyen)

pjsekai.moe API使用参考 Reference of pjsekai.moe API use [FLAG250/hoshino-plugin-pjsk](https://github.com/FLAG250/hoshino-plugin-pjsk)

maimai b50功能参考 Reference of maimai Best50 function [Yuri-YuzuChaN/maimaiDX](https://github.com/Yuri-YuzuChaN/maimaiDX)

你 You 
> <font color=gray size=5>*Funding of this programme was made possible by viewers like you*</font>
