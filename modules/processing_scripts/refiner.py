import gradio as gr

from modules import scripts, sd_models
from modules.infotext_utils import PasteField
from modules.ui_common import create_refresh_button
from modules.ui_components import InputAccordion


class ScriptRefiner(scripts.ScriptBuiltinUI):
    section = "accordions"
    create_group = False

    def __init__(self):
        pass

    def title(self):
        return "Refiner"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with InputAccordion(False, label="ตัวปรับแต่ง", elem_id=self.elem_id("enable")) as enable_refiner:
            with gr.Row():
                refiner_checkpoint = gr.Dropdown(label='เช็คพอยต์', elem_id=self.elem_id("checkpoint"), choices=sd_models.checkpoint_tiles(), value='', tooltip="สลับไปยังโมเดลอื่นระหว่างการสร้างภาพ")
                create_refresh_button(refiner_checkpoint, sd_models.list_models, lambda: {"choices": sd_models.checkpoint_tiles()}, self.elem_id("checkpoint_refresh"))

                refiner_switch_at = gr.Slider(value=0.8, label="สลับที่", minimum=0.01, maximum=1.0, step=0.01, elem_id=self.elem_id("switch_at"), tooltip="สัดส่วนของขั้นตอนการสร้างภาพที่จะสลับไปใช้โมเดล refiner; 1=ไม่สลับ, 0.5=สลับกลางทาง")

        def lookup_checkpoint(title):
            info = sd_models.get_closet_checkpoint_match(title)
            return None if info is None else info.title

        self.infotext_fields = [
            PasteField(enable_refiner, lambda d: 'Refiner' in d),
            PasteField(refiner_checkpoint, lambda d: lookup_checkpoint(d.get('Refiner')), api="refiner_checkpoint"),
            PasteField(refiner_switch_at, 'Refiner switch at', api="refiner_switch_at"),
        ]

        return enable_refiner, refiner_checkpoint, refiner_switch_at

    def setup(self, p, enable_refiner, refiner_checkpoint, refiner_switch_at):
        # the actual implementation is in sd_samplers_common.py, apply_refiner

        if not enable_refiner or refiner_checkpoint in (None, "", "None"):
            p.refiner_checkpoint = None
            p.refiner_switch_at = None
        else:
            p.refiner_checkpoint = refiner_checkpoint
            p.refiner_switch_at = refiner_switch_at
