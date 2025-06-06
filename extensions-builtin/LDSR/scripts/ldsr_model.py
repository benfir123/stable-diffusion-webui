import os

from modules.modelloader import load_file_from_url
from modules.upscaler import Upscaler, UpscalerData
from ldsr_model_arch import LDSR
from modules import shared, script_callbacks, errors
import sd_hijack_autoencoder  # noqa: F401
import sd_hijack_ddpm_v1  # noqa: F401


class UpscalerLDSR(Upscaler):
    def __init__(self, user_path):
        self.name = "LDSR"
        self.user_path = user_path
        self.model_url = "https://heibox.uni-heidelberg.de/f/578df07c8fc04ffbadf3/?dl=1"
        self.yaml_url = "https://heibox.uni-heidelberg.de/f/31a76b13ea27482981b4/?dl=1"
        super().__init__()
        scaler_data = UpscalerData("LDSR", None, self)
        self.scalers = [scaler_data]

    def load_model(self, path: str):
        # Remove incorrect project.yaml file if too big
        yaml_path = os.path.join(self.model_path, "project.yaml")
        old_model_path = os.path.join(self.model_path, "model.pth")
        new_model_path = os.path.join(self.model_path, "model.ckpt")

        local_model_paths = self.find_models(ext_filter=[".ckpt", ".safetensors"])
        local_ckpt_path = next(iter([local_model for local_model in local_model_paths if local_model.endswith("model.ckpt")]), None)
        local_safetensors_path = next(iter([local_model for local_model in local_model_paths if local_model.endswith("model.safetensors")]), None)
        local_yaml_path = next(iter([local_model for local_model in local_model_paths if local_model.endswith("project.yaml")]), None)

        if os.path.exists(yaml_path):
            statinfo = os.stat(yaml_path)
            if statinfo.st_size >= 10485760:
                print("Removing invalid LDSR YAML file.")
                os.remove(yaml_path)

        if os.path.exists(old_model_path):
            print("Renaming model from model.pth to model.ckpt")
            os.rename(old_model_path, new_model_path)

        if local_safetensors_path is not None and os.path.exists(local_safetensors_path):
            model = local_safetensors_path
        else:
            model = local_ckpt_path or load_file_from_url(self.model_url, model_dir=self.model_download_path, file_name="model.ckpt")

        yaml = local_yaml_path or load_file_from_url(self.yaml_url, model_dir=self.model_download_path, file_name="project.yaml")

        return LDSR(model, yaml)

    def do_upscale(self, img, path):
        try:
            ldsr = self.load_model(path)
        except Exception:
            errors.report(f"Failed loading LDSR model {path}", exc_info=True)
            return img
        ddim_steps = shared.opts.ldsr_steps
        return ldsr.super_resolution(img, ddim_steps, self.scale)


def on_ui_settings():
    import gradio as gr

    shared.opts.add_option("ldsr_steps", shared.OptionInfo(100, "ขั้นตอนการประมวลผล LDSR จำนวนต่ำ = เร็วขึ้น", gr.Slider, {"minimum": 1, "maximum": 200, "step": 1}, section=('upscaling', "การขยายภาพ")))
    shared.opts.add_option("ldsr_cached", shared.OptionInfo(False, "แคชโมเดล LDSR ในหน่วยความจำ", gr.Checkbox, {"interactive": True}, section=('upscaling', "การขยายภาพ")))


script_callbacks.on_ui_settings(on_ui_settings)
