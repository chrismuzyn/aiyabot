import discord
from discord import option
from discord.ext import commands
from typing import Optional

from core import settings


class SettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # pulls from model_names list and makes some sort of dynamic list to bypass Discord 25 choices limit
    # these are used also by stablecog /draw command
    # this also updates list when using /settings "refresh" option
    def model_autocomplete(self: discord.AutocompleteContext):
        return [
            model for model in settings.global_var.model_info
        ]

    # do for any other lists that may exceed 25 values
    def sampler_autocomplete(self: discord.AutocompleteContext):
        return [
            sampler for sampler in settings.global_var.sampler_names
        ]

    def style_autocomplete(self: discord.AutocompleteContext):
        return [
            style for style in settings.global_var.style_names
        ]

    def hyper_autocomplete(self: discord.AutocompleteContext):
        return [
            hyper for hyper in settings.global_var.hyper_names
        ]

    def lora_autocomplete(self: discord.AutocompleteContext):
        return [
            lora for lora in settings.global_var.lora_names
        ]

    def extra_net_autocomplete(self: discord.AutocompleteContext):
        return [
            network for network in settings.global_var.extra_nets
        ]

    def upscaler_autocomplete(self: discord.AutocompleteContext):
        return [
            upscaler for upscaler in settings.global_var.upscaler_names
        ]

    def hires_autocomplete(self: discord.AutocompleteContext):
        return [
            hires for hires in settings.global_var.hires_upscaler_names
        ]

    def video_engine_autocomplete(self: discord.AutocompleteContext):
        return [
            engine for engine in settings.global_var.video_engines
        ]

    def video_model_autocomplete(self: discord.AutocompleteContext):
        # filter by engine if the user has typed one, otherwise return all
        engines = settings.global_var.video_engines
        models = settings.global_var.video_models
        return [
            vm['name'] for vm in models
        ]

    @commands.slash_command(name='settings', description='Review and change channel defaults', guild_only=True)
    @option(
        'current_settings',
        bool,
        description='Show the current defaults for the channel.',
        required=False,
    )
    @option(
        'n_prompt',
        str,
        description='Set default negative prompt for the channel (put "reset" to return to empty prompt)',
        required=False,
    )
    @option(
        'data_model',
        str,
        description='Set default data model for image generation',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(model_autocomplete),
    )
    @option(
        'steps',
        int,
        description='Set default amount of steps for the channel',
        min_value=1,
        required=False,
    )
    @option(
        'max_steps',
        int,
        description='Set maximum steps for the channel',
        min_value=1,
        required=False,
    )
    @option(
        'width',
        int,
        description='Set default width for the channel',
        required=False,
    )
    @option(
        'height',
        int,
        description='Set default height for the channel',
        required=False,
    )
    @option(
        'guidance_scale',
        str,
        description='Set default Classifier-Free Guidance scale for the channel.',
        required=False,
    )
    @option(
        'sampler',
        str,
        description='Set default sampler for the channel',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(sampler_autocomplete),
    )
    @option(
        'styles',
        str,
        description='Apply a predefined style to the generation.',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(style_autocomplete),
    )
    @option(
        'hypernet',
        str,
        description='Set default hypernetwork model for the channel',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(hyper_autocomplete),
    )
    @option(
        'lora',
        str,
        description='Set default LoRA for the channel',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(lora_autocomplete),
    )
    @option(
        'facefix',
        str,
        description='Tries to improve faces in images.',
        required=False,
        choices=settings.global_var.facefix_models,
    )
    @option(
        'full_quality_vae',
        bool,
        description='(SD.Next) Use full quality VAE to decode samples',
        required=False,
    )
    @option(
        'highres_fix',
        str,
        description='Set default highres fix model for the channel',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(hires_autocomplete),
    )
    @option(
        'clip_skip',
        int,
        description='Set default CLIP skip for the channel',
        required=False,
        choices=[x for x in range(1, 13, 1)]
    )
    @option(
        'strength',
        str,
        description='Set default strength (for init_img) for the channel (0.0 to 1.0).'
    )
    @option(
        'batch',
        str,
        description='Set default batch for the channel (count,size)',
        required=False,
    )
    @option(
        'max_batch',
        str,
        description='Set maximum batch for the channel (count,size)',
        required=False,
    )
    @option(
        'upscaler_1',
        str,
        description='Set default upscaler model for the channel.',
        required=True,
        autocomplete=discord.utils.basic_autocomplete(upscaler_autocomplete),
    )
    @option(
        'refresh',
        bool,
        description='Use to update global lists (models, styles, embeddings, etc.)',
        required=False,
    )
    @option(
        'spoiler',
        bool,
        description='Mark images as spoilers (when not specified in /draw)',
        required=False,
    )
    @option(
        'spoiler_role',
        discord.Role,
        description='Force images from users in this role as spoilers',
        required=False,
    )
    @option(
        'remove_spoiler_role',
        bool,
        description='Remove assigned spoiler role',
        required=False,
    )
    @option(
        'live_preview',
        bool,
        description='Enable/Disable live previews in this channel',
        required=False,
    )
    @option(
        'video_engine',
        str,
        description='Set default video engine for the channel',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(video_engine_autocomplete),
    )
    @option(
        'video_model',
        str,
        description='Set default video model for the channel',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(video_model_autocomplete),
    )
    @option(
        'video_negative_prompt',
        str,
        description='Set default negative prompt for video generation',
        required=False,
    )
    @option(
        'video_width',
        int,
        description='Set default video width for the channel',
        required=False,
    )
    @option(
        'video_height',
        int,
        description='Set default video height for the channel',
        required=False,
    )
    @option(
        'video_frames',
        int,
        description='Set default number of video frames for the channel',
        required=False,
    )
    @option(
        'video_steps',
        int,
        description='Set default video steps for the channel',
        min_value=1,
        required=False,
    )
    @option(
        'video_fps',
        int,
        description='Set default video FPS for the channel (1-60)',
        min_value=1,
        max_value=60,
        required=False,
    )
    @option(
        'video_audio',
        bool,
        description='Set default audio generation for video (True/False)',
        required=False,
    )
    @option(
        'video_guidance_scale',
        str,
        description='Set default video guidance scale (-1 for model default)',
        required=False,
    )
    @option(
        'video_sampler',
        str,
        description='Set default video sampler for the channel',
        required=False,
    )
    @option(
        'video_init_strength',
        str,
        description='Set default init strength for video img2vid (0.0 to 1.0)',
        required=False,
    )
    @option(
        'max_video_frames',
        int,
        description='Set maximum video frames for the channel',
        min_value=1,
        required=False,
    )
    @option(
        'max_video_steps',
        int,
        description='Set maximum video steps for the channel',
        min_value=1,
        required=False,
    )
    @option(
        'max_video_size',
        int,
        description='Set maximum video width/height for the channel',
        required=False,
    )
    @option(
        'video_spoiler',
        bool,
        description='Mark videos as spoilers (when not specified in /video)',
        required=False,
    )
    async def settings_handler(self, ctx,
                               current_settings: Optional[bool] = True,
                               n_prompt: Optional[str] = None,
                               data_model: Optional[str] = None,
                               steps: Optional[int] = None,
                               max_steps: Optional[int] = 1,
                               width: Optional[int] = None, height: Optional[int] = None,
                               guidance_scale: Optional[str] = None,
                               sampler: Optional[str] = None,
                               styles: Optional[str] = None,
                               hypernet: Optional[str] = None,
                               lora: Optional[str] = None,
                               facefix: Optional[str] = None,
                               full_quality_vae: Optional[bool] = None,
                               highres_fix: Optional[str] = None,
                               clip_skip: Optional[int] = None,
                               strength: Optional[str] = None,
                               batch: Optional[str] = None,
                               max_batch: Optional[str] = None,
                               upscaler_1: Optional[str] = None,
                               refresh: Optional[bool] = False,
                               spoiler: Optional[bool] = None,
                               spoiler_role: Optional[discord.Role] = None,
                               remove_spoiler_role: Optional[bool] = None,
                               live_preview: Optional[bool] = None,
                               video_engine: Optional[str] = None,
                               video_model: Optional[str] = None,
                               video_negative_prompt: Optional[str] = None,
                               video_width: Optional[int] = None,
                               video_height: Optional[int] = None,
                               video_frames: Optional[int] = None,
                               video_steps: Optional[int] = None,
                               video_fps: Optional[int] = None,
                               video_audio: Optional[bool] = None,
                               video_guidance_scale: Optional[str] = None,
                               video_sampler: Optional[str] = None,
                               video_init_strength: Optional[str] = None,
                               max_video_frames: Optional[int] = None,
                               max_video_steps: Optional[int] = None,
                               max_video_size: Optional[int] = None,
                               video_spoiler: Optional[bool] = None
                               ):
        # get the channel id and check if a settings file exists
        channel = '% s' % ctx.channel.id
        settings.check(channel)
        reviewer = settings.read(channel)
        # create the embed for the reply
        embed = discord.Embed(title="Channel Defaults Summary", description="")
        embed.set_footer(text=f'Channel id: {channel}')
        embed.colour = settings.global_var.embed_color
        current, new, new_n_prompt, new_vn_prompt = '', '', '', ''
        dummy_prompt, lora_multi, hyper_multi = '', 0.85, 0.85
        set_new = False

        if current_settings:
            cur_set = settings.read(channel)
            for key, value in cur_set.items():
                if key == 'negative_prompt' or key == 'video_negative_prompt':
                    pass
                elif key == 'spoiler_role' and value is not None:
                    current += f'\n{key} - <@&{value}>'
                else:
                    if value == '':
                        value = ' '
                    current += f'\n{key} - ``{value}``'
            embed.add_field(name=f'Current parameters', value=current, inline=True)
            # put negative prompt on new field for hosts who like massive negative prompts
            cur_n_prompt = f'{cur_set["negative_prompt"]}'
            if cur_n_prompt == '':
                cur_n_prompt = ' '
            elif len(cur_n_prompt) > 1024:
                cur_n_prompt = f'{cur_n_prompt[:1010]}....'
            embed.add_field(name=f'Current negative prompt', value=f'``{cur_n_prompt}``', inline=True)
            # put video negative prompt on new field as well
            cur_vn_prompt = f'{cur_set["video_negative_prompt"]}'
            if cur_vn_prompt == '':
                cur_vn_prompt = ' '
            elif len(cur_vn_prompt) > 1024:
                cur_vn_prompt = f'{cur_vn_prompt[:1010]}....'
            embed.add_field(name=f'Current video negative prompt', value=f'``{cur_vn_prompt}``', inline=True)

        # run function to update global variables
        if refresh:
            settings.global_var.model_info.clear()
            settings.global_var.sampler_names.clear()
            settings.global_var.facefix_models.clear()
            settings.global_var.style_names.clear()
            settings.global_var.embeddings_1.clear()
            settings.global_var.embeddings_2.clear()
            settings.global_var.hyper_names.clear()
            settings.global_var.lora_names.clear()
            settings.global_var.upscaler_names.clear()
            settings.global_var.video_models.clear()
            settings.global_var.video_engines.clear()
            settings.populate_global_vars()
            embed.add_field(name=f'Refreshed!', value=f'Updated global lists', inline=False)

        # run through each command and update the defaults user selects
        if n_prompt is not None:
            new_n_prompt = f'{n_prompt}'
            if n_prompt == 'reset':
                n_prompt = ''
                new_n_prompt = ' '
            elif len(new_n_prompt) > 1024:
                new_n_prompt = f'{new_n_prompt[:1010]}....'
            settings.update(channel, 'negative_prompt', n_prompt)

        if data_model is not None:
            settings.update(channel, 'data_model', data_model)
            new += f'\nData model: ``"{data_model}"``'
            set_new = True

        if max_steps != 1:
            settings.update(channel, 'max_steps', max_steps)
            new += f'\nMax steps: ``{max_steps}``'
            # automatically lower default steps if max steps goes below it
            if max_steps < reviewer['steps']:
                settings.update(channel, 'steps', max_steps)
                new += f'\nDefault steps is too high! Lowering to ``{max_steps}``.'
            set_new = True

        if width is not None:
            width = settings.dimensions_validator(width)
            settings.update(channel, 'width', width)
            new += f'\nWidth: ``"{width}"``'
            set_new = True

        if height is not None:
            height = settings.dimensions_validator(height)
            settings.update(channel, 'height', height)
            new += f'\nHeight: ``"{height}"``'
            set_new = True

        if full_quality_vae is not None:
            settings.update(channel, 'full_quality_vae', full_quality_vae)
            new += f'\nFull Quality VAE: ``"{full_quality_vae}"``'
            set_new = True

        if guidance_scale is not None:
            try:
                float(guidance_scale)
                settings.update(channel, 'guidance_scale', guidance_scale)
                new += f'\nGuidance Scale: ``{guidance_scale}``'
            except(Exception,):
                settings.update(channel, 'guidance_scale', '7.0')
                new += f'\nHad trouble setting Guidance Scale! Setting to default of `7.0`.'
            set_new = True

        if sampler is not None:
            settings.update(channel, 'sampler', sampler)
            new += f'\nSampler: ``"{sampler}"``'
            set_new = True

        if styles is not None:
            settings.update(channel, 'style', styles)
            new += f'\nStyle: ``"{styles}"``'
            set_new = True

        if facefix is not None:
            settings.update(channel, 'facefix', facefix)
            new += f'\nFacefix: ``"{facefix}"``'
            set_new = True

        if highres_fix is not None:
            settings.update(channel, 'highres_fix', highres_fix)
            new += f'\nhighres_fix: ``"{highres_fix}"``'
            set_new = True

        if clip_skip is not None:
            settings.update(channel, 'clip_skip', clip_skip)
            new += f'\nCLIP skip: ``{clip_skip}``'
            set_new = True

        if hypernet is not None:
            message = ''
            if ':' in hypernet:
                dummy_prompt, hypernet, hyper_multi = settings.extra_net_check(dummy_prompt, hypernet, hyper_multi)
                settings.update(channel, 'hypernet_multi', hyper_multi)
                message = f' (multiplier: ``{hyper_multi}``)'
            settings.update(channel, 'hypernet', hypernet)
            new += f'\nHypernet: ``"{hypernet}"``{message}'
            set_new = True

        if lora is not None:
            message = ''
            if ':' in lora:
                dummy_prompt, lora, lora_multi = settings.extra_net_check(dummy_prompt, lora, lora_multi)
                settings.update(channel, 'lora_multi', lora_multi)
                message = f' (multiplier: ``{lora_multi}``)'
            settings.update(channel, 'lora', lora)
            new += f'\nLoRA: ``"{lora}"``{message}'
            set_new = True

        if strength is not None:
            settings.update(channel, 'strength', strength)
            new += f'\nStrength: ``"{strength}"``'
            set_new = True

        if upscaler_1 is not None:
            settings.update(channel, 'upscaler_1', upscaler_1)
            new += f'\nUpscaler 1: ``"{upscaler_1}"``'
            set_new = True

        if max_batch is not None:
            batch_check = settings.batch_format(reviewer['batch'])
            max_batch = settings.batch_format(max_batch)

            settings.update(channel, 'max_batch', f'{max_batch[0]},{max_batch[1]}')
            new += f'\nMax batch (count,size): ``{max_batch[0]},{max_batch[1]}``'
            # automatically lower default batch if max batch goes below it
            if max_batch[0] < batch_check[0]:
                settings.update(channel, 'batch', f'{max_batch[0]},{batch_check[1]}')
                new += f'\nDefault batch count is too high! Lowering to ``{max_batch[0]}``.'
            if max_batch[1] < batch_check[1]:
                if max_batch[0] < batch_check[0]:
                    settings.update(channel, 'batch', f'{max_batch[0]},{max_batch[1]}')
                else:
                    settings.update(channel, 'batch', f'{batch_check[0]},{max_batch[1]}')
                new += f'\nDefault batch size is too high! Lowering to ``{max_batch[1]}``.'
            set_new = True

        # review settings again in case user is trying to set steps/counts and max steps/counts simultaneously
        reviewer = settings.read(channel)
        if steps is not None:
            if steps > reviewer['max_steps']:
                new += f"\nMax steps is ``{reviewer['max_steps']}``! You can't go beyond it!"
            else:
                settings.update(channel, 'steps', steps)
                new += f'\nSteps: ``{steps}``'
            set_new = True

        if batch is not None:
            batch = settings.batch_format(batch)
            max_batch_check = settings.batch_format(reviewer['max_batch'])

            if batch[0] > max_batch_check[0]:
                new += f"\nMax batch count is ``{max_batch_check[0]}``! You can't go beyond it!"
            elif batch[1] > max_batch_check[1]:
                new += f"\nMax batch size is ``{max_batch_check[1]}``! You can't go beyond it!"
            else:
                settings.update(channel, 'batch', f'{batch[0]},{batch[1]}')
                new += f'\nbatch (count,size): ``{batch[0]},{batch[1]}``'
            set_new = True

        # validate video steps against max video steps (reviewer already re-read above)
        if video_steps is not None:
            if video_steps > reviewer['max_video_steps']:
                new += f"\nMax video steps is ``{reviewer['max_video_steps']}``! You can't go beyond it!"
            else:
                settings.update(channel, 'video_steps', video_steps)
                new += f'\nVideo Steps: ``{video_steps}``'
            set_new = True

        # validate video frames against max video frames
        if video_frames is not None:
            if video_frames > reviewer['max_video_frames']:
                new += f"\nMax video frames is ``{reviewer['max_video_frames']}``! You can't go beyond it!"
            else:
                settings.update(channel, 'video_frames', video_frames)
                new += f'\nVideo Frames: ``{video_frames}``'
            set_new = True

        # validate video dimensions against max video size
        if video_width is not None:
            if video_width > reviewer['max_video_size']:
                new += f"\nMax video size is ``{reviewer['max_video_size']}``! Width can't go beyond it!"
                video_width = reviewer['max_video_size']
            settings.update(channel, 'video_width', video_width)
            new += f'\nVideo Width: ``"{video_width}"``'
            set_new = True
        if video_height is not None:
            if video_height > reviewer['max_video_size']:
                new += f"\nMax video size is ``{reviewer['max_video_size']}``! Height can't go beyond it!"
                video_height = reviewer['max_video_size']
            settings.update(channel, 'video_height', video_height)
            new += f'\nVideo Height: ``"{video_height}"``'
            set_new = True

        if spoiler is not None:
            settings.update(channel, 'spoiler', spoiler)
            new += f'\nDefault Spoiler: ``{spoiler}``'
            set_new = True
        if remove_spoiler_role is not None and remove_spoiler_role:
            settings.update(channel, 'spoiler_role', None)
            new += '\nRemoved Spoiler Role'
            set_new = True
        elif spoiler_role is not None:
            settings.update(channel, 'spoiler_role', str(spoiler_role.id))
            new += f'\n Spoiler Role: <@&{spoiler_role.id}>'
            set_new = True

        if live_preview is not None:
            settings.update(channel, 'live_preview', live_preview)
            new += f'\nLive Preview: ``{live_preview}``'
            set_new = True

        if video_engine is not None:
            settings.update(channel, 'video_engine', video_engine)
            new += f'\nVideo Engine: ``"{video_engine}"``'
            set_new = True

        if video_model is not None:
            settings.update(channel, 'video_model', video_model)
            new += f'\nVideo Model: ``"{video_model}"``'
            set_new = True

        if video_negative_prompt is not None:
            new_vn_prompt = f'{video_negative_prompt}'
            if video_negative_prompt == 'reset':
                video_negative_prompt = ''
                new_vn_prompt = ' '
            elif len(new_vn_prompt) > 1024:
                new_vn_prompt = f'{new_vn_prompt[:1010]}....'
            settings.update(channel, 'video_negative_prompt', video_negative_prompt)

        if video_fps is not None:
            settings.update(channel, 'video_fps', video_fps)
            new += f'\nVideo FPS: ``{video_fps}``'
            set_new = True

        if video_audio is not None:
            settings.update(channel, 'video_audio', video_audio)
            new += f'\nVideo Audio: ``{video_audio}``'
            set_new = True

        if video_guidance_scale is not None:
            try:
                float(video_guidance_scale.replace(",", "."))
                settings.update(channel, 'video_guidance_scale', video_guidance_scale)
                new += f'\nVideo Guidance Scale: ``{video_guidance_scale}``'
            except(Exception,):
                settings.update(channel, 'video_guidance_scale', '-1.0')
                new += f'\nHad trouble setting Video Guidance Scale! Setting to default of `-1.0`.'
            set_new = True

        if video_sampler is not None:
            settings.update(channel, 'video_sampler', video_sampler)
            new += f'\nVideo Sampler: ``"{video_sampler}"``'
            set_new = True

        if video_init_strength is not None:
            try:
                float(video_init_strength.replace(",", "."))
                settings.update(channel, 'video_init_strength', video_init_strength)
                new += f'\nVideo Init Strength: ``"{video_init_strength}"``'
            except(Exception,):
                settings.update(channel, 'video_init_strength', '0.8')
                new += f'\nHad trouble setting Video Init Strength! Setting to default of `0.8`.'
            set_new = True

        if max_video_frames is not None:
            settings.update(channel, 'max_video_frames', max_video_frames)
            new += f'\nMax Video Frames: ``{max_video_frames}``'
            if reviewer['video_frames'] > max_video_frames:
                settings.update(channel, 'video_frames', max_video_frames)
                new += f'\nDefault video frames is too high! Lowering to ``{max_video_frames}``.'
            set_new = True

        if max_video_steps is not None:
            settings.update(channel, 'max_video_steps', max_video_steps)
            new += f'\nMax Video Steps: ``{max_video_steps}``'
            if reviewer['video_steps'] > max_video_steps:
                settings.update(channel, 'video_steps', max_video_steps)
                new += f'\nDefault video steps is too high! Lowering to ``{max_video_steps}``.'
            set_new = True

        if max_video_size is not None:
            settings.update(channel, 'max_video_size', max_video_size)
            new += f'\nMax Video Size: ``{max_video_size}``'
            set_new = True

        if video_spoiler is not None:
            settings.update(channel, 'video_spoiler', video_spoiler)
            new += f'\nVideo Spoiler: ``{video_spoiler}``'
            set_new = True

        if set_new:
            embed.add_field(name=f'New defaults', value=new, inline=False)
        if new_n_prompt:
            embed.add_field(name=f'New default negative prompt', value=f'``{new_n_prompt}``', inline=False)
        if new_vn_prompt:
            embed.add_field(name=f'New video negative prompt', value=f'``{new_vn_prompt}``', inline=False)

        await ctx.send_response(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(SettingsCog(bot))
