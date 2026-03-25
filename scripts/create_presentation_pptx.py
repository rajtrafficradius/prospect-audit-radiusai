import os
import json
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import subprocess

def create_ppt_package(session_dir, company_name):
    """
    Orchestrates the new Premium HTML-to-PPTX workflow.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(project_root, "scripts")
    
    deliv_dir = os.path.join(session_dir, "deliverables")
    os.makedirs(deliv_dir, exist_ok=True)
    
    output_path = os.path.join(deliv_dir, "Master_Presentation.pptx")
    
    # 1. Synthesize Content JSON
    print(" [1/3] Synthesizing Strategic Slide Content...")
    subprocess.run([sys.executable, os.path.join(scripts_dir, "synthesize_ppt_json.py"), session_dir, company_name], check=True)
    
    # 2. Render HTML to PNGs using Playwright
    print(" [2/3] Rendering High-Fidelity Slides via Playwright...")
    # We use node directly or npx
    try:
        subprocess.run(["node", os.path.join(scripts_dir, "render_slides.js"), session_dir], check=True)
    except Exception as e:
        print(f" [!] Web Render Error: {e}. Ensure Node.js and Playwright are installed.")
        raise
    
    # 3. Package PNGs into PPTX
    print(" [3/3] Packaging Master Presentation Container...")
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    
    render_dir = os.path.join(session_dir, "rendered_slides")
    if not os.path.exists(render_dir):
        print(f" [!] Error: Render directory missing: {render_dir}")
        return

    slides = sorted([f for f in os.listdir(render_dir) if f.endswith(".png")])
    if not slides:
        print(" [!] Error: No rendered slides found to package.")
        return
        
    for slide_img in slides:
        slide_layout = prs.slide_layouts[6] # Blank
        slide = prs.slides.add_slide(slide_layout)
        img_path = os.path.join(render_dir, slide_img)
        slide.shapes.add_picture(img_path, 0, 0, width=prs.slide_width, height=prs.slide_height)

    prs.save(output_path)
    print(f" [+] Success: Master Presentation finalized at {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_presentation_pptx.py <session_dir> <company_name>")
        sys.exit(1)
        
    s_dir = sys.argv[1]
    c_name = sys.argv[2]
    
    try:
        create_ppt_package(s_dir, c_name)
    except Exception as e:
        print(f" [!] Master PPT Engine Failed: {e}")
        sys.exit(1)
