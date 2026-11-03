from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# 1. Initialize 16:9 Presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette (Dark Theme / Gold Accents)
BG_COLOR = RGBColor(9, 9, 11)        # #09090b
CARD_COLOR = RGBColor(20, 20, 23)    # #141417
CARD_BORDER = RGBColor(45, 45, 52)
GOLD = RGBColor(212, 175, 55)        # #d4af37
TEXT_WHITE = RGBColor(244, 244, 245)
TEXT_MUTED = RGBColor(161, 161, 170)
GREEN = RGBColor(34, 197, 94)
RED = RGBColor(239, 68, 68)

def apply_background(slide):
    bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = BG_COLOR
    bg_shape.line.fill.background()
    return bg_shape

def add_header(slide, title_text, highlight_text=""):
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    
    r1 = p.add_run()
    r1.text = title_text + " "
    r1.font.bold = True
    r1.font.size = Pt(28)
    r1.font.color.rgb = TEXT_WHITE
    r1.font.name = "Arial"
    
    if highlight_text:
        r2 = p.add_run()
        r2.text = highlight_text
        r2.font.bold = True
        r2.font.size = Pt(28)
        r2.font.color.rgb = GOLD
        r2.font.name = "Arial"

def add_bullets(slide, bullets, left=Inches(0.8), top=Inches(1.5), width=Inches(6.8), height=Inches(5.2)):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    
    for i, b in enumerate(bullets):
        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p.space_after = Pt(16)
        
        # Lead bold tag
        r1 = p.add_run()
        r1.text = "• " + b[0] + ": "
        r1.font.bold = True
        r1.font.size = Pt(17)
        r1.font.color.rgb = GOLD
        r1.font.name = "Arial"
        
        # Body text
        r2 = p.add_run()
        r2.text = b[1]
        r2.font.size = Pt(16)
        r2.font.color.rgb = TEXT_WHITE
        r2.font.name = "Arial"

# ==========================================
# SLIDE 0: TITLE SLIDE
# ==========================================
s0 = prs.slides.add_slide(prs.slide_layouts[6])
apply_background(s0)

title_box = s0.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.333), Inches(2.2))
tf = title_box.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "Smart Insole Pre-Fall Prediction Engine:\n"
r.font.bold = True
r.font.size = Pt(36)
r.font.color.rgb = TEXT_WHITE

r2 = p.add_run()
r2.text = "Real-Time Fall Interception in Elderly Gait"
r2.font.bold = True
r2.font.size = Pt(36)
r2.font.color.rgb = GOLD

p2 = tf.add_paragraph()
p2.alignment = PP_ALIGN.CENTER
p2.space_before = Pt(14)
r_sub = p2.add_run()
r_sub.text = "Sub-20 ms TinyML Gait Analysis, Plantar Pressure Dynamics & Embedded Microcontroller Telemetry"
r_sub.font.size = Pt(16)
r_sub.font.color.rgb = TEXT_MUTED

# Meta Card 1: Team
card1 = s0.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.5), Inches(3.8), Inches(4.8), Inches(2.4))
card1.fill.solid()
card1.fill.fore_color.rgb = CARD_COLOR
card1.line.color.rgb = CARD_BORDER
tf1 = card1.text_frame
tf1.word_wrap = True
p_c1 = tf1.paragraphs[0]
r = p_c1.add_run()
r.text = "PRESENTED BY (TEAM MEMBERS)\n\n"
r.font.bold = True
r.font.size = Pt(13)
r.font.color.rgb = GOLD

for name in ["Swarnava Chaudhuri", "Chiranshee Rustagi", "Sparsh Singh"]:
    p = tf1.add_paragraph()
    r = p.add_run()
    r.text = f"•  {name}"
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = TEXT_WHITE

# Meta Card 2: Guide
card2 = s0.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.0), Inches(3.8), Inches(4.8), Inches(2.4))
card2.fill.solid()
card2.fill.fore_color.rgb = CARD_COLOR
card2.line.color.rgb = CARD_BORDER
tf2 = card2.text_frame
tf2.word_wrap = True
p_c2 = tf2.paragraphs[0]
r = p_c2.add_run()
r.text = "GUIDED BY\n\n"
r.font.bold = True
r.font.size = Pt(13)
r.font.color.rgb = GOLD

