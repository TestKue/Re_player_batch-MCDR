from mcdreforged.api.all import *
import os
import json

DEFAULT_CONFIG = {
    'base_name': 'bot_',
    'permission': 0
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
                    Literal('li').then(
                        QuotableText('name').then(
                            Integer('start').then(
                                Integer('end').then(
                                    QuotableText('direction').then(
                                        Integer('interval').then(
                                            GreedyText('action_args').runs(self.process_line_command)
                                        )
                                    )
                                )
                            )
                        )
                    )
                ).then(
                    Literal('re').then(
                        QuotableText('name').then(
                            Integer('start').then(
                                Integer('end').then(
                                    QuotableText('direction1').then(
                                        QuotableText('direction2').then(
                                            Integer('interval').then(
                                                GreedyText('action_args').runs(self.process_square_command)
                                            )
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
            '§7!!plb li <名称> <起始> <结束> <方向> <间隔> <动作> §e- 沿指定方向生成直线排列假人',
            '§e方向参数: §a+x, -x, +z, -z',
            '§6方形阵列:',
            '§7!!plb re <名称> <起始> <结束> <方向1> <方向2> <间隔> <动作> §e- 生成二维排列假人',
            '§e示例:',
            '§7!!plb li bot 1 5 +x 1 spawn §e- 生成bot1到bot5，每个向东间隔3格',
            '§7!!plb re bot 1 4 +x +z 1 spawn §e- 生成bot1到bot4，在X/Z平面形成5格间距方阵',
        ]
        src.reply('\n'.join(help_msg))

    def process_command(self, src: CommandSource, ctx: dict):
        try:
            name = ctx['name']
            start = ctx['start']
            end = ctx['end']
            action_args = ctx['action_args']
            base = self.config['base_name']
            
            if start > end:
                return src.reply('§c错误：起始值不能大于结束值')

            for i in range(start, end + 1):
                bot_name = f'{base}{name}{i}'
                if src.is_player:
                    player_name = src.player
                    cmd = f'/execute as {player_name} at @s run player {bot_name} {action_args}'
                else:
                    cmd = f'/player {bot_name} {action_args}'
                self.server.execute(cmd)
                
            src.reply(f'§a已操作假人 {base}{name}[{start}-{end}] 的 {action_args} 指令')

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
            end = ctx['end']
            direction = ctx['direction']
            interval = ctx['interval']
            action_args = ctx['action_args']
            base = self.config['base_name']
            
            if start > end:
                return src.reply('§c错误：起始值不能大于结束值')

            axis, sign = self.parse_direction(direction)
            if axis is None:
                return src.reply(f'§c错误的方向参数：{direction}')

            for i in range(start, end + 1):
                bot_name = f'{base}{name}{i}'
                offset = (i - start) * interval * sign
                if axis == 'x':
                    coord = f'~{offset} ~ ~'
                else:
                    coord = f'~ ~ ~{offset}'
                
                full_action = f'{action_args} at {coord}' if 'at' not in action_args else action_args
                if src.is_player:
                    player_name = src.player
                    cmd = f'/execute as {player_name} at @s run player {bot_name} {full_action}'
                else:
                    cmd = f'/player {bot_name} {full_action}'
                self.server.execute(cmd)

            src.reply(f'§a成功生成直线假人 {base}{name}[{start}-{end}]，方向 {direction} 间隔 {interval}')

        except Exception as e:
            self.server.logger.error(f'§c直线生成出错: {str(e)}')
            src.reply('§c直线生成失败，请查看日志')

    def process_square_command(self, src: CommandSource, ctx: dict):
        try:
            name = ctx['name']
            start = ctx['start']
            end = ctx['end']
            dir1 = ctx['direction1']
            dir2 = ctx['direction2']
            interval = ctx['interval']
            action_args = ctx['action_args']
            base = self.config['base_name']
            
            if start > end:
                return src.reply('§c错误：起始值不能大于结束值')

            axis1, sign1 = self.parse_direction(dir1)
            axis2, sign2 = self.parse_direction(dir2)
            if None in [axis1, axis2]:
                return src.reply(f'§c错误的方向参数：{dir1} 或 {dir2}')

            total = end - start + 1
            side_length = int(total ** 0.5)
            if side_length ** 2 != total:
                src.reply('§e警告：假人数量不是完全平方数')
                side_length += 1

            for idx in range(total):
                i = start + idx
                bot_name = f'{base}{name}{i}'
                
                x_offset = 0
                z_offset = 0
                row = idx // side_length 
                col = idx % side_length

                if axis1 == 'x':
                    x_offset += row * interval * sign1
                elif axis1 == 'z':
                    z_offset += row * interval * sign1

                if axis2 == 'x':
                    x_offset += col * interval * sign2
                elif axis2 == 'z':
                    z_offset += col * interval * sign2

                coord = f'~{x_offset} ~ ~{z_offset}'
                full_action = f'{action_args} at {coord}' if 'at' not in action_args else action_args
                
                if src.is_player:
                    player_name = src.player
                    cmd = f'/execute as {player_name} at @s run player {bot_name} {full_action}'
                else:
                    cmd = f'/player {bot_name} {full_action}'
                self.server.execute(cmd)

            src.reply(f'§a成功生成方阵假人 {base}{name}[{start}-{end}]，方向 {dir1}×{dir2} 间隔 {interval}')

        except Exception as e:
            self.server.logger.error(f'§c方阵生成出错: {str(e)}')
            src.reply('§c方阵生成失败，请查看日志')

def on_load(server: PluginServerInterface, old):
    PlayerBatch(server).on_load()