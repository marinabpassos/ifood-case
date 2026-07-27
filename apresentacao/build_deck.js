/**
 * Gera o deck de apresentação do iFood Data Architect Case a partir do
 * conteúdo de `apresentacao-outline.md`.
 *
 * Todos os números vêm de artefatos reais do repositório — nada é inventado:
 *   - profiling ....... specs/003-data-profiling/findings.md
 *   - DQ da silver .... specs/006-silver-data-quality/dq-run-log.md
 *   - contrato ........ contracts/nyc_taxi_silver.yaml
 *   - Q1 / Q2 / bônus . analysis/answers.md
 *   - catálogo ........ src/ingestion/landing_zone.py, src/bronze, src/silver
 *
 * Uso: node apresentacao/build_deck.js   (ou: npm run build)
 */

const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.join(__dirname, "..");
// DECK_OUT permite gerar num caminho alternativo (ex.: quando o arquivo final
// está aberto no PowerPoint e o Windows o mantém travado para escrita).
const OUT = process.env.DECK_OUT || path.join(__dirname, "ifood-case-apresentacao.pptx");

const AUTOR = "Marina Barreto Passos";

// --- Paleta: vermelho iFood sobre fundo claro -----------------------------
// Escuro reservado à capa e ao fechamento (estrutura "sanduíche"); o miolo
// é claro para leitura confortável em projeção.
const RED = "EA1D2C";
const DARK = "17171C";
const DARK_SOFT = "26262E";
const WHITE = "FFFFFF";
const CARD = "F4F4F5"; // cinza neutro
const CARD_WARM = "FDF2F3"; // tinte vermelho leve
const CARD_ACCENT = "FBE3E6"; // tinte vermelho mais forte, para destaque
const INK = "1F1F26";
const MUTED = "56565F";
const MUTED_DK = "A0A0AC"; // texto secundário sobre fundo escuro
const FAINT = "8A8A94";

const H_FONT = "Arial";
const B_FONT = "Calibri";
const M_FONT = "Courier New";

const W = 13.333;
const H = 7.5;
const M = 0.75;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // precisa vir ANTES de qualquer addSlide
pres.author = AUTOR;
pres.title = "iFood Data Architect Case — Engenharia de Dados Agêntica";

// --- Helpers --------------------------------------------------------------

/** Sombra suave; objeto novo a cada chamada (pptxgenjs muta options in place). */
const softShadow = () => ({
  type: "outer", color: "000000", blur: 12, offset: 2, angle: 90, opacity: 0.1,
});

function lightSlide() {
  const s = pres.addSlide();
  s.background = { color: WHITE };
  return s;
}

function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: DARK };
  return s;
}

function eyebrow(slide, text, opts = {}) {
  slide.addText(text.toUpperCase(), {
    x: M, y: opts.y ?? 0.5, w: opts.w ?? W - 2 * M, h: 0.3,
    fontFace: H_FONT, fontSize: 12, bold: true,
    color: opts.color ?? RED, charSpacing: 2, margin: 0,
  });
}

function slideTitle(slide, text, opts = {}) {
  slide.addText(text, {
    x: M, y: opts.y ?? 0.82, w: opts.w ?? W - 2 * M, h: opts.h ?? 0.7,
    fontFace: H_FONT, fontSize: opts.fontSize ?? 32, bold: true,
    color: opts.color ?? INK, margin: 0, valign: "top",
  });
}

function card(slide, x, y, w, h, fill = CARD, opts = {}) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.09,
    fill: { color: fill },
    line: opts.line ?? { color: fill, width: 0 },
    shadow: opts.shadow ? softShadow() : undefined,
  });
}

/** Seta vermelha sem contorno (o PowerPoint desenha borda se `line` não for explícito). */
function arrow(slide, x, y, w, h) {
  slide.addShape(pres.ShapeType.rightArrow, {
    x, y, w, h, fill: { color: RED }, line: { color: RED, width: 0 },
  });
}

/** Selo circular vermelho — o motivo visual repetido em todo o deck. */
function badge(slide, x, y, label, opts = {}) {
  const d = opts.d ?? 0.46;
  slide.addText(label, {
    shape: pres.ShapeType.ellipse, x, y, w: d, h: d,
    fill: { color: opts.fill ?? RED },
    color: opts.color ?? WHITE,
    fontFace: H_FONT, fontSize: opts.fontSize ?? 12, bold: true,
    align: "center", valign: "middle", margin: 0,
  });
}

function body(slide, text, o) {
  slide.addText(text, {
    fontFace: B_FONT, fontSize: 14, color: MUTED,
    lineSpacingMultiple: 1.15, margin: 0, valign: "top", ...o,
  });
}

/** Rodapé de fonte/observação. */
function footnote(slide, text, y = 6.85) {
  slide.addText(text, {
    x: M, y, w: W - 2 * M, h: 0.3,
    fontFace: B_FONT, fontSize: 10.5, italic: true, color: FAINT, margin: 0,
  });
}

// =========================================================================
// 1 — Capa
// =========================================================================
{
  const s = darkSlide();

  s.addShape(pres.ShapeType.ellipse, {
    x: 9.5, y: -1.4, w: 5.6, h: 5.6,
    fill: { color: RED, transparency: 88 }, line: { width: 0 },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: 10.35, y: -0.55, w: 3.9, h: 3.9,
    fill: { color: DARK, transparency: 100 },
    line: { color: RED, width: 1.25, transparency: 55 },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: 11.35, y: 0.45, w: 1.9, h: 1.9,
    fill: { color: RED }, line: { width: 0 },
  });

  s.addText("IFOOD DATA ARCHITECT CASE", {
    x: M, y: 1.7, w: 8.5, h: 0.34,
    fontFace: H_FONT, fontSize: 13, bold: true, color: RED, charSpacing: 3, margin: 0,
  });

  s.addText("Engenharia de\nDados Agêntica", {
    x: M, y: 2.2, w: 8.6, h: 1.95,
    fontFace: H_FONT, fontSize: 48, bold: true, color: WHITE,
    lineSpacingMultiple: 1.0, margin: 0,
  });

  s.addText(AUTOR, {
    x: M, y: 4.24, w: 8.6, h: 0.42,
    fontFace: H_FONT, fontSize: 19, bold: true, color: WHITE, margin: 0, valign: "middle",
  });

  const facts = [
    "NYC Yellow Taxi  ·  Jan–Mai 2023",
    "Databricks (Free Edition)  ·  PySpark + Delta Lake + Unity Catalog",
  ];
  facts.forEach((t, i) => {
    s.addShape(pres.ShapeType.ellipse, {
      x: M + 0.02, y: 4.92 + i * 0.42 + 0.09, w: 0.11, h: 0.11,
      fill: { color: RED }, line: { width: 0 },
    });
    s.addText(t, {
      x: M + 0.32, y: 4.92 + i * 0.42, w: 9.0, h: 0.32,
      fontFace: B_FONT, fontSize: 15, color: MUTED_DK, margin: 0, valign: "middle",
    });
  });

  card(s, M, 6.05, 7.4, 0.68, DARK_SOFT);
  s.addText("Desenvolvido com Spec-Driven Development + Claude Code", {
    x: M + 0.35, y: 6.05, w: 6.9, h: 0.68,
    fontFace: B_FONT, fontSize: 14, bold: true, color: WHITE, margin: 0, valign: "middle",
  });

  s.addNotes(
    "Case do iFood para Data Architect. O fio condutor da apresentação não é só a pipeline — " +
    "é a metodologia agêntica (Spec-Driven Development) que a produziu. " +
    "Dados: NYC Yellow Taxi, 5 meses de 2023, rodando em Databricks Free Edition."
  );
}