p_g = tf2.add_paragraph()
r = p_g.add_run()
r.text = "Dr. Debashish Dash"
r.font.size = Pt(18)
r.font.bold = True
r.font.color.rgb = TEXT_WHITE

# ==========================================
# SLIDE 1: CORE NOVELTY
# ==========================================
s1 = prs.slides.add_slide(prs.slide_layouts[6])
apply_background(s1)
add_header(s1, "Core Novelty:", "Pre-Impact Prediction vs. Post-Fall Alarms")
add_bullets(s1, [
    ("Conventional Flaw", "Existing systems are reactive—triggering only after the user strikes the ground with 0 ms lead time."),
    ("Our Novel Paradigm", "We intercept the descending flight phase, alerting 200–400 ms before floor contact."),
    ("Direct Injury Prevention", "Shifts the clinical goal from summoning help post-injury to active mid-air trauma prevention."),
    ("Wearable Airbag Integration", "Output signal is engineered to trigger fast-inflating hip airbags instead of just sounding a buzzer."),
    ("Autonomous Edge Action", "100% on-device embedded inference guarantees deterministic triggering without wireless lag.")
])

# Card Box
c_box = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(1.6), Inches(4.5), Inches(5.0))
c_box.fill.solid()
c_box.fill.fore_color.rgb = CARD_COLOR
c_box.line.color.rgb = GOLD
tf_c = c_box.text_frame
tf_c.word_wrap = True
p = tf_c.paragraphs[0]
r = p.add_run()
r.text = "PARADIGM SHIFT METRIC\n\n"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = GOLD

p = tf_c.add_paragraph()
r = p.add_run()
r.text = "Traditional Detectors:\n0 ms Lead Time\n(Triggers after fracture)\n\n"
r.font.size = Pt(14)
r.font.color.rgb = RED

p = tf_c.add_paragraph()
r = p.add_run()
r.text = "Proposed Smart Insole:\n~250 ms Pre-Impact Window\n(Airbag Inflates Mid-Air)"
r.font.bold = True
r.font.size = Pt(16)
r.font.color.rgb = GREEN

# ==========================================
# SLIDE 2: BIOMECHANICAL ADVANTAGE
# ==========================================
s2 = prs.slides.add_slide(prs.slide_layouts[6])
apply_background(s2)
add_header(s2, "Biomechanical Advantage:", "Why the Footwear Insole?")
add_bullets(s2, [
    ("Direct GRF", "Directly measures foot-ground contact forces where postural stability is mechanically maintained."),
    ("True Base of Support", "Plantar pressure tracking eliminates gesture motion artifacts and non-fall transient noise."),
    ("Early Gait Warning", "Captures stance-phase loading asymmetry and heel-strike collapse 250–400 ms prior to impact."),
    ("High Sensitivity", "Direct Center of Pressure (COP) monitoring yields ~93–96% sensitivity with minimal false alarms."),
    ("Seamless Daily Wear", "Ergonomically integrated beneath the foot, requiring no active user intervention.")
])

c_box2 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(1.6), Inches(4.5), Inches(5.0))
c_box2.fill.solid()
c_box2.fill.fore_color.rgb = CARD_COLOR
c_box2.line.color.rgb = CARD_BORDER
tf_c2 = c_box2.text_frame
tf_c2.word_wrap = True
p = tf_c2.paragraphs[0]
r = p.add_run()
r.text = "PLANTAR ADVANTAGE\n\n"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = GOLD

for line in [
    ("Kinematic Origin", "Plantar Contact Base"),
    ("Signal Fidelity", "Direct GRF Tracking"),
    ("Sensitivity", "~93–96% Validated"),
    ("Lead Window", "250–400 ms")
]:
    p = tf_c2.add_paragraph()
    r1 = p.add_run()
    r1.text = f"{line[0]}: "
    r1.font.size = Pt(13)
    r1.font.color.rgb = TEXT_MUTED
    r2 = p.add_run()
    r2.text = f"{line[1]}\n"
    r2.font.bold = True
    r2.font.size = Pt(14)
    r2.font.color.rgb = TEXT_WHITE

