from modules import scripts_postprocessing, ui_components, deepbooru, shared
import gradio as gr


class ScriptPostprocessingCeption(scripts_postprocessing.ScriptPostprocessing):
    name = "Caption"
    order = 4040

    def ui(self):
        with ui_components.InputAccordion(False, label="แคพชั่น") as enable:
            option = gr.CheckboxGroup(value=["Deepbooru"], choices=["Deepbooru", "BLIP"], show_label=False)

        return {
            "enable": enable,
            "option": option,
        }

    def process(self, pp: scripts_postprocessing.PostprocessedImage, enable, option):
        if not enable:
            return

        captions = [pp.caption]

        if "Deepbooru" in option:
            captions.append(deepbooru.model.tag(pp.image))

        if "BLIP" in option:
            captions.append(shared.interrogator.interrogate(pp.image.convert("RGB")))

        pp.caption = ", ".join([x for x in captions if x])
