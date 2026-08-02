#!/usr/bin/env node

import { existsSync, readFileSync, statSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

const rootDir = process.cwd();
const venvDirs = ["venv", ".venv"];
const pythonDeps = [
  "ezdxf",
  "shapely",
  "rtree",
  "scikit-learn",
  "numpy",
  "matplotlib",
  "trimesh",
  "ifcopenshell",
];
const topologyHealthReportRelativePath = path.join("outputs", "topology_health_report.json");
const targetedTestMap = {
  geometry: "backend.tests.test_modern_pipeline",
  topology: "backend.tests.test_topology_validator",
  pipeline: "backend.tests.test_modern_pipeline",
  bim: "backend.tests.test_regression_bim_core_opening_parent_wall",
  regression: "backend.tests.test_regression_topology_report_path",
};

function isWindows() {
  return process.platform === "win32";
}

function getNpmCommand() {
  return isWindows() ? "npm.cmd" : "npm";
}

function getNpmRunner() {
  const npmExecPath = process.env.npm_execpath;
  if (npmExecPath && existsSync(npmExecPath)) {
    return {
      command: process.execPath,
      prefixArgs: [npmExecPath],
      label: "npm (npm_execpath)",
    };
  }

  return {
    command: getNpmCommand(),
    prefixArgs: [],
    label: getNpmCommand(),
  };
}

function getVenvPythonCandidates() {
  return venvDirs.flatMap((venvDir) => [
    path.join(rootDir, venvDir, "Scripts", "python.exe"),
    path.join(rootDir, venvDir, "bin", "python3"),
    path.join(rootDir, venvDir, "bin", "python"),
  ]);
}

function findExistingVenvPython() {
  return getVenvPythonCandidates().find((candidate) => existsSync(candidate)) ?? null;
}

function trySpawn(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: rootDir,
    env: { ...process.env, ...(options.env ?? {}) },
    encoding: "utf8",
    shell: false,
    stdio: options.captureOutput ? "pipe" : "inherit",
  });

  return {
    ok: !result.error && result.status === 0,
    status: result.status ?? 1,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
    error: result.error ?? null,
  };
}

function runOrExit(command, args, options = {}) {
  const result = trySpawn(command, args, options);
  if (!result.ok) {
    if (result.error) {
      console.error(`Komut çalıştırılamadı: ${command} ${args.join(" ")}`);
      console.error(result.error.message);
    }
    process.exit(result.status || 1);
  }
  return result;
}

function runNpm(args, options = {}) {
  const runner = getNpmRunner();
  return runOrExit(runner.command, [...runner.prefixArgs, ...args], options);
}

function detectSystemPython() {
  const candidates = isWindows()
    ? [
        { command: "py", args: ["-3", "--version"], label: "py -3" },
        { command: "python", args: ["--version"], label: "python" },
      ]
    : [
        { command: "python3", args: ["--version"], label: "python3" },
        { command: "python", args: ["--version"], label: "python" },
      ];

  for (const candidate of candidates) {
    const result = trySpawn(candidate.command, candidate.args, { captureOutput: true });
    if (result.ok) {
      return {
        command: candidate.command,
        argsPrefix: candidate.args.slice(0, -1),
        label: candidate.label,
        version: (result.stdout || result.stderr).trim(),
      };
    }
  }

  return null;
}

function resolvePythonForWork() {
  const venvPython = findExistingVenvPython();
  if (venvPython) {
    return { command: venvPython, argsPrefix: [], source: "venv" };
  }

  const systemPython = detectSystemPython();
  if (systemPython) {
    return {
      command: systemPython.command,
      argsPrefix: systemPython.argsPrefix,
      source: systemPython.label,
    };
  }

  return null;
}

function runPython(pythonConfig, args) {
  return runOrExit(pythonConfig.command, [...pythonConfig.argsPrefix, ...args], {
    env: { PYTHONPATH: rootDir },
  });
}

function printHeader(title) {
  console.log(`\n=== ${title} ===`);
}

function readTextFileIfExists(relativePath) {
  const filePath = path.join(rootDir, relativePath);
  if (!existsSync(filePath)) {
    return null;
  }

  return readFileSync(filePath, "utf8");
}

