import base64
import discord
import io
import random
import requests
import time
import traceback
from discord import option
from discord.ext import commands
from typing import Optional

from core import queuehandler
from core import viewhandler
from core import settings
from core import settingscog
from . import constants
from threading import Thread


async def update_video_progress(event_loop, status_message_task, s, queue_object,
                                tries=0, any_job=False, tries_since_no_progress=0):
    """Poll /sdapi/v1/progress and update the status message during video generation."""
    status_message = status_message_task.result()
    user_id, user_name = settings.fuzzy_get_id_name(queue_object.ctx)
    try:
        progress_data = s.get(url=f'{settings.global_var.url}/sdapi/v1/progress').json()
        job_name = progress_data.get('state', {}).get('job', '')

        if job_name != '':
            any_job = True

        if job_name == '':
            if any_job:
                if tries_since_no_progress >= 2:
                    return
            else:
                if tries > 10:
                    return

            time.sleep(settings.global_var.preview_update_interval)
            event_loop.create_task(
                update_video_progress(event_loop, status_message_task, s, queue_object,
                                      tries + 1, any_job, tries_since_no_progress + 1 if any_job else 0))
            return

        view = viewhandler.ProgressView()

        await status_message.edit(
            content=f'**Author**: {user_id} ({user_name})\n'
                    f'**Prompt**: `{queue_object.prompt}`\n**Progress**: {round(progress_data.get("progress", 0) * 100, 2)}% '
                    f'\n{progress_data.get("state", {}).get("sampling_step", 0)}/{queue_object.steps} iterations'
                    f'\n**ETA**: {round(progress_data.get("eta_relative", 0), 2)} seconds',
            view=view)
    except Exception as e:
        print('Something goes wrong in video progress...', str(e))
        if tries_since_no_progress >= 3:
            return
        time.sleep(settings.global_var.preview_update_interval)
        event_loop.create_task(
            update_video_progress(event_loop, status_message_task, s, queue_object,
                                  tries + 1, any_job, tries_since_no_progress + 1))
        return

    time.sleep(settings.global_var.preview_update_interval)
    event_loop.create_task(
        update_video_progress(event_loop, status_message_task, s, queue_object, tries + 1, any_job, 0))


