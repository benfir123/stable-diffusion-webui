import os
import gradio as gr

from modules import (
    localization,
    ui_components,
    shared_items,
    shared,
    interrogate,
    shared_gradio_themes,
    util,
    sd_emphasis,
)
from modules.paths_internal import (
    models_path,
    script_path,
    data_path,
    sd_configs_path,
    sd_default_config,
    sd_model_file,
    default_sd_model_file,
    extensions_dir,
    extensions_builtin_dir,
    default_output_dir,
)  # noqa: F401
from modules.shared_cmd_options import cmd_opts
from modules.options import options_section, OptionInfo, OptionHTML, categories

options_templates = {}
hide_dirs = shared.hide_dirs

restricted_opts = {
    "samples_filename_pattern",
    "directories_filename_pattern",
    "outdir_samples",
    "outdir_txt2img_samples",
    "outdir_img2img_samples",
    "outdir_extras_samples",
    "outdir_grids",
    "outdir_txt2img_grids",
    "outdir_save",
    "outdir_init_images",
    "temp_dir",
    "clean_temp_dir_at_start",
}

categories.register_category("saving", "การบันทึกภาพ")
categories.register_category("sd", "SIIN AI")
categories.register_category("ui", "ส่วนติดต่อผู้ใช้")
categories.register_category("system", "ระบบ")
categories.register_category("postprocessing", "การประมวลผลหลังสร้างภาพ")
categories.register_category("training", "การฝึกฝน")


options_templates.update(
    options_section(
        ('saving-images', "การบันทึกรูปภาพ/ตารางภาพ", "saving"),
        {
            "samples_save": OptionInfo(True, "บันทึกรูปภาพที่สร้างทั้งหมดเสมอ"),
            "samples_format": OptionInfo('png', 'รูปแบบไฟล์ของรูปภาพ'),
            "samples_filename_pattern": OptionInfo(
                "", "รูปแบบชื่อไฟล์ของรูปภาพ", component_args=hide_dirs
            ).link(
                "wiki",
                "https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Images-Filename-Name-and-Subdirectory",
            ),
            "save_images_add_number": OptionInfo(
                True, "เพิ่มตัวเลขลงในชื่อไฟล์เมื่อบันทึก", component_args=hide_dirs
            ),
            "save_images_replace_action": OptionInfo(
                "Replace",
                "การบันทึกรูปภาพทับไฟล์ที่มีอยู่",
                gr.Radio,
                {"choices": ["Replace", "Add number suffix"], **hide_dirs},
            ),
            "grid_save": OptionInfo(True, "บันทึกตารางภาพที่สร้างทั้งหมดเสมอ"),
            "grid_format": OptionInfo('png', 'รูปแบบไฟล์ของตารางภาพ'),
            "grid_extended_filename": OptionInfo(
                False, "เพิ่มข้อมูลเพิ่มเติม (seed, prompt) ลงในชื่อไฟล์เมื่อตารางภาพถูกบันทึก"
            ),
            "grid_only_if_multiple": OptionInfo(True, "ไม่บันทึกตารางภาพที่มีเพียงภาพเดียว"),
            "grid_prevent_empty_spots": OptionInfo(
                False, "ป้องกันช่องว่างในตารางภาพ (เมื่อถูกตั้งค่าเป็นตรวจจับอัตโนมัติ)"
            ),
            "grid_zip_filename_pattern": OptionInfo(
                "", "รูปแบบชื่อไฟล์ของไฟล์ zip", component_args=hide_dirs
            ).link(
                "wiki",
                "https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Images-Filename-Name-and-Subdirectory",
            ),
            "n_rows": OptionInfo(
                -1,
                "จำนวนแถวในตารางภาพ; ใช้ -1 เพื่อให้ตรวจจับอัตโนมัติ และ 0 เพื่อให้เหมือนกับขนาด batch",
                gr.Slider,
                {"minimum": -1, "maximum": 16, "step": 1},
            ),
            "font": OptionInfo("", "ฟอนต์สำหรับตารางภาพที่มีข้อความ"),
            "grid_text_active_color": OptionInfo(
                "#000000", "สีข้อความในตารางภาพ", ui_components.FormColorPicker, {}
            ),
            "grid_text_inactive_color": OptionInfo(
                "#999999", "สีข้อความไม่ทำงานในตารางภาพ", ui_components.FormColorPicker, {}
            ),
            "grid_background_color": OptionInfo(
                "#ffffff", "สีพื้นหลังของตารางภาพ", ui_components.FormColorPicker, {}
            ),
            "save_images_before_face_restoration": OptionInfo(False, "บันทึกรูปภาพก่อนการฟื้นฟูใบหน้า"),
            "save_images_before_highres_fix": OptionInfo(False, "บันทึกรูปภาพก่อนการปรับความละเอียดสูง"),
            "save_images_before_color_correction": OptionInfo(False, "บันทึกรูปภาพก่อนแก้ไขสีใน img2img"),
            "save_mask": OptionInfo(False, "สำหรับการวาดซ่อม บันทึกมาสก์แบบเกรย์สเกล"),
            "save_mask_composite": OptionInfo(False, "สำหรับการวาดซ่อม บันทึกภาพผสมที่มีมาสก์"),
            "jpeg_quality": OptionInfo(
                80,
                "คุณภาพของไฟล์ jpeg และ avif ที่บันทึก",
                gr.Slider,
                {"minimum": 1, "maximum": 100, "step": 1},
            ),
            "webp_lossless": OptionInfo(False, "ใช้การบีบอัดแบบไม่สูญเสียสำหรับภาพ webp"),
            "export_for_4chan": OptionInfo(True, "บันทึกภาพขนาดใหญ่เป็น JPG").info(
                "หากขนาดไฟล์เกินขีดจำกัด หรือความกว้างหรือความสูงเกินขีดจำกัด"
            ),
            "img_downscale_threshold": OptionInfo(
                4.0, "ขีดจำกัดขนาดไฟล์สำหรับตัวเลือกด้านบน หน่วยเป็น MB", gr.Number
            ),
            "target_side_length": OptionInfo(
                4000, "ขีดจำกัดความกว้าง/ความสูงสำหรับตัวเลือกด้านบน หน่วยเป็นพิกเซล", gr.Number
            ),
            "img_max_size_mp": OptionInfo(200, "ขนาดภาพสูงสุด", gr.Number).info("หน่วยเป็นเมกะพิกเซล"),
            "use_original_name_batch": OptionInfo(
                True, "ใช้ชื่อไฟล์ต้นฉบับในระหว่างการประมวลผล batch ในแท็บ extras"
            ),
            "use_upscaler_name_as_suffix": OptionInfo(
                False, "ใช้ชื่ออัปสเกลเลอร์เป็นคำต่อท้ายชื่อไฟล์ในแท็บ extras"
            ),
            "save_selected_only": OptionInfo(True, "เมื่อใช้ปุ่ม 'Save' บันทึกเฉพาะภาพที่เลือกไว้"),
            "save_write_log_csv": OptionInfo(True, "เขียน log.csv เมื่อบันทึกรูปภาพด้วยปุ่ม 'Save'"),
            "save_init_img": OptionInfo(False, "บันทึกรูปต้นฉบับเมื่อใช้ img2img"),
            "temp_dir": OptionInfo("", "ไดเรกทอรีสำหรับรูปภาพชั่วคราว; ปล่อยว่างเพื่อใช้ค่าเริ่มต้น"),
            "clean_temp_dir_at_start": OptionInfo(
                False, "ล้างโฟลเดอร์ชั่วคราวที่ไม่ใช่ค่าเริ่มต้นเมื่อเริ่มต้น webui"
            ),
            "save_incomplete_images": OptionInfo(False, "บันทึกรูปภาพที่ยังไม่สมบูรณ์").info(
                "บันทึกรูปภาพที่ถูกขัดจังหวะระหว่างการสร้าง; ถึงจะไม่ถูกบันทึก ก็จะแสดงในหน้าผลลัพธ์ของ webui"
            ),
            "notification_audio": OptionInfo(True, "เล่นเสียงแจ้งเตือนหลังจากการสร้างรูปภาพเสร็จสิ้น")
            .info("ควรมีไฟล์ notification.mp3 อยู่ในไดเรกทอรีหลัก")
            .needs_reload_ui(),
            "notification_volume": OptionInfo(
                100, "ระดับเสียงของเสียงแจ้งเตือน", gr.Slider, {"minimum": 0, "maximum": 100, "step": 1}
            ).info("เป็นเปอร์เซ็นต์"),
        },
    )
)

