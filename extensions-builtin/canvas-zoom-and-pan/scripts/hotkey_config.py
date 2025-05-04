import gradio as gr
from modules import shared

shared.options_templates.update(shared.options_section(('canvas_hotkey', "ปุ่มลัดสำหรับแคนวาส"), {
    "canvas_hotkey_zoom": shared.OptionInfo("Alt", "ซูมแคนวาส", gr.Radio, {"choices": ["Shift", "Ctrl", "Alt"]}).info("ถ้าคุณเลือก 'Shift' จะไม่สามารถเลื่อนขวางได้, 'Alt' อาจทำให้เกิดปัญหาเล็กน้อยใน Firefox"),
    "canvas_hotkey_adjust": shared.OptionInfo("Ctrl", "ปรับขนาดแปรง", gr.Radio, {"choices": ["Shift", "Ctrl", "Alt"]}).info("ถ้าคุณเลือก 'Shift' จะไม่สามารถเลื่อนขวางได้, 'Alt' อาจทำให้เกิดปัญหาเล็กน้อยใน Firefox"),
    "canvas_hotkey_shrink_brush": shared.OptionInfo("Q", "ย่อขนาดแปรง"),
    "canvas_hotkey_grow_brush": shared.OptionInfo("W", "ขยายขนาดแปรง"),
    "canvas_hotkey_move": shared.OptionInfo("F", "เลื่อนแคนวาส").info("เพื่อให้ทำงานถูกต้องใน Firefox ให้ปิดการตั้งค่า 'ค้นหาข้อความในหน้าของคุณโดยอัตโนมัติ' ในการตั้งค่าเบราว์เซอร์"),
    "canvas_hotkey_fullscreen": shared.OptionInfo("S", "โหมดเต็มหน้าจอ, ขยายภาพให้พอดีกับหน้าจอและยืดให้เต็มความกว้าง"),
    "canvas_hotkey_reset": shared.OptionInfo("R", "รีเซ็ตการซูมและตำแหน่งแคนวาส"),
    "canvas_hotkey_overlap": shared.OptionInfo("O", "สลับการทับซ้อน").info("ปุ่มทางเทคนิค, จำเป็นสำหรับการทดสอบ"),
    "canvas_show_tooltip": shared.OptionInfo(True, "เปิดคำแนะนำเมื่อเลื่อนเมาส์บนแคนวาส"),
    "canvas_auto_expand": shared.OptionInfo(True, "ขยายภาพอัตโนมัติเมื่อภาพไม่พอดีกับพื้นที่แคนวาส, คล้ายกับการกดปุ่ม S และ R"),
    "canvas_blur_prompt": shared.OptionInfo(False, "เบลอการโฟกัสจากคำสั่งเมื่อทำงานกับแคนวาส"),
    "canvas_disabled_functions": shared.OptionInfo(["Overlap"], "ปิดฟังก์ชันที่คุณไม่ใช้", gr.CheckboxGroup, {"choices": ["Zoom", "ปรับขนาดแปรง", "ปุ่มลัดขยายแปรง", "ปุ่มลัดย่อแปรง", "การเลื่อนแคนวาส", "โหมดเต็มหน้าจอ", "รีเซ็ตซูม", "ทับซ้อน"]}),
}))
