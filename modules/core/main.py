# WindBot Core Functions Module
# May 2024

# Standard Lib Imports
import random
import time

# Third Party Imports

# Module Helper Imports
from ..moduleHelper import ModuleHelper, ModuleMetadata

mh = ModuleHelper()

__module_meta__ = ModuleMetadata(
    name =  "Core",
    desc =  "Windbot Basic Functions",
    extra = {
        "moduleuid": "core",
        "version": "0.0.1",
        "author": ["Windsun"],
    }
)

class Core(object):
    # Module Properties
    META: ModuleMetadata
    USER_FUNCTIONS: dict
    MNGNG_FUNCTIONS: dict
    STATIC_PATH: str

    def __init__(self):
        super(Core, self).__init__()
        self.META = __module_meta__
        self.USER_FUNCTIONS = {
            "nop": self.no_op,
            "swym": self.no_op,
            "rand": self.rand_item,
            "listfunc": self.list_functions,
            "bind": self.bind,
            "reperr": self.report_error,
            "mdsts": self.module_status,
            "patstat": self.patstat,
            "fdbk": self.feedback,
        }
        self.MNGNG_FUNCTIONS = {
            "listmng": self.list_functions_mng,
            "funcswitch": self.function_switch,
            "modswitch": self.module_switch,
            "unmark": self.unmark,
            "mdsts_mng": self.module_status,
            "announce": self.announce,
            "annswitch": self.announce_switch,
            "annview": self.announce_list,
            "funcrank": self.func_called_rank,
            "refresh": self.refresh,
        }
        self.STATIC_PATH = mh.compose_static_path("core")

    # Do Nothing
    # Sympathize with Your Machine
    def no_op(self, args):
        return mh.compose_txt_msg("")

    # Provides a random selection from a list of options.
    def rand_item(self, args):
        func_data = args[0]

        data_len = len(list(set(func_data)))
        if data_len < 1:
            reply = "请提供随机清单。"
        elif data_len == 1:
            reply = "您知道吗？WDS曾经说WB做决策的时候很困难，但是现在WB不确定了。"
        else:
            reply = f"WB为您随机(1/{data_len})挑选了:\n"
            reply += random.choice(func_data)

        return mh.compose_txt_msg(reply)

    # List User Functions
    def list_functions(self, args):
        avail_usr_func = args[-1][0]
        marked_usr_func = args[-1][5]

        current_date = time.strftime("%Y-%m-%d")
        reply = f"WB的指令一览({current_date}):\n"
        for module in avail_usr_func:
            reply += f"[{module}]\n"
            for func in avail_usr_func[module]:
                avail_status = [" [X]", " [O]"]
                marked_status = ["", " [*]"]
                func_status = avail_status[int(avail_usr_func[module][func])]
                func_mark = marked_status[int(marked_usr_func[module][func])]
                reply += f" - {func}{func_status}{func_mark}\n"

        return mh.compose_txt_msg(reply)

    # List Management Functions
    def list_functions_mng(self, args):
        print("CALLED list_mng")
        avail_mng_func = args[-1][1]

        current_date = time.strftime("%Y-%m-%d")
        reply = f"WB的管理指令一览({current_date}):\n"
        for module in avail_mng_func:
            reply += f"[{module}]\n"
            for func in avail_mng_func[module]:
                avail_status = ["[X]", "[O]"]
                func_status = avail_status[int(avail_mng_func[module][func])]
                reply += f" - {func}{func_status}\n"

        return mh.compose_txt_msg(reply)

    # Binding Data with User
    def bind(self, args):
        wb_db = args[-1][2]
        all_func = args[-1][4]
        func_data = args[0]
        usr_id = args[1] 

        if len(func_data) == 0:
            reply = "请指明需要绑定的项目类型和内容。"
            return mh.compose_txt_msg(reply)

        bind_categories = {
            'arc': 'arcID',
            # 'qq': 'qqID', # For Now, QQID Serves no purpose.
            'pjsk': 'pjskID',
            'mai': 'maiID',
            'pat': 'patAction'
        }

        reply = ""
        keyword = func_data[0]

        # Bind View
        if keyword == "view":
            reply = self.bind_view(args)

        # Bind Category not Found
        elif keyword not in bind_categories:
            reply = f"没有该项目: {keyword}"

        # Binding Data
        else:
            content = " ".join(func_data[1:]).strip()
            app_sql_ID = bind_categories.get(keyword)

            # For Game IDs
            if keyword != "pat":
                reply = f"已绑定至 {app_sql_ID}：{content}"
            # For PatAction
            else:
                if len(content) > 30:
                    reply = "您的PatAction超过了30个字符。"
                    return mh.compose_txt_msg(reply)
                elif content.isspace() or content == "":
                    reply = "请提供PatAction。"
                    return mh.compose_txt_msg(reply)
                elif content.split(" ")[0] not in all_func:
                    reply = f"您的PatAction功能[{content.split(' ')[0]}]不可用。"
                    return mh.compose_txt_msg(reply)
                elif "bind" in content:
                    reply = "https://www.google.com/search?q=recursion"
                    return mh.compose_txt_msg(reply)
                elif "patstat" in content:
                    reply = "为了解决WB对群聊具有高度侵入性的情况，"
                    reply += "您不能将patstat绑定为PatAction。谢谢您的理解。"
                    return mh.compose_txt_msg(reply)
                else:
                    reply = f"已将PatAction设置为： {content}"

            # Bind User's content to corresponding app_sql_ID item
            wb_db.update("Users", app_sql_ID, content, "wxid", usr_id)

        return mh.compose_txt_msg(reply)

    # Helper of bind, provides an overview of binded data.
    def bind_view(self, args):
        wb_db = args[-1][2]
        BOT_GC_INVOKER = args[-1][3]
        usr_id = args[1] 

        usr_info = wb_db.fetch("Users",\
                               ["arcID", "maiID", "pjskID", "patAction"],\
                               "wxid", usr_id)[0]
        id_type = ["Arcaea","maimai查分器","pjsk","PatAction指令"]
        reply = ""

        unbound_cnt = 0
        # Game IDs
        for i in range(len(usr_info)-1):
            if str(usr_info[i]) != "-1":
                reply += f'已绑定的{id_type[i]}ID： {usr_info[i]}\n'
            else:
                unbound_cnt += 1
                reply += f'您没有绑定{id_type[i]}ID\n'

        # PatAction
        if usr_info[-1] == "-1":
            reply += "PatAction指令： 无\n"
            reply += f"示例PatAction绑定： {BOT_GC_INVOKER} bind pat mb50\n"
        else:
            pat_action = usr_info[-1]
            reply += f"PatAction指令： {pat_action}"

        if unbound_cnt == len(usr_info) - 1:
            reply = f"您还没有绑定任何ID。\n"
            reply += f"示例: {BOT_GC_INVOKER} bind mai xxxxx"

        return reply

    # Temporarily Block Function Until Restart or Manually Unblocked.
    def function_switch(self, args):
        avail_usr_func = args[-1][0]
        func_data = args[0]

        reply = "[调整情况]\n"
        for module in avail_usr_func:
            for func in avail_usr_func[module]:
                if func in func_data:
                    func_status = avail_usr_func[module][func]
                    new_status = bool((int(func_status) + 1) % 2)
                    avail_usr_func[module][func] = new_status

                    reply += f"- 已调整{func}为：{new_status}\n"
                    func_data.remove(func)
        for unfound_func in func_data:
            reply += f"- 未找到 [{unfound_func}]"

        return mh.compose_txt_msg(reply)

    # Temporarily Block Module Until Restart or Manually Unblocked.
    def module_switch(self, args):
        avail_usr_func = args[-1][0]
        func_data = args[0]

        reply = "[调整情况]\n"
        for module in avail_usr_func:
            if module in func_data:
                for func in avail_usr_func[module]:
                    func_status = avail_usr_func[module][func]
                    new_status = bool((int(func_status) + 1) % 2)
                    avail_usr_func[module][func] = new_status

                    reply += f"- 已调整{func}为：{new_status}\n"
                func_data.remove(module)
        for unfound_mod in func_data:
            reply += f"- 未找到 [{unfound_mod}]"

        return mh.compose_txt_msg(reply)

    # Mark a function as problematic.
    def report_error(self, args):
        marked_usr_func = args[-1][5]
        func_data = args[0]
        usr_id = args[1]

        if len(func_data) < 1:
            reply = "请提供您需要标记错误的功能。"
        elif len(func_data) > 1:
            reply = "您一次只能标记一个功能。"
        else:
            func_keyword = func_data[0]
            found = False
            for module in marked_usr_func:
                for keyword in marked_usr_func[module]:
                    if keyword == func_keyword:
                        found = True
                        marked_usr_func[module][keyword] = True
            if not found:
                reply = f"未找到功能 {func_keyword}"
            else:
                reply = "已标记。"

        return mh.compose_txt_msg(reply)
    
    # Unmark a function.
    def unmark(self, args):
        marked_usr_func = args[-1][5]
        func_data = args[0]
        usr_id = args[1]

        if len(func_data) < 1:
            reply = "请提供需要清除标记的功能。"
        elif len(func_data) > 1:
            reply = "您一次只能清除一个功能的标记。"
        else:
            func_keyword = func_data[0]
            found = False
            for module in marked_usr_func:
                for keyword in marked_usr_func[module]:
                    if keyword == func_keyword:
                        found = True
                        marked_usr_func[module][keyword] = False
            if not found:
                reply = f"未找到功能 {func_keyword}"
            else:
                reply = "已清除标记。"

        return mh.compose_txt_msg(reply)
    
    # Provide a module health overview. 
    def module_status(self, args):
        avail_usr_func = args[-1][0]
        marked_usr_func = args[-1][5]

        reply = "[模块运作情况]\n"

        for module in avail_usr_func:
            mod_func = avail_usr_func[module]
            mod_func_cnt = len(avail_usr_func[module])
            func_disabled_cnt = 0
            func_marked_cnt = 0

            for func in mod_func:
                if avail_usr_func[module][func] == False:
                    func_disabled_cnt += 1
                if marked_usr_func[module][func] == True:
                    func_marked_cnt += 1

            disabled_per = (func_disabled_cnt / mod_func_cnt * 100)
            disabled_per_20 = round(disabled_per / 20.0) 
            marked = " [Marked]" if func_marked_cnt > 1 else "" 

            reply += f"[{module}]{marked}"
            reply += f" {mod_func_cnt}T | {func_disabled_cnt}D | {func_marked_cnt}M\n"
            reply += "- [ "
            for _ in range(5 - disabled_per_20):
                reply += "#"
            for _ in range(disabled_per_20):
                reply += "-"
            reply += f" ]  {round(100-disabled_per)}%\n"

        return mh.compose_txt_msg(reply)

    # Retrieves patTimes data for user
    def patstat(self, args):
        wb_db = args[-1][2]
        usr_id = args[1]

        pat_times = wb_db.fetch("Users", ["patTimes"], "wxid", usr_id)[0][0]

        if pat_times > 109:
            reply = f"你总共拍了WB{pat_times}次。\n0MG"
        else:
            reaction = {
                0: '(*´-`)',
                1: "(( _ _ ))..zzzZZ",
                2: "٩( 'ω' )و",
                3: "٩( ᐛ )و",
                4: "(*^ω^*)",
                5: "（╹◡╹）♡",
                6: "♪(*^^)o∀*∀o(^^*)♪",
                7: "（＾Ｏ＾☆♪",
                8: "☆彡",
                9: "(=´∀｀)人(´∀｀=)",
                10: "♪───Ｏ（≧∇≦）Ｏ────♪"
            }

            react = reaction[pat_times // 10]
            reply = f"你总共拍了WB{pat_times}次{react}"

        return mh.compose_txt_msg(reply)

    # Push a message to groups with annouce on. 
    def announce(self, args):
        wb_db = args[-1][2]
        msgr = args[-1][6]
        func_data = args[0]

        groups = wb_db.fetch("Groupchats", ["*"], "announce", 1)
        if len(groups) == 0:
            reply = "目前没有群聊开启公告推送"
        else:
            content = "[推送公告]\n"
            content += " ".join(func_data)

            reply = f"内容:{content}\n已向以下群聊推送公告:\n"

            for g in groups:
                msgr.send_txt_msg(content, f"{g[0]}@chatroom")
                reply += f"{g[1]}({g[0]})\n"

        return mh.compose_txt_msg(reply)
    
    # Toggle the announce status for groupchats.
    def announce_switch(self, args):
        wb_db = args[-1][2]
        func_data = args[0]

        if len(func_data) == 0:
            reply = "请提供群组ID。"
        elif not func_data[0].isnumeric():
            reply = "请提供纯数字的群组ID。"
        else:
            reply = ""
            for room_num in func_data:
                announce_status = wb_db.fetch("Groupchats", ["announce"],\
                                              "roomid", room_num)
                if len(announce_status) == 0:
                    reply += f"群组ID{room_num}不存在\n"
                    continue

                new_status = (announce_status[0][0] + 1) % 2
                wb_db.update("Groupchats", "announce", new_status,\
                             "roomid", room_num)
                reply += f'群组{room_num} 公告:{bool(new_status)}\n'
        
        return mh.compose_txt_msg(reply)

    # View the announce status of groupchats.
    def announce_list(self, args):
        wb_db = args[-1][2]
        func_data = args[0]

        reply = "群组公告推送情况:\n"
        announce_status = wb_db.fetch("Groupchats",["*"], 1, 1)
        for group in announce_status:
            reply += f"{group[1]} ( {group[0]} ): {bool(group[2])}\n"

        return mh.compose_txt_msg(reply)

    # View the most called Function
    def func_called_rank(self, args):
        func_called_times = args[-1][7]
        end_valve = 0

        current_date = time.strftime("%Y-%m-%d")
        reply = f"从开机至现在({current_date})指令调用数量:"
        for keyword in sorted(func_called_times,\
                              key = func_called_times.get,\
                              reverse = True):
            called_cnt = func_called_times[keyword]
            if called_cnt <= end_valve:
                break
            else:
                reply += f"\n{keyword} - {called_cnt}次"

        return mh.compose_txt_msg(reply)

    # Feedback an Message to Sudoer
    def feedback(self, args):
        func_data = args[0]
        wb_db = args[-1][2]
        msgr = args[-1][6]
        sudo_list = args[-1][8]

        usr_id = args[1]
        from_id = args[2]

        # User did not provide message 
        if len(func_data) == 0:
            reply = "请提供反馈内容。"
        # User provided message 
        else:
            reply = "发送完成"
            msg = " ".join(func_data)
            recipient = sudo_list[0]

            # Group Chat
            if usr_id != from_id:
                room_num = from_id.replace("@chatroom", "")
                room_name = wb_db.fetch("Groupchats", ["groupname"],\
                                        "roomid", room_num)[0][0]
                usr_nick = wb_db.fetch(f"r{room_num}", ["groupUsrName"],\
                                        "wxid", usr_id)[0][0]
                feedback = f"来自{room_name}-{usr_nick}({usr_id})的反馈:\n"
            # DM
            else:
                usr_nick = wb_db.fetch("Users", ["realUsrName"],\
                                       "wxid", usr_id)[0][0]
                feedback = f"来自{usr_nick}({usr_id})的DM反馈:\n"

            feedback += msg
            msgr.send_txt_msg(feedback, recipient)

        return mh.compose_txt_msg(reply)

    # Manually Refresh the Windbot DB.
    def refresh(self, args):
        reply = "已刷新。"
        msgr = args[-1][6]

        msgr.get_wxuser_list()

        return mh.compose_txt_msg(reply)
