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
        
        // Simple string replacement for data injection
        let html = templateHtml
            .replace('id="title">Competitive Dominance', `id="title">${slide.title}`)
            .replace('id="subtitle">MARKET INTELLIGENCE & GAP ANALYSIS', `id="subtitle">${slide.subtitle || ''}`)
            .replace('id="quote">"Search is evolving from <strong>Links</strong> to <strong>Answers</strong>. This is your first-mover advantage."', `id="quote">${slide.quote || ''}`)
            .replace('id="slide-num">SLIDE 01 OF 15', `id="slide-num">SLIDE ${slideNum} OF ${slidesData.length}`);

        // Bullet points injection
        const bulletHtml = (slide.bullets || []).map(b => 
            `<li class="bullet-item"><div class="bullet-icon"></div><span>${b}</span></li>`
        ).join('');
        html = html.replace('<ul class="bullet-list" id="bullets">', `<ul class="bullet-list" id="bullets">${bulletHtml}`);
        
        // Remove the original placeholder bullets if they exist
        html = html.replace(/<li class="bullet-item">[\s\S]*?<\/li>/g, '');

        // Visual injection (Charts / Architecture)
        if (slide.visual) {
            let visualPath = "";
            
            // Priority 1: Check session directory (e.g. charts/)
            const sessionPath = path.join(sessionDir, slide.visual);
            // Priority 2: Check project root (e.g. src/static/ppt_assets/)
            const projectRoot = path.dirname(__dirname); // parent of scripts/
            const rootPath = path.join(projectRoot, "src", slide.visual);
            
            if (fs.existsSync(sessionPath)) {
                visualPath = sessionPath;
            } else if (fs.existsSync(rootPath)) {
                visualPath = rootPath;
            }

            if (visualPath && fs.existsSync(visualPath)) {
                const base64Image = fs.readFileSync(visualPath).toString('base64');
                html = html.replace('src="https://via.placeholder.com/800x600/1B2A4A/00CCFF?text=Data+Visualization"', `src="data:image/png;base64,${base64Image}"`);
            } else {
                console.warn(` [!] Warning: Visual not found: ${slide.visual}`);
            }
        }

        await page.setContent(html);
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
