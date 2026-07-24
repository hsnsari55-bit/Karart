import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import fs from "fs";
import { spawn, execSync } from "child_process";

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Ensure outputs and run initial parsing if missing
  const outputsDir = path.join(process.cwd(), "outputs");
  if (!fs.existsSync(outputsDir)) {
    fs.mkdirSync(outputsDir, { recursive: true });
  }
  const dxfRawPath = path.join(outputsDir, "dxf_raw.json");
  if (!fs.existsSync(dxfRawPath)) {
    console.log("[KaRar] Initializing default project parsing for GÜZELCE 467 ADA 3 PARSEL...");
    try {
      const pythonCmd = fs.existsSync(path.join(process.cwd(), "venv", "bin", "python3"))
        ? "venv/bin/python3"
        : "python3";
      execSync(`PYTHONPATH=. ${pythonCmd} backend/run_regression_tests.py`, { stdio: "inherit" });
    } catch (e) {
      console.warn("[KaRar] Auto-parsing on startup warning:", e);
    }
  }

  // LAZY INITIALIZER FOR GEMINI API
  let aiClient: GoogleGenAI | null = null;
  function getGeminiClient() {
    if (!aiClient) {
      const apiKey = process.env.GEMINI_API_KEY;
      if (!apiKey) {
        throw new Error("GEMINI_API_KEY is not defined in environment variables.");
      }
      aiClient = new GoogleGenAI({ apiKey });
    }
    return aiClient;
  }

  // API ROUTES
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", message: "KaRar Backend is running." });
  });

  // GET PROJECT DATA STAGES
  app.get("/api/project-data", (req, res) => {
    const dxfRawPath = path.join(process.cwd(), "outputs", "dxf_raw.json");
    const wallsCleanPath = path.join(process.cwd(), "outputs", "walls_clean.json");
    const bimCleanPath = path.join(process.cwd(), "outputs", "bim_model.json");
    const spacesPath = path.join(process.cwd(), "outputs", "spaces.json");

    const response: any = {};

    if (fs.existsSync(dxfRawPath)) {
      try {
        response.cad = JSON.parse(fs.readFileSync(dxfRawPath, "utf-8"));
      } catch (e) {}
    }
    if (fs.existsSync(wallsCleanPath)) {
      try {
        response.walls = JSON.parse(fs.readFileSync(wallsCleanPath, "utf-8"));
      } catch (e) {}
    }
    if (fs.existsSync(bimCleanPath)) {
      try {
        response.bim = JSON.parse(fs.readFileSync(bimCleanPath, "utf-8"));
      } catch (e) {}
    }
    if (fs.existsSync(spacesPath)) {
      try {
        response.spaces = JSON.parse(fs.readFileSync(spacesPath, "utf-8"));
      } catch (e) {}
    }


    res.json(response);
  });

  // RUN PIPELINE STEP ENDPOINT
  const stepCommands: Record<string, string> = {
    parsing: "PYTHONPATH=. python3 backend/dxf_parser.py",
    geometry: "PYTHONPATH=. python3 backend/geometry_engine.py",
    topology: "PYTHONPATH=. python3 backend/topology_engine.py",
    semantic: "PYTHONPATH=. python3 backend/semantic_engine.py",
    spaces: "PYTHONPATH=. python3 backend/space_engine.py",
    core: "PYTHONPATH=. python3 backend/bim_core.py",
  };

  app.post("/api/run-step", (req, res) => {
    const { stepId, fileName, blockId } = req.body;
    if (!stepId || !stepCommands[stepId]) {
      return res.status(400).json({ error: `Invalid stepId provided: ${stepId}` });
    }

    let command = stepCommands[stepId];
    if (stepId === "parsing" && fileName) {
      const safeFileName = path.basename(fileName);
      let blockFilter = "";
      if (blockId === "block_a") blockFilter = "467-3 A BLOK A-A";
      else if (blockId === "block_b") blockFilter = "467-3 B BLOK A-A";
      else if (blockId === "block_c") blockFilter = "467-3 A BLOK B-B";
      else if (blockId === "block_d") blockFilter = "467-3 B BLOK B-B";
      else if (blockId === "block_savak") blockFilter = "SAVAK";

      if (blockFilter) {
        command = `PYTHONPATH=. venv/bin/python3 backend/dxf_parser.py "data/${safeFileName}" "${blockFilter}"`;
      } else {
        command = `PYTHONPATH=. venv/bin/python3 backend/dxf_parser.py "data/${safeFileName}"`;
      }
    } else {
      command = command.replace("python3", "venv/bin/python3");
    }

    res.setHeader("Content-Type", "text/plain; charset=utf-8");
    res.setHeader("Transfer-Encoding", "chunked");

    const child = spawn(command, [], { shell: true });

    child.stdout.on("data", (data) => {
      res.write(data);
    });

    child.stderr.on("data", (data) => {
      res.write(data);
    });

    child.on("close", (code) => {
      if (code !== 0) {
        res.write(`\n[ERROR] Process exited with code ${code}\n`);
      }
      res.end();
    });

    child.on("error", (error) => {
      res.write(`\n[ERROR] Failed to start process: ${error.message}\n`);
      res.end();
    });
  });

  // GEMINI CHAT ENDPOINT
  app.post("/api/chat", async (req, res) => {
    try {
      const { message, history } = req.body;
      if (!message) {
        return res.status(400).json({ error: "Message is required." });
      }

      let responseText = "";

      try {
        const ai = getGeminiClient();
        
        // Structure system prompt with details about the parsed CAD design
        const systemInstruction = `You are the KaRar AI Assistant, an elite architectural AI & structural engineering agent integrated into the KaRar CAD-to-BIM platform.
The user is viewing their analyzed CAD blueprint (Twin Villa Project, 'GÜZELCE 467 ADA 9 PARSEL').

Here is the current architectural intelligence summary for the project:
1. CAD Segmentation:
   - Total Entities: 12,049 vectors (Lines, Arcs, Polylines)
   - Total Text Entities: 1,794 tags
   - Total Regions: 12 distinct sub-drawings
   - Structure Type: Twin Villa (A Blok & B Blok)
   - Floor levels detected: Bodrum Kat (Basement), Zemin Kat (Ground), 1. Normal Kat, Çatı Katı (Attic).
2. Layers parsed:
   - 'duvar' (Walls - structural layers containing wall outlines, thickness 20cm/25cm for main walls, 10cm/15cm for partition walls)
   - 'kapı' (Doors - widths ranging from 70cm to 100cm)
   - 'k pencere' (Windows - multiple window openings on exterior walls)
   - 'aks' (Grid axes for columns alignment)
   - 'kolon' (Structural load-bearing columns)
3. Coordinate Normalizer Offset:
   - X Offset: 18,274.87, Y Offset: 16,346.3 (used to normalize CAD drawings to coordinate origin)
4. Scale Calibration:
   - ~32.0 mm per DXF unit

Answer the user's questions about this drawing, BIM, construction, geometry snapping, or general CAD-to-3D questions.
Keep answers professional, insightful, and concise. Since the interface is in Turkish/English, feel free to respond in Turkish if the query is in Turkish, or English if the query is in English. Use elegant markdown styling.`;

        // Map client history to Gemini format if provided
        const formattedHistory = (history || []).map((h: any) => ({
          role: h.role === "user" ? "user" : "model",
          parts: [{ text: h.content }]
        }));

        // Call Gemini using the recommended model
        const response = await ai.models.generateContent({
          model: "gemini-2.5-flash",
          contents: [
            ...formattedHistory,
            { role: "user", parts: [{ text: message }] }
          ],
          config: {
            systemInstruction,
            temperature: 0.7,
          }
        });

        responseText = response.text || "Özür dilerim, cevap üretemedim.";
      } catch (geminiError: any) {
        console.warn("Gemini API call failed, falling back to local simulation:", geminiError.message);
        
        // Intelligent fallback simulator for local/offline mode
        const msgLower = message.toLowerCase();
        if (msgLower.includes("kapı") || msgLower.includes("door")) {
          responseText = "**KaRar AI (Çevrimdışı Simülasyon)**:\n\nProjede **'kapı'** katmanında yapılan geometrik analiz sonucunda toplam **34 adet kapı** tespit edilmiştir. Bunlar çoğunlukla tek kanatlı (Single Swing) kapılardır ve genişlikleri 70cm ile 100cm arasında değişmektedir. Çatı katında çift kanatlı sürgülü kapı izlerine de rastlanmıştır.";
        } else if (msgLower.includes("duvar") || msgLower.includes("wall") || msgLower.includes("thickness")) {
          responseText = "**KaRar AI (Çevrimdışı Simülasyon)**:\n\nDuvar kalınlık analizimiz şunları göstermektedir:\n- **Dış Duvarlar**: Ortalama **20.0 cm** ile **25.0 cm** kalınlığında (Yalıtımlı / Taşıyıcı).\n- **İç Bölme Duvarları**: Ortalama **10.0 cm** ile **15.0 cm** kalınlığında.\n\nToplam **229 duvar segmenti** başarıyla birleştirilmiş ve T-birleşimleri (T-Junctions) temizlenmiştir.";
        } else if (msgLower.includes("oda") || msgLower.includes("room") || msgLower.includes("alan")) {
          responseText = "**KaRar AI (Çevrimdışı Simülasyon)**:\n\nOda sınır belirleme motoru (Room Detector Engine v2), duvar döngülerini (closed loops) tarayarak zemin katta **Salon (32.4 m²)**, **Mutfak (14.2 m²)** ve **Hol (8.5 m²)** dahil olmak üzere toplam **8 adet bağımsız bölüm** tespit etmiştir.";
        } else if (msgLower.includes("3d") || msgLower.includes("blender") || msgLower.includes("ifc")) {
          responseText = "**KaRar AI (Çevrimdışı Simülasyon)**:\n\nKaRar 3D İnşa motoru, tespit edilen 2D duvar, kapı ve pencereleri kullanarak parametrik bir **IFC** modeli oluşturur. Blender entegrasyonu yardımıyla `blender_builder.py` scripti üzerinden bu elemanları 3 boyutlu yükseltir. Şu anki web arayüzünde 3D BIM modelini anlık olarak interaktif WebGL (Three.js) üzerinden inceleyebilirsiniz!";
        } else {
          responseText = `**KaRar AI (Çevrimdışı Simülasyon)**: 

Sorunuzu aldım: "${message}". 
Şu anda API anahtarı eklenmemiş olduğundan çevrimdışı modda yanıt veriyorum. KaRar platformu, 2D mimari DXF dosyalarını analiz eder, duvar eksenlerini bulur ve bunları 3 boyutlu parametrik BIM modellerine dönüştürür. 

*İpucu: Sorunuzda 'duvar', 'kapı', 'oda' veya '3D' anahtar kelimelerini kullanarak detaylı simülasyonları tetikleyebilirsiniz.*`;
        }
      }

      return res.json({ response: responseText });
    } catch (error: any) {
      console.error("Server API Error:", error);
      return res.status(500).json({ error: error.message });
    }
  });

  // GET REGRESSION TESTING REPORT
  app.get("/api/regression-report", (req, res) => {
    const reportPath = path.join(process.cwd(), "outputs", "production_validation_report.json");
    if (fs.existsSync(reportPath)) {
      try {
        const report = JSON.parse(fs.readFileSync(reportPath, "utf-8"));
        return res.json(report);
      } catch (e: any) {
        return res.status(500).json({ error: "Failed to parse regression report JSON" });
      }
    }
    return res.status(404).json({ error: "Regression report not found. Run regression first." });
  });

  // RUN ALL REGRESSION TESTS
  app.post("/api/run-regression", (req, res) => {
    const command = "PYTHONPATH=. venv/bin/python3 backend/run_regression_tests.py";
    
    res.setHeader("Content-Type", "text/plain; charset=utf-8");
    res.setHeader("Transfer-Encoding", "chunked");

    const child = spawn(command, [], { shell: true });

    child.stdout.on("data", (data) => {
      res.write(data);
    });

    child.stderr.on("data", (data) => {
      res.write(data);
    });

    child.on("close", (code) => {
      if (code !== 0) {
        res.write(`\n[ERROR] Process exited with code ${code}\n`);
      }
      res.end();
    });

    child.on("error", (error) => {
      res.write(`\n[ERROR] Failed to start process: ${error.message}\n`);
      res.end();
    });
  });

  // Serve static files in production or hook Vite in development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`[KaRar Server] Running at http://localhost:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error("Failed to start server:", err);
});