# ==========================================
# SLIDE 3: HARDWARE & SENSOR SUITE
# ==========================================
s3 = prs.slides.add_slide(prs.slide_layouts[6])
apply_background(s3)
add_header(s3, "Smart Insole:", "Hardware & Sensor Suite")
add_bullets(s3, [
    ("5-Point FSR Matrix", "Piezoresistive array located at the heel, 3 metatarsal heads, and hallux (great toe)."),
    ("6-Axis MPU-6050 IMU", "Configured at ±8g (accel) and ±500°/s (gyro) with onboard DMP quaternion filtering."),
    ("BMP280 Altimeter", "0.16 hPa barometric resolution (~1.3 m altitude sensitivity) for rapid vertical drop validation."),
    ("Thickness Constraint", "Flex-PCB assembly kept under 8 mm to fit standard therapeutic footwear."),
    ("Heel Pod Module", "Houses ESP32-S3 MCU, IMU, altimeter, and LiPo flat cell encapsulated in flexible TPU.")
])

c_box3 = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(1.6), Inches(4.5), Inches(5.0))
c_box3.fill.solid()
c_box3.fill.fore_color.rgb = CARD_COLOR
c_box3.line.color.rgb = CARD_BORDER
tf_c3 = c_box3.text_frame
tf_c3.word_wrap = True
p = tf_c3.paragraphs[0]
r = p.add_run()
r.text = "INSOLE STACKUP (<8 mm)\n\n"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = GOLD

for layer in [
    "Layer 1: Moisture-Wicking Foam",
    "Layer 2: 5× FSR-402 Matrix (Flex-PCB)",
    "Layer 3: Heel Pod (ESP32-S3 + IMU)",
    "Layer 4: 3.7V Flat LiPo Cell",
    "Layer 5: Protective Rubber/TPU Sole"
]:
    p = tf_c3.add_paragraph()
    p.space_after = Pt(10)
    r = p.add_run()
    r.text = f"▪  {layer}"
    r.font.size = Pt(13)
    r.font.color.rgb = TEXT_WHITE

# ==========================================
# SLIDE 4: GAIT DYNAMICS & BUTTERFLY LOOPS
# ==========================================
s4 = prs.slides.add_slide(prs.slide_layouts[6])
apply_background(s4)
add_header(s4, "Gait Kinematics &", "Center of Pressure Butterfly Loops")
add_bullets(s4, [
    ("Gait Phase Ratio", "Normal ambulation maintains 60% stance phase (heel-strike to toe-off) and 40% swing phase."),
    ("Step Variability Index", "Elevated step-time coefficient of variation correlates directly with prodromal fall risk."),
    ("COP Butterfly Loop", "Continuous bipedal weight transfers produce a smooth, symmetric intersecting butterfly loop."),
    ("Pre-Fall Collapse", "Stumble onset causes immediate loop deformation, lateral lobe collapse, and sudden COP excursion."),
    ("Cross-Modal Unloading", "Simultaneous FSR unweighting and altitude drop flags true loss of balance.")
])

c_box4 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(1.6), Inches(4.5), Inches(5.0))
c_box4.fill.solid()
c_box4.fill.fore_color.rgb = CARD_COLOR
c_box4.line.color.rgb = CARD_BORDER
tf_c4 = c_box4.text_frame
tf_c4.word_wrap = True
p = tf_c4.paragraphs[0]
r = p.add_run()
r.text = "BUTTERFLY LOOP DYNAMICS\n\n"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = GOLD

p = tf_c4.add_paragraph()
p.space_after = Pt(14)
r = p.add_run()
r.text = "Normal Gait Pattern:\n"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = GREEN
r2 = p.add_run()
r2.text = "Symmetrical lobes, balanced medial-lateral weight transfer, repeatable heel strikes."
r2.font.size = Pt(12)
r2.font.color.rgb = TEXT_WHITE

p2 = tf_c4.add_paragraph()
r = p2.add_run()
r.text = "Pre-Fall Instability Pattern:\n"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = RED
r2 = p2.add_run()
r2.text = "Asymmetric lobe collapse, COP outside support base, sudden stance shortening."
r2.font.size = Pt(12)
r2.font.color.rgb = TEXT_WHITE

