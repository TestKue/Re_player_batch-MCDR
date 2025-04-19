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
                .then(
                    QuotableText('name').then(
                        Integer('start').then(
                            Integer('end').then(
                                GreedyText('action_args').runs(self.process_command)
                            )
                        )
                    )
                )
        
        for cmd in ['!!playerbatch', '!!plb']:
            self.server.register_help_message(
                cmd,
                f"§6批量操作假人 §7格式：{cmd} <名称> <起始> <结束> <动作> §e示例：{cmd} test 1 3 spawn"
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

def on_load(server: PluginServerInterface, old):
    PlayerBatch(server).on_load()