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
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.setViewportSize({ width: 1280, height: 720 }); // Standard PPT aspect ratio

    const logoPath = path.join(path.dirname(__dirname), 'src', 'static', 'logo.png');
    let logoBase64 = "";
    if (fs.existsSync(logoPath)) {
        logoBase64 = fs.readFileSync(logoPath).toString('base64');
    }

    console.log(`Starting render for ${slidesData.length} slides...`);

    for (let i = 0; i < slidesData.length; i++) {
        const slide = slidesData[i];
        const slideNum = (i + 1).toString().padStart(2, '0');
        
        await page.setContent(templateHtml);

        // Inject data via DOM manipulation
        await page.evaluate(({ data, sNum, sTotal, logoB64 }) => {
            // 1. Layout Selection
            document.body.className = `layout-${data.layout || 'split'}`;
            
            const titleEl = document.getElementById('title');
            const subtitleEl = document.getElementById('subtitle');
            const bigTitleEl = document.getElementById('big-title');
            const bigSubtitleEl = document.getElementById('big-subtitle');
            const quoteEl = document.getElementById('quote');
            const slideNumEl = document.getElementById('slide-num');
            const bulletList = document.getElementById('bullets');
            const logoImg = document.getElementById('logo-img');
            const logoText = document.getElementById('logo-text');
            const visualSection = document.getElementById('visual-section');

            // Header/Text injection
            if (titleEl) titleEl.innerText = data.title;
            if (subtitleEl) subtitleEl.innerText = data.subtitle || '';
            if (bigTitleEl) bigTitleEl.innerText = data.title;
            if (bigSubtitleEl) bigSubtitleEl.innerText = data.subtitle || '';
            if (quoteEl) {
                quoteEl.innerHTML = data.quote || '';
                if (!data.quote) quoteEl.style.display = 'none';
            }
            if (slideNumEl) slideNumEl.innerText = `SLIDE ${sNum} OF ${sTotal}`;

            // Logo Injection
            if (logoB64 && logoImg) {
                logoImg.src = `data:image/png;base64,${logoB64}`;
                logoImg.style.display = 'block';
                if (logoText) logoText.style.display = 'none';
            }

            // Bullets Injection
            if (bulletList) {
                bulletList.innerHTML = '';
                (data.bullets || []).forEach(b => {
                    const li = document.createElement('li');
                    li.className = 'bullet-item';
                    li.innerHTML = `<div class="bullet-icon"></div><span>${b}</span>`;
                    bulletList.appendChild(li);
                });
                if ((data.bullets || []).length === 0) bulletList.style.display = 'none';
            }

            // Visual Section visibility toggle
            if (data.layout === 'bullets' || data.layout === 'title' || data.layout === 'quote') {
                if (visualSection) visualSection.style.display = 'none';
            }
        }, { data: slide, sNum: slideNum, sTotal: slidesData.length, logoB64: logoBase64 });

        // Handle Image Path Resolution (relative to sessionDir)
        if (slide.visual) {
            let assetPath = path.join(sessionDir, slide.visual);
            if (fs.existsSync(assetPath)) {
                const imgData = fs.readFileSync(assetPath).toString('base64');
                await page.evaluate(({ b64 }) => {
                    const img = document.getElementById('visual-img');
                    if (img) img.src = `data:image/png;base64,${b64}`;
                }, { b64: imgData });
            } else {
                console.warn(` [!] Warning: Visual not found: ${slide.visual}`);
                await page.evaluate(() => {
                    const img = document.getElementById('visual-img');
                    const fb = document.getElementById('visual-fallback');
                    if (img) img.style.display = 'none';
                    if (fb) fb.style.display = 'flex';
                });
            }
        }

        await page.waitForLoadState('networkidle');
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