class VideoCog(commands.Cog, name='Video', description='Create videos from text or images using SD.Next video API.'):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(viewhandler.VideoView(self))

    @commands.slash_command(name='video', description='Create a video from text or an image (SD.Next only)', guild_only=True)
    @option('prompt', str, description='A prompt to condition the video model with.', required=True)
    @option('negative_prompt', str, description='Negative prompts to exclude from output.', required=False)
    @option('engine', str, description='Video engine to use.', required=False,
            autocomplete=discord.utils.basic_autocomplete(settingscog.SettingsCog.video_engine_autocomplete))
    @option('model', str, description='Video model to use.', required=False,
            autocomplete=discord.utils.basic_autocomplete(settingscog.SettingsCog.video_model_autocomplete))
    @option('width', int, description='Width of the generated video.', required=False)
    @option('height', int, description='Height of the generated video.', required=False)
    @option('frames', int, description='Number of frames to generate (17n+5 for MiniMax).', required=False)
    @option('steps', int, description='The amount of steps to sample the model.', min_value=1, required=False)
    @option('seed', int, description='The seed to use for reproducibility.', required=False)
    @option('guidance_scale', str, description='Classifier-Free Guidance scale (-1 for model default).', required=False)
    @option('sampler_name', str, description='The sampler to use for generation.', required=False)
    @option('init_image', discord.Attachment, description='The starter image for img2vid.', required=False)
    @option('init_url', str, description='The starter URL image for img2vid. This overrides init_image!', required=False)
    @option('init_strength', str, description='The amount init_image will be altered (0.0 to 1.0).', required=False)
    @option('audio', bool, description='Generate audio for the video.', required=False)
    @option('spoiler', bool, description='Mark generated video as spoiler?', required=False)
    async def video_handler(self, ctx: discord.ApplicationContext, *,
                            prompt: str, negative_prompt: Optional[str] = None,
                            engine: Optional[str] = None,
                            model: Optional[str] = None,
                            width: Optional[int] = None,
                            height: Optional[int] = None,
                            frames: Optional[int] = None,
                            steps: Optional[int] = None,
                            seed: Optional[int] = -1,
                            guidance_scale: Optional[str] = None,
                            sampler_name: Optional[str] = None,
                            init_image: Optional[discord.Attachment] = None,
                            init_url: Optional[str] = None,
                            init_strength: Optional[str] = None,
                            audio: Optional[bool] = None,
                            spoiler: Optional[bool] = None):

        # video generation is only available on SD.Next
        if settings.global_var.backend != constants.BACKEND_SDNEXT:
            await ctx.respond('Video generation is only available on SD.Next backend!', ephemeral=True)
            return

        # update defaults with any new defaults from settingscog
        channel = '% s' % ctx.channel.id
        settings.check(channel)
        channel_settings = settings.read(channel)

        if negative_prompt is None:
            negative_prompt = channel_settings['video_negative_prompt']
        if engine is None:
            engine = channel_settings['video_engine']
        if model is None:
            model = channel_settings['video_model']
        if width is None:
            width = channel_settings['video_width']
        if height is None:
            height = channel_settings['video_height']
        if frames is None:
            frames = channel_settings['video_frames']
        if steps is None:
            steps = channel_settings['video_steps']
        if guidance_scale is None:
            guidance_scale = channel_settings['video_guidance_scale']
        if sampler_name is None:
            sampler_name = channel_settings['video_sampler']
        if init_strength is None:
            init_strength = channel_settings['video_init_strength']
        if audio is None:
            audio = channel_settings['video_audio']
        if spoiler is None:
            spoiler = channel_settings['video_spoiler']

        # mp4_fps and mp4_interpolate are not exposed as slash command options
        mp4_fps = channel_settings['video_fps']
        mp4_interpolate = 0

        # derived spoiler (check spoiler role)
        derived_spoiler = spoiler
        spoiler_role = channel_settings['spoiler_role']
        if not derived_spoiler and spoiler_role is not None:
            for role in ctx.author.roles:
                if str(role.id) == spoiler_role:
                    derived_spoiler = True
                    break

        simple_prompt = prompt

        # run through mod function if any moderation values are set
        if settings.global_var.prompt_ban_list or settings.global_var.prompt_ignore_list or settings.global_var.negative_prompt_prefix:
            mod_results = settings.prompt_mod(simple_prompt, negative_prompt)
            if mod_results[0] == "Stop":
                await ctx.respond(f"I'm not allowed to generate the word {mod_results[1]}!", ephemeral=True)
                return
            if mod_results[0] == "Mod":
                if settings.global_var.display_ignored_words == "False":
                    simple_prompt = mod_results[1]
                prompt = mod_results[1]
                negative_prompt = mod_results[2]

        # validate dimensions against max_video_size
        max_video_size = channel_settings['max_video_size']
        if width > max_video_size:
            width = max_video_size
        if height > max_video_size:
            height = max_video_size

        # validate frames against max_video_frames
        max_video_frames = channel_settings['max_video_frames']
        if frames > max_video_frames:
            frames = max_video_frames

        # validate steps against max_video_steps
        max_video_steps = channel_settings['max_video_steps']
        if steps > max_video_steps:
            steps = max_video_steps

        # validate guidance_scale
        try:
            guidance_scale = guidance_scale.replace(",", ".")
            float(guidance_scale)
        except(Exception,):
            guidance_scale = '-1.0'

        # validate init_strength if init_image is provided
        if init_image or init_url:
            try:
                init_strength = init_strength.replace(",", ".")
                float(init_strength)
            except(Exception,):
                init_strength = '0.8'

        # handle seed
        if seed == -1:
            seed = random.randint(0, 0xFFFFFFFF)

        # url overrides init_image
        if init_url:
            try:
                init_image = requests.get(init_url)
            except(Exception,):
                await ctx.send_response('URL image not found!\nI will do my best without it!')

        print(f'Video Request -- {ctx.author.name}#{ctx.author.discriminator}'
              f' -- Prompt: {prompt} -- Engine: {engine} -- Model: {model}')

        # format initial reply
        reply_adds = f' - Size: ``{width}``x``{height}``'
        reply_adds += f' - Frames: ``{frames}``'
        reply_adds += f' - Seed: ``{seed}``'
        if engine != channel_settings['video_engine']:
            reply_adds += f'\nEngine: ``{engine}``'
        if model != channel_settings['video_model']:
            reply_adds += f'\nModel: ``{model}``'
        if steps > channel_settings['video_steps']:
            reply_adds += f'\nExceeded maximum of ``{max_video_steps}`` steps! This is the best I can do...'
        elif steps != channel_settings['video_steps']:
            reply_adds += f'\nSteps: ``{steps}``'
        if frames > channel_settings['video_frames']:
            reply_adds += f'\nExceeded maximum of ``{max_video_frames}`` frames! This is the best I can do...'
        elif frames != channel_settings['video_frames']:
            reply_adds += f'\nFrames: ``{frames}``'
        if guidance_scale != channel_settings['video_guidance_scale']:
            reply_adds += f'\nGuidance Scale: ``{guidance_scale}``'
        if sampler_name != channel_settings['video_sampler']:
            reply_adds += f'\nSampler: ``{sampler_name}``'
        if init_image:
            reply_adds += f'\nInit Strength: ``{init_strength}``'
            if init_url:
                reply_adds += f'\nURL Init Image: ``{init_url}``'
        if audio != channel_settings['video_audio']:
            reply_adds += f'\nAudio: ``{audio}``'
        if derived_spoiler:
            reply_adds += '\nSpoiler: :white_check_mark:'

        epoch_time = int(time.time())

        # set up tuple
        input_tuple = (
            ctx, simple_prompt, prompt, negative_prompt, engine, model,
            width, height, frames, steps, seed, guidance_scale, sampler_name,
            init_image, init_strength, audio, mp4_fps, mp4_interpolate,
            derived_spoiler, epoch_time)
        view = viewhandler.VideoView(input_tuple)

        # setup the queue
        user_queue_limit = settings.queue_check(ctx.author)
        if queuehandler.GlobalQueue.dream_thread.is_alive():
            if user_queue_limit == "Stop":
                await ctx.send_response(
                    content=f"Please wait! You're past your queue limit of {settings.global_var.queue_limit}.",
                    ephemeral=True)
            else:
                queuehandler.GlobalQueue.queue.append(queuehandler.VideoObject(self, *input_tuple, view))
        else:
            await queuehandler.process_dream(self, queuehandler.VideoObject(self, *input_tuple, view))
        if user_queue_limit != "Stop":
            await ctx.send_response(
                f'<@{ctx.author.id}>, {settings.messages()}\nQueue: ``{len(queuehandler.GlobalQueue.queue)}``'
                f' - ``{simple_prompt}``\nFrames: ``{frames}``{reply_adds}')

    # the function to queue Discord posts
    def post(self, event_loop: queuehandler.GlobalQueue.post_event_loop, post_queue_object: queuehandler.PostObject):
        event_loop.create_task(
            post_queue_object.ctx.channel.send(
                content=post_queue_object.content,
                file=post_queue_object.file,
                view=post_queue_object.view
            )
        )
        if queuehandler.GlobalQueue.post_queue:
            self.post(self.event_loop, self.queue.pop(0))

    def dream(self, event_loop, queue_object):
        try:
            start_time = time.time()
            user_id, user_name = settings.fuzzy_get_id_name(queue_object.ctx)
            view = queue_object.view

            # authenticate
            s = settings.authenticate_user()

            # build payload
            payload = {
                'engine': queue_object.engine,
                'model': queue_object.model,
                'prompt': queue_object.prompt,
                'negative_prompt': queue_object.negative_prompt,
                'width': queue_object.width,
                'height': queue_object.height,
                'frames': queue_object.frames,
                'steps': queue_object.steps,
                'seed': queue_object.seed,
                'guidance_scale': float(queue_object.guidance_scale),
                'sampler_name': queue_object.sampler_name,
                'audio': queue_object.audio,
                'mp4_fps': queue_object.mp4_fps,
                'mp4_interpolate': queue_object.mp4_interpolate,
                'send_video': True,
                'send_thumbnail': True,
            }

            # add init_image if provided
            if queue_object.init_image is not None:
                image_bytes = requests.get(queue_object.init_image.url, stream=True).content
                init_b64 = base64.b64encode(image_bytes).decode('utf-8')
                payload['init_image'] = 'data:image/png;base64,' + init_b64
                payload['init_strength'] = float(queue_object.init_strength)

            # start progress monitoring
            status_message_task = event_loop.create_task(queue_object.ctx.channel.send(
                f'**Author**: {user_id} ({user_name})\n'
                f'**Prompt**: `{queue_object.prompt}`\n**Progress**: initialization...'
                f'\n0/{queue_object.steps} iterations'
                f'\n**Relative ETA**: initialization...'))

            def worker():
                event_loop.create_task(update_video_progress(event_loop, status_message_task, s, queue_object))

            status_thread = Thread(target=worker)

            def start_thread(*args):
                status_thread.start()

            status_message_task.add_done_callback(start_thread)

            # send request
            response = s.post(url=f'{settings.global_var.url}/sdapi/v1/video', json=payload, timeout=3600)
            response_data = response.json()
            end_time = time.time()

            # delete progress message
            def post_dream():
                event_loop.create_task(status_message_task.result().delete())
            Thread(target=post_dream, daemon=True).start()

            # extract response data
            video_b64 = response_data.get('video', '') or ''
            video_path = response_data.get('video_path', '') or ''
            thumbnail_b64 = response_data.get('thumbnail', '') or ''
            info = response_data.get('info', '')

            # prepare filename
            video_filename = f'{queue_object.epoch_time}-{queue_object.seed}.mp4'
            if queue_object.spoiler:
                video_filename = f'SPOILER_{video_filename}'

            draw_time = '{0:.3f}'.format(end_time - start_time)

            # try to get video bytes from base64 response
            video_bytes = None
            if video_b64:
                try:
                    video_bytes = base64.b64decode(video_b64)
                except Exception:
                    video_bytes = None

            # if no video bytes from base64, try fetching from video_path
            if video_bytes is None and video_path:
                try:
                    file_response = s.get(
                        f'{settings.global_var.url}/sdapi/v1/video/file',
                        params={'file': video_path},
                        timeout=3600)
                    if file_response.status_code == 200:
                        video_bytes = file_response.content
                except Exception:
                    pass

            if video_bytes is not None and len(video_bytes) > 0:
                # check Discord 25MB upload limit
                if len(video_bytes) > 25 * 1024 * 1024:
                    content = (f'<@{user_id}>, my video of ``{queue_object.simple_prompt}`` '
                               f'took me ``{draw_time}`` seconds!\n'
                               f'Video is too large for Discord.'
                               + (f' Video path: ``{video_path}``' if video_path else ''))
                    event_loop.create_task(queue_object.ctx.channel.send(content=content, view=view))
                else:
                    # save to disk
                    if settings.global_var.save_outputs == 'True':
                        save_path = f'{settings.global_var.dir}/{queue_object.epoch_time}-{queue_object.seed}.mp4'
                        with open(save_path, 'wb') as f:
                            f.write(video_bytes)
                        print(f'Saved video: {save_path}')

                    # save thumbnail if available
                    if thumbnail_b64:
                        try:
                            thumb_bytes = base64.b64decode(thumbnail_b64)
                            thumb_path = f'{settings.global_var.dir}/{queue_object.epoch_time}-{queue_object.seed}-thumb.png'
                            with open(thumb_path, 'wb') as f:
                                f.write(thumb_bytes)
                        except Exception:
                            pass

                    # send to Discord
                    content = f'<@{user_id}>, my video of ``{queue_object.simple_prompt}`` took me ``{draw_time}`` seconds!'
                    file = discord.File(io.BytesIO(video_bytes), filename=video_filename)
                    queuehandler.process_post(
                        self, queuehandler.PostObject(
                            self, queue_object.ctx, content=content, file=file, embed='', view=view))

                    # update stats
                    settings.stats_count(1)
            else:
                # no video returned
                content = (f'<@{user_id}>, my video of ``{queue_object.simple_prompt}`` '
                           f'took me ``{draw_time}`` seconds!\n'
                           f'But no video was returned.'
                           + (f' Info: ``{info}``' if info else ''))
                event_loop.create_task(queue_object.ctx.channel.send(content=content, view=view))

        except Exception as e:
            embed = discord.Embed(title='video generation failed', description=f'{e}\n{traceback.print_exc()}',
                                  color=settings.global_var.embed_color)
            event_loop.create_task(queue_object.ctx.channel.send(embed=embed))

        # check queue for remaining tasks
        queuehandler.process_queue()


def setup(bot):
    bot.add_cog(VideoCog(bot))