# ==========================================
# SLIDE 5: DUAL-TIER TINYML ENGINE
# ==========================================
s5 = prs.slides.add_slide(prs.slide_layouts[6])
apply_background(s5)
add_header(s5, "Dual-Tier Decision Engine:", "50 Hz TinyML Pipeline")
add_bullets(s5, [
    ("50 Hz Pipeline", "2nd-order Butterworth LPF (25 Hz cutoff) feeds a 1-second sliding window (50 samples)."),
    ("Tier 1 Fast Gate", "Instant resultant vector check |a| < 0.5g evaluates in < 0.1 ms during the free-fall dip."),
    ("Tier 2 Deep 1D-CNN", "Temporal convolutional network evaluates multi-axis dynamic context across all 50 frames."),
    ("False Alarm Rejection", "Suppresses false triggers from benign daily activities like fast sitting or stair descent."),
    ("Closed-Loop Action", "Zero cloud dependency guarantees sub-20 ms deterministic real-time execution.")
])

c_box5 = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(1.6), Inches(4.5), Inches(5.0))
c_box5.fill.solid()
c_box5.fill.fore_color.rgb = CARD_COLOR
c_box5.line.color.rgb = GOLD
tf_c5 = c_box5.text_frame
tf_c5.word_wrap = True
p = tf_c5.paragraphs[0]
r = p.add_run()
r.text = "EDGE TIMING & BUDGET\n\n"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = GOLD

for item in [
    ("Loop Time Limit", "20.0 ms (50 Hz)"),
    ("Tier 1 Heuristic", "< 0.1 ms"),
    ("Tier 2 INT8 1D-CNN", "12.5 ms"),
    ("Memory Footprint", "19 KB SRAM"),
    ("Remaining Headroom", "37.5% CPU Surplus")
]:
    p = tf_c5.add_paragraph()
    r1 = p.add_run()
    r1.text = f"{item[0]}: "
    r1.font.size = Pt(13)
    r1.font.color.rgb = TEXT_MUTED
    r2 = p.add_run()
    r2.text = f"{item[1]}\n"
    r2.font.bold = True
    r2.font.size = Pt(14)
    r2.font.color.rgb = TEXT_WHITE

# ==========================================
# SLIDE 6: WEARABLE AIRBAG ACTUATION
# ==========================================
s6 = prs.slides.add_slide(prs.slide_layouts[6])
apply_background(s6)
add_header(s6, "Active Safety:", "Wearable Airbag & Actuation")
add_bullets(s6, [
    ("Replacing the Buzzer", "While a buzzer only warns, the GPIO output pin directly deploys active pyrotechnic/gas airbags."),
    ("Airbag Inflation Speed", "Wearable hip airbags require 100–150 ms to achieve full protective pressurization."),
    ("Our 250 ms Advantage", "Provides the critical window required to fully inflate before the hip makes floor contact."),
    ("Dual-Stage Response", "Insole haptic motor prompts voluntary bracing while the airbag absorbs physical impact energy."),
    ("Fracture Elimination", "Attenuates ground collision deceleration forces below clinical bone fracture thresholds.")
])

c_box6 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(1.6), Inches(4.5), Inches(5.0))
c_box6.fill.solid()
c_box6.fill.fore_color.rgb = CARD_COLOR
c_box6.line.color.rgb = GREEN
tf_c6 = c_box6.text_frame
tf_c6.word_wrap = True
p = tf_c6.paragraphs[0]
r = p.add_run()
r.text = "AIRBAG DEPLOYMENT TIMELINE\n\n"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = GOLD

for step in [
    ("t = 0 ms", "Balance Loss Perturbation"),
    ("t = 70 ms", "TinyML Flags Fall (Pin HIGH)"),
    ("t = 220 ms", "Airbag Fully Inflated"),
    ("t = 320 ms", "Floor Collision (Impact Absorbed)")
]:
    p = tf_c6.add_paragraph()
    r1 = p.add_run()
    r1.text = f"{step[0]}: "
    r1.font.bold = True
    r1.font.size = Pt(13)
    r1.font.color.rgb = GREEN
    r2 = p.add_run()
    r2.text = f"{step[1]}\n"
    r2.font.size = Pt(13)
    r2.font.color.rgb = TEXT_WHITE

