from mcdreforged.api.all import *
import os
import json
import time
import threading

DEFAULT_CONFIG = {
    'base_name': 'bot_',
    'permission': 0,
    'interval': 1.0  
}

class PlayerBatch:
    def __init__(self, server: PluginServerInterface):
        self.server = server
        self.config = None
        self.config_file = os.path.join(server.get_data_folder(), 'player_batch.json')
        
    def on_load(self):
        self.load_config()
        self.register_commands()
        self.server.logger.info('§a插件初始化完成')
        
    def register_commands(self):
        def create_command(root: str):
            return Literal(root)\
                .requires(lambda src: src.has_permission(self.config['permission']))\
                .runs(self.show_help)\
                .then(
                    QuotableText('name').then(
                        Integer('start').then(
                            Integer('end').then(
                                GreedyText('action_args').runs(self.process_command)
                        )
                    )
                )
                ).then(
                    Literal('l').then(  
                        QuotableText('name').then(
                            Integer('start').then(
                                Integer('length').then(  
                                    QuotableText('direction').then(
                                        Number('interval').runs(self.process_line_command)  
                                )
                            )
                        )
                    )
                )
                ).then(
                    Literal('s').then(  
                        QuotableText('name').then(
                            Integer('start').then(
                                Integer('long').then(  
                                    Integer('width').then(  
                                        QuotableText('direction1').then(
                                            QuotableText('direction2').then(
                                                Number('interval').runs(self.process_square_command)  
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                ).then(
                    Literal('init').then(
                        QuotableText('name').then(
                            Integer('start').then(
                                Integer('length').then(
                                    Number('interval1').then(
                                        Number('interval2').then(
                                            GreedyText('action').runs(self.process_init_command)
                                        )
                                    )
                                )
                            )
                        )
                    )
                )

        for cmd in ['!!playerbatch', '!!plb']:
            self.server.register_help_message(
                cmd,
                "§6批量操作假人 §7输入 §e{} §7查看完整帮助".format(cmd)
            )
            self.server.register_command(create_command(cmd))
            self.server.logger.info(f'§6已注册命令 {cmd}')

    def load_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            if not os.path.exists(self.config_file):
                with open(self.config_file, 'w') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4)
                    
            with open(self.config_file) as f:
                self.config = {**DEFAULT_CONFIG, **json.load(f)}
                if not isinstance(self.config['permission'], int) or self.config['permission'] < 0:
                    self.config['permission'] = 0
                if not isinstance(self.config['interval'], (int, float)) or self.config['interval'] < 0:
                    self.config['interval'] = 1.0
            self.save_config()
        except Exception as e:
            self.server.logger.error(f'§c配置加载失败: {e}')
            self.config = DEFAULT_CONFIG.copy()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def show_help(self, src: CommandSource):
        help_msg = [
            '§6==== PlayerBatch 帮助 ====',
            '§6!!plb §7或 §6!!playerbatch §7- 显示本帮助信息',
            '§6基础命令:',
            '§7!!plb <名称> <起始> <结束> <动作> §e- 批量操作假人',
            '§6直线生成:',
            '§7!!plb l <名称> <起始> <长度> <方向> <间隔> §e- 生成直线排列假人',
            '§e方向参数: §a+x, -x, +z, -z',
            '§6方形阵列:',
            '§7!!plb s <名称> <起始> <长> <宽> <方向1> <方向2> <间隔> §e- 生成二维排列假人',
            '§6初始化序列:',
            '§7!!plb init <名称> <起始> <长度> <间隔1> <间隔2> <动作> §e- 生成假人并依次执行动作和退出，间隔控制',
            '§e示例:',
            '§7!!plb l bot 1 5 +x 1 §e- 生成bot1到bot5，每个向东间隔1格',
            '§7!!plb s bot 1 2 3 +x +z 1 §e- 生成bot1到bot6，在X/Z平面形成2x3方阵',
            '§7!!plb init bot 1 3 1 2 kill §e- 生成bot1-3，每个生成后立即kill，间隔1秒后退出，间隔2秒处理下一个',
            f'§a当前生成间隔: §e{self.config["interval"]}秒'
        ]
        src.reply('\n'.join(help_msg))

    def __execute_commands(self, commands: list, src: CommandSource, reply_msg: str, use_interval: bool):
        def task():
            try:
                for idx, cmd in enumerate(commands):
                    if use_interval and idx > 0 and self.config['interval'] > 0:
                        time.sleep(self.config['interval'])  
                    self.server.execute(cmd)
                src.reply(reply_msg)
            except Exception as e:
                self.server.logger.error(f'§c命令执行出错: {str(e)}')
                src.reply('§c命令执行失败，请查看日志')

        threading.Thread(target=task, daemon=True).start()

    def process_command(self, src: CommandSource, ctx: dict):
        try:
            name = ctx['name']
            start = ctx['start']
            end = ctx['end']
            action_args = ctx['action_args']
            base = self.config['base_name']
            
            if start > end:
                return src.reply('§c错误：起始值不能大于结束值')

            is_spawn = action_args.strip().lower().startswith('spawn')
            use_interval = is_spawn
            interval_info = f'（间隔 {self.config["interval"]}秒）' if is_spawn else ''

            commands = []
            for i in range(start, end + 1):
                bot_name = f'{base}{name}{i}'
                if src.is_player:
                    player_name = src.player
                    cmd = f'/execute as {player_name} at @s run player {bot_name} {action_args}'
                else:
                    cmd = f'/player {bot_name} {action_args}'
                commands.append(cmd)

            self.__execute_commands(
                commands,
                src,
                f'§a已操作假人 {base}{name}[{start}-{end}] 的 {action_args} 指令{interval_info}',
                use_interval
            )

        except Exception as e:
            self.server.logger.error(f'§c执行出错: {str(e)}')
            src.reply('§c命令执行失败，请查看日志')

    def parse_direction(self, direction: str):
        valid = {
            '+x': ('x', 1),
            '-x': ('x', -1),
            '+z': ('z', 1),
            '-z': ('z', -1)
        }
        return valid.get(direction, (None, None))

    def process_line_command(self, src: CommandSource, ctx: dict):
        try:
            name = ctx['name']
            start = ctx['start']
            length = ctx['length']
            direction = ctx['direction']
            interval = ctx['interval'] 
            base = self.config['base_name']
            
            if length < 1:
                return src.reply('§c错误：长度必须≥1')
            end = start + length - 1  

            axis, sign = self.parse_direction(direction)
            if axis is None:
                return src.reply(f'§c错误的方向参数：{direction}')

            commands = []
            for i in range(start, end + 1):
                bot_name = f'{base}{name}{i}'
                offset = (i - start) * interval * sign
                if axis == 'x':
                    coord = f'~{offset} ~ ~'
                else:
                    coord = f'~ ~ ~{offset}'
                
                full_action = 'spawn'
                if src.is_player:
                    player_name = src.player
                    cmd = f'/execute as {player_name} at @s positioned {coord} positioned over world_surface run player {bot_name} {full_action}'
                else:
                    cmd = f'/execute positioned {coord} positioned over world_surface run player {bot_name} {full_action}'
                commands.append(cmd)

            self.__execute_commands(
                commands,
                src,
                f'§a成功生成直线假人 {base}{name}[{start}-{end}]，方向 {direction} 间隔 {interval}格（命令间隔 {self.config["interval"]}秒）',
                True  
            )

        except Exception as e:
            self.server.logger.error(f'§c直线生成出错: {str(e)}')
            src.reply('§c直线生成失败，请查看日志')

    def process_square_command(self, src: CommandSource, ctx: dict):
        try:
            name = ctx['name']
            start = ctx['start']
            long = ctx['long']
            width = ctx['width']
            dir1 = ctx['direction1']
            dir2 = ctx['direction2']
            interval = ctx['interval']  
            base = self.config['base_name']
            
            if long < 1 or width < 1:
                return src.reply('§c错误：长和宽必须≥1')
            total = long * width
            end = start + total - 1  

            axis1, sign1 = self.parse_direction(dir1)
            axis2, sign2 = self.parse_direction(dir2)
            if None in [axis1, axis2]:
                return src.reply(f'§c错误的方向参数：{dir1} 或 {dir2}')

            commands = []
            for idx in range(total):
                i = start + idx
                bot_name = f'{base}{name}{i}'
                
                x_offset = 0.0  
                z_offset = 0.0
                row = idx // width  
                col = idx % width

                if axis1 == 'x':
                    x_offset += row * interval * sign1
                elif axis1 == 'z':
                    z_offset += row * interval * sign1

                if axis2 == 'x':
                    x_offset += col * interval * sign2
                elif axis2 == 'z':
                    z_offset += col * interval * sign2

                coord = f'~{x_offset} ~ ~{z_offset}'
                full_action = 'spawn'
                
                if src.is_player:
                    player_name = src.player
                    cmd = f'/execute as {player_name} at @s positioned {coord} positioned over world_surface run player {bot_name} {full_action}'
                else:
                    cmd = f'/execute positioned {coord} positioned over world_surface run player {bot_name} {full_action}'
                commands.append(cmd)

            self.__execute_commands(
                commands,
                src,
                f'§a成功生成方阵假人 {base}{name}[{start}-{end}]，方向 {dir1}×{dir2} 间隔 {interval}格（命令间隔 {self.config["interval"]}秒）',
                True  
            )

        except Exception as e:
            self.server.logger.error(f'§c方阵生成出错: {str(e)}')
            src.reply('§c方阵生成失败，请查看日志')

    def process_init_command(self, src: CommandSource, ctx: dict):
        try:
            name = ctx['name']
            start = ctx['start']
            length = ctx['length']
            interval1 = ctx['interval1']
            interval2 = ctx['interval2']
            action = ctx['action'].strip()
            base = self.config['base_name']
            
            if length < 1:
                return src.reply('§c错误：长度必须≥1')
            end = start + length - 1

            commands_with_waits = []
            for i in range(start, start + length):
                bot_name = f'{base}{name}{i}'
                if src.is_player:
                    player_name = src.player
                    spawn_cmd = f'/execute as {player_name} at @s run player {bot_name} spawn'
                else:
                    spawn_cmd = f'/player {bot_name} spawn'
                commands_with_waits.append( (spawn_cmd, 0) )
                action_cmd = f'/player {bot_name} {action}'
                commands_with_waits.append( (action_cmd, 0) )
                commands_with_waits.append( (None, interval1) )
                kill_cmd = f'/player {bot_name} kill'
                commands_with_waits.append( (kill_cmd, 0) )
                if i != end:
                    commands_with_waits.append( (None, interval2) )

            def task():
                try:
                    for cmd, wait_time in commands_with_waits:
                        if cmd is not None:
                            self.server.execute(cmd)
                        if wait_time > 0:
                            time.sleep(wait_time)
                    src.reply(f'§a成功处理假人序列 {base}{name}[{start}-{end}]，动作间隔 {interval1}秒，循环间隔 {interval2}秒')
                except Exception as e:
                    self.server.logger.error(f'§c初始化命令执行出错: {str(e)}')
                    src.reply('§c初始化命令执行失败，请查看日志')

            threading.Thread(target=task, daemon=True).start()

        except Exception as e:
            self.server.logger.error(f'§c初始化命令解析出错: {str(e)}')
            src.reply('§c命令格式错误，请检查参数')

def on_load(server: PluginServerInterface, old):
    PlayerBatch(server).on_load()