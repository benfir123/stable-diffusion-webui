import re

import gradio as gr
from fastapi import FastAPI

import network
import networks
import lora  # noqa:F401
import lora_patches
import extra_networks_lora
import ui_extra_networks_lora
from modules import script_callbacks, ui_extra_networks, extra_networks, shared


def unload():
    networks.originals.undo()


def before_ui():
    ui_extra_networks.register_page(ui_extra_networks_lora.ExtraNetworksPageLora())

    networks.extra_network_lora = extra_networks_lora.ExtraNetworkLora()
    extra_networks.register_extra_network(networks.extra_network_lora)
    extra_networks.register_extra_network_alias(networks.extra_network_lora, "lyco")


networks.originals = lora_patches.LoraPatches()

script_callbacks.on_model_loaded(networks.assign_network_names_to_compvis_modules)
script_callbacks.on_script_unloaded(unload)
script_callbacks.on_before_ui(before_ui)
script_callbacks.on_infotext_pasted(networks.infotext_pasted)


shared.options_templates.update(shared.options_section(('extra_networks', "เครือข่ายเพิ่มเติม"), {
    "sd_lora": shared.OptionInfo("None", "เพิ่มเครือข่ายลงในคำสั่ง", gr.Dropdown, lambda: {"choices": ["None", *networks.available_networks]}, refresh=networks.list_available_networks),
    "lora_preferred_name": shared.OptionInfo("Alias from file", "เมื่อเพิ่มลงในคำสั่ง, อ้างอิงถึง Lora โดยใช้", gr.Radio, {"choices": ["Alias from file", "Filename"]}),
    "lora_add_hashes_to_infotext": shared.OptionInfo(True, "เพิ่มแฮชของ Lora ลงใน infotext"),
    "lora_bundled_ti_to_infotext": shared.OptionInfo(True, "เพิ่มชื่อ Lora เป็น TI hashes สำหรับ Textual Inversion ที่บันเดิล").info('"เพิ่ม Textual Inversion hashes ลงใน infotext" ต้องเปิดใช้งาน'),
    "lora_show_all": shared.OptionInfo(False, "แสดงทุกเครือข่ายบนหน้า Lora เสมอ").info("ไม่เช่นนั้น, เครือข่ายที่ตรวจพบว่าไม่เข้ากันกับเวอร์ชันของ Stable Diffusion จะถูกซ่อน"),
    "lora_hide_unknown_for_versions": shared.OptionInfo([], "ซ่อนเครือข่ายสำหรับเวอร์ชันที่ไม่รู้จักสำหรับรุ่นของโมเดล", gr.CheckboxGroup, {"choices": ["SD1", "SD2", "SDXL"]}),
    "lora_in_memory_limit": shared.OptionInfo(0, "จำนวนเครือข่าย Lora ที่เก็บในแคชในหน่วยความจำ", gr.Number, {"precision": 0}),
    "lora_not_found_warning_console": shared.OptionInfo(False, "แสดงคำเตือน Lora ไม่พบในคอนโซล"),
    "lora_not_found_gradio_warning": shared.OptionInfo(False, "แสดงคำเตือน Lora ไม่พบในหน้าต่างป๊อปอัพของเว็บ UI"),
}))


shared.options_templates.update(shared.options_section(('compatibility', "ความเข้ากันได้"), {
    "lora_functional": shared.OptionInfo(False, "Lora/เครือข่าย: ใช้วิธีเก่าที่ใช้เวลานานเมื่อมี Lora หลายตัวที่ทำงานพร้อมกันและให้ผลลัพธ์เหมือนกับส่วนขยาย kohya-ss/sd-webui-additional-networks"),
}))


def create_lora_json(obj: network.NetworkOnDisk):
    return {
        "name": obj.name,
        "alias": obj.alias,
        "path": obj.filename,
        "metadata": obj.metadata,
    }


def api_networks(_: gr.Blocks, app: FastAPI):
    @app.get("/sdapi/v1/loras")
    async def get_loras():
        return [create_lora_json(obj) for obj in networks.available_networks.values()]

    @app.post("/sdapi/v1/refresh-loras")
    async def refresh_loras():
        return networks.list_available_networks()


script_callbacks.on_app_started(api_networks)

re_lora = re.compile("<lora:([^:]+):")


def infotext_pasted(infotext, d):
    hashes = d.get("Lora hashes")
    if not hashes:
        return

    hashes = [x.strip().split(':', 1) for x in hashes.split(",")]
    hashes = {x[0].strip().replace(",", ""): x[1].strip() for x in hashes}

    def network_replacement(m):
        alias = m.group(1)
        shorthash = hashes.get(alias)
        if shorthash is None:
            return m.group(0)

        network_on_disk = networks.available_network_hash_lookup.get(shorthash)
        if network_on_disk is None:
            return m.group(0)

        return f'<lora:{network_on_disk.get_alias()}:'

    d["Prompt"] = re.sub(re_lora, network_replacement, d["Prompt"])


script_callbacks.on_infotext_pasted(infotext_pasted)

shared.opts.onchange("lora_in_memory_limit", networks.purge_networks_from_memory)