function readJsonFileIfExists(relativePath) {
  const text = readTextFileIfExists(relativePath);
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch (error) {
    console.error(`JSON parse hatası (${relativePath}): ${error instanceof Error ? error.message : String(error)}`);
    return null;
  }
}

function getFileModifiedAt(relativePath) {
  const filePath = path.join(rootDir, relativePath);
  if (!existsSync(filePath)) {
    return null;
  }

  return statSync(filePath).mtime;
}

function extractBulletValue(text, label) {
  if (!text) {
    return null;
  }

  const escapedLabel = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`^-\\s+(?:\\*\\*)?${escapedLabel}(?:\\*\\*)?:\\s*(.+)$`, "m");
  const match = text.match(regex);
  return match?.[1]?.trim() ?? null;
}

function normalizeMarkdownValue(value) {
  if (!value) {
    return null;
  }

  const normalized = value
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^[-*]\s+/, "")
    .replace(/\s+/g, " ")
    .trim();

  return normalized || null;
}

function extractFirstBulletValue(text, labels) {
  for (const label of labels) {
    const value = extractBulletValue(text, label);
    if (value) {
      return value;
    }
  }

  return null;
}

function extractStructuredBulletValue(text, label) {
  if (!text) {
    return null;
  }

  const escapedLabel = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const lines = text.split(/\r?\n/);
  const headerRegex = new RegExp(`^\\s*-\\s+(?:\\*\\*)?${escapedLabel}(?:\\*\\*)?:\\s*(.*)$`);

  for (let index = 0; index < lines.length; index += 1) {
    const match = lines[index].match(headerRegex);
    if (!match) {
      continue;
    }

    const inlineValue = normalizeMarkdownValue(match[1]);
    if (inlineValue) {
      return inlineValue;
    }

    const nestedValues = [];

    for (let cursor = index + 1; cursor < lines.length; cursor += 1) {
      const line = lines[cursor];

      if (/^\s*##\s+/.test(line)) {
        break;
      }

      const bulletMatch = line.match(/^(\s*)-\s+(.+)$/);
      if (bulletMatch) {
        const indent = bulletMatch[1].length;
        const bulletValue = normalizeMarkdownValue(bulletMatch[2])?.replace(/[;,]\s*$/, "");

        if (indent >= 2) {
          if (bulletValue) {
            nestedValues.push(bulletValue);
          }
          continue;
        }

        break;
      }

      if (nestedValues.length > 0 && line.trim() === "") {
        continue;
      }

      if (nestedValues.length > 0 && !/^\s+/.test(line)) {
        break;
      }
    }

    if (nestedValues.length > 0) {
      return nestedValues.join("; ");
    }
  }

  return null;
}

function extractFirstStructuredBulletValue(text, labels) {
  for (const label of labels) {
    const value = extractStructuredBulletValue(text, label);
    if (value) {
      return value;
    }
  }

  return null;
}

function extractInlineCodeValue(text, label) {
  const value = extractBulletValue(text, label);
  if (!value) {
    return null;
  }

  const inlineCodeMatch = value.match(/`([^`]+)`/);
  return inlineCodeMatch?.[1] ?? value;
}

function extractFirstInlineCodeValue(text, labels) {
  const value = extractFirstBulletValue(text, labels);
  if (!value) {
    return null;
  }

  const inlineCodeMatch = value.match(/`([^`]+)`/);
  return inlineCodeMatch?.[1] ?? value;
}

