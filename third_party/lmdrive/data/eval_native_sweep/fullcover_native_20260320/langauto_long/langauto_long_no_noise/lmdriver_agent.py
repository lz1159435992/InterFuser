import os
import json
import random
import datetime
import pathlib
import time
import imp
from collections import deque
import math

import yaml
import cv2
import torch
import carla
import numpy as np
from PIL import Image
from easydict import EasyDict
from torchvision import transforms
try:
    import huggingface_hub
except ModuleNotFoundError:
    huggingface_hub = None

if huggingface_hub is not None and not hasattr(huggingface_hub, "cached_download"):
    try:
        from huggingface_hub.file_download import hf_hub_download

        def cached_download(*args, **kwargs):
            return hf_hub_download(*args, **kwargs)

        huggingface_hub.cached_download = cached_download
    except Exception:
        pass

from leaderboard.autoagents import autonomous_agent
from team_code.planner import RoutePlanner, InstructionPlanner
from team_code.pid_controller import PIDController
from timm.models import create_model
from lavis.common.registry import registry
import lavis.models.drive_models.drive
from sensor_data_processor_module.data_processor import SensorDataProcessor
from sensor_data_processor_module.data_processor_config import ACTIVE_CONFIG

from team_code.lmdrive_native_config_parser import load_config_from_env

try:
    import pygame
except ImportError:
    raise RuntimeError("cannot import pygame, make sure pygame package is installed")


SAVE_PATH = os.environ.get("SAVE_PATH", 'eval')
IMAGENET_DEFAULT_MEAN = (0.485, 0.456, 0.406)
IMAGENET_DEFAULT_STD = (0.229, 0.224, 0.225)


def _env_flag_true(name, default=False):
    value = os.environ.get(name, None)
    if value is None:
        return default
    value = str(value).strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    return default


