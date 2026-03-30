import argparse
import csv
import json
import math
import os
from collections import deque

import numpy as np


def _read_image_rgb_uint8(path):
    try:
        import imageio.v2 as imageio
    except Exception:
        import imageio

    img = imageio.imread(path)
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    if img.shape[-1] == 4:
        img = img[..., :3]
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)
    return img


def iter_ch2_frames(images_dir, steering_csv_path, *, stride=1, max_frames=None, start_index=0):
    count = 0
    with open(steering_csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return

        for idx, row in enumerate(reader):
            if idx < start_index:
                continue
            if stride > 1 and ((idx - start_index) % stride != 0):
                continue
            if len(row) < 2:
                continue

            frame_id = row[0].strip()
            try:
                steering = float(row[1])
            except ValueError:
                continue

            img_path = os.path.join(images_dir, f"{frame_id}.jpg")
            if not os.path.exists(img_path):
                continue

            img = _read_image_rgb_uint8(img_path)
            yield frame_id, img, steering

            count += 1
            if max_frames is not None and count >= max_frames:
                return


class LegacyMerge(object):
    def __new__(cls, *args, **kwargs):
        from keras.engine.topology import Layer

        class _LegacyMerge(Layer):
            def __init__(
                self,
                layers=None,
                mode="sum",
                concat_axis=-1,
                dot_axes=-1,
                **kw,
            ):
                if "mode_type" in kw and (mode is None or mode == "sum"):
                    mode = kw.get("mode_type")

                name = kw.pop("name", None)
                trainable = kw.pop("trainable", True)
                dtype = kw.pop("dtype", None)

                kw.pop("mode_type", None)
                kw.pop("output_shape", None)
                kw.pop("layers", None)
                kw.pop("node_indices", None)
                kw.pop("tensor_indices", None)
                kw.pop("input_shape", None)
                kw.pop("batch_input_shape", None)

                super(_LegacyMerge, self).__init__(name=name, trainable=trainable, dtype=dtype)
                self.layers = layers
                self.mode = mode
                self.concat_axis = concat_axis
                self.dot_axes = dot_axes

            def call(self, inputs, **kw):
                from keras import backend as K

                if not isinstance(inputs, (list, tuple)):
                    return inputs
                if self.mode in ("sum", "add"):
                    out = inputs[0]
                    for x in inputs[1:]:
                        out = out + x
                    return out
                if self.mode in ("mul", "multiply"):
                    out = inputs[0]
                    for x in inputs[1:]:
                        out = out * x
                    return out
                if self.mode in ("ave", "avg", "average"):
                    out = inputs[0]
                    for x in inputs[1:]:
                        out = out + x
                    return out / float(len(inputs))
                if self.mode == "max":
                    out = inputs[0]
                    for x in inputs[1:]:
                        out = K.maximum(out, x)
                    return out
                if self.mode in ("concat", "concatenate"):
                    return K.concatenate(list(inputs), axis=self.concat_axis)
                if self.mode in ("dot", "cos"):
                    axes = self.dot_axes
                    if isinstance(axes, int):
                        axes = (axes, axes)
                    out = K.batch_dot(inputs[0], inputs[1], axes=axes)
                    if self.mode == "cos":
                        x = inputs[0]
                        y = inputs[1]
                        x = K.l2_normalize(x, axis=axes[0])
                        y = K.l2_normalize(y, axis=axes[1])
                        out = K.batch_dot(x, y, axes=axes)
                    return out
                raise ValueError("Unsupported Merge mode: %s" % self.mode)

            def compute_output_shape(self, input_shape):
                if not isinstance(input_shape, (list, tuple)) or not input_shape:
                    return input_shape
                if self.mode in ("concat", "concatenate"):
                    axis = self.concat_axis
                    ref = list(input_shape[0])
                    if axis < 0:
                        axis = len(ref) + axis
                    total = 0
                    unknown = False
                    for s in input_shape:
                        dim = s[axis]
                        if dim is None:
                            unknown = True
                        else:
                            total += dim
                    ref[axis] = None if unknown else total
                    return tuple(ref)
                return input_shape[0]

            def get_config(self):
                base = super(_LegacyMerge, self).get_config()
                base.update(
                    {
                        "mode": self.mode,
                        "concat_axis": self.concat_axis,
                        "dot_axes": self.dot_axes,
                    }
                )
                return base

        return _LegacyMerge(*args, **kwargs)


def _convert_legacy_keras_config(obj):
    if isinstance(obj, list):
        return [_convert_legacy_keras_config(x) for x in obj]

    if not isinstance(obj, dict):
        return obj

    if (
        "class_name" not in obj
        and obj.get("name") == "WeightRegularizer"
        and "l1" in obj
        and "l2" in obj
    ):
        try:
            l1 = float(obj.get("l1", 0.0) or 0.0)
            l2 = float(obj.get("l2", 0.0) or 0.0)
        except Exception:
            l1 = 0.0
            l2 = 0.0
        return {"class_name": "L1L2", "config": {"l1": l1, "l2": l2}}

    return {k: _convert_legacy_keras_config(v) for k, v in obj.items()}


def _read_json_with_legacy_fixes(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    data = _convert_legacy_keras_config(data)
    return json.dumps(data)


class RamboPredictor:
    def __init__(self, model_path, x_train_mean_path):
        from keras.models import load_model
        from skimage.exposure import rescale_intensity

        self._rescale_intensity = rescale_intensity
        self.model = load_model(model_path, custom_objects={"Merge": LegacyMerge})
        self.model.compile(optimizer="adam", loss="mse")
        self.x_mean = np.load(x_train_mean_path)
        self.mean_angle = np.array([-0.004179079], dtype=np.float32)

        self.img0 = None
        self.state = deque(maxlen=2)

    def reset(self):
        self.img0 = None
        self.state.clear()

    def _preprocess_gray(self, img_rgb):
        from PIL import Image

        pil = Image.fromarray(img_rgb)
        pil = pil.convert("L")
        pil = pil.resize((256, 192))
        arr = np.asarray(pil)
        return arr.reshape((192, 256, 1)).astype(np.float32)

    def predict(self, img_rgb):
        img1 = self._preprocess_gray(img_rgb)

        if self.img0 is None:
            self.img0 = img1
            return float(self.mean_angle[0])

        if len(self.state) < 1:
            img = img1 - self.img0
            img = self._rescale_intensity(img, in_range=(-255, 255), out_range=(0, 255))
            img = np.array(img, dtype=np.uint8)
            self.state.append(img)
            self.img0 = img1
            return float(self.mean_angle[0])

        img = img1 - self.img0
        img = self._rescale_intensity(img, in_range=(-255, 255), out_range=(0, 255))
        img = np.array(img, dtype=np.uint8)
        self.state.append(img)
        self.img0 = img1

        x = np.concatenate(self.state, axis=-1)
        x = x[:, :, ::-1]
        x = np.expand_dims(x, axis=0)
        x = x.astype("float32")
        x -= self.x_mean
        x /= 255.0
        return float(self.model.predict(x)[0][0])


class ChauffeurPredictor:
    def __init__(
        self,
        cnn_json_path,
        cnn_weights_path,
        lstm_json_path,
        lstm_weights_path,
        *,
        timesteps=100,
        scale=16.0,
    ):
        import cv2
        from keras import backend as K
        from keras.models import Model, model_from_json

        self._cv2 = cv2
        self.scale = float(scale)
        self.timesteps = int(timesteps)
        K.set_learning_phase(0)

        cnn = model_from_json(
            _read_json_with_legacy_fixes(cnn_json_path),
            custom_objects={"Merge": LegacyMerge},
        )
        cnn.load_weights(cnn_weights_path)
        self.cnn = cnn
        self.encoder = Model(inputs=cnn.input, outputs=cnn.layers[-2].output)

        lstm = model_from_json(
            _read_json_with_legacy_fixes(lstm_json_path),
            custom_objects={"Merge": LegacyMerge},
        )
        lstm.load_weights(lstm_weights_path)
        self.lstm = lstm

        self._steps = deque(maxlen=self.timesteps)

    def reset(self):
        self._steps.clear()

    def _preprocess(self, img_rgb):
        cv2 = self._cv2
        img = cv2.resize(img_rgb, (320, 240))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        img = img[120:240, :, :]
        img[:, :, 0] = cv2.equalizeHist(img[:, :, 0])
        img = ((img - (255.0 / 2)) / 255.0)
        return img

    def predict(self, img_rgb):
        img = self._preprocess(img_rgb)
        feats = self.encoder.predict_on_batch(img.reshape((1, 120, 320, 3)))
        feats_vec = np.asarray(feats).reshape(-1)

        if not len(self._steps):
            for _ in range(self.timesteps):
                self._steps.append(feats_vec)
        else:
            self._steps.append(feats_vec)

        feat_dim = int(feats_vec.shape[0])
        timestepped_x = np.empty((1, self.timesteps, feat_dim), dtype=np.float32)
        for i, f in enumerate(self._steps):
            timestepped_x[0, i] = f
        return float(self.lstm.predict_on_batch(timestepped_x)[0, 0] / self.scale)


class KomandaPredictor:
    def __init__(self, metagraph_file, checkpoint_dir, *, left_context=5):
        import cv2
        import tensorflow as tf

        tf.compat.v1.disable_eager_execution()

        self.left_context = int(left_context)
        self._cv2 = cv2
        self.graph = tf.Graph()
        with self.graph.as_default():
            saver = tf.compat.v1.train.import_meta_graph(metagraph_file)
            ckpt = tf.train.latest_checkpoint(checkpoint_dir)
            if ckpt is None:
                raise RuntimeError(f"No checkpoint found in dir: {checkpoint_dir}")

        self.session = tf.compat.v1.Session(graph=self.graph)
        saver.restore(self.session, ckpt)

        self.input_images = deque()
        self.internal_state = []

        self.input_tensors = [
            self.graph.get_tensor_by_name("input_images:0"),
            self.graph.get_tensor_by_name("controller_initial_state_0:0"),
            self.graph.get_tensor_by_name("controller_initial_state_1:0"),
            self.graph.get_tensor_by_name("controller_initial_state_2:0"),
        ]

        expected_h = None
        expected_w = None
        try:
            shape = self.input_tensors[0].shape.as_list()
            if shape and len(shape) >= 4:
                expected_h = shape[1]
                expected_w = shape[2]
        except Exception:
            pass
        self._expected_hw = (expected_h, expected_w)
        self.output_tensors = [
            self.graph.get_tensor_by_name("output_steering:0"),
            self.graph.get_tensor_by_name("controller_final_state_0:0"),
            self.graph.get_tensor_by_name("controller_final_state_1:0"),
            self.graph.get_tensor_by_name("controller_final_state_2:0"),
        ]

    def reset(self):
        self.input_images.clear()
        self.internal_state = []

    def predict(self, img_rgb):
        exp_h, exp_w = self._expected_hw
        if exp_h is not None and exp_w is not None:
            if img_rgb.shape[0] != exp_h or img_rgb.shape[1] != exp_w:
                img_rgb = self._cv2.resize(img_rgb, (int(exp_w), int(exp_h)))

        if len(self.input_images) == 0:
            self.input_images.extend([img_rgb] * (self.left_context + 1))
        else:
            self.input_images.popleft()
            self.input_images.append(img_rgb)

        input_images_tensor = np.stack(self.input_images)
        if not self.internal_state:
            feed_dict = {self.input_tensors[0]: input_images_tensor}
        else:
            feed_dict = dict(zip(self.input_tensors, [input_images_tensor] + self.internal_state))

        steering, c0, c1, c2 = self.session.run(self.output_tensors, feed_dict=feed_dict)
        self.internal_state = [c0, c1, c2]
        return float(steering[0][0])


class AutumnPredictor:
    def __init__(self, cnn_meta_path, cnn_weights_path):
        import cv2
        import tensorflow as tf

        tf.compat.v1.disable_eager_execution()

        self._cv2 = cv2
        self.graph = tf.Graph()
        with self.graph.as_default():
            saver = tf.compat.v1.train.import_meta_graph(cnn_meta_path)

        self.session = tf.compat.v1.Session(graph=self.graph)
        saver.restore(self.session, cnn_weights_path)

        self.fc3 = self.graph.get_tensor_by_name("fc3/mul:0")
        self.y = self.graph.get_tensor_by_name("y:0")
        self.x = self.graph.get_tensor_by_name("x:0")
        self.keep_prob = self.graph.get_tensor_by_name("keep_prob:0")

        self.prev_image = None
        self.last = []

    def reset(self):
        self.prev_image = None
        self.last = []

    def _process(self, img_rgb):
        cv2 = self._cv2

        prev_image = self.prev_image if self.prev_image is not None else img_rgb
        self.prev_image = img_rgb

        prev = cv2.cvtColor(prev_image, cv2.COLOR_RGB2GRAY)
        nxt = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        flow = cv2.calcOpticalFlowFarneback(prev, nxt, None, 0.5, 3, 15, 3, 5, 1.2, 0)

        self.last.append(flow)
        if len(self.last) > 4:
            self.last.pop(0)

        weights = [1, 1, 2, 2]
        last = list(self.last)
        for i in range(len(last)):
            last[i] = last[i] * weights[i]

        weight_sum = float(sum(weights[: len(last)]))
        avg_flow = sum(last) / weight_sum
        mag, ang = cv2.cartToPolar(avg_flow[..., 0], avg_flow[..., 1])

        hsv = np.zeros_like(prev_image)
        hsv[..., 1] = 255
        hsv[..., 0] = ang * 180 / np.pi / 2
        hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        return rgb

    def predict(self, img_rgb):
        img = self._process(img_rgb)

        crop = img[-400:] if img.shape[0] > 400 else img
        crop = self._cv2.resize(crop, (200, 66))
        image = crop.astype(np.float32) / 255.0

        feed = {self.x: [image], self.keep_prob: 1.0}
        output = self.session.run(self.y, feed_dict=feed)
        return float(output[0][0])


def calc_rmse(model_predict, frames_iter, *, print_every=50):
    mse = 0.0
    count = 0
    for frame_id, img, gt in frames_iter:
        pred = model_predict(img)
        err = gt - pred
        mse += float(err * err)
        count += 1
        if print_every and count % print_every == 0:
            rmse = math.sqrt(mse / count)
            print(f"{count}: rmse={rmse}")
    if count == 0:
        raise RuntimeError("No frames evaluated (check paths / csv / images).")
    return math.sqrt(mse / count)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=["rambo", "chauffeur", "komanda", "autumn"])
    parser.add_argument("--images-dir", required=True)
    parser.add_argument("--steering-csv", required=True)

    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--print-every", type=int, default=50)

    parser.add_argument("--rambo-model", type=str, default=None)
    parser.add_argument("--rambo-mean", type=str, default=None)

    parser.add_argument("--chauffeur-cnn-json", type=str, default=None)
    parser.add_argument("--chauffeur-cnn-weights", type=str, default=None)
    parser.add_argument("--chauffeur-lstm-json", type=str, default=None)
    parser.add_argument("--chauffeur-lstm-weights", type=str, default=None)

    parser.add_argument("--komanda-metagraph", type=str, default=None)
    parser.add_argument("--komanda-checkpoint-dir", type=str, default=None)

    parser.add_argument("--autumn-cnn-meta", type=str, default=None)
    parser.add_argument("--autumn-cnn-weights", type=str, default=None)

    args = parser.parse_args()

    frames = iter_ch2_frames(
        args.images_dir,
        args.steering_csv,
        stride=args.stride,
        max_frames=args.max_frames,
        start_index=args.start_index,
    )

    if args.model == "rambo":
        if not args.rambo_model or not args.rambo_mean:
            raise SystemExit("rambo requires --rambo-model and --rambo-mean")
        predictor = RamboPredictor(args.rambo_model, args.rambo_mean)
        rmse = calc_rmse(predictor.predict, frames, print_every=args.print_every)
        print(f"rmse={rmse}")
        return

    if args.model == "chauffeur":
        required = [
            args.chauffeur_cnn_json,
            args.chauffeur_cnn_weights,
            args.chauffeur_lstm_json,
            args.chauffeur_lstm_weights,
        ]
        if any(x is None for x in required):
            raise SystemExit(
                "chauffeur requires --chauffeur-cnn-json --chauffeur-cnn-weights --chauffeur-lstm-json --chauffeur-lstm-weights"
            )
        predictor = ChauffeurPredictor(
            args.chauffeur_cnn_json,
            args.chauffeur_cnn_weights,
            args.chauffeur_lstm_json,
            args.chauffeur_lstm_weights,
        )
        rmse = calc_rmse(predictor.predict, frames, print_every=args.print_every)
        print(f"rmse={rmse}")
        return

    if args.model == "komanda":
        if not args.komanda_metagraph or not args.komanda_checkpoint_dir:
            raise SystemExit("komanda requires --komanda-metagraph and --komanda-checkpoint-dir")
        predictor = KomandaPredictor(args.komanda_metagraph, args.komanda_checkpoint_dir)
        rmse = calc_rmse(predictor.predict, frames, print_every=args.print_every)
        print(f"rmse={rmse}")
        return

    if args.model == "autumn":
        if not args.autumn_cnn_meta or not args.autumn_cnn_weights:
            raise SystemExit("autumn requires --autumn-cnn-meta and --autumn-cnn-weights")
        predictor = AutumnPredictor(args.autumn_cnn_meta, args.autumn_cnn_weights)
        rmse = calc_rmse(predictor.predict, frames, print_every=args.print_every)
        print(f"rmse={rmse}")
        return


if __name__ == "__main__":
    main()
