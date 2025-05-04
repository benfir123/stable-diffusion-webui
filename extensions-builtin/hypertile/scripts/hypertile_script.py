import hypertile
from modules import scripts, script_callbacks, shared


class ScriptHypertile(scripts.Script):
    name = "Hypertile"

    def title(self):
        return self.name

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def process(self, p, *args):
        hypertile.set_hypertile_seed(p.all_seeds[0])

        configure_hypertile(p.width, p.height, enable_unet=shared.opts.hypertile_enable_unet)

        self.add_infotext(p)

    def before_hr(self, p, *args):

        enable = shared.opts.hypertile_enable_unet_secondpass or shared.opts.hypertile_enable_unet

        # exclusive hypertile seed for the second pass
        if enable:
            hypertile.set_hypertile_seed(p.all_seeds[0])

        configure_hypertile(p.hr_upscale_to_x, p.hr_upscale_to_y, enable_unet=enable)

        if enable and not shared.opts.hypertile_enable_unet:
            p.extra_generation_params["Hypertile U-Net second pass"] = True

            self.add_infotext(p, add_unet_params=True)

    def add_infotext(self, p, add_unet_params=False):
        def option(name):
            value = getattr(shared.opts, name)
            default_value = shared.opts.get_default(name)
            return None if value == default_value else value

        if shared.opts.hypertile_enable_unet:
            p.extra_generation_params["Hypertile U-Net"] = True

        if shared.opts.hypertile_enable_unet or add_unet_params:
            p.extra_generation_params["Hypertile U-Net max depth"] = option('hypertile_max_depth_unet')
            p.extra_generation_params["Hypertile U-Net max tile size"] = option('hypertile_max_tile_unet')
            p.extra_generation_params["Hypertile U-Net swap size"] = option('hypertile_swap_size_unet')

        if shared.opts.hypertile_enable_vae:
            p.extra_generation_params["Hypertile VAE"] = True
            p.extra_generation_params["Hypertile VAE max depth"] = option('hypertile_max_depth_vae')
            p.extra_generation_params["Hypertile VAE max tile size"] = option('hypertile_max_tile_vae')
            p.extra_generation_params["Hypertile VAE swap size"] = option('hypertile_swap_size_vae')


def configure_hypertile(width, height, enable_unet=True):
    hypertile.hypertile_hook_model(
        shared.sd_model.first_stage_model,
        width,
        height,
        swap_size=shared.opts.hypertile_swap_size_vae,
        max_depth=shared.opts.hypertile_max_depth_vae,
        tile_size_max=shared.opts.hypertile_max_tile_vae,
        enable=shared.opts.hypertile_enable_vae,
    )

    hypertile.hypertile_hook_model(
        shared.sd_model.model,
        width,
        height,
        swap_size=shared.opts.hypertile_swap_size_unet,
        max_depth=shared.opts.hypertile_max_depth_unet,
        tile_size_max=shared.opts.hypertile_max_tile_unet,
        enable=enable_unet,
        is_sdxl=shared.sd_model.is_sdxl
    )