def rotate_lidar(lidar, angle):
    radian = np.deg2rad(angle)
    return lidar @ [
        [np.cos(radian), np.sin(radian), 0, 0],
        [-np.sin(radian), np.cos(radian), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]


def lidar_to_raw_features(lidar):
    def preprocess(lidar_xyzr, lidar_painted=None):
        idx = (
            (lidar_xyzr[:, 0] > -1.2)
            & (lidar_xyzr[:, 0] < 1.2)
            & (lidar_xyzr[:, 1] > -1.2)
            & (lidar_xyzr[:, 1] < 1.2)
        )

        idx = np.argwhere(idx)

        if lidar_painted is None:
            return np.delete(lidar_xyzr, idx, axis=0)
        else:
            return np.delete(lidar_xyzr, idx, axis=0), np.delete(lidar_painted, idx, axis=0)

    lidar_xyzr = preprocess(lidar)

    idxs = np.arange(len(lidar_xyzr))
    np.random.shuffle(idxs)
    lidar_xyzr = lidar_xyzr[idxs]

    lidar = np.zeros((40000, 4), dtype=np.float32)
    num_points = min(40000, len(lidar_xyzr))
    lidar[:num_points, :4] = lidar_xyzr
    lidar[np.isinf(lidar)] = 0
    lidar[np.isnan(lidar)] = 0
    lidar = rotate_lidar(lidar, -90).astype(np.float32)
    return lidar, num_points


class DisplayInterface(object):
    def __init__(self):
        self._width = 1200
        self._height = 900
        self._surface = None

        pygame.init()
        pygame.font.init()
        self._clock = pygame.time.Clock()
        self._display = pygame.display.set_mode(
            (self._width, self._height), pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("LMDrive Agent")

    def run_interface(self, input_data):
        rgb = input_data['rgb_front']
        rgb_left = input_data['rgb_left']
        rgb_right = input_data['rgb_right']
        rgb_focus = input_data['rgb_center']
        surface = np.zeros((900, 1200, 3), np.uint8)
        surface[:, :1200] = rgb
        surface[:210, :280] = input_data['rgb_left']
        surface[:210, 920:1200] = input_data['rgb_right']
        surface[:210, 495:705] = input_data['rgb_center']
        surface = cv2.putText(surface, input_data['time'], (20, 710), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (0, 0, 255), 1)
        surface = cv2.putText(surface, input_data['meta_control'], (20, 740), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (0, 0, 255), 1)
        surface = cv2.putText(surface, input_data['waypoints'], (20, 770), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (0, 0, 255), 1)
        surface = cv2.putText(surface, input_data['instruction'], (20, 800), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (0, 0, 255), 1)
        surface = cv2.putText(surface, input_data['notice'], (20, 830), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (0, 0, 255), 1)

        surface = cv2.putText(surface, 'Left  View', (60, 245), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (139, 69, 19), 2)
        surface = cv2.putText(surface, 'Focus View', (535, 245), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (139, 69, 19), 2)
        surface = cv2.putText(surface, 'Right View', (980, 245), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (139, 69, 19), 2)

        surface[:210, 278:282] = [139, 69, 19]
        surface[:210, 493:497] = [139, 69, 19]
        surface[:210, 703:707] = [139, 69, 19]
        surface[:210, 918:922] = [139, 69, 19]
        surface[208:212, :280] = [139, 69, 19]
        surface[208:212, 920:1200] = [139, 69, 19]
        surface[208:212, 495:705] = [139, 69, 19]

        self._surface = pygame.surfarray.make_surface(surface.swapaxes(0, 1))

        if self._surface is not None:
            self._display.blit(self._surface, (0, 0))

        pygame.display.flip()
        pygame.event.get()
        return surface

    def _quit(self):
        pygame.quit()


class DummyDisplayInterface(object):
    def __init__(self):
        self._width = 1200
        self._height = 900

    def run_interface(self, input_data):
        surface = np.zeros((self._height, self._width, 3), np.uint8)
        return surface

    def _quit(self):
        pass


def get_entry_point():
    return "LMDriveAgent"


class Resize2FixedSize:
    def __init__(self, size):
        self.size = size

    def __call__(self, pil_img):
        pil_img = pil_img.resize(self.size)
        return pil_img


def create_carla_rgb_transform(input_size, need_scale=True, mean=IMAGENET_DEFAULT_MEAN, std=IMAGENET_DEFAULT_STD):
    if isinstance(input_size, (tuple, list)):
        img_size = input_size[-2:]
    else:
        img_size = input_size
    tfl = []

    if isinstance(input_size, (tuple, list)):
        input_size_num = input_size[-1]
    else:
        input_size_num = input_size

    if need_scale:
        if input_size_num == 112:
            tfl.append(Resize2FixedSize((170, 128)))
        elif input_size_num == 128:
            tfl.append(Resize2FixedSize((195, 146)))
        elif input_size_num == 224:
            tfl.append(Resize2FixedSize((341, 256)))
        elif input_size_num == 256:
            tfl.append(Resize2FixedSize((288, 288)))
        else:
            raise ValueError("Can't find proper crop size")
    tfl.append(transforms.CenterCrop(img_size))
    tfl.append(transforms.ToTensor())
    tfl.append(transforms.Normalize(mean=torch.tensor(mean), std=torch.tensor(std)))

    return transforms.Compose(tfl)


class LMDriveAgent(autonomous_agent.AutonomousAgent):
    def setup(self, path_to_conf_file):
        print("[LMDriveAgentNative.setup] start", flush=True)

        self.native_config = load_config_from_env()
        self.sim_hz = float(self.native_config.frame_rate)

        use_dummy_display = os.environ.get("LMDRIVE_HEADLESS", "1") == "1"
        if use_dummy_display:
            self._hic = DummyDisplayInterface()
        else:
            self._hic = DisplayInterface()

        self.track = autonomous_agent.Track.SENSORS
        self.step = -1
        self.wall_start = time.time()
        self.initialized = False
        self.rgb_front_transform = create_carla_rgb_transform(224)
        self.rgb_left_transform = create_carla_rgb_transform(128)
        self.rgb_right_transform = create_carla_rgb_transform(128)
        self.rgb_center_transform = create_carla_rgb_transform(128, need_scale=False)

        self.active_misleading_instruction = False
        self.remaining_misleading_frames = 0
        self.visual_feature_buffer = []

        self.config = imp.load_source("MainModel", path_to_conf_file).GlobalConfig()

        self.use_data_processor = getattr(self.config, "use_data_processor", False)
        if self.use_data_processor:
            self.data_processor = SensorDataProcessor(ACTIVE_CONFIG)
            print("[LMDriveAgentNative.setup] data processor enabled", flush=True)

        self.turn_controller = PIDController(
            K_P=self.config.turn_KP,
            K_I=self.config.turn_KI,
            K_D=self.config.turn_KD,
            n=self.config.turn_n,
        )
        self.speed_controller = PIDController(
            K_P=self.config.speed_KP,
            K_I=self.config.speed_KI,
            K_D=self.config.speed_n,
            n=self.config.speed_n,
        )

        model_cls = registry.get_model_class('vicuna_drive')

        self.agent_use_notice = self.config.agent_use_notice
        self.traffic_light_notice = ''
        self.curr_notice = ''
        self.now_notice_frame_id = -1

        lidar_base_stack_frames = 2
        self.lidar_stack_frames = int(max(1, round(lidar_base_stack_frames * (self.sim_hz / 20.0))))
        self.lidar_buffer = deque(maxlen=self.lidar_stack_frames)

        # Keep the same semantic as original code: config.sample_rate assumes 20Hz and then multiplies by 2.
        # Generalize it to arbitrary sim_hz (default 20 or 40 via native_config).
        base_hz = 20.0
        base_visual_stride = float(self.config.sample_rate) * 2.0
        self.sample_rate = int(max(1, round(base_visual_stride * (self.sim_hz / base_hz))))

        print(f"[LMDriveAgentNative.setup] NATIVE_ENHANCE={','.join(self.native_config.tokens)} sim_hz={self.sim_hz} sample_rate={self.sample_rate}", flush=True)

        model = model_cls(
            preception_model=self.config.preception_model,
            preception_model_ckpt=self.config.preception_model_ckpt,
            llm_model=self.config.llm_model,
            max_txt_len=64,
            use_notice_prompt=self.config.agent_use_notice,
        )
        self.net = model
        _ckpt_state = torch.load(self.config.lmdrive_ckpt)["model"]
        _load_ret = self.net.load_state_dict(_ckpt_state, strict=False)
        _missing = list(getattr(_load_ret, "missing_keys", []))
        _unexpected = list(getattr(_load_ret, "unexpected_keys", []))
        print(
            f"[LMDriveAgentNative.setup] load_state_dict(strict=False) missing={len(_missing)} unexpected={len(_unexpected)}",
            flush=True,
        )
        if len(_missing) > 0:
            _prefixes = (
                "visual_encoder.",
                "ln_vision.",
                "Qformer.",
                "query_tokens",
                "llm_model.",
                "llm_proj.",
                "waypoints_predictor.",
                "end_predictor.",
            )
            _counts = {p: 0 for p in _prefixes}
            _counts["<other>"] = 0
            for k in _missing:
                matched = False
                for p in _prefixes:
                    if k.startswith(p):
                        _counts[p] += 1
                        matched = True
                        break
                if not matched:
                    _counts["<other>"] += 1
            _counts_str = ", ".join([f"{k}{v}" for k, v in _counts.items() if v > 0])
            print(f"[LMDriveAgentNative.setup] missing_keys(summary)={_counts_str}", flush=True)
        if len(_missing) > 0:
            print(f"[LMDriveAgentNative.setup] missing_keys(head)={_missing[:50]}", flush=True)
        if len(_unexpected) > 0:
            print(f"[LMDriveAgentNative.setup] unexpected_keys(head)={_unexpected[:50]}", flush=True)
        self.net.cuda()
        self.net.eval()
        self.softmax = torch.nn.Softmax(dim=1)
        self.prev_lidar = None
        self.prev_control = None
        self.curr_instruction = 'Drive safely.'
        self.sampled_scenarios = None
        self.instruction = ''

        self.disable_meta = _env_flag_true("DISABLE_META", default=False) or (not _env_flag_true("SAVE_META", default=False))

        self.save_path = None
        if SAVE_PATH is not None and not self.disable_meta:
            now = datetime.datetime.now()
            string = pathlib.Path(os.environ["ROUTES"]).stem + "_"
            string += "_".join(map(lambda x: "%02d" % x, (now.month, now.day, now.hour, now.minute, now.second)))
            self.save_path = pathlib.Path(SAVE_PATH) / string
            self.save_path.mkdir(parents=True, exist_ok=False)
            (self.save_path / "meta").mkdir(parents=True, exist_ok=False)

        print("[LMDriveAgentNative.setup] completed", flush=True)

    def _init(self):
        self._route_planner = RoutePlanner(5, 50.0)
        self._route_planner.set_route(self._global_plan, True)
        self._instruction_planner = InstructionPlanner(self.scenario_cofing_name, True)
        self.initialized = True
        random.seed(''.join([str(x[0]) for x in self._global_plan]))

    def _get_position(self, tick_data):
        gps = tick_data["gps"]
        gps = (gps - self._route_planner.mean) * self._route_planner.scale
        return gps

    def sensors(self):
        cfg = self.native_config

        cam_common = {
            "fov": 100,
            "sensor_tick": cfg.sensor_tick,
            "motion_blur_intensity": cfg.motion_blur_intensity,
            "motion_blur_max_distortion": cfg.motion_blur_max_distortion,
            "bloom_intensity": cfg.bloom_intensity,
            "lens_flare_intensity": cfg.lens_flare_intensity,
            "lens_circle_falloff": cfg.lens_circle_falloff,
            "lens_k": cfg.lens_k,
            "lens_kcube": cfg.lens_kcube,
        }

        return [
            {
                "type": "sensor.camera.rgb",
                "x": 1.3,
                "y": 0.0,
                "z": 2.3,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "width": cfg.camera_front_width,
                "height": cfg.camera_front_height,
                "id": "rgb_front",
                **cam_common,
            },
            {
                "type": "sensor.camera.rgb",
                "x": 1.3,
                "y": 0.0,
                "z": 2.3,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": -60.0,
                "width": cfg.camera_side_width,
                "height": cfg.camera_side_height,
                "id": "rgb_left",
                **cam_common,
            },
            {
                "type": "sensor.camera.rgb",
                "x": 1.3,
                "y": 0.0,
                "z": 2.3,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 60.0,
                "width": cfg.camera_side_width,
                "height": cfg.camera_side_height,
                "id": "rgb_right",
                **cam_common,
            },
            {
                "type": "sensor.camera.rgb",
                "x": -1.3,
                "y": 0.0,
                "z": 2.3,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 180.0,
                "width": cfg.camera_side_width,
                "height": cfg.camera_side_height,
                "id": "rgb_rear",
                **cam_common,
            },
            {
                "type": "sensor.lidar.ray_cast",
                "x": 1.3,
                "y": 0.0,
                "z": 2.5,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": -90.0,
                "id": "lidar",
            },
            {
                "type": "sensor.other.imu",
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "sensor_tick": 0.0,
                "id": "imu",
            },
            {
                "type": "sensor.other.gnss",
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "sensor_tick": 0.01,
                "id": "gps",
            },
            {"type": "sensor.speedometer", "reading_frequency": int(cfg.frame_rate), "id": "speed"},
        ]

    def tick(self, input_data):
        rgb_front = cv2.cvtColor(input_data["rgb_front"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        rgb_left = cv2.cvtColor(input_data["rgb_left"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        rgb_right = cv2.cvtColor(input_data["rgb_right"][1][:, :, :3], cv2.COLOR_BGR2RGB)
        rgb_rear = cv2.cvtColor(input_data["rgb_rear"][1][:, :, :3], cv2.COLOR_BGR2RGB)

        sigma = getattr(self.native_config, "gaussian_noise_sigma", 0)
        if sigma and sigma > 0:
            def _add_gaussian_noise_uint8(img: np.ndarray, sigma_: int) -> np.ndarray:
                noise = np.random.normal(loc=0.0, scale=float(sigma_), size=img.shape).astype(np.float32)
                out = img.astype(np.float32) + noise
                out = np.clip(out, 0.0, 255.0)
                return out.astype(np.uint8)

            rgb_front = _add_gaussian_noise_uint8(rgb_front, sigma)
            rgb_left = _add_gaussian_noise_uint8(rgb_left, sigma)
            rgb_right = _add_gaussian_noise_uint8(rgb_right, sigma)
            rgb_rear = _add_gaussian_noise_uint8(rgb_rear, sigma)

        if getattr(self, "use_data_processor", False):
            rgb_front = self.data_processor.process_rgb(rgb_front, "rgb_front")
            rgb_left, rgb_right, rgb_rear = self.data_processor.process_rgb_batch([rgb_left, rgb_right, rgb_rear])

        gps = input_data["gps"][1][:2]
        speed = input_data["speed"][1]["speed"]
        compass = input_data["imu"][1][-1]
        if math.isnan(compass):
            compass = 0.0

        result = {
            "rgb_front": rgb_front,
            "rgb_left": rgb_left,
            "rgb_right": rgb_right,
            "rgb_rear": rgb_rear,
            "gps": gps,
            "speed": speed,
            "compass": compass,
        }

        pos = self._get_position(result)

        lidar_data = input_data['lidar'][1]
        result['raw_lidar'] = lidar_data

        lidar_unprocessed = lidar_data[..., :4]
        self.lidar_buffer.append(lidar_unprocessed)
        if len(self.lidar_buffer) > 1:
            lidar_unprocessed_full = np.concatenate(list(self.lidar_buffer), axis=0)
        else:
            lidar_unprocessed_full = lidar_unprocessed

        lidar_processed, num_points = lidar_to_raw_features(lidar_unprocessed_full)
        result['lidar'] = lidar_processed
        result['num_points'] = num_points

        result["gps"] = pos
        next_wp, next_cmd = self._route_planner.run_step(pos)
        result["next_waypoint"] = next_wp
        result["next_command"] = next_cmd.value
        result['measurements'] = [pos[0], pos[1], compass, speed]
        result['speed'] = speed

        theta = compass + np.pi / 2
        R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
        local_command_point = np.array([next_wp[0] - pos[0], next_wp[1] - pos[1]])
        local_command_point = R.T.dot(local_command_point)
        result["target_point"] = local_command_point

        return result

    def update_and_collect(self, image_embeds):
        self.visual_feature_buffer.append(image_embeds)
        result = self.visual_feature_buffer[:: self.sample_rate]
        if (len(self.visual_feature_buffer) - 1) % self.sample_rate != 0:
            result.append(self.visual_feature_buffer[-1])
        return torch.stack(result, 1)

    @torch.no_grad()
    def run_step(self, input_data, timestamp):
        if not self.initialized:
            self._init()

        self.step += 1

        warmup_frames = int(max(1, round(20.0 * (self.sim_hz / 20.0))))
        if self.step < warmup_frames:
            control = carla.VehicleControl()
            control.steer = float(0)
            control.throttle = float(0)
            control.brake = float(1)
            return control

        control_period = 2
        if (self.step % control_period) != 0 and self.step > 4:
            return self.prev_control

        tick_data = self.tick(input_data)

        velocity = tick_data["speed"]
        command = tick_data["next_command"]

        rgb_front = self.rgb_front_transform(Image.fromarray(tick_data["rgb_front"]))
        rgb_front = rgb_front.unsqueeze(0).cuda().float()
        rgb_left = self.rgb_left_transform(Image.fromarray(tick_data["rgb_left"]))
        rgb_left = rgb_left.unsqueeze(0).cuda().float()
        rgb_right = self.rgb_right_transform(Image.fromarray(tick_data["rgb_right"]))
        rgb_right = rgb_right.unsqueeze(0).cuda().float()
        rgb_rear = self.rgb_right_transform(Image.fromarray(tick_data["rgb_rear"]))
        rgb_rear = rgb_rear.unsqueeze(0).cuda().float()
        rgb_center = self.rgb_center_transform(Image.fromarray(cv2.resize(tick_data["rgb_front"], (800, 600))))
        rgb_center = rgb_center.unsqueeze(0).cuda().float()

        last_instruction = self._instruction_planner.command2instruct(self.town_id, tick_data, self._route_planner.route)
        last_notice = self._instruction_planner.pos2notice(self.sampled_scenarios, tick_data)
        last_traffic_light_notice = self._instruction_planner.traffic_notice(tick_data)
        last_misleading_instruction = self._instruction_planner.command2mislead(self.town_id, tick_data)

        if last_notice == '':
            last_notice = last_traffic_light_notice

        if self.curr_instruction != last_instruction or len(self.visual_feature_buffer) > 400:
            if self.remaining_misleading_frames > 0:
                self.remaining_misleading_frames = self.remaining_misleading_frames - 1
            else:
                self.active_misleading_instruction = False
                if last_misleading_instruction != '' and random.random() < 0.2:
                    self.curr_instruction = last_misleading_instruction
                    self.active_misleading_instruction = True
                    self.remaining_misleading_frames = 20
                else:
                    self.curr_instruction = last_instruction
                self.visual_feature_buffer = []
                self.curr_notice = ''
                self.curr_notice_frame_id = -1

        model_input = {}
        model_input["rgb_front"] = rgb_front
        model_input["rgb_left"] = rgb_left
        model_input["rgb_right"] = rgb_right
        model_input["rgb_center"] = rgb_center
        model_input["rgb_rear"] = rgb_rear
        model_input['target_point'] = torch.tensor(tick_data['target_point']).cuda().view(1, 2).float()
        model_input["lidar"] = torch.from_numpy(tick_data["lidar"]).float().cuda().unsqueeze(0)
        model_input['num_points'] = torch.tensor([tick_data['num_points']]).cuda().unsqueeze(0)
        model_input['velocity'] = torch.tensor([tick_data['speed']]).cuda().view(1, 1).float()
        model_input['text_input'] = [self.curr_instruction]

        image_embeds = self.net.visual_encoder(model_input)
        image_embeds = self.update_and_collect(image_embeds)
        model_input['valid_frames'] = [image_embeds.size(1)]

        if last_notice != '' and last_notice != self.curr_notice:
            self.curr_notice = last_notice
            self.curr_notice_frame_id = image_embeds.size(1) - 1

        if self.agent_use_notice:
            model_input['notice_text'] = [self.curr_notice]
            model_input['notice_frame_id'] = [self.curr_notice_frame_id]

        with torch.cuda.amp.autocast(enabled=True):
            waypoints, is_end = self.net(model_input, inference_mode=True, image_embeds=image_embeds)

        waypoints = waypoints[-1].view(5, 2)
        end_prob = self.softmax(is_end)[-1][1]

        steer, throttle, brake, metadata = self.control_pid(waypoints, velocity)

        if end_prob > 0.75:
            self.visual_feature_buffer = []
            self.curr_notice = ''
            self.curr_notice_frame_id = -1

        if brake < 0.05:
            brake = 0.0
        if brake > 0.1:
            throttle = 0.0

        control = carla.VehicleControl()
        control.steer = float(steer) * 0.8
        control.throttle = float(throttle)
        control.brake = float(brake)

        display_data = {}
        display_data['rgb_front'] = cv2.resize(tick_data['rgb_front'], (1200, 900))
        display_data['rgb_left'] = cv2.resize(tick_data['rgb_left'], (280, 210))
        display_data['rgb_right'] = cv2.resize(tick_data['rgb_right'], (280, 210))
        display_data['rgb_center'] = cv2.resize(tick_data['rgb_front'][330:570, 480:720], (210, 210))
        if self.active_misleading_instruction:
            display_data['instruction'] = "Instruction: [Misleading] %s" % model_input['text_input'][0]
        else:
            display_data['instruction'] = "Instruction: %s" % model_input['text_input'][0]
        display_data['time'] = 'Time: %.3f. Frames: %d. End prob: %.2f' % (timestamp, len(self.visual_feature_buffer), end_prob)
        display_data['meta_control'] = 'Throttle: %.2f. Steer: %.2f. Brake: %.2f' % (control.steer, control.throttle, control.brake)
        display_data['waypoints'] = 'Waypoints: (%.1f, %.1f), (%.1f, %.1f)' % (
            waypoints[0, 0], -waypoints[0, 1], waypoints[1, 0], -waypoints[1, 1]
        )
        display_data['notice'] = "Notice: %s" % last_notice
        surface = self._hic.run_interface(display_data)
        tick_data['surface'] = surface

        self.prev_control = control

        if self.save_path is not None:
            self.save(tick_data)

        return control

    def save(self, tick_data):
        if self.save_path is None:
            return
        frame = (self.step)
        headless = os.environ.get("LMDRIVE_HEADLESS", "1") == "1"
        if headless:
            front = cv2.resize(tick_data["rgb_front"], (1200, 900))
            left = cv2.resize(tick_data["rgb_left"], (280, 210))
            right = cv2.resize(tick_data["rgb_right"], (280, 210))
            center_crop = tick_data["rgb_front"][330:570, 480:720]
            center = cv2.resize(center_crop, (210, 210))

            surface = np.zeros((900, 1200, 3), np.uint8)
            surface[:, :1200] = front
            surface[:210, :280] = left
            surface[:210, 920:1200] = right
            surface[:210, 495:705] = center

            Image.fromarray(surface).save(self.save_path / "meta" / ("%04d.jpg" % frame))
        else:
            Image.fromarray(tick_data["surface"]).save(self.save_path / "meta" / ("%04d.jpg" % frame))
        return

    def destroy(self):
        del self.net

    def control_pid(self, waypoints, velocity):
        assert waypoints.size(0) == 5
        waypoints = waypoints.data.cpu().numpy()

        waypoints[:, 1] *= -1
        speed = velocity

        desired_speed = np.linalg.norm(waypoints[0] - waypoints[1]) * 2.0
        brake = desired_speed < self.config.brake_speed or (speed / desired_speed) > self.config.brake_ratio

        aim = (waypoints[1] + waypoints[0]) / 2.0
        angle = np.degrees(np.pi / 2 - np.arctan2(aim[1], aim[0])) / 90
        if speed < 0.01:
            angle = np.array(0.0)
        steer = self.turn_controller.step(angle)
        steer = np.clip(steer, -1.0, 1.0)

        delta = np.clip(desired_speed - speed, 0.0, self.config.clip_delta)
        throttle = self.speed_controller.step(delta)
        throttle = np.clip(throttle, 0.0, self.config.max_throttle)
        throttle = throttle if not brake else 0.0

        metadata = {
            'speed': float(speed.astype(np.float64)) if hasattr(speed, 'astype') else float(speed),
            'steer': float(steer),
            'throttle': float(throttle),
            'brake': float(brake),
            'wp_2': tuple(waypoints[1].astype(np.float64)),
            'wp_1': tuple(waypoints[0].astype(np.float64)),
            'desired_speed': float(desired_speed.astype(np.float64)) if hasattr(desired_speed, 'astype') else float(desired_speed),
            'angle': float(angle.astype(np.float64)) if hasattr(angle, 'astype') else float(angle),
            'aim': tuple(aim.astype(np.float64)),
            'delta': float(delta.astype(np.float64)) if hasattr(delta, 'astype') else float(delta),
        }

        return steer, throttle, brake, metadata