options_templates.update(
    options_section(
        ('saving-paths', "เส้นทางสำหรับการบันทึก", "saving"),
        {
            "outdir_samples": OptionInfo(
                "",
                "โฟลเดอร์สำหรับบันทึกรูปภาพ; หากเว้นว่างไว้ จะใช้โฟลเดอร์เริ่มต้นด้านล่าง",
                component_args=hide_dirs,
            ),
            "outdir_txt2img_samples": OptionInfo(
                util.truncate_path(os.path.join(default_output_dir, 'txt2img-images')),
                'โฟลเดอร์สำหรับบันทึกรูปภาพ txt2img',
                component_args=hide_dirs,
            ),
            "outdir_img2img_samples": OptionInfo(
                util.truncate_path(os.path.join(default_output_dir, 'img2img-images')),
                'โฟลเดอร์สำหรับบันทึกรูปภาพ img2img',
                component_args=hide_dirs,
            ),
            "outdir_extras_samples": OptionInfo(
                util.truncate_path(os.path.join(default_output_dir, 'extras-images')),
                'โฟลเดอร์สำหรับบันทึกรูปภาพจากแท็บ extras',
                component_args=hide_dirs,
            ),
            "outdir_grids": OptionInfo(
                "",
                "โฟลเดอร์สำหรับบันทึกตารางภาพ; หากเว้นว่างไว้ จะใช้สองโฟลเดอร์ด้านล่าง",
                component_args=hide_dirs,
            ),
            "outdir_txt2img_grids": OptionInfo(
                util.truncate_path(os.path.join(default_output_dir, 'txt2img-grids')),
                'โฟลเดอร์สำหรับบันทึกตารางภาพจาก txt2img',
                component_args=hide_dirs,
            ),
            "outdir_img2img_grids": OptionInfo(
                util.truncate_path(os.path.join(default_output_dir, 'img2img-grids')),
                'โฟลเดอร์สำหรับบันทึกตารางภาพจาก img2img',
                component_args=hide_dirs,
            ),
            "outdir_save": OptionInfo(
                util.truncate_path(os.path.join(data_path, 'log', 'images')),
                "โฟลเดอร์สำหรับบันทึกรูปภาพที่กดปุ่ม Save",
                component_args=hide_dirs,
            ),
            "outdir_init_images": OptionInfo(
                util.truncate_path(os.path.join(default_output_dir, 'init-images')),
                "โฟลเดอร์สำหรับบันทึกรูปภาพเริ่มต้นใน img2img",
                component_args=hide_dirs,
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('saving-to-dirs', "การบันทึกไปยังโฟลเดอร์", "saving"),
        {
            "save_to_dirs": OptionInfo(True, "บันทึกรูปภาพลงในโฟลเดอร์ย่อย"),
            "grid_save_to_dirs": OptionInfo(True, "บันทึกตารางภาพลงในโฟลเดอร์ย่อย"),
            "use_save_to_dirs_for_ui": OptionInfo(
                False, "เมื่อใช้ปุ่ม \"Save\" ให้บันทึกภาพลงในโฟลเดอร์ย่อย"
            ),
            "directories_filename_pattern": OptionInfo(
                "[date]", "รูปแบบชื่อโฟลเดอร์", component_args=hide_dirs
            ).link(
                "wiki",
                "https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Images-Filename-Name-and-Subdirectory",
            ),
            "directories_max_prompt_words": OptionInfo(
                8,
                "จำนวนคำสูงสุดจาก prompt สำหรับ [prompt_words]",
                gr.Slider,
                {"minimum": 1, "maximum": 20, "step": 1, **hide_dirs},
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('upscaling', "การขยายภาพ", "postprocessing"),
        {
            "ESRGAN_tile": OptionInfo(
                192,
                "ขนาดไทล์สำหรับตัวขยายภาพ ESRGAN.",
                gr.Slider,
                {"minimum": 0, "maximum": 512, "step": 16},
            ).info("0 = ไม่แบ่งไทล์"),
            "ESRGAN_tile_overlap": OptionInfo(
                8, "การซ้อนทับไทล์สำหรับ ESRGAN.", gr.Slider, {"minimum": 0, "maximum": 48, "step": 1}
            ).info("ค่าน้อย = มีรอยต่อชัดเจน"),
            "realesrgan_enabled_models": OptionInfo(
                ["R-ESRGAN 4x+", "R-ESRGAN 4x+ Anime6B"],
                "เลือกรุ่น Real-ESRGAN ที่จะแสดงใน UI",
                gr.CheckboxGroup,
                lambda: {"choices": shared_items.realesrgan_models_names()},
            ),
            "dat_enabled_models": OptionInfo(
                ["DAT x2", "DAT x3", "DAT x4"],
                "เลือกรุ่น DAT ที่จะแสดงใน UI",
                gr.CheckboxGroup,
                lambda: {"choices": shared_items.dat_models_names()},
            ),
            "DAT_tile": OptionInfo(
                192, "ขนาดไทล์สำหรับ DAT.", gr.Slider, {"minimum": 0, "maximum": 512, "step": 16}
            ).info("0 = ไม่แบ่งไทล์"),
            "DAT_tile_overlap": OptionInfo(
                8, "การซ้อนทับไทล์สำหรับ DAT.", gr.Slider, {"minimum": 0, "maximum": 48, "step": 1}
            ).info("ค่าน้อย = มีรอยต่อชัดเจน"),
            "upscaler_for_img2img": OptionInfo(
                None,
                "ตัวขยายภาพสำหรับ img2img",
                gr.Dropdown,
                lambda: {"choices": [x.name for x in shared.sd_upscalers]},
            ),
            "set_scale_by_when_changing_upscaler": OptionInfo(
                False, "ตั้งค่าการขยายอัตโนมัติตามชื่อของตัวขยายภาพที่เลือก"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('face-restoration', "การฟื้นฟูใบหน้า", "postprocessing"),
        {
            "face_restoration": OptionInfo(False, "ฟื้นฟูใบหน้า", infotext='Face restoration').info(
                "ใช้โมเดลภายนอกในการฟื้นฟูใบหน้าหลังสร้างภาพ"
            ),
            "face_restoration_model": OptionInfo(
                "CodeFormer",
                "โมเดลฟื้นฟูใบหน้า",
                gr.Radio,
                lambda: {"choices": [x.name() for x in shared.face_restorers]},
            ),
            "code_former_weight": OptionInfo(
                0.5, "น้ำหนักของ CodeFormer", gr.Slider, {"minimum": 0, "maximum": 1, "step": 0.01}
            ).info("0 = ฟื้นฟูมากสุด; 1 = ฟื้นฟูน้อยสุด"),
            "face_restoration_unload": OptionInfo(
                False, "ย้ายโมเดลฟื้นฟูใบหน้าจาก VRAM ไปยัง RAM หลังประมวลผล"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('system', "ระบบ", "system"),
        {
            "auto_launch_browser": OptionInfo(
                "Local",
                "เปิดเว็บเบราว์เซอร์โดยอัตโนมัติเมื่อเริ่มต้น",
                gr.Radio,
                lambda: {"choices": ["Disable", "Local", "Remote"]},
            ),
            "enable_console_prompts": OptionInfo(
                shared.cmd_opts.enable_console_prompts, "แสดงพรอมต์ในคอนโซลเมื่อสร้างภาพ"
            ),
            "show_warnings": OptionInfo(False, "แสดงคำเตือนในคอนโซล").needs_reload_ui(),
            "show_gradio_deprecation_warnings": OptionInfo(
                True, "แสดงคำเตือนของ gradio ที่เลิกใช้งานแล้วในคอนโซล"
            ).needs_reload_ui(),
            "memmon_poll_rate": OptionInfo(
                8,
                "จำนวนครั้งต่อวินาทีในการตรวจสอบการใช้ VRAM",
                gr.Slider,
                {"minimum": 0, "maximum": 40, "step": 1},
            ).info("0 = ปิดการทำงาน"),
            "samples_log_stdout": OptionInfo(False, "พิมพ์ข้อมูลการสร้างภาพทั้งหมดไปยัง stdout เสมอ"),
            "multiple_tqdm": OptionInfo(True, "เพิ่มแถบความคืบหน้าชุดที่สองในคอนโซลสำหรับงานทั้งหมด"),
            "enable_upscale_progressbar": OptionInfo(
                True, "แสดงแถบความคืบหน้าในคอนโซลเมื่อขยายภาพแบบไทล์"
            ),
            "print_hypernet_extra": OptionInfo(False, "พิมพ์ข้อมูลเพิ่มเติมของ hypernetwork ไปยังคอนโซล"),
            "list_hidden_files": OptionInfo(True, "โหลดโมเดล/ไฟล์ในไดเรกทอรีที่ซ่อนอยู่").info(
                "ชื่อไดเรกทอรีเริ่มต้นด้วย \".\" ถือว่าเป็นแบบซ่อน"
            ),
            "disable_mmap_load_safetensors": OptionInfo(
                False, "ปิดการใช้ memmap เมื่อโหลดไฟล์ .safetensors"
            ).info("แก้ปัญหาความช้าในการโหลดในบางกรณี"),
            "hide_ldm_prints": OptionInfo(True, "ซ่อนข้อความที่พิมพ์จากโมดูล ldm/sgm ของ Stability-AI"),
            "dump_stacks_on_signal": OptionInfo(
                False, "พิมพ์ stack trace ก่อนออกจากโปรแกรมเมื่อกด ctrl+c"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('profiler', "โปรไฟล์การประมวลผล", "system"),
        {
            "profiling_explanation": OptionHTML(
                """
การตั้งค่าเหล่านี้จะเปิดใช้ torch profiler เมื่อสร้างภาพ
Profiler ช่วยให้ดูได้ว่าโค้ดส่วนใดใช้ทรัพยากรของเครื่องคอมพิวเตอร์มากที่สุด
ทุกการสร้างภาพจะเขียนโปรไฟล์ลงไฟล์เดียวและจะเขียนทับของเดิม
สามารถดูไฟล์ได้ที่ <a href=\"chrome:tracing\">Chrome</a> หรือเว็บไซต์ <a href=\"https://ui.perfetto.dev/\">Perfetto</a>
คำเตือน: การเขียนโปรไฟล์อาจใช้เวลานานถึง 30 วินาที และไฟล์อาจมีขนาดประมาณ 500MB
"""
            ),
            "profiling_enable": OptionInfo(False, "เปิดใช้การโปรไฟล์"),
            "profiling_activities": OptionInfo(
                ["CPU"], "กิจกรรมที่โปรไฟล์", gr.CheckboxGroup, {"choices": ["CPU", "CUDA"]}
            ),
            "profiling_record_shapes": OptionInfo(True, "บันทึกรูปร่างของข้อมูล"),
            "profiling_profile_memory": OptionInfo(True, "โปรไฟล์การใช้หน่วยความจำ"),
            "profiling_with_stack": OptionInfo(True, "รวม stack ของ python"),
            "profiling_filename": OptionInfo("trace.json", "ชื่อไฟล์โปรไฟล์"),
        },
    )
)

options_templates.update(
    options_section(
        ('API', "API", "system"),
        {
            "api_enable_requests": OptionInfo(
                True, "อนุญาต URL ที่ขึ้นต้นด้วย http:// และ https:// สำหรับรูปภาพใน API", restrict_api=True
            ),
            "api_forbid_local_requests": OptionInfo(
                True, "ไม่อนุญาตให้ใช้ URL ที่ชี้ไปยังทรัพยากรภายในเครื่อง", restrict_api=True
            ),
            "api_useragent": OptionInfo("", "User agent สำหรับการร้องขอผ่าน API", restrict_api=True),
        },
    )
)

options_templates.update(
    options_section(
        ('training', "การฝึก", "training"),
        {
            "unload_models_when_training": OptionInfo(
                False, "ย้าย VAE และ CLIP ไปยัง RAM ขณะฝึก หากเป็นไปได้ เพื่อประหยัด VRAM"
            ),
            "pin_memory": OptionInfo(
                False, "เปิดใช้งาน pin_memory สำหรับ DataLoader ช่วยให้ฝึกเร็วขึ้นเล็กน้อย แต่ใช้หน่วยความจำมากขึ้น"
            ),
            "save_optimizer_state": OptionInfo(
                False,
                "บันทึกสถานะ Optimizer แยกเป็นไฟล์ *.optim การฝึก embedding หรือ HN สามารถดำเนินต่อได้จากไฟล์นี้",
            ),
            "save_training_settings_to_txt": OptionInfo(
                True, "บันทึกค่าการฝึกสำหรับ textual inversion และ hypernet เป็นไฟล์ข้อความทุกครั้งที่เริ่มการฝึก"
            ),
            "dataset_filename_word_regex": OptionInfo("", "Regex สำหรับชื่อไฟล์ข้อมูล"),
            "dataset_filename_join_string": OptionInfo(" ", "ตัวเชื่อมระหว่างคำในชื่อไฟล์"),
            "training_image_repeats_per_epoch": OptionInfo(
                1,
                "จำนวนครั้งที่ใช้ภาพเดียวกันต่อ epoch ใช้สำหรับแสดงเลข epoch เท่านั้น",
                gr.Number,
                {"precision": 0},
            ),
            "training_write_csv_every": OptionInfo(
                500, "บันทึกค่า loss ลงไฟล์ csv ทุก ๆ N ขั้นตอน (0 = ปิดการบันทึก)"
            ),
            "training_xattention_optimizations": OptionInfo(
                False, "ใช้การปรับแต่ง cross attention ขณะฝึก"
            ),
            "training_enable_tensorboard": OptionInfo(False, "เปิดใช้งานการบันทึกผ่าน tensorboard"),
            "training_tensorboard_save_images": OptionInfo(False, "บันทึกรูปภาพที่สร้างใน tensorboard"),
            "training_tensorboard_flush_every": OptionInfo(
                120, "ระยะเวลาการ flush ข้อมูล tensorboard ลงดิสก์ (วินาที)"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('sd', "SIIN AI", "sd"),
        {
            "sd_model_checkpoint": OptionInfo(
                None,
                "เจนโมเดล",
                gr.Dropdown,
                lambda: {
                    "choices": shared_items.list_checkpoint_tiles(
                        shared.opts.sd_checkpoint_dropdown_use_short
                    )
                },
                refresh=shared_items.refresh_checkpoints,
                infotext='Model hash',
            ),
            "sd_checkpoints_limit": OptionInfo(
                1,
                "จำนวน checkpoints สูงสุดที่โหลดพร้อมกัน",
                gr.Slider,
                {"minimum": 1, "maximum": 10, "step": 1},
            ),
            "sd_checkpoints_keep_in_cpu": OptionInfo(True, "เก็บโมเดลอื่นใน RAM แทน VRAM"),
            "sd_checkpoint_cache": OptionInfo(
                0,
                "จำนวน checkpoints ที่แคชไว้ใน RAM",
                gr.Slider,
                {"minimum": 0, "maximum": 10, "step": 1},
            ),
            "sd_unet": OptionInfo(
                "Automatic",
                "SD Unet",
                gr.Dropdown,
                lambda: {"choices": shared_items.sd_unet_items()},
                refresh=shared_items.refresh_unet_list,
            ).info(
                "เลือกโมเดล Unet: Automatic = ใช้ชื่อเดียวกับ checkpoint; None = ใช้ Unet จาก checkpoint"
            ),
            "enable_quantization": OptionInfo(
                False, "เปิด quantization ใน K samplers เพื่อให้ผลลัพธ์คมชัดขึ้น (อาจทำให้ seed เปลี่ยน)"
            ),
            "emphasis": OptionInfo(
                "Original",
                "โหมดการเน้นข้อความ",
                gr.Radio,
                lambda: {"choices": [x.name for x in sd_emphasis.options]},
                infotext="การเน้น",
            ).info(
                "กำหนดระดับความสนใจของโมเดลต่อข้อความ เช่น (more:1.1) หรือ (less:0.9); "
                + sd_emphasis.get_options_descriptions()
            ),
            "enable_batch_seeds": OptionInfo(
                True, "ให้ K-diffusion samplers สร้างภาพชุดเดียวกันใน batch เหมือนกับการสร้างภาพเดี่ยว"
            ),
            "comma_padding_backtrack": OptionInfo(
                20,
                "ขีดจำกัดการ wrap คำใน prompt",
                gr.Slider,
                {"minimum": 0, "maximum": 74, "step": 1},
            ),
            "sdxl_clip_l_skip": OptionInfo(False, "Clip skip สำหรับ SDXL", gr.Checkbox),
            "CLIP_stop_at_last_layers": OptionInfo(
                1,
                "Clip skip",
                gr.Slider,
                {"minimum": 1, "maximum": 12, "step": 1},
                infotext="Clip skip",
            )
            .link(
                "wiki",
                "https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Features#clip-skip",
            )
            .info("ละเว้นเลเยอร์ท้ายสุดของเครือข่าย CLIP; 1 = ไม่ละเว้น, 2 = ละเว้น 1 เลเยอร์"),
            "upcast_attn": OptionInfo(False, "Upcast cross attention เป็น float32"),
            "randn_source": OptionInfo(
                "GPU", "แหล่งสุ่มตัวเลข", gr.Radio, {"choices": ["GPU", "CPU", "NV"]}, infotext="RNG"
            ).info(
                "เปลี่ยน seed อย่างมาก; CPU = ให้ผลเหมือนกันข้ามการ์ดจอ; NV = เหมือนกับบนการ์ด NVIDIA"
            ),
            "tiling": OptionInfo(False, "การทำ tile", infotext='Tiling').info(
                "สร้างภาพที่สามารถนำไปทำ pattern ต่อได้"
            ),
            "hires_fix_refiner_pass": OptionInfo(
                "second pass",
                "Hires fix: ใช้ refiner ในรอบใด",
                gr.Radio,
                {"choices": ["first pass", "second pass", "both passes"]},
                infotext="Hires refiner",
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('sdxl', "SIIN AI XL", "sd"),
        {
            "sdxl_crop_top": OptionInfo(0, "ตำแหน่งครอปด้านบน"),
            "sdxl_crop_left": OptionInfo(0, "ตำแหน่งครอปด้านซ้าย"),
            "sdxl_refiner_low_aesthetic_score": OptionInfo(
                2.5, "คะแนนสุนทรียะต่ำของ SDXL", gr.Number
            ).info("ใช้กับ negative prompt ของ refiner"),
            "sdxl_refiner_high_aesthetic_score": OptionInfo(
                6.0, "คะแนนสุนทรียะสูงของ SDXL", gr.Number
            ).info("ใช้กับ prompt ของ refiner"),
        },
    )
)

options_templates.update(
    options_section(
        ('sd3', "SIIN AI 3", "sd"),
        {
            "sd3_enable_t5": OptionInfo(False, "เปิดใช้งาน T5").info(
                "โหลด text encoder T5 เพิ่ม VRAM ใช้งาน แต่เพิ่มคุณภาพได้ ต้องรีโหลดโมเดล"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('vae', "VAE", "sd"),
        {
            "sd_vae_explanation": OptionHTML(
                """
<abbr title='Variational autoencoder'>VAE</abbr> เป็นโครงข่ายประสาทที่แปลงภาพ <abbr title='red/green/blue'>RGB</abbr>
ให้เป็น latent space และกลับคืน SIIN AI ทำงานกับ latent space นี้ระหว่างการประมวลผล
(ขณะ progress bar กำลังโหลด) สำหรับ txt2img, VAE จะใช้ตอนสิ้นสุดการสร้างภาพ
ส่วน img2img จะใช้ทั้งก่อนและหลังการประมวลผลภาพ
"""
            ),
            "sd_vae_checkpoint_cache": OptionInfo(
                0,
                "จำนวนโมเดล VAE ที่แคชไว้ใน RAM",
                gr.Slider,
                {"minimum": 0, "maximum": 10, "step": 1},
            ),
            "sd_vae": OptionInfo(
                "Automatic",
                "SD VAE",
                gr.Dropdown,
                lambda: {"choices": shared_items.sd_vae_items()},
                refresh=shared_items.refresh_vae_list,
                infotext='VAE',
            ).info(
                "เลือกโมเดล VAE: Automatic = ใช้ชื่อเดียวกับ checkpoint; None = ใช้ VAE จาก checkpoint"
            ),
            "sd_vae_overrides_per_model_preferences": OptionInfo(
                True, "VAE ที่เลือกจะเขียนทับค่าจากแต่ละโมเดล"
            ).info("สามารถตั้ง VAE รายโมเดลได้จาก metadata หรือใช้ชื่อไฟล์เดียวกับ checkpoint"),
            "auto_vae_precision_bfloat16": OptionInfo(
                False, "แปลง VAE เป็น bfloat16 โดยอัตโนมัติ"
            ).info("ใช้เมื่อ tensor มีค่า NaN หากปิดจะได้ภาพสีดำ"),
            "auto_vae_precision": OptionInfo(True, "แปลง VAE กลับเป็น float32 โดยอัตโนมัติ").info(
                "ใช้เมื่อ tensor มีค่า NaN หากปิดจะได้ภาพสีดำ"
            ),
            "sd_vae_encode_method": OptionInfo(
                "Full",
                "ประเภท VAE สำหรับ encode",
                gr.Radio,
                {"choices": ["Full", "TAESD"]},
                infotext='VAE Encoder',
            ).info("วิธี encode ภาพเป็น latent สำหรับ img2img, hires-fix หรือ inpaint"),
            "sd_vae_decode_method": OptionInfo(
                "Full",
                "ประเภท VAE สำหรับ decode",
                gr.Radio,
                {"choices": ["Full", "TAESD"]},
                infotext='VAE Decoder',
            ).info("วิธี decode latent กลับเป็นภาพ"),
        },
    )
)

options_templates.update(
    options_section(
        ('img2img', "ภาพ > ภาพ", "sd"),
        {
            "inpainting_mask_weight": OptionInfo(
                1.0,
                "ความเข้มของหน้ากากการปรับเงื่อนไขการซ่อมภาพ",
                gr.Slider,
                {"minimum": 0.0, "maximum": 1.0, "step": 0.01},
                infotext='น้ำหนักของหน้ากากเงื่อนไข',
            ),
            "initial_noise_multiplier": OptionInfo(
                1.0,
                "ตัวคูณสัญญาณรบกวนเริ่มต้นสำหรับ img2img",
                gr.Slider,
                {"minimum": 0.0, "maximum": 1.5, "step": 0.001},
                infotext='ตัวคูณสัญญาณรบกวน',
            ),
            "img2img_extra_noise": OptionInfo(
                0.0,
                "ตัวคูณสัญญาณรบกวนเพิ่มเติมสำหรับ img2img และแก้ไขความละเอียดสูง",
                gr.Slider,
                {"minimum": 0.0, "maximum": 1.0, "step": 0.01},
                infotext='สัญญาณรบกวนเพิ่มเติม',
            ).info("0 = ปิดใช้งาน (ค่าเริ่มต้น); ควรน้อยกว่าค่าความแรงในการลดสัญญาณรบกวน"),
            "img2img_color_correction": OptionInfo(False, "ปรับสีของผลลัพธ์ img2img ให้ตรงกับภาพต้นฉบับ"),
            "img2img_fix_steps": OptionInfo(
                False, "กับ img2img, ทำจำนวนขั้นตอนตามที่กำหนดในแถบเลื่อน"
            ).info("ปกติจะใช้ขั้นตอนน้อยลงเมื่อใช้การลดสัญญาณรบกวนน้อยลง"),
            "img2img_background_color": OptionInfo(
                "#ffffff",
                "กับ img2img, เติมส่วนโปร่งใสของภาพต้นฉบับด้วยสีนี้",
                ui_components.FormColorPicker,
                {},
            ),
            "img2img_editor_height": OptionInfo(
                720, "ความสูงของตัวแก้ไขภาพ", gr.Slider, {"minimum": 80, "maximum": 1600, "step": 1}
            )
            .info("หน่วยเป็นพิกเซล")
            .needs_reload_ui(),
            "img2img_sketch_default_brush_color": OptionInfo(
                "#ffffff", "สีเริ่มต้นของแปรงสเก็ต img2img", ui_components.FormColorPicker, {}
            )
            .info("สีแปรงเริ่มต้นของ img2img sketch")
            .needs_reload_ui(),
            "img2img_inpaint_mask_brush_color": OptionInfo(
                "#ffffff", "สีแปรงหน้ากากการซ่อมภาพ", ui_components.FormColorPicker, {}
            )
            .info("สีของแปรงที่ใช้ในหน้ากากการซ่อมภาพ")
            .needs_reload_ui(),
            "img2img_inpaint_sketch_default_brush_color": OptionInfo(
                "#ffffff", "สีเริ่มต้นของแปรงสเก็ตการซ่อมภาพ", ui_components.FormColorPicker, {}
            )
            .info("สีแปรงเริ่มต้นของ sketch การซ่อมภาพ")
            .needs_reload_ui(),
            "return_mask": OptionInfo(False, "สำหรับการซ่อมภาพ, แสดงหน้ากากสีเทาในผลลัพธ์สำหรับเว็บ"),
            "return_mask_composite": OptionInfo(
                False, "สำหรับการซ่อมภาพ, แสดงภาพผสมหน้ากากในผลลัพธ์สำหรับเว็บ"
            ),
            "img2img_batch_show_results_limit": OptionInfo(
                32,
                "แสดงผลลัพธ์ batch img2img จำนวน N รายการแรกใน UI",
                gr.Slider,
                {"minimum": -1, "maximum": 1000, "step": 1},
            ).info('0: ปิดใช้งาน, -1: แสดงภาพทั้งหมด อาจทำให้เกิดความล่าช้า'),
            "overlay_inpaint": OptionInfo(True, "ซ้อนทับต้นฉบับสำหรับการซ่อมภาพ").info(
                "เมื่อซ่อมภาพ, ซ้อนภาพต้นฉบับเหนือบริเวณที่ไม่ได้ซ่อม"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('optimizations', "การปรับแต่งประสิทธิภาพ", "sd"),
        {
            "cross_attention_optimization": OptionInfo(
                "Automatic",
                "การเพิ่มประสิทธิภาพ Cross Attention",
                gr.Dropdown,
                lambda: {"choices": shared_items.cross_attention_optimizations()},
            ),
            "s_min_uncond": OptionInfo(
                0.0,
                "Negative Guidance sigma ขั้นต่ำ",
                gr.Slider,
                {"minimum": 0.0, "maximum": 15.0, "step": 0.01},
                infotext='NGMS',
            )
            .link("PR", "https://github.com/AUTOMATIC1111/stablediffusion-webui/pull/9177")
            .info("ข้าม prompt เชิงลบในบางขั้นตอนเมื่อภาพใกล้เสร็จ; 0=ปิดการใช้งาน, ค่าสูง=เร็วขึ้น"),
            "s_min_uncond_all": OptionInfo(
                False, "ใช้ Negative Guidance sigma ขั้นต่ำในทุกขั้นตอน", infotext='NGMS ทุกขั้นตอน'
            ).info("โดยปกติจะข้ามขั้นเว้นขั้น; ตัวเลือกนี้จะให้ข้ามทุกขั้น"),
            "token_merging_ratio": OptionInfo(
                0.0,
                "อัตราการรวม Token",
                gr.Slider,
                {"minimum": 0.0, "maximum": 0.9, "step": 0.1},
                infotext='อัตราการรวม Token',
            )
            .link("PR", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/9256")
            .info("0=ปิด, ค่าสูง=เร็วขึ้น"),
            "token_merging_ratio_img2img": OptionInfo(
                0.0,
                "อัตราการรวม Token สำหรับ img2img",
                gr.Slider,
                {"minimum": 0.0, "maximum": 0.9, "step": 0.1},
            ).info("ใช้เฉพาะเมื่อไม่เป็นศูนย์ และจะ override ค่าด้านบน"),
            "token_merging_ratio_hr": OptionInfo(
                0.0,
                "อัตราการรวม Token สำหรับขั้นตอนความละเอียดสูง",
                gr.Slider,
                {"minimum": 0.0, "maximum": 0.9, "step": 0.1},
                infotext='Token merging ratio hr',
            ).info("ใช้เฉพาะเมื่อไม่เป็นศูนย์ และจะ override ค่าด้านบน"),
            "pad_cond_uncond": OptionInfo(
                False, "ปรับความยาว prompt/negative prompt ให้เท่ากัน", infotext='เติม prompt'
            ).info(
                "ช่วยเพิ่มประสิทธิภาพเมื่อ prompt กับ negative prompt ยาวไม่เท่ากัน; มีผลต่อ seed"
            ),
            "pad_cond_uncond_v0": OptionInfo(
                False, "ปรับ prompt/negative prompt (v0)", infotext='เติม prompt แบบเก่า'
            ).info(
                "การทำงานแบบเก่า (ก่อนเวอร์ชัน 1.6.0); truncate negative prompt ถ้ายาวเกิน; มีผลต่อ seed"
            ),
            "persistent_cond_cache": OptionInfo(True, "แคชเงื่อนไขจาก prompt ถาวร").info(
                "ไม่คำนวณซ้ำหาก prompt เหมือนเดิม"
            ),
            "batch_cond_uncond": OptionInfo(True, "ประมวลผลเงื่อนไข/ไม่มีเงื่อนไขแบบ batch").info(
                "ประมวลผลทั้งสองพร้อมกัน ช่วยเพิ่มความเร็วแต่ใช้ VRAM เพิ่ม"
            ),
            "fp8_storage": OptionInfo(
                "Disable",
                "การใช้ FP8 กับน้ำหนักโมเดล",
                gr.Radio,
                {"choices": ["Disable", "Enable for SDXL", "Enable"]},
            ).info("ใช้ FP8 สำหรับจัดเก็บน้ำหนัก Linear/Conv layer; ต้องการ PyTorch >= 2.1.0"),
            "cache_fp16_weight": OptionInfo(False, "แคชน้ำหนัก FP16 สำหรับ LoRA").info(
                "ใช้ร่วมกับ FP8 เพื่อเพิ่มคุณภาพ LoRA แต่ใช้ RAM มากขึ้น"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('compatibility', "ความเข้ากันได้", "sd"),
        {
            "auto_backcompat": OptionInfo(True, "เปิดใช้งานความเข้ากันได้ย้อนหลังอัตโนมัติ").info(
                "เปิดใช้งานตัวเลือกที่จำเป็นเพื่อความเข้ากันได้เมื่อโหลดพารามิเตอร์จากเวอร์ชันก่อนหน้า"
            ),
            "use_old_emphasis_implementation": OptionInfo(False, "ใช้วิธีการเน้นคำแบบเก่า").info(
                "ใช้เมื่อจำเป็นต้องได้ผลลัพธ์แบบเดียวกับ seed เก่า"
            ),
            "use_old_karras_scheduler_sigmas": OptionInfo(
                False, "ใช้ sigma ของ scheduler แบบ Karras แบบเก่า (0.1 ถึง 10)"
            ),
            "no_dpmpp_sde_batch_determinism": OptionInfo(
                False, "ไม่ทำให้ DPM++ SDE เป็น deterministic ระหว่าง batch ขนาดต่างกัน"
            ),
            "use_old_hires_fix_width_height": OptionInfo(
                False, "ใช้ความกว้าง/สูงของ hires fix สำหรับผลลัพธ์สุดท้าย แทนที่จะใช้กับ pass แรก"
            ),
            "hires_fix_use_firstpass_conds": OptionInfo(
                False, "ให้ hires fix ใช้เงื่อนไขจาก pass แรกในการคำนวณ pass ที่สอง"
            ),
            "use_old_scheduling": OptionInfo(
                False, "ใช้ลำดับเวลา prompt แบบเก่า", infotext="ลำดับเวลาแบบเก่า"
            ).info(
                "สำหรับ [red:green:N]; แบบเก่า: N < 1 คือสัดส่วนของขั้นตอน, N >= 1 คือจำนวนขั้นตอน; แบบใหม่: N ที่มีจุดทศนิยมคือสัดส่วน, ตัวอื่นคือนับเป็นขั้น"
            ),
            "use_downcasted_alpha_bar": OptionInfo(
                False,
                "ลดขนาด alphas_cumprod เป็น fp16 ก่อนการ sample",
                infotext="ลดขนาด alphas_cumprod",
            ).info("ใช้เพื่อให้ผลเหมือนกับ seed จากเวอร์ชันก่อน"),
            "refiner_switch_by_sample_steps": OptionInfo(
                False,
                "สลับไปใช้ refiner ตามจำนวน sampling steps แทนที่จะเป็น timestep",
                infotext="สลับ refiner ตามขั้นตอนการ sample",
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('interrogate', "วิเคราะห์ภาพ (Interrogate)"),
        {
            "interrogate_keep_models_in_memory": OptionInfo(False, "เก็บโมเดลไว้ใน VRAM"),
            "interrogate_return_ranks": OptionInfo(False, "แสดงอันดับของแท็กที่ตรงกับโมเดล").info(
                "ใช้กับ booru เท่านั้น"
            ),
            "interrogate_clip_num_beams": OptionInfo(
                1, "BLIP: จำนวน beams", gr.Slider, {"minimum": 1, "maximum": 16, "step": 1}
            ),
            "interrogate_clip_min_length": OptionInfo(
                24, "BLIP: ความยาวคำอธิบายขั้นต่ำ", gr.Slider, {"minimum": 1, "maximum": 128, "step": 1}
            ),
            "interrogate_clip_max_length": OptionInfo(
                48, "BLIP: ความยาวคำอธิบายสูงสุด", gr.Slider, {"minimum": 1, "maximum": 256, "step": 1}
            ),
            "interrogate_clip_dict_limit": OptionInfo(1500, "CLIP: จำนวนบรรทัดสูงสุดในไฟล์ข้อความ").info(
                "0 = ไม่จำกัด"
            ),
            "interrogate_clip_skip_categories": OptionInfo(
                [],
                "CLIP: ข้ามหมวดหมู่ในการวิเคราะห์",
                gr.CheckboxGroup,
                lambda: {"choices": interrogate.category_types()},
                refresh=interrogate.category_types,
            ),
            "interrogate_deepbooru_score_threshold": OptionInfo(
                0.5, "deepbooru: ค่าคะแนนขั้นต่ำ", gr.Slider, {"minimum": 0, "maximum": 1, "step": 0.01}
            ),
            "deepbooru_sort_alpha": OptionInfo(True, "deepbooru: เรียงแท็กตามตัวอักษร").info(
                "ถ้าปิด: เรียงตามคะแนน"
            ),
            "deepbooru_use_spaces": OptionInfo(True, "deepbooru: ใช้ช่องว่างในแท็ก").info(
                "ถ้าปิด: ใช้ขีดล่าง"
            ),
            "deepbooru_escape": OptionInfo(True, "deepbooru: escape วงเล็บด้วย \\").info(
                "เพื่อให้วงเล็บไม่ถูกตีความเป็นการเน้นคำ"
            ),
            "deepbooru_filter_tags": OptionInfo("", "deepbooru: กรองแท็กที่ไม่ต้องการ").info(
                "คั่นแต่ละแท็กด้วยเครื่องหมายคอมมา"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('extra_networks', "เน็คเวิร์คเสริม", "sd"),
        {
            "extra_networks_show_hidden_directories": OptionInfo(True, "แสดงโฟลเดอร์ที่ซ่อนไว้").info(
                "โฟลเดอร์จะถูกซ่อนไว้หากชื่อขึ้นต้นด้วย \".\""
            ),
            "extra_networks_dir_button_function": OptionInfo(
                False, "เพิ่ม '/' หน้าโฟลเดอร์เมื่อกดปุ่ม"
            ).info("ปุ่มจะแสดงเนื้อหาของโฟลเดอร์โดยไม่ใช้เป็นตัวกรองการค้นหา"),
            "extra_networks_hidden_models": OptionInfo(
                "When searched",
                "แสดงการ์ดของโมเดลในโฟลเดอร์ที่ซ่อน",
                gr.Radio,
                {"choices": ["Always", "When searched", "Never"]},
            ).info(
                'ตัวเลือก "When searched" จะแสดงเฉพาะเมื่อค้นหาด้วยคำที่มีความยาวตั้งแต่ 4 ตัวอักษรขึ้นไป'
            ),
            "extra_networks_default_multiplier": OptionInfo(
                1.0,
                "ค่าคูณเริ่มต้นของ Extra Networks",
                gr.Slider,
                {"minimum": 0.0, "maximum": 2.0, "step": 0.01},
            ),
            "extra_networks_card_width": OptionInfo(0, "ความกว้างของการ์ด Extra Networks").info(
                "หน่วยเป็นพิกเซล"
            ),
            "extra_networks_card_height": OptionInfo(0, "ความสูงของการ์ด Extra Networks").info(
                "หน่วยเป็นพิกเซล"
            ),
            "extra_networks_card_text_scale": OptionInfo(
                1.0, "ขนาดข้อความบนการ์ด", gr.Slider, {"minimum": 0.0, "maximum": 2.0, "step": 0.01}
            ).info("1 = ขนาดปกติ"),
            "extra_networks_card_show_desc": OptionInfo(True, "แสดงคำอธิบายบนการ์ด"),
            "extra_networks_card_description_is_html": OptionInfo(False, "แสดงคำอธิบายแบบ HTML"),
            "extra_networks_card_order_field": OptionInfo(
                "Path",
                "เรียงลำดับการ์ด Extra Networks ตาม",
                gr.Dropdown,
                {"choices": ['Path', 'Name', 'Date Created', 'Date Modified']},
            ).needs_reload_ui(),
            "extra_networks_card_order": OptionInfo(
                "Ascending",
                "ทิศทางการเรียงลำดับ",
                gr.Dropdown,
                {"choices": ['Ascending', 'Descending']},
            ).needs_reload_ui(),
            "extra_networks_tree_view_style": OptionInfo(
                "Dirs",
                "รูปแบบการแสดงโฟลเดอร์ของ Extra Networks",
                gr.Radio,
                {"choices": ["Tree", "Dirs"]},
            ).needs_reload_ui(),
            "extra_networks_tree_view_default_enabled": OptionInfo(
                True, "เปิดการแสดงโฟลเดอร์ Extra Networks โดยค่าเริ่มต้น"
            ).needs_reload_ui(),
            "extra_networks_tree_view_default_width": OptionInfo(
                180, "ความกว้างเริ่มต้นของแถบโฟลเดอร์ Extra Networks", gr.Number
            ).needs_reload_ui(),
            "extra_networks_add_text_separator": OptionInfo(
                " ", "ตัวแบ่งข้อความของ Extra Networks"
            ).info("ข้อความที่เติมก่อน <...> เมื่อเพิ่มเข้า prompt"),
            "ui_extra_networks_tab_reorder": OptionInfo(
                "", "เรียงลำดับแท็บ Extra Networks ใหม่"
            ).needs_reload_ui(),
            "textual_inversion_print_at_load": OptionInfo(
                False, "แสดงรายการ Textual Inversion ขณะโหลดโมเดล"
            ),
            "textual_inversion_add_hashes_to_infotext": OptionInfo(
                True, "เพิ่มแฮชของ Textual Inversion ใน infotext"
            ),
            "sd_hypernetwork": OptionInfo(
                "None",
                "เพิ่ม Hypernetwork ใน prompt",
                gr.Dropdown,
                lambda: {"choices": ["None", *shared.hypernetworks]},
                refresh=shared_items.reload_hypernetworks,
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('ui_prompt_editing', "การแก้ไขพรอมต์", "ui"),
        {
            "keyedit_precision_attention": OptionInfo(
                0.1,
                "ความละเอียดสำหรับ (attention:1.1) เมื่อแก้ไขพรอมต์ด้วย Ctrl+ลูกศรขึ้น/ลง",
                gr.Slider,
                {"minimum": 0.01, "maximum": 0.2, "step": 0.001},
            ),
            "keyedit_precision_extra": OptionInfo(
                0.05,
                "ความละเอียดสำหรับ <extra networks:0.9> เมื่อแก้ไขพรอมต์ด้วย Ctrl+ลูกศรขึ้น/ลง",
                gr.Slider,
                {"minimum": 0.01, "maximum": 0.2, "step": 0.001},
            ),
            "keyedit_delimiters": OptionInfo(
                r".,\/!?%^*;:{}=`~() ", "ตัวแบ่งคำเมื่อแก้ไขพรอมต์ด้วย Ctrl+ลูกศรขึ้น/ลง"
            ),
            "keyedit_delimiters_whitespace": OptionInfo(
                ["Tab", "Carriage Return", "Line Feed"],
                "ตัวแบ่งช่องว่างสำหรับ Ctrl+ลูกศรขึ้น/ลง",
                gr.CheckboxGroup,
                lambda: {"choices": ["Tab", "Carriage Return", "Line Feed"]},
            ),
            "keyedit_move": OptionInfo(True, "Alt+ซ้าย/ขวา เพื่อย้ายส่วนของพรอมต์"),
            "disable_token_counters": OptionInfo(False, "ปิดการแสดงตัวนับโทเคนของพรอมต์"),
            "include_styles_into_token_counters": OptionInfo(True, "นับโทเคนของสไตล์ที่เปิดใช้ด้วย").info(
                "เมื่อคำนวณจำนวนโทเคนในพรอมต์ ให้นับโทเคนจากสไตล์ที่เปิดใช้งานด้วย"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('ui_gallery', "แกลเลอรี", "ui"),
        {
            "return_grid": OptionInfo(True, "แสดงตารางภาพในแกลเลอรี"),
            "do_not_show_images": OptionInfo(False, "ไม่แสดงภาพในแกลเลอรีเลย"),
            "js_modal_lightbox": OptionInfo(True, "เปิดใช้งานแสดงภาพเต็มหน้าจอ"),
            "js_modal_lightbox_initially_zoomed": OptionInfo(
                True, "แสดงภาพแบบขยายโดยค่าเริ่มต้นในโหมดเต็มหน้าจอ"
            ),
            "js_modal_lightbox_gamepad": OptionInfo(False, "ควบคุมแกลเลอรีเต็มจอด้วยจอยเกม"),
            "js_modal_lightbox_gamepad_repeat": OptionInfo(
                250, "ช่วงเวลาการเลื่อนภาพด้วยจอยเกม (มิลลิวินาที)"
            ).info("ในหน่วยมิลลิวินาที"),
            "sd_webui_modal_lightbox_icon_opacity": OptionInfo(
                1,
                "ความโปร่งใสของไอคอนควบคุม (ไม่โฟกัส)",
                gr.Slider,
                {"minimum": 0.0, "maximum": 1, "step": 0.01},
                onchange=shared.reload_gradio_theme,
            )
            .info("เฉพาะเมาส์")
            .needs_reload_ui(),
            "sd_webui_modal_lightbox_toolbar_opacity": OptionInfo(
                0.9,
                "ความโปร่งใสของแถบเครื่องมือในโหมดเต็มหน้าจอ",
                gr.Slider,
                {"minimum": 0.0, "maximum": 1, "step": 0.01},
                onchange=shared.reload_gradio_theme,
            )
            .info("เฉพาะเมาส์")
            .needs_reload_ui(),
            "gallery_height": OptionInfo("", "ความสูงของแกลเลอรี", gr.Textbox)
            .info("สามารถใช้ค่า CSS ได้ เช่น 768px หรือ 20em")
            .needs_reload_ui(),
            "open_dir_button_choice": OptionInfo(
                "Subdirectory",
                "เมื่อกดปุ่ม [📂] ให้เปิดไดเรกทอรีใด",
                gr.Radio,
                {"choices": ["Output Root", "Subdirectory", "Subdirectory (even temp dir)"]},
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('ui_alternatives', "ตัวเลือก UI เพิ่มเติม", "ui"),
        {
            "compact_prompt_box": OptionInfo(False, "แสดงพรอมต์แบบกะทัดรัด")
            .info("แสดงพรอมต์และเนกาทีฟพรอมต์ในแท็บ Generate ทำให้มีพื้นที่แสดงภาพมากขึ้น")
            .needs_reload_ui(),
            "samplers_in_dropdown": OptionInfo(
                True, "ใช้เมนูแบบเลื่อนลงสำหรับเลือกตัวอย่าง (Sampler) แทนปุ่มตัวเลือก"
            ).needs_reload_ui(),
            "dimensions_and_batch_together": OptionInfo(
                True, "จัดวางตัวเลื่อนขนาดภาพและจำนวนชุดในแถวเดียวกัน"
            ).needs_reload_ui(),
            "sd_checkpoint_dropdown_use_short": OptionInfo(
                False, "รายการเช็คพอยต์: แสดงเฉพาะชื่อไฟล์ไม่รวมพาธ"
            ).info("โมเดลในโฟลเดอร์ย่อยเช่น photo/sd15.ckpt จะแสดงเป็น sd15.ckpt เท่านั้น"),
            "hires_fix_show_sampler": OptionInfo(
                False, "Hires fix: แสดงตัวเลือกเช็คพอยต์และ Sampler"
            ).needs_reload_ui(),
            "hires_fix_show_prompts": OptionInfo(
                False, "Hires fix: แสดงพรอมต์และเนกาทีฟพรอมต์ของรอบ Hires"
            ).needs_reload_ui(),
            "txt2img_settings_accordion": OptionInfo(
                False, "ซ่อนการตั้งค่า txt2img ใต้ Accordion"
            ).needs_reload_ui(),
            "img2img_settings_accordion": OptionInfo(
                False, "ซ่อนการตั้งค่า img2img ใต้ Accordion"
            ).needs_reload_ui(),
            "interrupt_after_current": OptionInfo(True, "หยุดหลังจบภาพปัจจุบัน").info(
                "เมื่อกดปุ่มหยุด (Interrupt) ถ้ากำลังสร้างหลายภาพ จะหยุดหลังสร้างภาพที่กำลังทำอยู่เสร็จ"
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('ui', "ส่วนติดต่อผู้ใช้", "ui"),
        {
            "localization": OptionInfo(
                "None",
                "ภาษา",
                gr.Dropdown,
                lambda: {"choices": ["None"] + list(localization.localizations.keys())},
                refresh=lambda: localization.list_localizations(cmd_opts.localizations_dir),
            ).needs_reload_ui(),
            "quicksettings_list": OptionInfo(
                ["sd_model_checkpoint"],
                "รายการการตั้งค่าอย่างรวดเร็ว",
                ui_components.DropdownMulti,
                lambda: {"choices": list(shared.opts.data_labels.keys())},
            )
            .js("info", "settingsHintsShowQuicksettings")
            .info("ตัวเลือกที่แสดงด้านบนของหน้า แทนที่อยู่ในแท็บ Settings")
            .needs_reload_ui(),
            "ui_tab_order": OptionInfo(
                [],
                "ลำดับแท็บของ UI",
                ui_components.DropdownMulti,
                lambda: {"choices": list(shared.tab_names)},
            ).needs_reload_ui(),
            "hidden_tabs": OptionInfo(
                [],
                "แท็บ UI ที่ซ่อนไว้",
                ui_components.DropdownMulti,
                lambda: {"choices": list(shared.tab_names)},
            ).needs_reload_ui(),
            "ui_reorder_list": OptionInfo(
                [],
                "ลำดับองค์ประกอบ UI ในแท็บ txt2img/img2img",
                ui_components.DropdownMulti,
                lambda: {"choices": list(shared_items.ui_reorder_categories())},
            )
            .info("รายการที่เลือกจะถูกแสดงก่อน")
            .needs_reload_ui(),
            "gradio_theme": OptionInfo(
                "Default",
                "ธีม Gradio",
                ui_components.DropdownEditable,
                lambda: {"choices": ["Default"] + shared_gradio_themes.gradio_hf_hub_themes},
            )
            .info(
                "คุณสามารถใส่ชื่อธีมเองจาก <a href='https://huggingface.co/spaces/gradio/theme-gallery'>แกลเลอรีธีม</a> ได้"
            )
            .needs_reload_ui(),
            "gradio_themes_cache": OptionInfo(True, "เก็บแคชธีมของ Gradio ไว้ในเครื่อง").info(
                "ปิดเพื่อโหลดธีมใหม่จากอินเทอร์เน็ต"
            ),
            "show_progress_in_title": OptionInfo(True, "แสดงความคืบหน้าในชื่อหน้าต่าง"),
            "send_seed": OptionInfo(True, "ส่งค่า seed เมื่อส่งพรอมต์หรือภาพไปยังอินเทอร์เฟซอื่น"),
            "send_size": OptionInfo(True, "ส่งขนาดภาพเมื่อส่งพรอมต์หรือภาพไปยังอินเทอร์เฟซอื่น"),
            "enable_reloading_ui_scripts": OptionInfo(
                False, "โหลดสคริปต์ UI ใหม่เมื่อใช้ตัวเลือก Reload UI"
            ).info(
                "เหมาะสำหรับนักพัฒนา: เมื่อมีการเปลี่ยนแปลงโค้ด UI จะถูกนำมาใช้เมื่อโหลด UI ใหม่"
            ),
        },
    )
)


options_templates.update(
    options_section(
        ('infotext', "ข้อความ Infotext", "ui"),
        {
            "infotext_explanation": OptionHTML(
                """
Infotext คือข้อความที่รวมพารามิเตอร์ที่ใช้สร้างภาพ ซึ่งสามารถใช้ซ้ำเพื่อสร้างภาพเดิมได้อีกครั้ง
จะแสดงใน UI ใต้ภาพที่สร้าง หากต้องการใช้งาน ให้วางข้อความลงในช่องพรอมต์แล้วกดปุ่ม ↙️ paste
"""
            ),
            "enable_pnginfo": OptionInfo(True, "เขียน Infotext ลงในเมตาดาต้าของภาพที่สร้าง"),
            "save_txt": OptionInfo(False, "สร้างไฟล์ .txt พร้อม Infotext ถัดจากภาพที่สร้างทุกภาพ"),
            "add_model_name_to_info": OptionInfo(True, "เพิ่มชื่อโมเดลลงใน Infotext"),
            "add_model_hash_to_info": OptionInfo(True, "เพิ่มค่าแฮชของโมเดลลงใน Infotext"),
            "add_vae_name_to_info": OptionInfo(True, "เพิ่มชื่อ VAE ลงใน Infotext"),
            "add_vae_hash_to_info": OptionInfo(True, "เพิ่มค่าแฮชของ VAE ลงใน Infotext"),
            "add_user_name_to_info": OptionInfo(False, "เพิ่มชื่อผู้ใช้ลงใน Infotext เมื่อมีการล็อกอิน"),
            "add_version_to_infotext": OptionInfo(True, "เพิ่มเวอร์ชันของโปรแกรมลงใน Infotext"),
            "disable_weights_auto_swap": OptionInfo(
                True, "ไม่ใช้ข้อมูล checkpoint จาก Infotext ที่วาง"
            ).info("ใช้เมื่อโหลดค่าพารามิเตอร์จากข้อความ Infotext"),
            "infotext_skip_pasting": OptionInfo(
                [],
                "ข้ามฟิลด์บางรายการเมื่อวาง Infotext",
                ui_components.DropdownMulti,
                lambda: {"choices": shared_items.get_infotext_names()},
            ),
            "infotext_styles": OptionInfo(
                "Apply if any",
                "จัดการสไตล์จากพรอมต์ใน Infotext",
                gr.Radio,
                {"choices": ["Ignore", "Apply", "Discard", "Apply if any"]},
            )
            .info("ใช้เมื่อโหลดค่าพารามิเตอร์จากข้อความ Infotext")
            .html(
                """<ul style='margin-left: 1.5em'>
<li>Ignore: คงค่าพรอมต์และสไตล์ไว้ตามเดิม</li>
<li>Apply: ลบข้อความสไตล์ออกจากพรอมต์ และตั้งค่ารายการสไตล์ใหม่ (แม้ไม่มีพบสไตล์ก็แทนที่)</li>
<li>Discard: ลบข้อความสไตล์ออกจากพรอมต์ แต่ไม่เปลี่ยนค่ารายการสไตล์</li>
<li>Apply if any: ลบข้อความสไตล์ออกจากพรอมต์; ถ้ามีสไตล์พบในพรอมต์ ให้ใส่ในรายการสไตล์ มิฉะนั้นคงค่าเดิม</li>
</ul>"""
            ),
        },
    )
)

options_templates.update(
    options_section(
        ('ui', "พรีวิวภาพแบบเรียลไทม์", "ui"),
        {
            "show_progressbar": OptionInfo(True, "แสดงแถบความคืบหน้า"),
            "live_previews_enable": OptionInfo(True, "แสดงพรีวิวภาพแบบเรียลไทม์"),
            "live_previews_image_format": OptionInfo(
                "png", "รูปแบบไฟล์ภาพพรีวิว", gr.Radio, {"choices": ["jpeg", "png", "webp"]}
            ),
            "show_progress_grid": OptionInfo(True, "แสดงภาพทั้งหมดในชุดเป็นตารางขณะสร้างภาพ"),
            "show_progress_every_n_steps": OptionInfo(
                10, "ช่วงเวลาในการอัปเดตพรีวิว", gr.Slider, {"minimum": -1, "maximum": 32, "step": 1}
            ).info("ระบุเป็นจำนวนขั้นตอนที่ใช้ในการสร้างภาพ; -1 = แสดงเมื่อเสร็จชุด"),
            "show_progress_type": OptionInfo(
                "Approx NN",
                "วิธีการแสดงพรีวิว",
                gr.Radio,
                {"choices": ["Full", "Approx NN", "Approx cheap", "TAESD"]},
            ).info(
                "Full = ชัดแต่ช้า; Approx NN และ TAESD = เร็วแต่คุณภาพต่ำ; Approx cheap = เร็วมากแต่คุณภาพแย่"
            ),
            "live_preview_allow_lowvram_full": OptionInfo(
                False, "อนุญาตให้ใช้พรีวิวแบบ Full ร่วมกับโหมด lowvram/medvram"
            ).info(
                "หากปิด จะใช้ Approx NN แทน; Full ส่งผลให้ทำงานช้าลงมากเมื่อใช้โหมด lowvram/medvram"
            ),
            "live_preview_content": OptionInfo(
                "Prompt",
                "เนื้อหาที่ใช้แสดงในพรีวิว",
                gr.Radio,
                {"choices": ["Combined", "Prompt", "Negative prompt"]},
            ),
            "live_preview_refresh_period": OptionInfo(
                1000, "ช่วงเวลาในการอัปเดตแถบความคืบหน้าและพรีวิว"
            ).info("หน่วย: มิลลิวินาที"),
            "live_preview_fast_interrupt": OptionInfo(False, "คืนค่าภาพจากพรีวิวเมื่อกดหยุด").info(
                "ช่วยให้หยุดการสร้างได้เร็วขึ้น"
            ),
            "js_live_preview_in_modal_lightbox": OptionInfo(
                False, "แสดงพรีวิวภาพในโหมดแสดงภาพเต็มหน้าจอ"
            ),
            "prevent_screen_sleep_during_generation": OptionInfo(True, "ป้องกันหน้าจอดับระหว่างสร้างภาพ"),
        },
    )
)

options_templates.update(
    options_section(
        ('sampler-params', "พารามิเตอร์ของ Sampler", "sd"),
        {
            "hide_samplers": OptionInfo(
                [],
                "ซ่อน Sampler ในหน้าผู้ใช้",
                gr.CheckboxGroup,
                lambda: {"choices": [x.name for x in shared_items.list_samplers()]},
            ).needs_reload_ui(),
            "eta_ddim": OptionInfo(
                0.0,
                "ค่า Eta สำหรับ DDIM",
                gr.Slider,
                {"minimum": 0.0, "maximum": 1.0, "step": 0.01},
                infotext='Eta DDIM',
            ).info("ตัวคูณความแปรปรวนของ noise; ยิ่งสูงผลลัพธ์ยิ่งไม่คาดเดา"),
            "eta_ancestral": OptionInfo(
                1.0,
                "ค่า Eta สำหรับ k-diffusion samplers",
                gr.Slider,
                {"minimum": 0.0, "maximum": 1.0, "step": 0.01},
                infotext='Eta',
            ).info("ตัวคูณความแปรปรวนของ noise; ใช้กับ ancestral samplers เช่น Euler a และ SDE"),
            "ddim_discretize": OptionInfo(
                'uniform',
                "วิธีแยกขั้นตอนของ DDIM (img2img)",
                gr.Radio,
                {"choices": ['uniform', 'quad']},
            ),
            's_churn': OptionInfo(
                0.0,
                "Sigma churn",
                gr.Slider,
                {"minimum": 0.0, "maximum": 100.0, "step": 0.01},
                infotext='Sigma churn',
            ).info("ระดับของความสุ่ม; ใช้กับ Euler, Heun, และ DPM2"),
            's_tmin': OptionInfo(
                0.0,
                "Sigma tmin",
                gr.Slider,
                {"minimum": 0.0, "maximum": 10.0, "step": 0.01},
                infotext='Sigma tmin',
            ).info("ค่าต่ำสุดของช่วง sigma; เปิด stochasticity"),
            's_tmax': OptionInfo(
                0.0,
                "Sigma tmax",
                gr.Slider,
                {"minimum": 0.0, "maximum": 999.0, "step": 0.01},
                infotext='Sigma tmax',
            ).info("0 = inf; ค่าสูงสุดของช่วง sigma"),
            's_noise': OptionInfo(
                1.0,
                "Sigma noise",
                gr.Slider,
                {"minimum": 0.0, "maximum": 1.1, "step": 0.001},
                infotext='Sigma noise',
            ).info("เพิ่ม noise เพื่อชดเชยรายละเอียดที่สูญหาย"),
            'sigma_min': OptionInfo(
                0.0, "Sigma ต่ำสุด", gr.Number, infotext='Schedule min sigma'
            ).info("0 = ค่าเริ่มต้น (~0.03); ค่าความแรงของ noise ต่ำสุดใน scheduler"),
            'sigma_max': OptionInfo(
                0.0, "Sigma สูงสุด", gr.Number, infotext='Schedule max sigma'
            ).info("0 = ค่าเริ่มต้น (~14.6); ค่าความแรงของ noise สูงสุดใน scheduler"),
            'rho': OptionInfo(0.0, "ค่า Rho", gr.Number, infotext='Schedule rho').info(
                "0 = ค่าเริ่มต้น (7 สำหรับ karras, 1 สำหรับ polyexponential); ยิ่งมาก noise จะลดเร็ว"
            ),
            'eta_noise_seed_delta': OptionInfo(
                0, "Eta noise seed delta", gr.Number, {"precision": 0}, infotext='ENSD'
            ).info("ใช้สำหรับเปรียบเทียบภาพ ไม่ส่งผลต่อคุณภาพ"),
            'always_discard_next_to_last_sigma': OptionInfo(
                False, "ตัดขั้น sigma รองสุดท้ายเสมอ", infotext='Discard penultimate sigma'
            ).link("PR", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/6044"),
            'sgm_noise_multiplier': OptionInfo(
                False, "ตัวคูณ noise สำหรับ SGM", infotext='SGM noise multiplier'
            )
            .link("PR", "https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/12818")
            .info("ให้ผลตรงกับ SDXL ดั้งเดิม - ใช้เพื่อสร้างภาพซ้ำ"),
            'uni_pc_variant': OptionInfo(
                "bh1",
                "ตัวเลือก UniPC",
                gr.Radio,
                {"choices": ["bh1", "bh2", "vary_coeff"]},
                infotext='UniPC variant',
            ),
            'uni_pc_skip_type': OptionInfo(
                "time_uniform",
                "ประเภทการข้ามของ UniPC",
                gr.Radio,
                {"choices": ["time_uniform", "time_quadratic", "logSNR"]},
                infotext='UniPC skip type',
            ),
            'uni_pc_order': OptionInfo(
                3,
                "ลำดับขั้นตอน UniPC",
                gr.Slider,
                {"minimum": 1, "maximum": 50, "step": 1},
                infotext='UniPC order',
            ).info("ต้องน้อยกว่าจำนวนขั้นตอนการสร้าง"),
            'uni_pc_lower_order_final': OptionInfo(
                True, "ใช้ขั้นต่ำสุดในขั้นตอนสุดท้ายของ UniPC", infotext='UniPC lower order final'
            ),
            'sd_noise_schedule': OptionInfo(
                "Default",
                "ตาราง noise สำหรับ sampling",
                gr.Radio,
                {"choices": ["Default", "Zero Terminal SNR"]},
                infotext="Noise Schedule",
            ).info("ใช้กับโมเดลที่ฝึกแบบ Zero Terminal SNR"),
            'skip_early_cond': OptionInfo(
                0.0,
                "ไม่ใช้ negative prompt ในขั้นตอนเริ่มต้น",
                gr.Slider,
                {"minimum": 0.0, "maximum": 1.0, "step": 0.01},
                infotext="Skip Early CFG",
            ).info("0 = ใช้ทั้งหมด, 1 = ไม่ใช้เลย; อาจช่วยให้คุณภาพและความหลากหลายดีขึ้น"),
            'beta_dist_alpha': OptionInfo(
                0.6,
                "Beta scheduler - alpha",
                gr.Slider,
                {"minimum": 0.01, "maximum": 1.0, "step": 0.01},
                infotext='Beta scheduler alpha',
            ).info('ค่า alpha ของการสุ่มแบบเบต้า (ค่าดั้งเดิม = 0.6)'),
            'beta_dist_beta': OptionInfo(
                0.6,
                "Beta scheduler - beta",
                gr.Slider,
                {"minimum": 0.01, "maximum": 1.0, "step": 0.01},
                infotext='Beta scheduler beta',
            ).info('ค่า beta ของการสุ่มแบบเบต้า (ค่าดั้งเดิม = 0.6)'),
        },
    )
)

options_templates.update(
    options_section(
        ('postprocessing', "การประมวลผลหลังสร้างภาพ", "postprocessing"),
        {
            'postprocessing_enable_in_main_ui': OptionInfo(
                [],
                "เปิดใช้งานการประมวลผลหลังในแท็บ txt2img และ img2img",
                ui_components.DropdownMulti,
                lambda: {"choices": [x.name for x in shared_items.postprocessing_scripts()]},
            ),
            'postprocessing_disable_in_extras': OptionInfo(
                [],
                "ปิดใช้งานการประมวลผลหลังในแท็บ extras",
                ui_components.DropdownMulti,
                lambda: {"choices": [x.name for x in shared_items.postprocessing_scripts()]},
            ),
            'postprocessing_operation_order': OptionInfo(
                [],
                "ลำดับการประมวลผลหลัง",
                ui_components.DropdownMulti,
                lambda: {"choices": [x.name for x in shared_items.postprocessing_scripts()]},
            ),
            'upscaling_max_images_in_cache': OptionInfo(
                5,
                "จำนวนภาพสูงสุดที่เก็บในแคชขณะอัปสเกล",
                gr.Slider,
                {"minimum": 0, "maximum": 10, "step": 1},
            ),
            'postprocessing_existing_caption_action': OptionInfo(
                "Ignore",
                "การจัดการคำบรรยายที่มีอยู่",
                gr.Radio,
                {"choices": ["Ignore", "Keep", "Prepend", "Append"]},
            ).info(
                "ใช้เมื่อสร้างคำบรรยายใหม่: Ignore = ใช้ของใหม่, Keep = ใช้ของเดิม, Prepend/Append = รวมทั้งสอง"
            ),
        },
    )
)

options_templates.update(
    options_section(
        (None, "ตัวเลือกที่ซ่อนไว้"),
        {
            "disabled_extensions": OptionInfo([], "ปิดใช้งานส่วนขยายเหล่านี้"),
            "disable_all_extensions": OptionInfo(
                "none",
                "ปิดใช้งานส่วนขยายทั้งหมด (แต่ยังจำว่าอันไหนถูกปิดไว้)",
                gr.Radio,
                {"choices": ["none", "extra", "all"]},
            ),
            "restore_config_state_file": OptionInfo(
                "", "ไฟล์สถานะ config ที่จะเรียกคืน จากโฟลเดอร์ 'config-states/'"
            ),
            "sd_checkpoint_hash": OptionInfo("", "ค่า SHA256 ของ checkpoint ที่ใช้อยู่"),
        },
    )
)