def on_ui_settings():
    import gradio as gr

    options = {
    "hypertile_explanation": shared.OptionHTML("""
<a href='https://github.com/tfernd/HyperTile'>Hypertile</a> ปรับปรุงชั้น self-attention ภายในโมเดล U-Net และ VAE,
ทำให้เวลาในการคำนวณลดลงตั้งแต่ 1 ถึง 4 เท่า ยิ่งขนาดของภาพที่สร้างขึ้นใหญ่ขึ้น, ผลประโยชน์ก็จะยิ่งมากขึ้น
    """),

    "hypertile_enable_unet": shared.OptionInfo(False, "เปิดใช้งาน Hypertile U-Net", infotext="Hypertile U-Net").info("เปิดใช้งาน hypertile สำหรับทุกโหมด รวมถึงการแก้ไข hires fix second pass; การเปลี่ยนแปลงที่เห็นได้ชัดในรายละเอียดของภาพที่สร้างขึ้น"),
    "hypertile_enable_unet_secondpass": shared.OptionInfo(False, "เปิดใช้งาน Hypertile U-Net สำหรับการแก้ไข hires fix second pass", infotext="Hypertile U-Net second pass").info("เปิดใช้งาน hypertile สำหรับการแก้ไข hires fix second pass เท่านั้น - ไม่ขึ้นอยู่กับการตั้งค่าด้านบน"),
    "hypertile_max_depth_unet": shared.OptionInfo(3, "ความลึกสูงสุดของ Hypertile U-Net", gr.Slider, {"minimum": 0, "maximum": 3, "step": 1}, infotext="ความลึกสูงสุดของ Hypertile U-Net").info("ค่าใหญ่ขึ้น = จะมีชั้นของเครือข่ายประสาทมากขึ้นที่ได้รับผลกระทบ; ผลกระทบต่อประสิทธิภาพจะน้อย"),
    "hypertile_max_tile_unet": shared.OptionInfo(256, "ขนาดสูงสุดของ Tile ใน Hypertile U-Net", gr.Slider, {"minimum": 0, "maximum": 512, "step": 16}, infotext="ขนาดสูงสุดของ Tile ใน Hypertile U-Net").info("ค่าใหญ่ขึ้น = ประสิทธิภาพจะลดลง"),
    "hypertile_swap_size_unet": shared.OptionInfo(3, "ขนาดการสลับของ Hypertile U-Net", gr.Slider, {"minimum": 0, "maximum": 64, "step": 1}, infotext="ขนาดการสลับของ Hypertile U-Net"),
    "hypertile_enable_vae": shared.OptionInfo(False, "เปิดใช้งาน Hypertile VAE", infotext="Hypertile VAE").info("การเปลี่ยนแปลงที่เกิดขึ้นในภาพที่สร้างขึ้นจะน้อย"),
    "hypertile_max_depth_vae": shared.OptionInfo(3, "ความลึกสูงสุดของ Hypertile VAE", gr.Slider, {"minimum": 0, "maximum": 3, "step": 1}, infotext="ความลึกสูงสุดของ Hypertile VAE"),
    "hypertile_max_tile_vae": shared.OptionInfo(128, "ขนาดสูงสุดของ Tile ใน Hypertile VAE", gr.Slider, {"minimum": 0, "maximum": 512, "step": 16}, infotext="ขนาดสูงสุดของ Tile ใน Hypertile VAE"),
    "hypertile_swap_size_vae": shared.OptionInfo(3, "ขนาดการสลับของ Hypertile VAE", gr.Slider, {"minimum": 0, "maximum": 64, "step": 1}, infotext="ขนาดการสลับของ Hypertile VAE"),
}

    for name, opt in options.items():
        opt.section = ('hypertile', "Hypertile")
        shared.opts.add_option(name, opt)


def add_axis_options():
    xyz_grid = [x for x in scripts.scripts_data if x.script_class.__module__ == "xyz_grid.py"][0].module
    xyz_grid.axis_options.extend([
        xyz_grid.AxisOption("[Hypertile] Unet First pass Enabled", str, xyz_grid.apply_override('hypertile_enable_unet', boolean=True), choices=xyz_grid.boolean_choice(reverse=True)),
        xyz_grid.AxisOption("[Hypertile] Unet Second pass Enabled", str, xyz_grid.apply_override('hypertile_enable_unet_secondpass', boolean=True), choices=xyz_grid.boolean_choice(reverse=True)),
        xyz_grid.AxisOption("[Hypertile] Unet Max Depth", int, xyz_grid.apply_override("hypertile_max_depth_unet"), confirm=xyz_grid.confirm_range(0, 3, '[Hypertile] Unet Max Depth'), choices=lambda: [str(x) for x in range(4)]),
        xyz_grid.AxisOption("[Hypertile] Unet Max Tile Size", int, xyz_grid.apply_override("hypertile_max_tile_unet"), confirm=xyz_grid.confirm_range(0, 512, '[Hypertile] Unet Max Tile Size')),
        xyz_grid.AxisOption("[Hypertile] Unet Swap Size", int, xyz_grid.apply_override("hypertile_swap_size_unet"), confirm=xyz_grid.confirm_range(0, 64, '[Hypertile] Unet Swap Size')),
        xyz_grid.AxisOption("[Hypertile] VAE Enabled", str, xyz_grid.apply_override('hypertile_enable_vae', boolean=True), choices=xyz_grid.boolean_choice(reverse=True)),
        xyz_grid.AxisOption("[Hypertile] VAE Max Depth", int, xyz_grid.apply_override("hypertile_max_depth_vae"), confirm=xyz_grid.confirm_range(0, 3, '[Hypertile] VAE Max Depth'), choices=lambda: [str(x) for x in range(4)]),
        xyz_grid.AxisOption("[Hypertile] VAE Max Tile Size", int, xyz_grid.apply_override("hypertile_max_tile_vae"), confirm=xyz_grid.confirm_range(0, 512, '[Hypertile] VAE Max Tile Size')),
        xyz_grid.AxisOption("[Hypertile] VAE Swap Size", int, xyz_grid.apply_override("hypertile_swap_size_vae"), confirm=xyz_grid.confirm_range(0, 64, '[Hypertile] VAE Swap Size')),
    ])


script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_before_ui(add_axis_options)