// =========================================================================
// 2 — O desafio
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "O desafio");
  slideTitle(s, "Um case com dois objetivos");

  const cards = [
    { n: "1", t: "Objetivo técnico", fill: CARD,
      d: "Ingerir corridas de táxi de NY, disponibilizar via SQL e responder a 2 perguntas analíticas." },
    { n: "2", t: "Meta-objetivo", fill: CARD_WARM,
      d: "Servir de exemplo de boas práticas de engenharia de dados agêntica, usando Claude Code como ferramenta de desenvolvimento." },
  ];

  cards.forEach((c, i) => {
    const x = M + i * 6.1;
    card(s, x, 2.0, 5.65, 2.35, c.fill, { shadow: true });
    badge(s, x + 0.45, 2.4, c.n);
    s.addText(c.t, {
      x: x + 1.08, y: 2.4, w: 4.1, h: 0.46,
      fontFace: H_FONT, fontSize: 19, bold: true, color: INK, margin: 0, valign: "middle",
    });
    body(s, c.d, { x: x + 0.45, y: 3.1, w: 4.8, h: 1.1, fontSize: 14 });
  });

  s.addText("Critérios de avaliação", {
    x: M, y: 4.78, w: 6, h: 0.3,
    fontFace: H_FONT, fontSize: 13, bold: true, color: RED, charSpacing: 1.5, margin: 0,
  });

  const criteria = [
    "Qualidade e organização do código",
    "Processo de EDA",
    "Justificativa das escolhas",
    "Criatividade",
    "Clareza na comunicação",
  ];
  criteria.forEach((t, i) => {
    const x = M + i * 2.4;
    card(s, x, 5.24, 2.2, 1.05, CARD);
    s.addText(t, {
      x: x + 0.22, y: 5.24, w: 1.78, h: 1.05,
      fontFace: B_FONT, fontSize: 12, color: INK, margin: 0, valign: "middle",
    });
  });

  s.addNotes(
    "Importante enquadrar: o case pede a pipeline, mas o que diferencia a entrega é o processo. " +
    "Os 5 critérios de avaliação são endereçados explicitamente ao longo do deck — especialmente " +
    "'justificativa das escolhas', que é o que o SDD força."
  );
}

// =========================================================================
// 3 — Metodologia SDD
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Metodologia");
  slideTitle(s, "Spec-Driven Development (SDD)");

  const steps = [
    { l: "Constitution", opt: false }, { l: "Specify", opt: false },
    { l: "Clarify", opt: true }, { l: "Plan", opt: false },
    { l: "Checklist", opt: true }, { l: "Tasks", opt: false },
    { l: "Analyze", opt: true }, { l: "Implement", opt: false },
    { l: "Converge", opt: false },
  ];

  const flowY = 2.35, d = 0.58;
  const span = W - 2 * M, gap = span / steps.length;

  s.addShape(pres.ShapeType.rect, {
    x: M + gap / 2, y: flowY + d / 2 - 0.01, w: span - gap, h: 0.02,
    fill: { color: "D9D9DE" }, line: { width: 0 },
  });

  steps.forEach((st, i) => {
    const cx = M + gap * i + gap / 2 - d / 2;
    if (st.opt) {
      s.addShape(pres.ShapeType.ellipse, {
        x: cx, y: flowY, w: d, h: d,
        fill: { color: WHITE }, line: { color: RED, width: 1.25, dashType: "dash" },
      });
      s.addText(String(i + 1), {
        x: cx, y: flowY, w: d, h: d,
        fontFace: H_FONT, fontSize: 12, bold: true, color: RED,
        align: "center", valign: "middle", margin: 0,
      });
    } else {
      badge(s, cx, flowY, String(i + 1), { d });
    }
    s.addText(st.l, {
      x: M + gap * i, y: flowY + d + 0.16, w: gap, h: 0.6,
      fontFace: B_FONT, fontSize: 11, bold: !st.opt,
      color: st.opt ? MUTED : INK, align: "center", margin: 0, valign: "top",
    });
  });

  s.addText(
    [
      { text: "○ ", options: { color: RED, bold: true } },
      { text: "tracejado = fase opcional, acionada quando a spec tem ambiguidade", options: { color: MUTED } },
    ],
    { x: M, y: 3.82, w: 8, h: 0.3, fontFace: B_FONT, fontSize: 11, italic: true, margin: 0 }
  );

  const notes = [
    { t: "Checkpoints humanos entre as fases",
      d: "O agente não avança sozinho: cada fase termina em revisão antes da seguinte começar." },
    { t: "Rastreabilidade FR → código",
      d: "Cada arquivo de código cita os requisitos funcionais e as decisões de research.md que implementa." },
    { t: "Ferramentas",
      d: "GitHub Spec Kit + Claude Code, com a constituição do projeto como camada de governança." },
  ];
  notes.forEach((n, i) => {
    const x = M + i * 4.07;
    card(s, x, 4.45, 3.72, 1.95, CARD);
    s.addText(n.t, {
      x: x + 0.3, y: 4.72, w: 3.15, h: 0.5,
      fontFace: H_FONT, fontSize: 14, bold: true, color: INK, margin: 0, valign: "top",
    });
    body(s, n.d, { x: x + 0.3, y: 5.3, w: 3.15, h: 0.95, fontSize: 12 });
  });

  s.addNotes(
    "O fluxo é o do GitHub Spec Kit. O ponto central para a banca: as fases opcionais " +
    "(Clarify, Checklist, Analyze) existem para não deixar o agente 'preencher lacunas' sozinho. " +
    "Quando a spec está ambígua, o humano resolve a ambiguidade antes do código existir."
  );
}

// =========================================================================
// 4 — Constituição
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Governança");
  slideTitle(s, "A Constituição do projeto");
  body(s, "Princípios que governaram todas as decisões técnicas do case.", {
    x: M, y: 1.58, w: 9, h: 0.32, fontSize: 14,
  });

  card(s, M, 2.2, 5.3, 4.1, CARD_ACCENT, { shadow: true });
  badge(s, M + 0.45, 2.62, "!", { fontSize: 15 });
  s.addText("Não-negociável", {
    x: M + 0.45, y: 3.3, w: 4.4, h: 0.3,
    fontFace: H_FONT, fontSize: 11, bold: true, color: RED, charSpacing: 1.5, margin: 0,
  });
  s.addText("Qualidade de dados\né um gate, não\num relatório", {
    x: M + 0.45, y: 3.67, w: 4.5, h: 1.5,
    fontFace: H_FONT, fontSize: 25, bold: true, color: INK,
    lineSpacingMultiple: 1.05, margin: 0, valign: "top",
  });
  s.addText("Registro de problema não basta — a regra bloqueia o dado.", {
    x: M + 0.45, y: 5.35, w: 4.5, h: 0.55,
    fontFace: B_FONT, fontSize: 12.5, color: MUTED, margin: 0, valign: "top",
  });

  const principles = [
    { t: "Contratos de dados antes do código", d: "O schema é acordado e versionado antes de existir escrita." },
    { t: "Observabilidade é entregável", d: "Faz parte do escopo, não é um extra opcional." },
    { t: "Stack fixa", d: "PySpark, Delta Lake e Unity Catalog — sem troca de ferramenta no meio." },
    { t: "Mínimo layering", d: "Nenhuma abstração especulativa: camada só existe se resolve problema real." },
  ];
  principles.forEach((p, i) => {
    const y = 2.2 + i * 1.06;
    card(s, 6.5, y, 6.08, 0.92, CARD);
    badge(s, 6.78, y + 0.23, String(i + 2));
    s.addText(p.t, {
      x: 7.42, y: y + 0.13, w: 5.0, h: 0.34,
      fontFace: H_FONT, fontSize: 14, bold: true, color: INK, margin: 0, valign: "middle",
    });
    s.addText(p.d, {
      x: 7.42, y: y + 0.47, w: 5.0, h: 0.34,
      fontFace: B_FONT, fontSize: 11.5, color: MUTED, margin: 0, valign: "middle",
    });
  });

  s.addNotes(
    "A constituição é um arquivo versionado (.specify/memory/constitution.md), não um slide de PowerPoint. " +
    "Ela é carregada pelo agente em toda sessão — é o que impede a deriva de decisão entre features. " +
    "O princípio de mínimo layering é o que justifica a ausência de camada Gold, explicada adiante."
  );
}

