const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function renderSlides(sessionDir, outputDir) {
    const dataPath = path.join(sessionDir, 'ppt_slides_data.json');
    const templatePath = path.join(__dirname, 'ppt_slide_template.html');
    
    if (!fs.existsSync(dataPath)) {
        console.error(`Error: Data file not found at ${dataPath}`);
        process.exit(1);
    }
    
    const slidesData = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
    const templateHtml = fs.readFileSync(templatePath, 'utf8');
    
    const browser = await chromium.launch({
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        deviceScaleFactor: 2 // Enable High-DPI (Retina) for 4K-ish quality
    });
    const page = await context.newPage();

    const logoPath = path.join(path.dirname(__dirname), 'src', 'static', 'logo.png');
    let logoBase64 = "";
    if (fs.existsSync(logoPath)) {
        logoBase64 = fs.readFileSync(logoPath).toString('base64');
    }

    console.log(`Starting render for ${slidesData.length} slides...`);

    for (let i = 0; i < slidesData.length; i++) {
        const slide = slidesData[i];
        const slideNum = (i + 1).toString().padStart(2, '0');
        
        // V9: Load Component HTML if archetype is present
        if (slide.archetype) {
            const componentPath = path.join(__dirname, 'components', `${slide.archetype}.html`);
            if (fs.existsSync(componentPath)) {
                slide.component_html = fs.readFileSync(componentPath, 'utf8');
            } else {
                console.warn(` [!] Archetype component not found: ${slide.archetype}`);
            }
        }

        await page.setContent(templateHtml);

        // Inject data via DOM manipulation
        await page.evaluate(({ slide, index, totalSlides, logoB64 }) => {
            // 1. Layout Selection & Visibility
            const layout = slide.layout || 'split';
            document.body.className = `layout-${layout}`;
            
            const titleEl = document.getElementById('title');
            const subtitleEl = document.getElementById('subtitle');
            const bigTitleEl = document.getElementById('big-title');
            const bigSubtitleEl = document.getElementById('big-subtitle');
            const titleLayoutCenter = document.getElementById('title-layout-center');
            const quoteEl = document.getElementById('quote');
            const slideNumEl = document.getElementById('slide-num');
            const bulletList = document.getElementById('bullets');
            const logoImg = document.getElementById('logo-img');
            const logoText = document.getElementById('logo-text');
            const visualSection = document.getElementById('visual-section');
            const footer = document.querySelector('.slide-footer');

            // Toggle Title Layout Container
            if (titleLayoutCenter) {
                titleLayoutCenter.style.display = (layout === 'title') ? 'flex' : 'none';
            }
            if (footer) {
                footer.style.display = (layout === 'title') ? 'none' : 'flex';
            }

            // Header/Text injection
            if (titleEl) titleEl.innerText = slide.title || '';
            if (subtitleEl) subtitleEl.innerText = slide.subtitle || '';
            if (bigTitleEl) bigTitleEl.innerText = slide.title || '';
            if (bigSubtitleEl) bigSubtitleEl.innerText = slide.subtitle || '';
            if (slideNumEl) slideNumEl.innerText = `SLIDE ${String(index + 1).padStart(2, '0')} OF ${totalSlides}`;

            // Logo Injection
            if (logoB64 && logoImg) {
                logoImg.src = `data:image/png;base64,${logoB64}`;
                logoImg.style.display = 'block';
                if (logoText) logoText.style.display = 'none';
            }

            // Bullets Injection with Auto-Scaling
            if (bulletList) {
                bulletList.innerHTML = '';
                const bullets = (slide.bullets || []);
                bullets.forEach(b => {
                    const li = document.createElement('li');
                    li.className = 'bullet-item';
                    li.innerHTML = `<div class="bullet-icon"></div><span>${b}</span>`;
                    bulletList.appendChild(li);
                });
                if (bullets.length === 0) {
                    bulletList.style.display = 'none';
                } else if (bullets.length > 6) {
                    bulletList.style.fontSize = '24px'; // Scale down for many bullets
                    bulletList.style.gap = '15px';
                } else {
                    bulletList.style.fontSize = '30px';
                    bulletList.style.gap = '25px';
                }
            }

            // Quote
            if (quoteEl) {
                if (slide.quote) {
                    quoteEl.innerHTML = `<strong>“</strong>${slide.quote}<strong>”</strong>`;
                    quoteEl.classList.remove('empty');
                } else {
                    quoteEl.innerHTML = '';
                    quoteEl.classList.add('empty');
                }
            }

            // LEGACY V8 SUPPORT (V9 component injection is handled outside this evaluate block)
            if (typeof window.renderDiagram === 'function') {
                if (slide.visual_type && slide.visual_data) {
                    window.renderDiagram(slide.visual_type, slide.visual_data);
                } else if (slide.visual) {
                    window.renderDiagram('image', slide.visual);
                }
            }

        }, { slide, index: i, totalSlides: slidesData.length, logoB64: logoBase64 });

        // Handle Image Path Resolution (relative to sessionDir) for 'image' type visuals
        // This needs to happen AFTER the page.evaluate call sets up the visual type
        // Handle Image Path Resolution (Only if type is image/undefined and visual is provided)
        const isDiagram = ['radar', 'pyramid', 'funnel', 'matrix'].includes(slide.visual_type);
        
        if (!isDiagram && slide.visual) {
            let assetPath = path.join(sessionDir, slide.visual);
            if (fs.existsSync(assetPath)) {
                const imgData = fs.readFileSync(assetPath).toString('base64');
                await page.evaluate(({ b64 }) => {
                    const img = document.getElementById('visual-img');
                    if (img) {
                        img.src = `data:image/png;base64,${b64}`;
                        img.style.display = 'block';
                    }
                    const fb = document.getElementById('visual-fallback');
                    if (fb) fb.style.display = 'none';
                }, { b64: imgData });
            } else {
                console.warn(` [!] Warning: Visual asset not found: ${slide.visual}`);
                await page.evaluate(() => {
                    const img = document.getElementById('visual-img');
                    const fb = document.getElementById('visual-fallback');
                    if (img) img.style.display = 'none';
                    if (fb) fb.style.display = 'flex';
                });
            }
        } else if (!isDiagram && !slide.visual) {
            // No visual provided and not a diagram - ensure fallback is hidden unless it's a layout that needs it
            await page.evaluate(() => {
                const fb = document.getElementById('visual-fallback');
                if (fb) fb.style.display = 'none';
            });
        }

        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000); // Give CSS diagrams extra time to settle
        const screenshotPath = path.join(outputDir, `slide_${slideNum}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log(` [+] Rendered slide ${slideNum}: ${screenshotPath}`);
    }

    await browser.close();
    console.log("Render complete.");
}

const sessionDir = process.argv[2];
const outputDir = path.join(sessionDir, 'rendered_slides');

if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

renderSlides(sessionDir, outputDir).catch(err => {
    console.error(err);
    process.exit(1);
});
