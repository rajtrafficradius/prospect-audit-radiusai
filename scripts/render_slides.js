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
    const page = await browser.newPage({
        viewport: { width: 1920, height: 1080 }
    });

    console.log(`Starting render for ${slidesData.length} slides...`);

    for (let i = 0; i < slidesData.length; i++) {
        const slide = slidesData[i];
        const slideNum = (i + 1).toString().padStart(2, '0');
        
        await page.setContent(templateHtml);

        // Inject data via DOM manipulation - 100% reliable
        await page.evaluate(({ data, sNum, sTotal }) => {
            const titleEl = document.getElementById('title');
            const subtitleEl = document.getElementById('subtitle');
            const quoteEl = document.getElementById('quote');
            const slideNumEl = document.getElementById('slide-num');
            const bulletList = document.getElementById('bullets');

            if (titleEl) titleEl.innerText = data.title;
            if (subtitleEl) subtitleEl.innerText = data.subtitle || '';
            if (quoteEl) quoteEl.innerHTML = data.quote || '';
            if (slideNumEl) slideNumEl.innerText = `SLIDE ${sNum} OF ${sTotal}`;

            if (bulletList) {
                bulletList.innerHTML = ''; // Clear placeholders
                (data.bullets || []).forEach(b => {
                    const li = document.createElement('li');
                    li.className = 'bullet-item';
                    li.innerHTML = `<div class="bullet-icon"></div><span>${b}</span>`;
                    bulletList.appendChild(li);
                });
            }
        }, { data: slide, sNum: slideNum, sTotal: slidesData.length });

        // Visual injection (Charts / Architecture)
        if (slide.visual) {
            let visualPath = "";
            const sessionPath = path.join(sessionDir, slide.visual);
            const projectRoot = path.dirname(__dirname);
            const rootStaticPath = path.join(projectRoot, "src", "static", "ppt_assets", path.basename(slide.visual));
            const rootLibPath = path.join(projectRoot, "src", slide.visual);
            
            if (fs.existsSync(sessionPath)) {
                visualPath = sessionPath;
            } else if (fs.existsSync(rootStaticPath)) {
                visualPath = rootStaticPath;
            } else if (fs.existsSync(rootLibPath)) {
                visualPath = rootLibPath;
            }

            if (visualPath && fs.existsSync(visualPath)) {
                const base64Image = fs.readFileSync(visualPath).toString('base64');
                await page.evaluate((b64) => {
                    const img = document.getElementById('visual');
                    if (img) img.src = `data:image/png;base64,${b64}`;
                }, base64Image);
            } else {
                console.warn(` [!] Warning: Visual not found: ${slide.visual}`);
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