// =========================================================================
// 5 — 9 features
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Execução");
  slideTitle(s, "9 features, 9 ciclos SDD completos");
  body(s, "Cada feature percorreu o ciclo inteiro: spec → plan → tasks → implement.", {
    x: M, y: 1.58, w: 9.5, h: 0.32, fontSize: 14,
  });

  const feats = [
    ["001", "Scaffold do repositório"], ["002", "Ambiente & Landing Zone"],
    ["003", "Data Profiling (EDA)"], ["004", "Camada Bronze"],
    ["005", "Contrato de dados da Silver"], ["006", "Data Quality & Camada Silver"],
    ["007", "Observabilidade da pipeline"], ["008", "Perguntas analíticas"],
    ["009", "POC App de chat"],
  ];

  const cw = 3.85, ch = 1.28, gx = 0.24, gy = 0.22;
  feats.forEach(([num, label], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = M + col * (cw + gx), y = 2.25 + row * (ch + gy);
    card(s, x, y, cw, ch, CARD);
    s.addText(num, {
      x: x + 0.3, y: y + 0.2, w: 1.2, h: 0.42,
      fontFace: H_FONT, fontSize: 20, bold: true, color: RED, margin: 0, valign: "middle",
    });
    s.addText(label, {
      x: x + 0.3, y: y + 0.66, w: cw - 0.6, h: 0.5,
      fontFace: B_FONT, fontSize: 13.5, color: INK, margin: 0, valign: "top",
    });
  });

  s.addNotes(
    "Nove features, cada uma com sua pasta em specs/ contendo spec.md, plan.md, research.md e tasks.md. " +
    "A numeração é a ordem real de execução — nenhuma feature começou antes da anterior ter passado no checkpoint humano."
  );
}

// =========================================================================
// 6 — Arquitetura Medallion
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Arquitetura");
  slideTitle(s, "Medallion em três camadas");

  const layers = [
    { n: "Landing", d: "Parquets crus da fonte NYC TLC, byte-a-byte. Nenhuma transformação.", fill: CARD },
    { n: "Bronze", d: "Ingestão 1:1 com tratamento técnico. Sem regras de negócio.", fill: CARD },
    { n: "Silver", d: "Schema validado por contrato + 4 regras de negócio aplicadas.", fill: CARD_WARM },
  ];

  const lw = 3.72, ly = 2.15, lh = 2.15;
  layers.forEach((l, i) => {
    const x = M + i * (lw + 0.62);
    card(s, x, ly, lw, lh, l.fill, { shadow: true });
    badge(s, x + 0.35, ly + 0.34, String(i + 1));
    s.addText(l.n, {
      x: x + 0.95, y: ly + 0.34, w: 2.5, h: 0.46,
      fontFace: H_FONT, fontSize: 21, bold: true, color: INK, margin: 0, valign: "middle",
    });
    body(s, l.d, { x: x + 0.35, y: ly + 1.0, w: lw - 0.7, h: 1.0, fontSize: 13 });
    if (i < layers.length - 1) arrow(s, x + lw + 0.14, ly + lh / 2 - 0.13, 0.34, 0.26);
  });

  s.addText("Cada camada em seu próprio schema no catalog ifood_case — decisão explícita por 3 camadas, não 2.", {
    x: M, y: 4.5, w: W - 2 * M, h: 0.32,
    fontFace: B_FONT, fontSize: 13, italic: true, color: MUTED, margin: 0,
  });

  card(s, M, 5.05, W - 2 * M, 1.5, CARD_ACCENT, { shadow: true });
  s.addText("Sem camada Gold — e isso é uma decisão, não um esquecimento", {
    x: M + 0.5, y: 5.28, w: 11.0, h: 0.36,
    fontFace: H_FONT, fontSize: 16, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText(
    "As 2 perguntas do case são agregações diretas sobre a silver; não há dimensões reais a modelar. " +
    "Adicionar um star schema violaria o princípio de mínimo layering da constituição.",
    { x: M + 0.5, y: 5.7, w: 11.0, h: 0.7,
      fontFace: B_FONT, fontSize: 13, color: MUTED, margin: 0, valign: "top", lineSpacingMultiple: 1.15 }
  );

  s.addNotes(
    "Esse é o slide onde a banca provavelmente vai perguntar 'cadê a Gold?'. A resposta está no slide: " +
    "não há dimensões reais a modelar para duas agregações. Construir um star schema aqui seria " +
    "abstração especulativa — exatamente o que a constituição proíbe. Decisão registrada em DECISOES_PROJETO.md."
  );
}

// =========================================================================
// 7 — Catálogo de dados (Unity Catalog)
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Feature 002 — Governança de dados");
  slideTitle(s, "O catálogo de dados no Unity Catalog");

  s.addText(
    [
      { text: "catalog  ", options: { color: MUTED, fontFace: B_FONT, fontSize: 13 } },
      { text: "ifood_case", options: { color: INK, bold: true, fontFace: M_FONT, fontSize: 17 } },
      { text: "   criado pela própria pipeline, de forma idempotente", options: { color: MUTED, fontFace: B_FONT, fontSize: 13 } },
    ],
    { x: M, y: 1.62, w: 11.5, h: 0.34, margin: 0, valign: "middle" }
  );

  const schemas = [
    {
      n: "landing",
      objs: [
        ["VOLUME", "yellow_taxi_raw"],
        ["", "5 parquets crus da NYC TLC"],
      ],
      fill: CARD,
    },
    {
      n: "bronze",
      objs: [
        ["TABLE", "yellow_taxi_trips"],
        ["", "16.186.386 linhas, 19 colunas"],
      ],
      fill: CARD,
    },
    {
      n: "silver",
      objs: [
        ["TABLE", "yellow_taxi_trips"],
        ["TABLE", "_pipeline_run_log"],
        ["", "15.339.417 linhas, 6 colunas"],
      ],
      fill: CARD_WARM,
    },
  ];

  const sw = 3.9, sy = 2.12, sh = 2.5;
  schemas.forEach((sc, i) => {
    const x = M + i * (sw + 0.32);
    card(s, x, sy, sw, sh, sc.fill, { shadow: true });
    s.addText("SCHEMA", {
      x: x + 0.32, y: sy + 0.24, w: 2.0, h: 0.26,
      fontFace: H_FONT, fontSize: 9.5, bold: true, color: RED, charSpacing: 1.5, margin: 0,
    });
    s.addText(sc.n, {
      x: x + 0.32, y: sy + 0.52, w: 3.2, h: 0.42,
      fontFace: M_FONT, fontSize: 20, bold: true, color: INK, margin: 0, valign: "middle",
    });
    sc.objs.forEach((o, j) => {
      const oy = sy + 1.06 + j * 0.44;
      if (o[0]) {
        s.addText(o[0], {
          x: x + 0.32, y: oy, w: 0.85, h: 0.3,
          fontFace: H_FONT, fontSize: 8.5, bold: true, color: FAINT, margin: 0, valign: "middle",
        });
        s.addText(o[1], {
          x: x + 1.2, y: oy, w: 2.5, h: 0.3,
          fontFace: M_FONT, fontSize: 11.5, color: INK, margin: 0, valign: "middle",
        });
      } else {
        s.addText(o[1], {
          x: x + 0.32, y: oy, w: 3.3, h: 0.3,
          fontFace: B_FONT, fontSize: 11.5, italic: true, color: MUTED, margin: 0, valign: "middle",
        });
      }
    });
    if (i < schemas.length - 1) arrow(s, x + sw + 0.02, sy + sh / 2 - 0.11, 0.26, 0.22);
  });

  const notes = [
    { t: "Provisionamento idempotente",
      d: "CREATE CATALOG / SCHEMA / VOLUME IF NOT EXISTS — reexecutar a pipeline nunca quebra nem duplica objetos." },
    { t: "Documentação no próprio objeto",
      d: "Cada schema e volume é criado com COMMENT: o catálogo se descreve, sem doc paralela para desatualizar." },
    { t: "Lineage e permissões nativos",
      d: "O Unity Catalog rastreia landing → bronze → silver e centraliza o controle de acesso." },
  ];
  notes.forEach((n, i) => {
    const x = M + i * 4.07;
    card(s, x, 4.88, 3.72, 1.72, CARD);
    s.addText(n.t, {
      x: x + 0.3, y: 5.08, w: 3.2, h: 0.34,
      fontFace: H_FONT, fontSize: 13, bold: true, color: INK, margin: 0, valign: "middle",
    });
    s.addText(n.d, {
      x: x + 0.3, y: 5.46, w: 3.15, h: 0.95,
      fontFace: B_FONT, fontSize: 11.5, color: MUTED, margin: 0, valign: "top", lineSpacingMultiple: 1.12,
    });
  });

  footnote(s, "Fallback previsto para o catalog `workspace` caso a criação falhe — não foi necessário: na Free Edition o CREATE CATALOG usa o Default Storage automaticamente.");

  s.addNotes(
    "O catálogo não foi criado clicando na UI — é código versionado (src/ingestion/landing_zone.py), " +
    "idempotente, que roda como parte da pipeline. Isso é o que torna o ambiente reproduzível do zero. " +
    "O fallback para o catalog 'workspace' existe como rede de segurança e está documentado em research.md; " +
    "na prática o CREATE CATALOG funcionou direto. Os COMMENT em cada objeto são o que faz o catálogo " +
    "ser autoexplicativo para quem chega depois."
  );
}