# ==========================================
# SLIDE 7: LIVE TELEMETRY EMULATION
# ==========================================
s7 = prs.slides.add_slide(prs.slide_layouts[6])
apply_background(s7)
add_header(s7, "Hardware-in-the-Loop:", "Live Emulation Results")
add_bullets(s7, [
    ("Deterministic Playback", "Evaluated on real 50 Hz motion data windows from public benchmarks (KFall & SisFall)."),
    ("Normal Walking (ADL #0)", "Smooth profile (|a| ≈ 1.0g), Tier 1 stable, 99.8% normal confidence with zero false alarms."),
    ("Pre-Fall Instability (#1350)", "Resultant gravity dips to 0.28g at 0.85 s; Tier 1 triggers instant neural escalation."),
    ("Neural Confirmation", "Pre-fall confidence surges to 94.5% well before any ground impact collision."),
    ("Standalone Web Engine", "Zero-server embedded telemetry dashboard renders waveforms and triggers acoustic alarm.")
])

c_box7 = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(1.6), Inches(4.5), Inches(5.0))
c_box7.fill.solid()
c_box7.fill.fore_color.rgb = CARD_COLOR
c_box7.line.color.rgb = GOLD
tf_c7 = c_box7.text_frame
tf_c7.word_wrap = True
p = tf_c7.paragraphs[0]
r = p.add_run()
r.text = "LIVE DASHBOARD STATUS\n\n"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = GOLD

p = tf_c7.add_paragraph()
r = p.add_run()
r.text = "ADL Gait Test:\nNormal Baseline (99.8%)\n|a| = 0.98g (No Alarm)\n\n"
r.font.size = Pt(13)
r.font.color.rgb = GREEN

p2 = tf_c7.add_paragraph()
r = p2.add_run()
r.text = "Fall Event #1350:\nPre-Fall Flagged (94.5%)\nResultant = 0.28g (Pin HIGH)\nLead Time = ~250 ms"
r.font.bold = True
r.font.size = Pt(14)
r.font.color.rgb = RED

# ==========================================
# SLIDE 8: BOM & CONCLUSION
# ==========================================
s8 = prs.slides.add_slide(prs.slide_layouts[6])
apply_background(s8)
add_header(s8, "Costing (INR) &", "Conclusion & Roadmap")
add_bullets(s8, [
    ("Low Prototype Cost", "Complete 5-point FSR insole prototype manufactured for ₹2,100."),
    ("Mass Scale-Up", "Projected bill of materials decreases by ~60% to ≈ ₹850 in production volumes."),
    ("Proven Lead Window", "Demonstrated a ~250 ms pre-impact window for stepping recovery or airbag inflation."),
    ("Edge Feasibility", "Requires only 19 KB of SRAM and runs in 12.5 ms, confirming suitability for microcontrollers."),
    ("Future Roadmap", "Dual-insole wireless synchronization and on-device continuous calibration.")
])

# Table on Right
rows, cols = 6, 2
left, top, width, height = Inches(8.0), Inches(1.6), Inches(4.5), Inches(4.8)
table_shape = s8.shapes.add_table(rows, cols, left, top, width, height)
table = table_shape.table
table.columns[0].width = Inches(3.2)
table.columns[1].width = Inches(1.3)

bom_data = [
    ("ESP32-S3 Dual-Core Module", "₹480"),
    ("5× FSR-402 Matrix Array", "₹600"),
    ("MPU-6050 6-Axis IMU", "₹150"),
    ("BMP280 Altimeter + LiPo", "₹310"),
    ("Flex-PCB & TPU Assembly", "₹560"),
    ("Total Prototype Unit BOM", "₹2,100")
]

for row_idx, (comp, cost) in enumerate(bom_data):
    cell_a = table.cell(row_idx, 0)
    cell_b = table.cell(row_idx, 1)
    
    cell_a.fill.solid()
    cell_a.fill.fore_color.rgb = CARD_COLOR
    cell_b.fill.solid()
    cell_b.fill.fore_color.rgb = CARD_COLOR
    
    cell_a.text = comp
    cell_b.text = cost
    
    for c in [cell_a, cell_b]:
        p = c.text_frame.paragraphs[0]
        p.runs[0].font.size = Pt(12)
        p.runs[0].font.color.rgb = GOLD if row_idx == 5 else TEXT_WHITE
        if row_idx == 5:
            p.runs[0].font.bold = True

# Save PPTX
output_filename = "presentation_deck.pptx"
prs.save(output_filename)
print(f"[SUCCESS] Native PowerPoint presentation generated: {output_filename}")