import os
import json
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

class PPTGenerator:
    def __init__(self, session_dir, company_name, domain):
        self.session_dir = session_dir
        self.company_name = company_name
        self.domain = domain
        self.output_path = os.path.join(session_dir, "deliverables", "Master_Presentation.pptx")
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        self.prs = Presentation()
        self._setup_slide_size()
        
        # Colors (Traffic Radius Branding)
        self.COLOR_NAVY = RGBColor(0x1B, 0x2A, 0x4A)
        self.COLOR_BLUE = RGBColor(0x2E, 0x50, 0x90)
        self.COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
        self.COLOR_ACCENT = RGBColor(0x00, 0xCC, 0xFF)

    def _setup_slide_size(self):
        # Widescreen 16:9
        self.prs.slide_width = Inches(13.33)
        self.prs.slide_height = Inches(7.5)

    def _add_background(self, slide, image_path=None):
        if image_path and os.path.exists(image_path):
            slide.shapes.add_picture(image_path, 0, 0, width=self.prs.slide_width, height=self.prs.slide_height)
        else:
            # Fallback to solid color
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = self.COLOR_NAVY

    def _create_title_slide(self, date_str):
        slide_layout = self.prs.slide_layouts[6] # Blank
        slide = self.prs.slides.add_slide(slide_layout)
        self._add_background(slide) # Using solid navy for title for impact
        
        # Title
        txBox = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11), Inches(2))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = f"INTEGRATED SEARCH TRANSFORMATION STRATEGY"
        p.font.bold = True
        p.font.size = Pt(44)
        p.font.color.rgb = self.COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER
        
        # Subtitle
        txBox2 = slide.shapes.add_textbox(Inches(1), Inches(4.5), Inches(11), Inches(1))
        p2 = txBox2.text_frame.paragraphs[0]
        p2.text = f"Custom Growth Audit for {self.company_name} ({self.domain})"
        p2.font.size = Pt(24)
        p2.font.color.rgb = self.COLOR_ACCENT
        p2.alignment = PP_ALIGN.CENTER

    def _add_content_slide(self, title, bullet_points, image_path=None):
        slide_layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(slide_layout)
        self._add_background(slide, image_path)
        
        # Overlay for readability
        overlay = slide.shapes.add_shape(1, Inches(0.5), Inches(0.5), Inches(12.33), Inches(6.5))
        overlay.fill.solid()
        overlay.fill.fore_color.rgb = self.COLOR_NAVY
        overlay.fill.transparency = 0.3
        overlay.line.color.rgb = self.COLOR_BLUE
        
        # Title
        txBox = slide.shapes.add_textbox(Inches(1), Inches(0.8), Inches(10), Inches(1))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = title.upper()
        p.font.bold = True
        p.font.size = Pt(32)
        p.font.color.rgb = self.COLOR_WHITE
        
        # Content
        txBox2 = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(11), Inches(5))
        tf2 = txBox2.text_frame
        tf2.word_wrap = True
        for point in bullet_points:
            p = tf2.add_paragraph()
            p.text = f"• {point}"
            p.font.size = Pt(18)
            p.font.color.rgb = self.COLOR_WHITE
            p.space_before = Pt(10)

    def generate(self, ba, mi, audit, narrative):
        # 1. Title
        import datetime
        date_str = datetime.datetime.now().strftime("%B %Y")
        self._create_title_slide(date_str)
        
        # 2. Executive ROI Summary
        roi_points = []
        for opp in narrative.get("revenue_opportunity_map", []):
            roi_points.append(f"{opp['service_product']}: {opp['estimated_roi_impact']} (Priority: {opp['strategic_priority']})")
        if not roi_points:
            roi_points = ["Immediate capture of high-intent commercial keywords", "Expansion into AI-driven answer engines (AEO/GEO)", "Technical modernization for search dominance"]
        
        self._add_content_slide("Strategic Revenue Roadmap", roi_points, image_path=os.path.join(self.session_dir, "ppt_bg_roi_growth.png"))
        
        # 3. Market Intelligence
        mi_points = [
            f"Organic Traffic Value: ${mi.get('prospect', {}).get('organic_traffic_value', 0):,}/mo",
            f"Total Search Visibility: {mi.get('prospect', {}).get('organic_keywords', 0):,} keywords",
            "Competitive Landscape: High-value opportunities identified in commercial core segments."
        ]
        self._add_content_slide("Market Intelligence Overview", mi_points, image_path=os.path.join(self.session_dir, "ppt_bg_seo.png"))
        
        # 4. Scorecard Slide
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._add_background(slide)
        title = slide.shapes.add_textbox(Inches(1), Inches(0.5), Inches(10), Inches(1))
        title.text_frame.paragraphs[0].text = "INTEGRATED PERFORMANCE SCORECARD"
        title.text_frame.paragraphs[0].font.bold = True
        title.text_frame.paragraphs[0].font.size = Pt(32)
        title.text_frame.paragraphs[0].font.color.rgb = self.COLOR_WHITE
        
        chart_path = os.path.join(self.session_dir, "charts", "integrated_scorecard.png")
        if os.path.exists(chart_path):
            slide.shapes.add_picture(chart_path, Inches(2), Inches(1.5), height=Inches(5))
        
        # 5. Conclusion
        self._add_content_slide("12-Month Execution Path", [
            "Month 1-3: Technical SEO & AEO Entity Foundation",
            "Month 4-6: Semantic Content Clusters & Money-Page Dominance",
            "Month 7-12: Full-Scale Authority Building & Citation Growth"
        ])
        
        self.prs.save(self.output_path)
        print(f"PPT Presentation saved to: {self.output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python create_presentation_pptx.py <session_dir> <company_name> <domain>")
        sys.exit(1)
        
    s_dir = sys.argv[1]
    c_name = sys.argv[2]
    dom = sys.argv[3]
    
    # Load data
    try:
        with open(os.path.join(s_dir, "business_analysis.json")) as f: ba = json.load(f)
        with open(os.path.join(s_dir, "market_intelligence.json")) as f: mi = json.load(f)
        with open(os.path.join(s_dir, "audit_findings.json")) as f: au = json.load(f)
        with open(os.path.join(s_dir, "strategy_narrative.json")) as f: na = json.load(f)
        
        gen = PPTGenerator(s_dir, c_name, dom)
        gen.generate(ba, mi, au, na)
    except Exception as e:
        print(f"PPT Error: {e}")
        sys.exit(1)
