import gradio as gr
from modules import scripts, shared, ui_common, postprocessing, call_queue, ui_toprow
import modules.infotext_utils as parameters_copypaste
from modules.ui_components import ResizeHandleRow


def create_ui():
    dummy_component = gr.Label(visible=False)
    tab_index = gr.Number(value=0, visible=False)

    with ResizeHandleRow(equal_height=False, variant='compact'):
        with gr.Column(variant='compact'):
            with gr.Tabs(elem_id="mode_extras"):
                with gr.TabItem('ภาพเดี่ยว', id="single_image", elem_id="extras_single_tab") as tab_single:
                    extras_image = gr.Image(label="แหล่งที่มา", source="upload", interactive=True, type="pil", elem_id="extras_image", image_mode="RGBA")

                with gr.TabItem('ประมวลผลแบทช์', id="batch_process", elem_id="extras_batch_process_tab") as tab_batch:
                    image_batch = gr.Files(label="ประมวลผลแบทช์", interactive=True, elem_id="extras_image_batch")

                with gr.TabItem('ประมวลผลจากไดเรกทอรี', id="batch_from_directory", elem_id="extras_batch_directory_tab") as tab_batch_dir:
                    extras_batch_input_dir = gr.Textbox(label="ไดเรกทอรีอินพุต", **shared.hide_dirs, placeholder="ไดเรกทอรีที่อยู่ในเครื่องเดียวกับเซิร์ฟเวอร์ที่ทำงานอยู่", elem_id="extras_batch_input_dir")
                    extras_batch_output_dir = gr.Textbox(label="ไดเรกทอรีเอาท์พุต", **shared.hide_dirs, placeholder="ทิ้งช่องนี้ว่างไว้เพื่อบันทึกรูปภาพไปยังเส้นทางเริ่มต้น", elem_id="extras_batch_output_dir")
                    show_extras_results = gr.Checkbox(label='แสดงผลลัพธ์ภาพ', value=True, elem_id="extras_show_extras_results")


            script_inputs = scripts.scripts_postproc.setup_ui()

        with gr.Column():
            toprow = ui_toprow.Toprow(is_compact=True, is_img2img=False, id_part="extras")
            toprow.create_inline_toprow_image()
            submit = toprow.submit

            output_panel = ui_common.create_output_panel("extras", shared.opts.outdir_extras_samples)

    tab_single.select(fn=lambda: 0, inputs=[], outputs=[tab_index])
    tab_batch.select(fn=lambda: 1, inputs=[], outputs=[tab_index])
    tab_batch_dir.select(fn=lambda: 2, inputs=[], outputs=[tab_index])

    submit.click(
        fn=call_queue.wrap_gradio_gpu_call(postprocessing.run_postprocessing_webui, extra_outputs=[None, '']),
        _js="submit_extras",
        inputs=[
            dummy_component,
            tab_index,
            extras_image,
            image_batch,
            extras_batch_input_dir,
            extras_batch_output_dir,
            show_extras_results,
            *script_inputs
        ],
        outputs=[
            output_panel.gallery,
            output_panel.generation_info,
            output_panel.html_log,
        ],
        show_progress=False,
    )

    parameters_copypaste.add_paste_fields("extras", extras_image, None)

    extras_image.change(
        fn=scripts.scripts_postproc.image_changed,
        inputs=[], outputs=[]
    )
