# windbot-wx
![](https://img.shields.io/github/last-commit/Windsun6688/windbot-wx?style=for-the-badge)
![](https://img.shields.io/github/commit-activity/w/Windsun6688/windbot-wx?style=for-the-badge)

```
#######################################################
# ___       ______       ________________      _____  #
# __ |     / /__(_)____________  /__  __ )_______  /_ #
# __ | /| / /__  /__  __ \  __  /__  __  |  __ \  __/ #
# __ |/ |/ / _  / _  / / / /_/ / _  /_/ // /_/ / /_   #
# ____/|__/  /_/  /_/ /_/\__,_/  /_____/ \____/\__/   #
#                                                     #
#######################################################
```

A chatbot that provides mainly rhythm-game-related features.
提供音乐游戏相关服务的聊天软件机器人。
> 还在开发中，写码能力不强，请见谅（

## :page_with_curl: 功能列表 Features List
WindBot主要提供 [Arcaea](https://arcaea.lowiro.com/) / [maimaiDX](https://maimai.sega.jp/) / [Project Sekai](https://pjsekai.sega.jp/) 相关的功能。
<details>
  <summary>主要功能 Main Features</summary>

- **Arcaea相关**: 查询歌曲信息，查询谱面信息，查询别名，获取指定定数所有曲目，定数表，随机曲目
- **maimaiDX相关**: 查询歌曲&谱面信息，查询别名，best50图片生成，随机曲目，新歌列表，牌子查询
- **pjsk相关**: 查询当前活动信息，查询个人FC/AP数据，查询皆传进度，查询别名
  

</details>

<details>
  <summary>其他功能 Other Features</summary>

  - 我想要五千兆系图片生成
  - 动画截图溯源
  - 拍一拍执行命令
  - RSS订阅推送

</details>

## :card_file_box: 开发日志 Develop Log

<details>
  <summary>点我展开 Click To Expand</summary>

- 2024.01.08
    - 更新功能：
        - rand <item1> <item2> [item3]...... 随机抽取项目
    - 修复功能：
        - mb50 rating框颜色不正确的问题

- 2023.12.30
    - 更新功能：
        - parrot, friday更改为@命令触发
        - parrot现在会发送parrot名称+更高清的parrot动图
        - parrot新增参数 `l`（lowres）发送之前的低像素版本动图

- 2023.12.23
    - 更新功能:
        - minfo现在会将DX后版本号显示为国行版本
        - parrot更改为触发词触发
- 2023.12.20
    - 添加功能:
        - parrot 随机发送一张派对鹦鹉图片
- 2023.12.15
    - 修复功能:
        - 当WB未记录昵称被拍时，会正确刷新用户
        - 调用时的前置和后置空格已被chomp
- 2023.12.15
    - 修复功能:
        - PatAction可以连环绑定的问题
        - 使用设定为patstat的PatAction对群组造成侵入性影响的问题
- 2023.12.13
  - WindBot一周年！🎉
  - 新增功能:
    - PatAction 拍一拍WB执行预设定命令
    - 使用“WB"呼出WindBot
    - listfunc 展示所有可用命令

- 2023.12.4
  - 修复功能: mplate
    - 修复了名牌版确定后会多次出现总共计数的问题
    - 解决了Re:Master计数出错的问题
    - 华&煌系列的国服特性已经正确显示

- 2023.12.3
  - 新增功能:
    - mplate <plate> maimai名牌版进度查询 (Diving-Fish数据源)

- 2023.12.1
  - 改善了功能呼叫结构
  - 新增功能:
    - 机器电池检测功能，失去墙插自动提醒管理员

- 2023.11.25
  - 修复了rss推送功能的
    ```
    题@个:
    这       
    Link: 问
    ```

- 2023.10.18
  - 修复功能: pjskpf, amikaiden
  - 新增功能:
    - pwhat [alias] pjsk别名库
    - pinfo [ID | Title] pjsk歌曲信息
    - pcinfo [ID] pjsk谱面信息

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