// =========================================================================
// 8 — Landing & Bronze
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Features 002 & 004 — Ingestão");
  slideTitle(s, "Landing & Bronze");

  card(s, M, 2.0, 5.65, 2.5, CARD);
  badge(s, M + 0.42, 2.35, "L");
  s.addText("Landing", {
    x: M + 1.05, y: 2.35, w: 3.0, h: 0.46,
    fontFace: H_FONT, fontSize: 19, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText(
    [
      { text: "5 parquets baixados byte-a-byte da fonte NYC TLC.", options: { bullet: true, breakLine: true } },
      { text: "Cada arquivo verificado: não vazio, legível pelo Spark, sem outlier de tamanho, Content-Length batendo.", options: { bullet: true, breakLine: true } },
      { text: "Nenhuma transformação.", options: { bullet: true } },
    ],
    { x: M + 0.42, y: 3.0, w: 4.85, h: 1.35,
      fontFace: B_FONT, fontSize: 12.5, color: MUTED, paraSpaceAfter: 5, margin: 0, valign: "top" }
  );

  card(s, M + 6.1, 2.0, 5.65, 2.5, CARD);
  badge(s, M + 6.52, 2.35, "B");
  s.addText("Bronze", {
    x: M + 7.15, y: 2.35, w: 3.0, h: 0.46,
    fontFace: H_FONT, fontSize: 19, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText(
    [
      { text: "Ingestão 1:1, sem regras de negócio.", options: { bullet: true, breakLine: true } },
      { text: "Só tratamento técnico: cast do drift de schema entre meses e metadados de ingestão.", options: { bullet: true, breakLine: true } },
      { text: "Dedup apenas de linhas 100% idênticas.", options: { bullet: true } },
    ],
    { x: M + 6.52, y: 3.0, w: 4.85, h: 1.35,
      fontFace: B_FONT, fontSize: 12.5, color: MUTED, paraSpaceAfter: 5, margin: 0, valign: "top" }
  );

  card(s, M, 4.82, W - 2 * M, 1.72, CARD_ACCENT, { shadow: true });
  const stats = [
    { v: "16.186.386", l: "linhas ingeridas na bronze" },
    { v: "0", l: "duplicatas de linha completa" },
    { v: "5", l: "arquivos mensais (Jan–Mai 2023)" },
  ];
  stats.forEach((st, i) => {
    const x = M + 0.55 + i * 3.9;
    s.addText(st.v, {
      x, y: 5.02, w: 3.6, h: 0.72,
      fontFace: H_FONT, fontSize: 38, bold: true, color: RED, margin: 0, valign: "middle",
    });
    s.addText(st.l, {
      x, y: 5.78, w: 3.6, h: 0.5,
      fontFace: B_FONT, fontSize: 12.5, color: MUTED, margin: 0, valign: "top",
    });
  });

  s.addNotes(
    "A separação Landing/Bronze é o que permite reprocessar sem baixar de novo. " +
    "As 0 duplicatas não são um acaso feliz: o profiling (feature 003) verificou os 5 meses e não achou " +
    "nenhuma duplicata de linha completa — por isso o contrato da silver marca a regra de duplicatas como " +
    "'resolvida a montante', sem lógica própria de dedup."
  );
}

// =========================================================================
// 9 — Profiling: resultados reais
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Feature 003 — Data Profiling (EDA)");
  slideTitle(s, "O que o profiling achou — e o que cada achado virou");

  card(s, M, 1.6, W - 2 * M, 0.62, CARD_ACCENT);
  s.addText(
    "“As regras não são arbitrárias — cada uma sai de um achado do profiling.”",
    { x: M + 0.4, y: 1.6, w: 11.4, h: 0.62,
      fontFace: H_FONT, fontSize: 14.5, bold: true, italic: true, color: INK, margin: 0, valign: "middle" }
  );

  // Colunas dimensionadas para não invadir a seta em x = 7.92
  const cols = [M + 0.35, 5.2, 8.35];
  const colW = [3.9, 2.6, 4.2];
  const headers = ["ACHADO", "NÚMERO REAL (POR MÊS)", "DECISÃO"];
  headers.forEach((h, i) => {
    s.addText(h, {
      x: cols[i], y: 2.42, w: colW[i], h: 0.26,
      fontFace: H_FONT, fontSize: 9.5, bold: true,
      color: i === 2 ? RED : MUTED, charSpacing: 1.5, margin: 0, valign: "middle",
    });
  });

  const rows = [
    ["Drift de tipo em passenger_count", "jan floating, fev–mai integer", "Cast explícito no contrato"],
    ["passenger_count nulo ou zero", "4,01% a 4,60% das linhas", "Regra de drop"],
    ["total_amount ≤ 0", "0,84% a 0,92% das linhas", "Regra de drop"],
    ["Datas fora da janela Jan–Mai", "de 5 a 1.015 linhas", "Regra de drop"],
    ["Duplicatas de linha completa", "0 em todos os 5 meses", "Nenhuma regra necessária"],
  ];
  rows.forEach((r, i) => {
    const y = 2.76 + i * 0.78;
    card(s, M, y, W - 2 * M, 0.68, i % 2 === 0 ? CARD : WHITE);
    s.addText(r[0], {
      x: cols[0], y, w: colW[0], h: 0.68,
      fontFace: B_FONT, fontSize: 13, bold: true, color: INK, margin: 0, valign: "middle",
    });
    s.addText(r[1], {
      x: cols[1], y, w: colW[1], h: 0.68,
      fontFace: B_FONT, fontSize: 12.5, color: MUTED, margin: 0, valign: "middle",
    });
    arrow(s, 7.92, y + 0.24, 0.26, 0.2);
    s.addText(r[2], {
      x: cols[2], y, w: colW[2], h: 0.68,
      fontFace: B_FONT, fontSize: 12.5, bold: true, color: i === 4 ? MUTED : INK, margin: 0, valign: "middle",
    });
  });

  footnote(s, "Volumetria por mês: 3.066.766 · 2.913.955 · 3.403.766 · 3.288.250 · 3.513.649 linhas. Fonte: specs/003-data-profiling/findings.md, rodado sobre a bronze em compute serverless.", 6.78);

  s.addNotes(
    "Este é o slide que responde 'por que essas regras e não outras'. A coluna do meio é a evidência: " +
    "cada regra nasceu de um número medido, não de intuição. Detalhes úteis se perguntarem: " +
    "total_amount tem mínimo de -982,95 e máximo de 6.304,90 na bronze — defeito conhecido da NYC TLC. " +
    "VendorID, total_amount e os dois timestamps têm zero nulos em todos os meses. " +
    "A última linha é importante: o profiling também serve para NÃO criar regra — duplicatas deram zero, " +
    "então a silver não carrega lógica de dedup que não faria nada."
  );
}

// =========================================================================
// 10 — Contrato de dados
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Feature 005");
  slideTitle(s, "Contrato de dados, escrito antes do código");

  card(s, M, 1.62, W - 2 * M, 0.8, CARD_ACCENT);
  s.addText(
    [
      { text: "contracts/nyc_taxi_silver.yaml", options: { bold: true, color: INK, fontFace: M_FONT } },
      { text: "  — versionado no repositório e carregado em runtime pelo job: o contrato dirige a pipeline, não só a documenta.", options: { color: MUTED } },
    ],
    { x: M + 0.4, y: 1.62, w: 10.95, h: 0.8, fontFace: B_FONT, fontSize: 13, margin: 0, valign: "middle" }
  );

  const blocks = [
    { t: "Grain declarado", d: "Uma linha = um evento de corrida. Sem chave primária formal sobre 6 colunas — a garantia de unicidade é herdada do dedup da bronze sobre as 19 colunas de origem." },
    { t: "6 colunas, tipos fixos", d: "VendorID, passenger_count, total_amount, os dois timestamps e _silver_processed_at. Metadados da bronze são descartados de propósito." },
    { t: "Schema validado antes de gravar", d: "O job compara o DataFrame com o contrato e falha em caso de drift — a silver nunca recebe schema divergente." },
    { t: "Política de versionamento", d: "MAJOR para remover coluna ou mudar política de regra; MINOR para coluna opcional nova; PATCH só para redação." },
  ];
  const bw = 6.08, bh = 1.9;
  blocks.forEach((b, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * (bw + 0.24), y = 2.68 + row * (bh + 0.24);
    card(s, x, y, bw, bh, CARD);
    badge(s, x + 0.32, y + 0.28, String(i + 1));
    s.addText(b.t, {
      x: x + 0.95, y: y + 0.24, w: bw - 1.3, h: 0.36,
      fontFace: H_FONT, fontSize: 14.5, bold: true, color: INK, margin: 0, valign: "middle",
    });
    s.addText(b.d, {
      x: x + 0.95, y: y + 0.66, w: bw - 1.3, h: 1.05,
      fontFace: B_FONT, fontSize: 12, color: MUTED, margin: 0, valign: "top", lineSpacingMultiple: 1.15,
    });
  });

  footnote(s, "O contrato foi implementado pela feature 006 sem nenhuma alteração: `git diff` no arquivo saiu limpo ao fim da implementação.", 6.82);

  s.addNotes(
    "Duas features distintas de propósito: 005 é só o contrato (nenhum código de escrita), 006 é a implementação. " +
    "Escrever o contrato primeiro força a decidir o schema sem a pressão de fazer o código passar. " +
    "O detalhe que costuma impressionar: o YAML é carregado em runtime pelo job (subido ao workspace via " +
    "databricks workspace import), então mudar o contrato muda o comportamento da pipeline — ele não é decorativo."
  );
}

// =========================================================================
// 11 — Regras de negócio da silver + resultado real
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Feature 006 — Data Quality");
  slideTitle(s, "As regras de negócio que barram dados na silver");

  const rules = [
    { n: "1", r: "total_amount ≤ 0", c: "144.146",
      w: "Não pode ser uma tarifa real cobrada; manteria a média da Q1 artificialmente baixa." },
    { n: "2", r: "passenger_count nulo ou zero", c: "702.146",
      w: "Corrida sem passageiro é defeito de registro, não corrida válida; enviesaria a Q2." },
    { n: "3", r: "dropoff anterior ao pickup", c: "795",
      w: "Corrida que termina antes de começar é fisicamente impossível — erro de timestamp." },
    { n: "4", r: "data fora de Jan–Mai 2023", c: "1.077",
      w: "Vazamento de período adjacente; fora da janela de análise do case." },
  ];
  const rw = 6.08, rh = 1.62;
  rules.forEach((rl, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * (rw + 0.24), y = 1.72 + row * (rh + 0.22);
    card(s, x, y, rw, rh, CARD);
    badge(s, x + 0.32, y + 0.28, rl.n);
    s.addText(rl.r, {
      x: x + 0.95, y: y + 0.22, w: 3.5, h: 0.4,
      fontFace: M_FONT, fontSize: 13, bold: true, color: INK, margin: 0, valign: "middle",
    });
    s.addText(
      [
        { text: rl.c, options: { bold: true, color: RED, fontSize: 15, fontFace: H_FONT } },
        { text: "  linhas", options: { color: MUTED, fontSize: 11, fontFace: B_FONT } },
      ],
      { x: x + 4.35, y: y + 0.22, w: 1.6, h: 0.4, align: "right", margin: 0, valign: "middle" }
    );
    s.addText(rl.w, {
      x: x + 0.95, y: y + 0.68, w: rw - 1.3, h: 0.8,
      fontFace: B_FONT, fontSize: 12, color: MUTED, margin: 0, valign: "top", lineSpacingMultiple: 1.15,
    });
  });

  // Funil real do run
  card(s, M, 5.32, W - 2 * M, 1.28, CARD_ACCENT, { shadow: true });
  const funnel = [
    { v: "16.186.386", l: "lidas da bronze" },
    { v: "846.969", l: "descartadas (5,23%)" },
    { v: "15.339.417", l: "escritas na silver" },
  ];
  funnel.forEach((f, i) => {
    const x = M + 0.5 + i * 3.55;
    s.addText(f.v, {
      x, y: 5.5, w: 3.0, h: 0.5,
      fontFace: H_FONT, fontSize: 25, bold: true,
      color: i === 1 ? MUTED : RED, margin: 0, valign: "middle",
    });
    s.addText(f.l, {
      x, y: 6.0, w: 3.0, h: 0.32,
      fontFace: B_FONT, fontSize: 12, color: MUTED, margin: 0, valign: "top",
    });
    if (i < funnel.length - 1) arrow(s, x + 3.1, 5.72, 0.28, 0.22);
  });

  footnote(s, "As 4 contagens são independentes, avaliadas sobre a bronze inteira — por isso somam 848.164, e não 846.969: 1.195 linhas violaram mais de uma regra e são contadas uma vez só no total.", 6.78);

  s.addNotes(
    "Todas as 4 regras são 'drop' — nenhuma tenta corrigir o dado, porque não há como inferir o valor " +
    "correto de uma corrida com duração negativa. As contagens por regra reproduzem exatamente a baseline " +
    "medida na bronze (feature 004), o que prova que foram avaliadas sobre o input completo e não sobre um " +
    "conjunto que encolhe a cada regra. Verificação pós-escrita: as 4 condições retornam 0 linhas na silver. " +
    "O run passou de primeira, sem correção durante a implementação."
  );
}