function extractBacktickList(text) {
  if (!text) {
    return [];
  }

  return [...text.matchAll(/`([^`]+)`/g)].map((match) => match[1]);
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function relativeDocPath(relativePath) {
  return relativePath.replace(/\\/g, "/");
}

function getGitStatusLines() {
  const result = trySpawn("git", ["status", "--short"], { captureOutput: true });
  if (!result.ok) {
    return [];
  }

  return result.stdout
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter(Boolean);
}

function getGitBranch() {
  const result = trySpawn("git", ["rev-parse", "--abbrev-ref", "HEAD"], { captureOutput: true });
  if (!result.ok) {
    return null;
  }

  return result.stdout.trim() || null;
}

function getGitHead() {
  const result = trySpawn("git", ["rev-parse", "--short", "HEAD"], { captureOutput: true });
  if (!result.ok) {
    return null;
  }

  return result.stdout.trim() || null;
}

function parseGitStatusPaths(statusLines) {
  return statusLines
    .map((line) => {
      const rawPath = line.slice(3).trim();
      if (!rawPath) {
        return null;
      }

      if (rawPath.includes(" -> ")) {
        return rawPath.split(" -> ").at(-1)?.trim() ?? null;
      }

      return rawPath;
    })
    .filter(Boolean);
}

function buildActiveEvidence() {
  const roadmapPath = "docs/STRATEGIC_ROADMAP.md";
  const currentFocusPath = "docs/CURRENT_FOCUS.md";
  const latestHandoffPath = "docs/LATEST_HANDOFF.md";
  const decisionsLogPath = "docs/DECISIONS_LOG.md";

  const roadmapText = readTextFileIfExists(roadmapPath);
  const currentFocusText = readTextFileIfExists(currentFocusPath);
  const latestHandoffText = readTextFileIfExists(latestHandoffPath);
  const decisionsLogText = readTextFileIfExists(decisionsLogPath);

  const programMode = normalizeMarkdownValue(extractFirstBulletValue(roadmapText, ["Program tipi", "Program modu"]));
  const programPhase = normalizeMarkdownValue(
    extractFirstBulletValue(roadmapText, ["Aktif faz", "Aktif program fazı"]),
  );
  const focusModule = normalizeMarkdownValue(extractFirstBulletValue(currentFocusText, ["Hedef modül"]));
  const focusProblem = normalizeMarkdownValue(extractFirstBulletValue(currentFocusText, ["Hedef problem"]));
  const successTest = extractFirstInlineCodeValue(currentFocusText, [
    "Geçmesi gereken test",
    "Geçmesi gereken çekirdek test",
  ]);
  const nextReadRaw = normalizeMarkdownValue(extractFirstBulletValue(currentFocusText, ["İlk okunacak dosya"]));
  const nextCommand = extractFirstInlineCodeValue(currentFocusText, ["İlk çalıştırılacak test/komut"]);
  const minimalChange = normalizeMarkdownValue(extractFirstBulletValue(currentFocusText, ["Yapılacak minimal değişiklik"]));
  const handoffNextGoal = extractFirstStructuredBulletValue(latestHandoffText, ["Bir sonraki hedef", "Sonraki en doğru adım"]);
  const handoffNextTest = extractFirstInlineCodeValue(latestHandoffText, [
    "Önce çalıştırılacak test",
    "Bir sonraki test/komut",
  ]);

  const referencedFiles = unique([
    ...extractBacktickList(roadmapText),
    ...extractBacktickList(currentFocusText),
    ...extractBacktickList(latestHandoffText),
  ]).filter((value) => value.includes("/") || value.endsWith(".md"));

  return {
    roadmapPath,
    currentFocusPath,
    latestHandoffPath,
    decisionsLogPath,
    roadmapText,
    currentFocusText,
    latestHandoffText,
    decisionsLogText,
    programMode,
    programPhase,
    focusModule,
    focusProblem,
    successTest,
    nextReadRaw,
    nextCommand,
    minimalChange,
    handoffNextGoal,
    handoffNextTest,
    referencedFiles,
    modifiedAt: {
      roadmap: getFileModifiedAt(roadmapPath),
      currentFocus: getFileModifiedAt(currentFocusPath),
      latestHandoff: getFileModifiedAt(latestHandoffPath),
      decisionsLog: getFileModifiedAt(decisionsLogPath),
    },
  };
}

function formatDate(date) {
  if (!(date instanceof Date)) {
    return "bilinmiyor";
  }

  return new Intl.DateTimeFormat("tr-TR", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(date);
}

function labelRisk(score) {
  if (score >= 60) {
    return "HIGH";
  }
  if (score >= 30) {
    return "MEDIUM";
  }
  return "LOW";
}

function runContextGuard() {
  printHeader("KaRar Context Guard");

  const evidence = buildActiveEvidence();
  const gitStatusLines = getGitStatusLines();
  const changedPaths = parseGitStatusPaths(gitStatusLines);
  const branch = getGitBranch();
  const head = getGitHead();

  let riskScore = 0;
  const risks = [];
  const recommendations = [];

  if (!evidence.currentFocusText) {
    riskScore += 45;
    risks.push("`docs/CURRENT_FOCUS.md` eksik; aktif hedef sabitlenmemiş.");
    recommendations.push("Önce aktif hedefi, başarı kriterini ve ilk doğrulama komutunu `docs/CURRENT_FOCUS.md` içine yaz.");
  }

  if (!evidence.roadmapText) {
    riskScore += 35;
    risks.push("`docs/STRATEGIC_ROADMAP.md` eksik; program yönü kalıcı olarak sabitlenmemiş.");
    recommendations.push("Program kuzey yıldızını ve öncelik sırasını `docs/STRATEGIC_ROADMAP.md` içine yaz.");
  }

  if (!evidence.latestHandoffText) {
    riskScore += 30;
    risks.push("`docs/LATEST_HANDOFF.md` eksik; yeni oturum için düşük maliyetli devir yok.");
    recommendations.push("Oturum kapanışında `docs/LATEST_HANDOFF.md` dosyasını gerçek son durumla güncelle.");
  }

  if (!evidence.decisionsLogText) {
    riskScore += 15;
    risks.push("`docs/DECISIONS_LOG.md` eksik; çözülmüş kararların yeniden açılma riski artar.");
    recommendations.push("Tekrarlı teknik tartışmaları önlemek için kararları `docs/DECISIONS_LOG.md` içinde kaydet.");
  }

  if (!evidence.successTest && !evidence.handoffNextTest) {
    riskScore += 20;
    risks.push("Aktif hedef için sabit bir doğrulama komutu çıkarılamadı.");
    recommendations.push("`CURRENT_FOCUS` veya `LATEST_HANDOFF` içine tek ve çalıştırılabilir bir hedef test/komut ekle.");
  }

  if (!evidence.focusModule) {
    riskScore += 15;
    risks.push("Aktif hedef modül açık biçimde belirtilmemiş.");
    recommendations.push("`Hedef modül` alanını tekil ve ölçülebilir bir modülle doldur.");
  }

  if (evidence.roadmapText && !evidence.programPhase) {
    riskScore += 10;
    risks.push("Stratejik yol haritasında aktif faz açık biçimde belirtilmemiş.");
    recommendations.push("`docs/STRATEGIC_ROADMAP.md` içinde `Aktif faz` alanını tekil biçimde doldur.");
  }

  if (changedPaths.length > 0) {
    const referencedSet = new Set(evidence.referencedFiles.map((file) => file.replace(/\\/g, "/")));
    const offFocusChanges = changedPaths.filter((changedPath) => !referencedSet.has(changedPath.replace(/\\/g, "/")));

    if (offFocusChanges.length > 0) {
      riskScore += Math.min(25, 10 + offFocusChanges.length * 3);
      risks.push(`Aktif bağlam dışında değişmiş dosyalar var: ${offFocusChanges.join(", ")}`);
      recommendations.push("Bu dosyalar kasıtlıysa handoff/focus kayıtlarına ekle; değilse değişiklikleri izole et veya ayrı göreve böl.");
    }
  }

  const riskLevel = labelRisk(riskScore);
  const nextCommand = evidence.nextCommand || evidence.successTest || evidence.handoffNextTest || "belirtilmemiş";
  const nextGoal = evidence.handoffNextGoal || evidence.minimalChange || "belirtilmemiş";

  console.log(`Branch         : ${branch ?? "bilinmiyor"}`);
  console.log(`HEAD           : ${head ?? "bilinmiyor"}`);
  console.log(`Risk seviyesi  : ${riskLevel} (${riskScore}/100)`);
  console.log(`Program modu   : ${evidence.programMode ?? "belirtilmemiş"}`);
  console.log(`Program fazı   : ${evidence.programPhase ?? "belirtilmemiş"}`);
  console.log(`Aktif modül    : ${evidence.focusModule ?? "belirtilmemiş"}`);
  console.log(`Aktif problem  : ${evidence.focusProblem ?? "belirtilmemiş"}`);
  console.log(`Sonraki komut  : ${nextCommand}`);
  console.log(`Sonraki hedef  : ${nextGoal}`);
  console.log(`Kirli dosya    : ${changedPaths.length === 0 ? "yok" : changedPaths.length}`);

  printHeader("Kanıt Özeti");
  console.log(`- STRATEGIC_ROADMAP güncellendi: ${formatDate(evidence.modifiedAt.roadmap)}`);
  console.log(`- CURRENT_FOCUS güncellendi : ${formatDate(evidence.modifiedAt.currentFocus)}`);
  console.log(`- LATEST_HANDOFF güncellendi: ${formatDate(evidence.modifiedAt.latestHandoff)}`);
  console.log(`- DECISIONS_LOG güncellendi : ${formatDate(evidence.modifiedAt.decisionsLog)}`);
  console.log(`- Başarı testi              : ${evidence.successTest ?? "yok"}`);
  console.log(`- İlk okunacak bağlam       : ${evidence.nextReadRaw ?? "yok"}`);
  console.log(`- Minimal değişiklik        : ${evidence.minimalChange ?? "yok"}`);

  printHeader("Git Çalışma Ağacı");
  if (gitStatusLines.length === 0) {
    console.log("- Çalışma ağacı temiz.");
  } else {
    for (const statusLine of gitStatusLines) {
      console.log(`- ${statusLine}`);
    }
  }

  printHeader("Sapma Riskleri");
  if (risks.length === 0) {
    console.log("- Kritik bağlam sapması sinyali tespit edilmedi.");
  } else {
    for (const risk of risks) {
      console.log(`- ${risk}`);
    }
  }

  printHeader("Önerilen Sonraki Adımlar");
  const finalRecommendations = unique([
    ...recommendations,
    nextCommand !== "belirtilmemiş" ? `Önce şu komutu çalıştır: ${nextCommand}` : null,
    evidence.nextReadRaw ? `Okuma sırası dışına çıkmadan önce şu bağlamı oku: ${evidence.nextReadRaw}` : null,
    "Her değişiklikten sonra `docs/CURRENT_FOCUS.md` ve `docs/LATEST_HANDOFF.md` dosyalarını gerçek durumla hizala.",
  ]);

  for (const recommendation of finalRecommendations) {
    console.log(`- ${recommendation}`);
  }

  const exitCode = riskLevel === "HIGH" ? 2 : riskLevel === "MEDIUM" ? 1 : 0;
  process.exitCode = exitCode;

  return {
    riskLevel,
    riskScore,
    exitCode,
    nextCommand,
    nextGoal,
    changedPaths,
  };
}

function doctor() {
  printHeader("KaRar Geliştirme Ortamı Doktoru");
  console.log(`Çalışma dizini : ${rootDir}`);
  console.log(`Platform       : ${process.platform} (${os.release()})`);
  console.log(`Node.js        : ${process.version}`);

  const npmRunner = getNpmRunner();
  const npmVersion = trySpawn(npmRunner.command, [...npmRunner.prefixArgs, "--version"], { captureOutput: true });
  console.log(`npm            : ${npmVersion.ok ? npmVersion.stdout.trim() : `bulunamadı (${npmRunner.label})`}`);

  const nodeModulesExists = existsSync(path.join(rootDir, "node_modules"));
  const localTsc = existsSync(path.join(rootDir, "node_modules", ".bin", isWindows() ? "tsc.cmd" : "tsc"));
  console.log(`node_modules/  : ${nodeModulesExists ? "mevcut" : "eksik"}`);
  console.log(`tsc            : ${localTsc ? "mevcut" : "eksik"}`);

  const venvPython = findExistingVenvPython();
  if (venvPython) {
    console.log(`Python ortamı  : venv bulundu (${path.relative(rootDir, venvPython)})`);
    const version = trySpawn(venvPython, ["--version"], { captureOutput: true });
    console.log(`Venv Python    : ${(version.stdout || version.stderr).trim() || "bilinmiyor"}`);
    const pipVersion = trySpawn(venvPython, ["-m", "pip", "--version"], { captureOutput: true });
    console.log(`pip            : ${pipVersion.ok ? pipVersion.stdout.trim() : "erişilemedi"}`);
  } else {
    console.log("Python ortamı  : proje venv bulunamadı (venv veya .venv)");
  }

  const systemPython = detectSystemPython();
  console.log(`Sistem Python  : ${systemPython ? `${systemPython.label} -> ${systemPython.version}` : "bulunamadı"}`);
  console.log(`backend/       : ${existsSync(path.join(rootDir, "backend")) ? "mevcut" : "eksik"}`);
  console.log(`package.json   : ${existsSync(path.join(rootDir, "package.json")) ? "mevcut" : "eksik"}`);

  if (!venvPython && !systemPython) {
    console.error("\nHATA: Kullanılabilir bir Python yorumlayıcısı bulunamadı.");
    console.error("Öneri: Önce sistem Python kurun, ardından 'npm run setup:python' çalıştırın.");
    process.exit(1);
  }

  if (!venvPython) {
    console.warn("\nUYARI: İzole bir Python sanal ortamı bulunamadı.");
    console.warn("Öneri: 'npm run setup:python' ile proje venv ortamını oluşturun.");
  }

  if (!nodeModulesExists || !localTsc) {
    console.warn("\nUYARI: Node bağımlılıkları eksik görünüyor.");
    console.warn("Öneri: Önce 'npm install' çalıştırın; ardından 'npm run check' deneyin.");
  }
}

function setupPython() {
  printHeader("KaRar Python Ortamı Kurulumu");
  const existingVenv = findExistingVenvPython();

  if (!existingVenv) {
    const systemPython = detectSystemPython();
    if (!systemPython) {
      console.error("Sistem Python bulunamadı. Kurulum yapılamıyor.");
      process.exit(1);
    }

    console.log(`venv oluşturuluyor -> ${systemPython.label} -m venv venv`);
    runOrExit(systemPython.command, [...systemPython.argsPrefix, "-m", "venv", "venv"]);
  } else {
    console.log(`Mevcut venv kullanılacak: ${path.relative(rootDir, existingVenv)}`);
  }

  const venvPython = findExistingVenvPython();
  if (!venvPython) {
    console.error("venv oluşturuldu ancak Python yürütücüsü bulunamadı.");
    process.exit(1);
  }

  console.log("pip güncelleniyor...");
  runOrExit(venvPython, ["-m", "pip", "install", "--upgrade", "pip"]);

  console.log(`Python bağımlılıkları kuruluyor: ${pythonDeps.join(", ")}`);
  runOrExit(venvPython, ["-m", "pip", "install", ...pythonDeps]);
}

function bootstrap() {
  printHeader("KaRar Bootstrap");
  console.log("Node bağımlılıkları kuruluyor...");
  runNpm(["install"]);
  setupPython();
}

function runPreflight(options = {}) {
  const requireLowRisk = options.requireLowRisk ?? true;

  printHeader("KaRar Preflight");
  doctor();
  const contextOutcome = runContextGuard() ?? { exitCode: 0, riskLevel: "LOW" };

  if (requireLowRisk && contextOutcome.exitCode !== 0) {
    console.error(
      `\nPreflight durduruldu: context guard ${contextOutcome.riskLevel} risk seviyesi verdi. ` +
        "Önce önerilen adımları uygulayıp bağlamı LOW seviyesine indirin.",
    );
    process.exit(contextOutcome.exitCode);
  }

  console.log("\nPreflight sonucu: ortam ve aktif bağlam hard-mode çalışma için hazır.");
}

function runUnitTests(moduleName) {
  const pythonConfig = resolvePythonForWork();
  if (!pythonConfig) {
    console.error("Python yorumlayıcısı bulunamadı. Önce 'npm run doctor' veya 'npm run setup:python' çalıştırın.");
    process.exit(1);
  }

  console.log(`Python testleri çalıştırılıyor (${pythonConfig.source}) -> ${moduleName}`);
  runPython(pythonConfig, ["-m", "unittest", moduleName]);
}

function runRegression() {
  const pythonConfig = resolvePythonForWork();
  if (!pythonConfig) {
    console.error("Python yorumlayıcısı bulunamadı. Önce 'npm run doctor' veya 'npm run setup:python' çalıştırın.");
    process.exit(1);
  }

  console.log(`Regresyon testi çalıştırılıyor (${pythonConfig.source}) -> backend/run_regression_tests.py`);
  runPython(pythonConfig, ["backend/run_regression_tests.py"]);
}

function runTargetedTest(targetName) {
  const moduleName = targetedTestMap[targetName];
  if (!moduleName) {
    console.error(`Bilinmeyen hedef test grubu: ${targetName}`);
    console.error(`Geçerli gruplar: ${Object.keys(targetedTestMap).join(", ")}`);
    process.exit(1);
  }

  runUnitTests(moduleName);
}

function runManifest(action) {
  const pythonConfig = resolvePythonForWork();
  if (!pythonConfig) {
    console.error("Python yorumlayıcısı bulunamadı. Önce 'npm run doctor' veya 'npm run setup:python' çalıştırın.");
    process.exit(1);
  }

  const safeAction = action === "update" ? "update" : "verify";
  console.log(`Output manifest komutu çalıştırılıyor (${pythonConfig.source}) -> ${safeAction}`);
  runPython(pythonConfig, ["-m", "backend.output_manifest", safeAction]);
}

function runMetrics(action) {
  const pythonConfig = resolvePythonForWork();
  if (!pythonConfig) {
    console.error("Python yorumlayıcısı bulunamadı. Önce 'npm run doctor' veya 'npm run setup:python' çalıştırın.");
    process.exit(1);
  }

  const safeAction = action === "update" ? "update" : "verify";
  console.log(`Output metrics komutu çalıştırılıyor (${pythonConfig.source}) -> ${safeAction}`);
  runPython(pythonConfig, ["-m", "backend.output_metrics", safeAction]);
}

function runTopologyHealth() {
  const pythonConfig = resolvePythonForWork();
  if (!pythonConfig) {
    console.error("Python yorumlayıcısı bulunamadı. Önce 'npm run doctor' veya 'npm run setup:python' çalıştırın.");
    process.exit(1);
  }

  console.log(`Topology health report komutu çalıştırılıyor (${pythonConfig.source})`);
  runPython(pythonConfig, ["-m", "backend.topology_health_report"]);
}

function getTopologyDiagnosticCodes(report) {
  if (!report || !Array.isArray(report.diagnostics)) {
    return [];
  }

  return unique(report.diagnostics.map((diagnostic) => diagnostic?.code));
}

function printTopologyHealthSummary(report) {
  const diagnosticCodes = getTopologyDiagnosticCodes(report);
  const graphMetrics = report?.graph_metrics ?? {};
  const loopMetrics = report?.loop_metrics ?? {};

  printHeader("Topology Health Özeti");
  console.log(`Durum                 : ${report?.status ?? "UNKNOWN"}`);
  console.log(`Diagnostic codes      : ${diagnosticCodes.length > 0 ? diagnosticCodes.join(", ") : "yok"}`);
  console.log(`Dangling nodes        : ${graphMetrics.dangling_node_count ?? 0}`);
  console.log(`Connected components  : ${graphMetrics.connected_components ?? 0}`);
  console.log(`Closed loops          : ${loopMetrics.closed_loop_count ?? 0}`);
  console.log(`Open loops            : ${loopMetrics.open_loop_count ?? 0}`);
}

function runP0Verification(options = {}) {
  const strictTopologyHealth = options.strictTopologyHealth ?? false;

  printHeader("KaRar P0 Verification");
  runTopologyHealth();

  const topologyHealthReport = readJsonFileIfExists(topologyHealthReportRelativePath);
  if (!topologyHealthReport) {
    console.error(`Topology health raporu okunamadı: ${topologyHealthReportRelativePath}`);
    process.exit(1);
  }

  printTopologyHealthSummary(topologyHealthReport);
  runManifest("verify");
  runMetrics("verify");

  printHeader("P0 Verification Sonucu");
  console.log(`Topology health       : ${topologyHealthReport.status ?? "UNKNOWN"}`);
  console.log("Manifest verify       : PASS");
  console.log("Metrics verify        : PASS");

  if (topologyHealthReport.status === "CRITICAL") {
    console.error("\nP0 doğrulama başarısız: topology health CRITICAL durumda.");
    process.exit(2);
  }

  if (strictTopologyHealth && topologyHealthReport.status !== "HEALTHY") {
    console.error(
      `\nRelease gate başarısız: topology health status '${topologyHealthReport.status}' ama HEALTHY bekleniyordu.`,
    );
    process.exit(1);
  }

  if (topologyHealthReport.status === "WARNING") {
    console.warn(
      "\nP0 notu: topology health WARNING. Manifest ve metrics doğrulamaları geçti; " +
        "warning sınıflandırması hâlâ aktif çekirdek algoritma işi olarak takip edilmeli.",
    );
  } else {
    console.log("\nP0 sonucu: topology health HEALTHY ve tamamlayıcı doğrulamalar başarılı.");
  }

  return topologyHealthReport;
}

function runReleaseGate() {
  printHeader("KaRar Release Gate");
  runP0Verification({ strictTopologyHealth: true });
  console.log("\nRelease gate sonucu: HEALTHY topology health + PASS manifest + PASS metrics.");
}

function runHardMode(targetName) {
  const safeTargetName = targetedTestMap[targetName] ? targetName : "topology";

  printHeader(`KaRar Hard Mode -> ${safeTargetName}`);
  runPreflight({ requireLowRisk: true });
  runTargetedTest(safeTargetName);
  const topologyHealthReport = runP0Verification({ strictTopologyHealth: false });

  printHeader("Hard Mode Sonucu");
  console.log(`Hedef test grubu      : ${safeTargetName}`);
  console.log(`Topology health       : ${topologyHealthReport.status ?? "UNKNOWN"}`);
  console.log(
    topologyHealthReport.status === "WARNING"
      ? "Sonraki doğru adım     : Warning diagnostic kodlarını tek regression + minimal kod değişikliği ile sınıflandır."
      : "Sonraki doğru adım     : Aynı disiplinle bir sonraki çekirdek hedefe ilerle.",
  );
}

const [command, ...restArgs] = process.argv.slice(2);

switch (command) {
  case "doctor":
    doctor();
    break;
  case "setup:python":
    setupPython();
    break;
  case "bootstrap":
    bootstrap();
    break;
  case "preflight":
    runPreflight();
    break;
  case "unittest":
    runUnitTests(restArgs[0] ?? "backend.tests.test_modern_pipeline");
    break;
  case "regression":
    runRegression();
    break;
  case "targeted-test":
    runTargetedTest(restArgs[0] ?? "pipeline");
    break;
  case "manifest":
    runManifest(restArgs[0] ?? "verify");
    break;
  case "metrics":
    runMetrics(restArgs[0] ?? "verify");
    break;
  case "topology-health":
    runTopologyHealth();
    break;
  case "verify:p0":
    runP0Verification();
    break;
  case "release-gate":
    runReleaseGate();
    break;
  case "hard-mode":
    runHardMode(restArgs[0] ?? "topology");
    break;
  case "context-guard":
    runContextGuard();
    break;
  default:
    console.log("Kullanım:");
    console.log("  node scripts/dev-tools.mjs doctor");
    console.log("  node scripts/dev-tools.mjs setup:python");
    console.log("  node scripts/dev-tools.mjs bootstrap");
    console.log("  node scripts/dev-tools.mjs preflight");
    console.log("  node scripts/dev-tools.mjs unittest [module]");
    console.log("  node scripts/dev-tools.mjs regression");
    console.log(`  node scripts/dev-tools.mjs targeted-test [${Object.keys(targetedTestMap).join("|")}]`);
    console.log("  node scripts/dev-tools.mjs manifest [update|verify]");
    console.log("  node scripts/dev-tools.mjs metrics [update|verify]");
    console.log("  node scripts/dev-tools.mjs topology-health");
    console.log("  node scripts/dev-tools.mjs verify:p0");
    console.log("  node scripts/dev-tools.mjs release-gate");
    console.log(`  node scripts/dev-tools.mjs hard-mode [${Object.keys(targetedTestMap).join("|")}]`);
    console.log("  node scripts/dev-tools.mjs context-guard");
    process.exit(command ? 1 : 0);
}