// =========================================================================
// 12 — Observabilidade
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Feature 007");
  slideTitle(s, "Observabilidade é entregável");

  const obs = [
    { t: "Log de execução", d: "Cada run — bronze e silver — grava uma linha em ifood_case.silver._pipeline_run_log." },
    { t: "O que é registrado", d: "Linhas lidas e escritas, drops por regra, status e duração de cada etapa." },
    { t: "Lineage nativo", d: "Unity Catalog rastreia landing → bronze → silver sem instrumentação extra." },
  ];
  obs.forEach((o, i) => {
    const y = 2.0 + i * 1.32;
    card(s, M, y, 6.05, 1.12, CARD);
    badge(s, M + 0.32, y + 0.33, String(i + 1));
    s.addText(o.t, {
      x: M + 0.95, y: y + 0.16, w: 4.8, h: 0.34,
      fontFace: H_FONT, fontSize: 14.5, bold: true, color: INK, margin: 0, valign: "middle",
    });
    s.addText(o.d, {
      x: M + 0.95, y: y + 0.5, w: 4.85, h: 0.52,
      fontFace: B_FONT, fontSize: 12, color: MUTED, margin: 0, valign: "top",
    });
  });

  card(s, 7.2, 2.0, 5.38, 2.32, CARD_ACCENT, { shadow: true });
  s.addText("ALERTA AUTOMÁTICO", {
    x: 7.6, y: 2.26, w: 4.6, h: 0.3,
    fontFace: H_FONT, fontSize: 11, bold: true, color: RED, charSpacing: 2, margin: 0,
  });
  s.addText("> 1%", {
    x: 7.6, y: 2.62, w: 4.6, h: 0.85,
    fontFace: H_FONT, fontSize: 46, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText("Dispara quando qualquer regra de qualidade derruba mais de 1% das linhas de um run.", {
    x: 7.6, y: 3.5, w: 4.6, h: 0.68,
    fontFace: B_FONT, fontSize: 12.5, color: MUTED, margin: 0, valign: "top", lineSpacingMultiple: 1.15,
  });

  card(s, 7.2, 4.55, 5.38, 1.98, CARD);
  s.addText("_pipeline_run_log", {
    x: 7.55, y: 4.73, w: 4.7, h: 0.3,
    fontFace: M_FONT, fontSize: 12, bold: true, color: INK, margin: 0, valign: "middle",
  });
  const logRows = [
    ["etapa", "lidas", "escritas", "status"],
    ["bronze", "16.186.386", "16.186.386", "OK"],
    ["silver", "16.186.386", "15.339.417", "OK"],
  ];
  const logX = [7.55, 8.65, 10.15, 11.75];
  logRows.forEach((row, ri) => {
    const y = 5.13 + ri * 0.42;
    row.forEach((cell, ci) => {
      s.addText(cell, {
        x: logX[ci], y, w: 1.45, h: 0.34,
        fontFace: B_FONT, fontSize: 11, bold: ri === 0,
        color: ri === 0 ? MUTED : (ci === 3 ? RED : INK),
        margin: 0, valign: "middle",
      });
    });
  });

  s.addNotes(
    "O log é uma tabela Delta, não um arquivo de texto — dá para consultar por SQL e montar série " +
    "histórica de qualidade. Os números da tabela são os do run real. O limiar de 1% é o que transforma " +
    "observabilidade em ação: abaixo disso é ruído esperado, acima disso alguém olha. " +
    "Note que a regra de passenger_count (4,3%) estouraria esse limiar — é exatamente o tipo de caso " +
    "que o alerta existe para trazer à tona, e aqui já sabíamos a causa pelo profiling."
  );
}

// =========================================================================
// 13 — Q1
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Pergunta 1");
  slideTitle(s, "Média de total_amount por mês");

  s.addChart(
    pres.ChartType.bar,
    [{ name: "Média total_amount (US$)", labels: ["Jan", "Fev", "Mar", "Abr", "Mai"],
       values: [27.46, 27.37, 28.29, 28.78, 29.45] }],
    {
      x: M, y: 1.95, w: 8.0, h: 4.15,
      barDir: "col", chartColors: [RED],
      showTitle: false, showLegend: false, showValue: true,
      dataLabelPosition: "outEnd", dataLabelFormatCode: '"$"0.00',
      dataLabelFontSize: 12, dataLabelFontBold: true, dataLabelColor: INK, dataLabelFontFace: B_FONT,
      valAxisMinVal: 25, valAxisMaxVal: 30.5,
      valAxisLabelColor: MUTED, valAxisLabelFontSize: 11, valAxisLabelFontFace: B_FONT,
      valAxisLabelFormatCode: '"$"0',
      catAxisLabelColor: INK, catAxisLabelFontSize: 13, catAxisLabelFontFace: B_FONT,
      valGridLine: { color: "EDEDF0", size: 1 }, catGridLine: { style: "none" },
      barGapWidthPct: 55,
    }
  );

  card(s, 9.1, 1.95, 3.48, 4.15, CARD);
  s.addText("O que os dados mostram", {
    x: 9.42, y: 2.25, w: 2.9, h: 0.32,
    fontFace: H_FONT, fontSize: 14, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText("+7,2%", {
    x: 9.42, y: 2.73, w: 2.9, h: 0.72,
    fontFace: H_FONT, fontSize: 36, bold: true, color: RED, margin: 0, valign: "middle",
  });
  s.addText("de janeiro a maio", {
    x: 9.42, y: 3.45, w: 2.9, h: 0.3,
    fontFace: B_FONT, fontSize: 12, color: MUTED, margin: 0, valign: "top",
  });
  s.addText(
    [
      { text: "Tendência de alta consistente: $27,46 em janeiro para $29,45 em maio.", options: { bullet: true, breakLine: true } },
      { text: "Única queda em fevereiro ($27,37), o mês com menos corridas do período.", options: { bullet: true } },
    ],
    { x: 9.42, y: 3.95, w: 2.86, h: 1.6,
      fontFace: B_FONT, fontSize: 12, color: MUTED, paraSpaceAfter: 8, margin: 0, valign: "top" }
  );

  footnote(s, "Eixo vertical inicia em $25 para evidenciar a variação. Fonte: ifood_case.silver.yellow_taxi_trips, agregação direta sem limpeza adicional.", 6.35);

  s.addNotes(
    "Valores exatos: Jan 27,46 / Fev 27,37 / Mar 28,29 / Abr 28,78 / Mai 29,45. " +
    "Ser honesta sobre o eixo truncado se perguntarem — está anotado no rodapé e os rótulos mostram os " +
    "valores absolutos. Fevereiro é o mês de menor volume (2,91M corridas), consistente com ser mês mais curto. " +
    "Comparação útil: na bronze, sem limpeza, as médias eram ~27,02 a 28,96 — a limpeza subiu ligeiramente " +
    "a média ao remover os valores negativos, sem distorcer a distribuição."
  );
}

// =========================================================================
// 14 — Q2
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Pergunta 2");
  slideTitle(s, "Média de passageiros por hora do dia — maio");

  const hours = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0") + "h");
  const vals = [1.43, 1.44, 1.46, 1.45, 1.41, 1.28, 1.26, 1.28, 1.30, 1.31, 1.35, 1.36,
                1.38, 1.39, 1.39, 1.40, 1.40, 1.39, 1.38, 1.39, 1.40, 1.42, 1.43, 1.42];

  s.addChart(
    pres.ChartType.line,
    [{ name: "Média passenger_count", labels: hours, values: vals }],
    {
      x: M, y: 1.95, w: 8.0, h: 4.15,
      chartColors: [RED], lineSize: 3, lineSmooth: false,
      showTitle: false, showLegend: false, showValue: false,
      valAxisMinVal: 1.2, valAxisMaxVal: 1.5, valAxisMajorUnit: 0.05,
      valAxisLabelColor: MUTED, valAxisLabelFontSize: 11, valAxisLabelFontFace: B_FONT,
      valAxisLabelFormatCode: "0.00",
      catAxisLabelColor: MUTED, catAxisLabelFontSize: 9, catAxisLabelFontFace: B_FONT,
      valGridLine: { color: "EDEDF0", size: 1 }, catGridLine: { style: "none" },
    }
  );

  card(s, 9.1, 1.95, 3.48, 4.15, CARD);
  s.addText("Variação pequena", {
    x: 9.42, y: 2.25, w: 2.9, h: 0.32,
    fontFace: H_FONT, fontSize: 14, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText("1,26 – 1,46", {
    x: 9.42, y: 2.73, w: 2.9, h: 0.72,
    fontFace: H_FONT, fontSize: 30, bold: true, color: RED, margin: 0, valign: "middle",
  });
  s.addText("passageiros por corrida", {
    x: 9.42, y: 3.45, w: 2.9, h: 0.3,
    fontFace: B_FONT, fontSize: 12, color: MUTED, margin: 0, valign: "top",
  });
  s.addText(
    [
      { text: "Mínimo às 6h (1,26) — deslocamento pendular, majoritariamente solo.", options: { bullet: true, breakLine: true } },
      { text: "Máximo às 2h (1,46) — corridas de madrugada tendem a ser compartilhadas.", options: { bullet: true, breakLine: true } },
      { text: "Nenhum pico de corridas multi-passageiro em hora específica.", options: { bullet: true } },
    ],
    { x: 9.42, y: 3.95, w: 2.86, h: 2.0,
      fontFace: B_FONT, fontSize: 12, color: MUTED, paraSpaceAfter: 8, margin: 0, valign: "top" }
  );

  footnote(s, "Eixo vertical entre 1,20 e 1,50 para evidenciar a variação. Fonte: ifood_case.silver.yellow_taxi_trips, maio/2023.", 6.35);

  s.addNotes(
    "A conclusão honesta aqui é a ausência de sinal forte: a amplitude é de 0,2 passageiro. " +
    "Vale dizer isso explicitamente — nem toda análise precisa achar um padrão dramático. " +
    "A leitura de madrugada versus hora do rush é plausível, mas é interpretação, não algo que o dado prove. " +
    "Lembrar que essa média só é confiável porque as linhas com passenger_count zero ou nulo (4,6% em maio) " +
    "foram removidas na silver — sem isso, a média cairia artificialmente."
  );
}

// =========================================================================
// 15 — Bônus Prophet
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Bônus — além do escopo pedido");
  slideTitle(s, "Decomposição do volume diário com Prophet");

  s.addImage({
    path: path.join(ROOT, "analysis", "charts", "daily_trip_volume_components.png"),
    x: 4.35, y: 1.85, w: 8.35, h: 4.9,
  });

  card(s, M, 1.9, 3.3, 1.72, CARD);
  s.addText("Tendência", {
    x: M + 0.28, y: 2.08, w: 2.8, h: 0.3,
    fontFace: H_FONT, fontSize: 13, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText("92k → 107k", {
    x: M + 0.28, y: 2.42, w: 2.8, h: 0.5,
    fontFace: H_FONT, fontSize: 24, bold: true, color: RED, margin: 0, valign: "middle",
  });
  s.addText("corridas/dia, de janeiro a maio", {
    x: M + 0.28, y: 2.94, w: 2.8, h: 0.5,
    fontFace: B_FONT, fontSize: 11.5, color: MUTED, margin: 0, valign: "top",
  });

  card(s, M, 3.78, 3.3, 1.72, CARD_WARM);
  s.addText("Sazonalidade semanal", {
    x: M + 0.28, y: 3.96, w: 2.8, h: 0.3,
    fontFace: H_FONT, fontSize: 13, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText("+10,6k", {
    x: M + 0.28, y: 4.3, w: 2.8, h: 0.5,
    fontFace: H_FONT, fontSize: 24, bold: true, color: RED, margin: 0, valign: "middle",
  });
  s.addText("pico na quinta; mínimo dom/seg, −13k a −15k", {
    x: M + 0.28, y: 4.82, w: 2.8, h: 0.6,
    fontFace: B_FONT, fontSize: 11.5, color: MUTED, margin: 0, valign: "top",
  });

  s.addText(
    "Modelo ajustado apenas sobre as datas históricas — sem previsão futura, " +
    "porque o objetivo era enxergar o padrão já presente nos dados.",
    { x: M, y: 5.68, w: 3.3, h: 1.0,
      fontFace: B_FONT, fontSize: 11.5, italic: true, color: MUTED, margin: 0, valign: "top", lineSpacingMultiple: 1.15 }
  );

  s.addNotes(
    "Deixar claro que isso é bônus, não uma das duas perguntas obrigatórias. " +
    "O gráfico é a saída real do Prophet (analysis/charts/), não uma recriação. " +
    "O padrão semanal é o esperado para táxi urbano: vale no fim de semana/início da semana, " +
    "pico nos dias úteis centrais."
  );
}

// =========================================================================
// 16 — POC chat NL→SQL
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Feature 009");
  slideTitle(s, "POC: chat em linguagem natural → SQL");

  const flow = [
    { t: "Pergunta em PT", d: "Interface Gradio" },
    { t: "Foundation Model", d: "Gera o SQL" },
    { t: "Execução real", d: "Sobre a silver" },
    { t: "Resposta formatada", d: "Volta ao usuário" },
  ];
  const fw = 2.72, fy = 2.0;
  flow.forEach((f, i) => {
    const x = M + i * (fw + 0.45);
    card(s, x, fy, fw, 1.55, CARD);
    badge(s, x + 0.28, fy + 0.26, String(i + 1), { d: 0.38, fontSize: 11 });
    s.addText(f.t, {
      x: x + 0.28, y: fy + 0.74, w: fw - 0.56, h: 0.34,
      fontFace: H_FONT, fontSize: 13.5, bold: true, color: INK, margin: 0, valign: "middle",
    });
    s.addText(f.d, {
      x: x + 0.28, y: fy + 1.06, w: fw - 0.56, h: 0.32,
      fontFace: B_FONT, fontSize: 11.5, color: MUTED, margin: 0, valign: "top",
    });
    if (i < flow.length - 1) arrow(s, x + fw + 0.06, fy + 0.66, 0.3, 0.22);
  });

  card(s, M, 3.88, 6.05, 2.4, CARD_ACCENT, { shadow: true });
  s.addText("É uma POC, não um produto", {
    x: M + 0.42, y: 4.14, w: 5.2, h: 0.4,
    fontFace: H_FONT, fontSize: 19, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText(
    [
      { text: "Guarda contra SQL injection: apenas SELECT é aceito.", options: { bullet: true, breakLine: true } },
      { text: "Demonstra o caminho de consumo da silver — não é entregável de produção.", options: { bullet: true } },
    ],
    { x: M + 0.42, y: 4.66, w: 5.25, h: 1.4,
      fontFace: B_FONT, fontSize: 13, color: MUTED, paraSpaceAfter: 8, margin: 0, valign: "top" }
  );

  card(s, 7.05, 3.88, 5.53, 2.4, CARD);
  s.addText("Por que não o Genie Space", {
    x: 7.45, y: 4.14, w: 4.8, h: 0.4,
    fontFace: H_FONT, fontSize: 16, bold: true, color: INK, margin: 0, valign: "middle",
  });
  s.addText(
    "O Genie é só-UI: não tem caminho via CLI ou API. Adotá-lo quebraria o padrão de " +
    "automação ponta-a-ponta do projeto, em que todo artefato é criado por código versionado.",
    { x: 7.45, y: 4.66, w: 4.75, h: 1.4,
      fontFace: B_FONT, fontSize: 13, color: MUTED, margin: 0, valign: "top", lineSpacingMultiple: 1.2 }
  );

  s.addNotes(
    "Enfatizar POC — está na constituição do projeto que isso nunca seja vendido como diferencial. " +
    "A troca do Genie pelo app próprio é uma decisão de coerência: se tudo no projeto é criado via CLI " +
    "e versionado, uma peça que só existe clicando na UI seria a exceção que quebra a reprodutibilidade."
  );
}

// =========================================================================
// 17 — Engenharia agêntica na prática
// =========================================================================
{
  const s = lightSlide();
  eyebrow(s, "Na prática");
  slideTitle(s, "Limitações reais encontradas — e contornadas");

  const rows = [
    ["Sem ALTER SCHEMA … RENAME no Unity Catalog", "Rename via create → copy → verify → drop"],
    ["input_file_name() não suportado em compute UC", "Troca por _metadata.file_name"],
    ["Endpoint de serving com rate limit", "Fallback automático de modelo"],
    ["SQL Warehouse frio na primeira query", "Lógica de polling até ficar disponível"],
  ];

  s.addText("LIMITAÇÃO", {
    x: M + 0.4, y: 1.95, w: 5.0, h: 0.28,
    fontFace: H_FONT, fontSize: 10.5, bold: true, color: MUTED, charSpacing: 1.5, margin: 0,
  });
  s.addText("CONTORNO", {
    x: 7.15, y: 1.95, w: 5.0, h: 0.28,
    fontFace: H_FONT, fontSize: 10.5, bold: true, color: RED, charSpacing: 1.5, margin: 0,
  });

  rows.forEach((r, i) => {
    const y = 2.35 + i * 0.92;
    card(s, M, y, W - 2 * M, 0.78, CARD);
    s.addText(r[0], {
      x: M + 0.4, y, w: 5.6, h: 0.78,
      fontFace: B_FONT, fontSize: 13, color: INK, margin: 0, valign: "middle",
    });
    arrow(s, 6.42, y + 0.29, 0.3, 0.2);
    s.addText(r[1], {
      x: 7.15, y, w: 5.2, h: 0.78,
      fontFace: B_FONT, fontSize: 13, bold: true, color: INK, margin: 0, valign: "middle",
    });
  });

  card(s, M, 6.03, W - 2 * M, 0.72, CARD_ACCENT);
  s.addText(
    [
      { text: "DECISOES_PROJETO.md", options: { bold: true, fontFace: M_FONT, color: INK } },
      { text: "  — o log de decisões do projeto: cada contorno acima ficou registrado com o motivo, não só com o código.", options: { color: MUTED } },
    ],
    { x: M + 0.4, y: 6.03, w: 11.4, h: 0.72, fontFace: B_FONT, fontSize: 12.5, margin: 0, valign: "middle" }
  );

  s.addNotes(
    "Esse slide existe para mostrar que engenharia agêntica não é 'o agente escreve e funciona'. " +
    "Cada uma dessas limitações apareceu em execução real na Free Edition e exigiu decisão de arquitetura. " +
    "O valor do DECISOES_PROJETO.md é que a sessão seguinte do agente não redescobre o mesmo problema do zero."
  );
}

// =========================================================================
// 18 — Fechamento
// =========================================================================
{
  const s = darkSlide();

  s.addShape(pres.ShapeType.ellipse, {
    x: 10.2, y: 3.6, w: 5.4, h: 5.4,
    fill: { color: RED, transparency: 88 }, line: { width: 0 },
  });

  eyebrow(s, "Fechamento", { color: RED });
  slideTitle(s, "O que foi entregue", { color: WHITE });

  const delivered = [
    "Catálogo e pipeline medallion completos (landing → bronze → silver)",
    "As 2 respostas analíticas pedidas pelo case",
    "Bônus: decomposição de série temporal com Prophet",
    "POC de consumo: chat em linguagem natural sobre a silver",
  ];
  delivered.forEach((t, i) => {
    const y = 1.95 + i * 0.62;
    s.addShape(pres.ShapeType.ellipse, {
      x: M + 0.04, y: y + 0.13, w: 0.13, h: 0.13,
      fill: { color: RED }, line: { width: 0 },
    });
    s.addText(t, {
      x: M + 0.38, y, w: 6.9, h: 0.42,
      fontFace: B_FONT, fontSize: 14.5, color: WHITE, margin: 0, valign: "middle",
    });
  });

  s.addText("O que a abordagem agêntica / SDD trouxe", {
    x: M, y: 4.66, w: 7.2, h: 0.36,
    fontFace: H_FONT, fontSize: 15, bold: true, color: RED, margin: 0, valign: "middle",
  });

  const gains = [
    ["Rastreabilidade", "de cada FR até a linha de código"],
    ["Contratos", "versionados antes da implementação"],
    ["Qualidade", "como gate de execução, não relatório"],
    ["Checkpoints", "humanos em cada fase do ciclo"],
  ];
  gains.forEach((g, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * 3.55, y = 5.18 + row * 0.92;
    card(s, x, y, 3.32, 0.78, DARK_SOFT);
    s.addText(g[0], {
      x: x + 0.28, y: y + 0.08, w: 2.9, h: 0.32,
      fontFace: H_FONT, fontSize: 13, bold: true, color: WHITE, margin: 0, valign: "middle",
    });
    s.addText(g[1], {
      x: x + 0.28, y: y + 0.4, w: 2.9, h: 0.3,
      fontFace: B_FONT, fontSize: 11, color: MUTED_DK, margin: 0, valign: "middle",
    });
  });

  s.addText("Obrigada", {
    x: 8.35, y: 2.55, w: 4.2, h: 0.8,
    fontFace: H_FONT, fontSize: 34, bold: true, color: WHITE, margin: 0, valign: "middle",
  });
  s.addText(AUTOR + "\niFood Data Architect Case", {
    x: 8.35, y: 3.4, w: 4.2, h: 0.85,
    fontFace: B_FONT, fontSize: 14, color: MUTED_DK, margin: 0, valign: "top", lineSpacingMultiple: 1.25,
  });

  s.addNotes(
    "Fechar reforçando o meta-objetivo: a pipeline é o artefato, mas o que se propõe como " +
    "boa prática é o processo que a produziu. Abrir para perguntas."
  );
}

pres.writeFile({ fileName: OUT }).then(() => {
  console.log("Deck gerado: " + OUT);
});
