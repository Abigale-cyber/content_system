const state = {
  settings: null,
  articles: [],
  selectedId: "",
  detail: null,
  activeView: "workbench",
  previewMode: "preview",
  lastSavedName: "wechat-preview.html",
  autoPreviewTimer: null,
  form: {
    tone: {
      theme: "",
      primaryColor: "#b3832f",
      saturation: 100,
      opacity: 88,
    },
    typography: {
      template: "default",
      titleStyle: "standard",
      bodySize: 16,
      lineHeight: 1.9,
      paragraphGap: 16,
      sectionStyle: "editorial",
      imageRadius: 24,
      imageSpacing: 22,
    },
    coverPrompt: "",
    inlinePrompt: "",
    inlinePositions: {
      1: "",
      2: "",
    },
    coverCandidatePath: "",
  },
};

const refs = {
  importButton: document.getElementById("importButton"),
  markdownFileInput: document.getElementById("markdownFileInput"),
  uploadDropzone: document.getElementById("uploadDropzone"),
  articleCount: document.getElementById("articleCount"),
  articleSwitcherWrap: document.getElementById("articleSwitcherWrap"),
  articleSwitcher: document.getElementById("articleSwitcher"),
  detailEmptyState: document.getElementById("detailEmptyState"),
  detailWrap: document.getElementById("detailWrap"),
  workspaceBadge: document.getElementById("workspaceBadge"),
  detailTitle: document.getElementById("detailTitle"),
  detailSubtitle: document.getElementById("detailSubtitle"),
  detailThemeBadge: document.getElementById("detailThemeBadge"),
  detailCoverBadge: document.getElementById("detailCoverBadge"),
  detailDraftBadge: document.getElementById("detailDraftBadge"),
  infoAuthor: document.getElementById("infoAuthor"),
  infoChars: document.getElementById("infoChars"),
  infoPath: document.getElementById("infoPath"),
  infoUpdatedAt: document.getElementById("infoUpdatedAt"),
  sourcePath: document.getElementById("sourcePath"),
  doocsPath: document.getElementById("doocsPath"),
  packPath: document.getElementById("packPath"),
  infoSummary: document.getElementById("infoSummary"),
  sourceWarningPanel: document.getElementById("sourceWarningPanel"),
  sourceWarningList: document.getElementById("sourceWarningList"),
  generatePreviewButton: document.getElementById("generatePreviewButton"),
  themeSelect: document.getElementById("themeSelect"),
  themeHint: document.getElementById("themeHint"),
  primaryColorInput: document.getElementById("primaryColorInput"),
  primaryColorValue: document.getElementById("primaryColorValue"),
  saturationRange: document.getElementById("saturationRange"),
  saturationValue: document.getElementById("saturationValue"),
  opacityRange: document.getElementById("opacityRange"),
  opacityValue: document.getElementById("opacityValue"),
  templateSelect: document.getElementById("templateSelect"),
  templateHint: document.getElementById("templateHint"),
  titleStyleSelect: document.getElementById("titleStyleSelect"),
  bodySizeRange: document.getElementById("bodySizeRange"),
  bodySizeValue: document.getElementById("bodySizeValue"),
  lineHeightRange: document.getElementById("lineHeightRange"),
  lineHeightValue: document.getElementById("lineHeightValue"),
  paragraphGapRange: document.getElementById("paragraphGapRange"),
  paragraphGapValue: document.getElementById("paragraphGapValue"),
  sectionStyleSelect: document.getElementById("sectionStyleSelect"),
  imageRadiusRange: document.getElementById("imageRadiusRange"),
  imageRadiusValue: document.getElementById("imageRadiusValue"),
  imageSpacingRange: document.getElementById("imageSpacingRange"),
  imageSpacingValue: document.getElementById("imageSpacingValue"),
  coverPromptInput: document.getElementById("coverPromptInput"),
  inlinePromptInput: document.getElementById("inlinePromptInput"),
  inlinePositionSlot1: document.getElementById("inlinePositionSlot1"),
  inlinePositionSlot2: document.getElementById("inlinePositionSlot2"),
  generateCoverButton: document.getElementById("generateCoverButton"),
  coverResultCard: document.getElementById("coverResultCard"),
  coverResultMeta: document.getElementById("coverResultMeta"),
  coverResultImage: document.getElementById("coverResultImage"),
  coverResultPrompt: document.getElementById("coverResultPrompt"),
  selectCoverButton: document.getElementById("selectCoverButton"),
  deleteCoverButton: document.getElementById("deleteCoverButton"),
  coverHistoryGallery: document.getElementById("coverHistoryGallery"),
  generateInlineButton: document.getElementById("generateInlineButton"),
  inlineGallery: document.getElementById("inlineGallery"),
  inlineHistoryGallery: document.getElementById("inlineHistoryGallery"),
  coverCandidatePath: document.getElementById("coverCandidatePath"),
  pushDraftButton: document.getElementById("pushDraftButton"),
  draftStatusTitle: document.getElementById("draftStatusTitle"),
  draftStatusText: document.getElementById("draftStatusText"),
  previewModeButton: document.getElementById("previewModeButton"),
  copyHtmlButton: document.getElementById("copyHtmlButton"),
  saveHtmlButton: document.getElementById("saveHtmlButton"),
  previewCharCount: document.getElementById("previewCharCount"),
  previewModeBadge: document.getElementById("previewModeBadge"),
  previewThemeBadge: document.getElementById("previewThemeBadge"),
  previewReferenceBadge: document.getElementById("previewReferenceBadge"),
  previewKicker: document.getElementById("previewKicker"),
  previewTitle: document.getElementById("previewTitle"),
  previewSummary: document.getElementById("previewSummary"),
  previewFrame: document.getElementById("previewFrame"),
  sourceView: document.getElementById("sourceView"),
  workbenchView: document.getElementById("workbenchView"),
  settingsView: document.getElementById("settingsView"),
  wechatMode: document.getElementById("wechatMode"),
  wechatAppid: document.getElementById("wechatAppid"),
  wechatConfigured: document.getElementById("wechatConfigured"),
  imageProvider: document.getElementById("imageProvider"),
  imageModel: document.getElementById("imageModel"),
  imageConfigured: document.getElementById("imageConfigured"),
  settingsWorkspace: document.getElementById("settingsWorkspace"),
  settingsTheme: document.getElementById("settingsTheme"),
  settingsCover: document.getElementById("settingsCover"),
  toast: document.getElementById("toast"),
};

function basename(path) {
  if (!path) return "";
  return String(path).split("/").pop() || path;
}

function formatCount(value) {
  return String(value || 0).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function sanitizeFilename(value) {
  return String(value || "wechat-preview")
    .trim()
    .replace(/[\\/:*?"<>|]+/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .toLowerCase();
}

function assetUrl(item) {
  return item?.localPreviewUrl || item?.previewUrl || item?.draftUrl || "";
}

function normalizeAssetUrl(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  try {
    const url = new URL(raw, window.location.href);
    return `${url.pathname}${url.search}`;
  } catch (_error) {
    return raw;
  }
}

function showToast(message) {
  refs.toast.textContent = message;
  refs.toast.classList.add("visible");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => refs.toast.classList.remove("visible"), 2200);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || payload.message || `请求失败：${response.status}`);
  }
  return payload;
}

function setButtonBusy(button, busy, idleLabel, busyLabel) {
  button.disabled = busy;
  button.textContent = busy ? busyLabel : idleLabel;
}

function renderSelect(select, items, currentValue, placeholder = "暂无可选项") {
  if (!items.length) {
    select.innerHTML = `<option value="">${placeholder}</option>`;
    select.disabled = true;
    return;
  }
  select.disabled = false;
  select.innerHTML = items.map((item) => `<option value="${item.value}">${item.label}</option>`).join("");
  select.value = items.some((item) => item.value === currentValue) ? currentValue : items[0].value;
}

function themeCatalog() {
  const items = Array.isArray(state.settings?.themes) ? state.settings.themes : [];
  return items.map((item) => (typeof item === "string" ? { id: item, label: item, description: "" } : item));
}

function templateCatalog() {
  const items = Array.isArray(state.settings?.templates) ? state.settings.templates : [];
  return items.map((item) => (typeof item === "string" ? { id: item, label: item, description: "" } : item));
}

function titleStyleCatalog() {
  const items = Array.isArray(state.settings?.titleStyles) ? state.settings.titleStyles : [];
  return items.map((item) => (typeof item === "string" ? { id: item, label: item, description: "" } : item));
}

function sectionStyleCatalog() {
  const items = Array.isArray(state.settings?.sectionStyles) ? state.settings.sectionStyles : [];
  return items.map((item) => (typeof item === "string" ? { id: item, label: item, description: "" } : item));
}

function themeMeta(themeId) {
  return themeCatalog().find((item) => item.id === themeId) || null;
}

function templateMeta(templateId) {
  return templateCatalog().find((item) => item.id === templateId) || null;
}

function titleStyleMeta(styleId) {
  return titleStyleCatalog().find((item) => item.id === styleId) || null;
}

function sectionStyleMeta(styleId) {
  return sectionStyleCatalog().find((item) => item.id === styleId) || null;
}

function themeLabel(themeId) {
  return themeMeta(themeId)?.label || themeId || "未设置";
}

function themeDescription(themeId) {
  return themeMeta(themeId)?.description || "";
}

function templateLabel(templateId) {
  return templateMeta(templateId)?.label || templateId || "默认正文";
}

function templateDescription(templateId) {
  return templateMeta(templateId)?.description || "";
}

function updateWorkspaceBadge() {
  if (!refs.workspaceBadge) return;
  const workspace = state.settings?.workspace || "";
  refs.workspaceBadge.textContent = workspace ? basename(workspace) : "当前工作区";
}

function updateRangeReadouts() {
  refs.primaryColorValue.textContent = refs.primaryColorInput.value;
  refs.saturationValue.textContent = `${refs.saturationRange.value}%`;
  refs.opacityValue.textContent = `${refs.opacityRange.value}%`;
  refs.bodySizeValue.textContent = `${refs.bodySizeRange.value}px`;
  refs.lineHeightValue.textContent = Number(refs.lineHeightRange.value).toFixed(2);
  refs.paragraphGapValue.textContent = `${refs.paragraphGapRange.value}px`;
  refs.imageRadiusValue.textContent = `${refs.imageRadiusRange.value}px`;
  refs.imageSpacingValue.textContent = `${refs.imageSpacingRange.value}px`;
}

function syncFormFromDetail() {
  if (!state.detail || !state.settings) return;
  const tone = state.detail.tone || {};
  const typography = state.detail.typography || {};
  const inlineTargetOptions = Array.isArray(state.detail.images?.inlineTargetOptions) ? state.detail.images.inlineTargetOptions : [];
  const inlinePositions = state.detail.images?.inlinePositions || {};
  state.form.tone = {
    theme: tone.theme || state.settings.defaultTheme || "elegant-gold",
    primaryColor: tone.primaryColor || "#b3832f",
    saturation: Number(tone.saturation || 100),
    opacity: Number(tone.opacity || 88),
  };
  state.form.typography = {
    template: typography.template || state.settings.defaultTemplate || "default",
    titleStyle: typography.titleStyle || "standard",
    bodySize: Number(typography.bodySize || 16),
    lineHeight: Number(typography.lineHeight || 1.9),
    paragraphGap: Number(typography.paragraphGap || 16),
    sectionStyle: typography.sectionStyle || "editorial",
    imageRadius: Number(typography.imageRadius || 24),
    imageSpacing: Number(typography.imageSpacing || 22),
  };
  state.form.coverPrompt = state.detail.images?.coverPrompt || "";
  state.form.inlinePrompt = state.detail.images?.inlinePrompt || "";
  state.form.inlinePositions = {
    1: inlinePositions["1"] || inlineTargetOptions[0]?.id || "",
    2: inlinePositions["2"] || inlineTargetOptions[1]?.id || inlineTargetOptions[0]?.id || "",
  };
  state.form.coverCandidatePath = state.detail.images?.coverCandidatePath || "";

  renderSelect(
    refs.themeSelect,
    themeCatalog().map((item) => ({
      value: item.id,
      label: item.description ? `${item.label} · ${item.description}` : item.label,
    })),
    state.form.tone.theme,
    "暂无主题"
  );
  renderSelect(
    refs.templateSelect,
    templateCatalog().map((item) => ({
      value: item.id,
      label: item.description ? `${item.label} · ${item.description}` : item.label,
    })),
    state.form.typography.template,
    "暂无模板"
  );
  renderSelect(
    refs.titleStyleSelect,
    titleStyleCatalog().map((item) => ({ value: item.id, label: item.label })),
    state.form.typography.titleStyle,
    "暂无标题样式"
  );
  renderSelect(
    refs.sectionStyleSelect,
    sectionStyleCatalog().map((item) => ({ value: item.id, label: item.label })),
    state.form.typography.sectionStyle,
    "暂无小节样式"
  );
  renderSelect(
    refs.inlinePositionSlot1,
    inlineTargetOptions.map((item) => ({
      value: item.id,
      label: item.description || item.label || item.id,
    })),
    state.form.inlinePositions[1],
    "暂无可选位置"
  );
  renderSelect(
    refs.inlinePositionSlot2,
    inlineTargetOptions.map((item) => ({
      value: item.id,
      label: item.description || item.label || item.id,
    })),
    state.form.inlinePositions[2],
    "暂无可选位置"
  );

  refs.themeHint.textContent = themeDescription(state.form.tone.theme) || "选择文章的整体气质基底。";
  refs.templateHint.textContent = templateDescription(state.form.typography.template) || "控制标题区、小节结构和图文节奏。";
  refs.primaryColorInput.value = state.form.tone.primaryColor;
  refs.saturationRange.value = String(state.form.tone.saturation);
  refs.opacityRange.value = String(state.form.tone.opacity);
  refs.bodySizeRange.value = String(state.form.typography.bodySize);
  refs.lineHeightRange.value = String(state.form.typography.lineHeight);
  refs.paragraphGapRange.value = String(state.form.typography.paragraphGap);
  refs.imageRadiusRange.value = String(state.form.typography.imageRadius);
  refs.imageSpacingRange.value = String(state.form.typography.imageSpacing);
  refs.coverPromptInput.value = state.form.coverPrompt;
  refs.inlinePromptInput.value = state.form.inlinePrompt;
  refs.coverCandidatePath.value = state.form.coverCandidatePath;
  updateRangeReadouts();
}

function renderArticleList() {
  const articles = state.articles || [];
  refs.articleCount.textContent = `${articles.length} 篇`;
  refs.articleSwitcherWrap.classList.toggle("hidden", articles.length === 0);
  if (!articles.length) {
    refs.articleSwitcher.innerHTML = '<option value="">当前工作区暂无文章</option>';
    refs.articleSwitcher.disabled = true;
    return;
  }
  refs.articleSwitcher.innerHTML = articles
    .map((article, index) => `<option value="${article.id}">${articles.length > 1 ? `${index + 1}. ` : ""}${article.title}</option>`)
    .join("");
  refs.articleSwitcher.value = articles.some((article) => article.id === state.selectedId) ? state.selectedId : articles[0].id;
  refs.articleSwitcher.disabled = articles.length <= 1;
}

function renderArticleInfo(detail) {
  refs.detailTitle.textContent = detail.article.title;
  refs.detailSubtitle.textContent = detail.article.summary || "暂无摘要";
  refs.infoAuthor.textContent = detail.article.author || "未填写";
  refs.infoChars.textContent = `${formatCount(detail.article.charCount)} 字`;
  refs.infoPath.textContent = detail.article.path;
  refs.infoUpdatedAt.textContent = detail.article.updatedAt || "-";
  refs.sourcePath.textContent = detail.article.sourceFiles.source?.path || "-";
  refs.doocsPath.textContent = detail.article.sourceFiles.doocs.path;
  refs.packPath.textContent = detail.article.sourceFiles.publishPack.path;
  refs.infoSummary.textContent = detail.article.summary || "暂无摘要";
}

function renderWarnings(detail) {
  const warnings = Array.isArray(detail.source?.warnings) ? detail.source.warnings : [];
  refs.sourceWarningPanel.classList.toggle("hidden", warnings.length === 0);
  refs.sourceWarningList.innerHTML = "";
  warnings.forEach((warning) => {
    const item = document.createElement("div");
    item.className = "warning-item";
    item.textContent = warning;
    refs.sourceWarningList.appendChild(item);
  });
}

function renderVisualStatus(detail) {
  const tone = detail.tone || {};
  const typography = detail.typography || {};
  const previewReady = Boolean(detail.preview?.ready);
  refs.detailThemeBadge.textContent = `${themeLabel(tone.theme)} / ${templateLabel(typography.template)}`;
  refs.previewThemeBadge.textContent = previewReady
    ? `${themeLabel(detail.preview?.themeName || tone.theme)} / ${templateLabel(detail.preview?.template || typography.template)}`
    : "预览待生成";
  refs.previewReferenceBadge.textContent = `${tone.primaryColor || "#b3832f"} · ${tone.saturation || 100}% / ${tone.opacity || 88}%`;
  refs.previewReferenceBadge.classList.remove("muted");
}

function renderPathDisclosure(path) {
  const value = path || "未保存";
  return `
    <details class="path-disclosure">
      <summary>本地路径</summary>
      <code>${value}</code>
    </details>
  `;
}

function renderCover(detail) {
  const generated = detail.images?.coverGenerated;
  const history = detail.images?.coverHistory || [];
  const candidatePath = detail.images?.coverCandidatePath || "";
  refs.detailCoverBadge.textContent = candidatePath ? `封面 · ${basename(candidatePath)}` : "未选封面";
  refs.detailCoverBadge.classList.toggle("muted", !candidatePath);
  refs.coverCandidatePath.value = candidatePath;
  state.form.coverCandidatePath = candidatePath;

  if (!assetUrl(generated)) {
    refs.coverResultCard.classList.add("hidden");
    refs.selectCoverButton.dataset.coverPath = "";
    refs.deleteCoverButton.dataset.deleteCoverPath = "";
    refs.deleteCoverButton.disabled = true;
  } else {
    refs.coverResultCard.classList.remove("hidden");
    refs.coverResultImage.src = assetUrl(generated);
    refs.coverResultMeta.textContent = `${generated.styleLabel || generated.preset || "cover"} · ${generated.width || "?"}x${generated.height || "?"}`;
    refs.coverResultPrompt.textContent = generated.prompt
      ? `提示词：${generated.prompt}\n素材路径：${generated.localPath || "未保存"}`
      : `素材路径：${generated.localPath || "未保存"}`;
    refs.selectCoverButton.dataset.coverPath = generated.localPath || "";
    refs.deleteCoverButton.dataset.deleteCoverPath = generated.localPath || "";
    refs.deleteCoverButton.disabled = !generated.localPath;
  }

  refs.coverHistoryGallery.innerHTML = "";
  const historyItems = history.filter((item) => item?.localPath);
  if (!historyItems.length) {
    refs.coverHistoryGallery.innerHTML = '<div class="history-empty">还没有封面候选。导入后或点击“重新生成封面候选”会自动生成 4 张核心封面。</div>';
    return;
  }
  historyItems.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "history-card";
    const isCurrent = item.localPath === candidatePath;
    card.innerHTML = `
      <div class="history-card-head">
        <div>
          <strong>${item.styleLabel || `封面候选 ${index + 1}`}</strong>
          <span>${item.createdAt || "未知时间"}</span>
        </div>
        <span class="list-chip ${isCurrent ? "success" : ""}">${isCurrent ? "当前封面" : (item.preset || "cover")}</span>
      </div>
      ${assetUrl(item) ? `<img src="${assetUrl(item)}" alt="${item.styleLabel || "封面候选"}" />` : ""}
      ${renderPathDisclosure(item.localPath)}
      <div class="history-actions">
        <button class="secondary-btn small" type="button" data-cover-path="${item.localPath || ""}" ${isCurrent ? "disabled" : ""}>${isCurrent ? "当前已使用" : "设为当前封面"}</button>
        <button class="secondary-btn danger small image-delete-btn" type="button" data-delete-cover-path="${item.localPath || ""}">删除</button>
      </div>
    `;
    refs.coverHistoryGallery.appendChild(card);
  });
}

function renderInlineImages(detail) {
  const items = detail.images?.inlineItems || [];
  const history = detail.images?.inlineHistory || [];
  refs.inlineGallery.innerHTML = "";
  if (!items.length) {
    refs.inlineGallery.innerHTML = '<div class="inline-empty">还没有正文配图。导入后会自动生成 2 张，或点击“重新生成正文配图”重新生成。</div>';
  } else {
    items.forEach((item) => {
      const card = document.createElement("article");
      card.className = "inline-card";
      card.dataset.inlineCardSlot = String(item.slot || "");
      card.innerHTML = `
        <div class="inline-card-head">
          <div>
            <strong>插图 ${item.slot}</strong>
            <span>${item.label}</span>
          </div>
          <button class="secondary-btn small" type="button" data-inline-regenerate="${item.slot}">重生成此位置</button>
        </div>
        <img src="${assetUrl(item)}" alt="${item.label}" />
        <p>${item.targetLabel ? `插入位置：${item.targetLabel}\n` : ""}${item.prompt ? `提示词：${item.prompt}` : "图片已生成。"}</p>
        ${renderPathDisclosure(item.localPath)}
        <div class="history-actions">
          <button class="secondary-btn danger small image-delete-btn" type="button" data-delete-inline-path="${item.localPath || ""}">删除</button>
        </div>
      `;
      refs.inlineGallery.appendChild(card);
    });
  }

  refs.inlineHistoryGallery.innerHTML = "";
  const currentPaths = new Set(items.map((item) => item.localPath).filter(Boolean));
  const historyItems = history.filter((item) => item?.localPath);
  if (!historyItems.length) {
    refs.inlineHistoryGallery.innerHTML = '<div class="history-empty">历史正文配图会保存在本地，后续可回切到当前插图位置。</div>';
    return;
  }
  historyItems.forEach((item, index) => {
    const isCurrent = currentPaths.has(item.localPath);
    const card = document.createElement("article");
    card.className = "history-card";
    card.innerHTML = `
      <div class="history-card-head">
        <div>
          <strong>插图 ${item.slot || "?"} · 历史 ${index + 1}</strong>
          <span>${item.label || "正文插图"}</span>
        </div>
        <span class="list-chip ${isCurrent ? "success" : ""}">${isCurrent ? "当前在文中" : (item.createdAt || "未知时间")}</span>
      </div>
      ${assetUrl(item) ? `<img src="${assetUrl(item)}" alt="${item.label || "历史插图"}" />` : ""}
      ${renderPathDisclosure(item.localPath)}
      <div class="history-actions">
        <button class="secondary-btn small" type="button" data-inline-slot="${item.slot || ""}" data-inline-path="${item.localPath || ""}" ${isCurrent ? "disabled" : ""}>${isCurrent ? "当前已使用" : "切换到此插图"}</button>
        <button class="secondary-btn danger small image-delete-btn" type="button" data-delete-inline-path="${item.localPath || ""}">删除</button>
      </div>
    `;
    refs.inlineHistoryGallery.appendChild(card);
  });
}

function renderDraft(detail) {
  const draft = detail.draft || {};
  const hasDraft = Boolean(draft.mediaId);
  refs.detailDraftBadge.textContent = hasDraft ? `草稿 · ${draft.mediaId.slice(0, 8)}...` : "未推草稿";
  refs.detailDraftBadge.classList.toggle("muted", !hasDraft);
  refs.draftStatusTitle.textContent = hasDraft ? "已推送到草稿箱" : "尚未推送";
  refs.draftStatusText.textContent = hasDraft
    ? `最近一次推送时间：${draft.pushedAt || "未知"}。media_id：${draft.mediaId}`
    : draft.lastError || "确认预览、封面和正文配图后，再推送到微信草稿箱。";
}

function previewPlaceholderHtml(title, message) {
  const safeTitle = String(title || "等待预览")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  const safeMessage = String(message || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <style>
      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 40px 24px;
        background: linear-gradient(180deg, #fffdfa 0%, #f7efe5 100%);
        color: #4c4035;
        font: 16px/1.7 "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      }
      .empty {
        width: min(560px, 100%);
        padding: 28px;
        border: 1px solid rgba(235, 224, 208, 0.9);
        border-radius: 28px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow: 0 18px 44px rgba(110, 77, 36, 0.10);
      }
      h1 {
        margin: 0 0 12px;
        font-size: 28px;
      }
      p {
        margin: 0;
      }
    </style>
  </head>
  <body>
    <section class="empty">
      <h1>${safeTitle}</h1>
      <p>${safeMessage}</p>
    </section>
  </body>
</html>`;
}

function renderPreview(detail) {
  const preview = detail.preview || {};
  const ready = Boolean(preview.ready);
  const title = preview.title || detail.article.title;
  const summary = ready
    ? (preview.summary || detail.article.summary || "暂无摘要")
    : (preview.statusText || "先调整风格和配色，再手动生成预览。");
  refs.previewTitle.textContent = title;
  refs.previewSummary.textContent = summary;
  refs.previewCharCount.textContent = formatCount(preview.charCount || detail.article.charCount || 0);
  refs.previewKicker.textContent = ready ? "微信发布预览" : "预览待生成";
  refs.previewModeBadge.textContent = ready ? "推草稿同源" : "等待手动刷新";
  refs.previewFrame.srcdoc = ready
    ? (preview.standaloneHtml || "")
    : previewPlaceholderHtml(title, summary);
  refs.sourceView.textContent = ready ? (preview.sourceHtml || "") : summary;
  refs.previewModeButton.disabled = !ready;
  refs.copyHtmlButton.disabled = !ready;
  refs.saveHtmlButton.disabled = !ready;
  state.lastSavedName = `${sanitizeFilename(title)}.html`;
  if (!ready && state.previewMode === "source") {
    state.previewMode = "preview";
  }
  renderPreviewMode();
}

function renderPreviewMode() {
  const isSource = state.previewMode === "source";
  refs.previewModeButton.textContent = isSource ? "预览" : "源码";
  refs.previewFrame.classList.toggle("hidden", isSource);
  refs.sourceView.classList.toggle("hidden", !isSource);
}

function resizePreviewFrame() {
  setTimeout(() => {
    try {
      const doc = refs.previewFrame.contentDocument;
      if (!doc) return;
      const height = Math.max(doc.body?.scrollHeight || 0, doc.documentElement?.scrollHeight || 0, 1100);
      refs.previewFrame.style.height = `${Math.min(height + 24, 24000)}px`;
      enhancePreviewInlineEditors(doc);
    } catch (_error) {
      refs.previewFrame.style.height = "1800px";
    }
  }, 80);
}

function focusInlineEditor(slot) {
  const card = refs.inlineGallery.querySelector(`[data-inline-card-slot="${slot}"]`);
  if (!card) {
    showToast(`没找到插图 ${slot} 的编辑卡片`);
    return;
  }
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  card.classList.remove("is-focused");
  void card.offsetWidth;
  card.classList.add("is-focused");
  clearTimeout(card.highlightTimer);
  card.highlightTimer = setTimeout(() => card.classList.remove("is-focused"), 2200);
  const actionButton =
    card.querySelector(`[data-inline-regenerate="${slot}"]`) ||
    card.querySelector("[data-delete-inline-path]") ||
    card.querySelector("button");
  if (actionButton) {
    actionButton.focus({ preventScroll: true });
  }
}

function injectPreviewInlineEditorStyles(doc) {
  if (!doc.head || doc.getElementById("previewInlineEditorStyles")) return;
  const style = doc.createElement("style");
  style.id = "previewInlineEditorStyles";
  style.textContent = `
    .preview-inline-edit-host {
      position: relative !important;
    }
    .preview-inline-edit-btn {
      position: absolute;
      top: 12px;
      right: 12px;
      z-index: 30;
      border: 0;
      border-radius: 999px;
      padding: 9px 12px;
      background: rgba(255, 255, 255, 0.96);
      color: #cb5e1d;
      font: 600 13px/1.1 "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      box-shadow: 0 12px 28px rgba(52, 40, 30, 0.16);
      cursor: pointer;
    }
    .preview-inline-edit-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 16px 32px rgba(52, 40, 30, 0.2);
    }
    .preview-inline-edit-btn:focus-visible {
      outline: 2px solid #ef7a34;
      outline-offset: 2px;
    }
    [data-inline-slot] img[data-inline-editable="true"] {
      cursor: pointer;
    }
  `;
  doc.head.appendChild(style);
}

function attachPreviewInlineEditControl(doc, figure, img, slot) {
  if (!figure || !img || !slot) return;
  figure.dataset.inlineSlot = String(slot);
  const host = img.parentElement && img.parentElement !== figure ? img.parentElement : figure;
  if (!host) return;
  host.classList.add("preview-inline-edit-host");
  if (!host.querySelector(`.preview-inline-edit-btn[data-inline-slot="${slot}"]`)) {
    const button = doc.createElement("button");
    button.type = "button";
    button.className = "preview-inline-edit-btn";
    button.dataset.inlineSlot = String(slot);
    button.textContent = `编辑插图 ${slot}`;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      focusInlineEditor(slot);
    });
    host.appendChild(button);
  }
  if (img.dataset.inlineEditBound !== "true") {
    img.dataset.inlineEditable = "true";
    img.dataset.inlineEditBound = "true";
    img.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      focusInlineEditor(slot);
    });
  }
}

function hideDuplicatePreviewImage(primaryImg, duplicateImg) {
  if (!primaryImg || !duplicateImg || primaryImg === duplicateImg) return;
  const duplicateCell = duplicateImg.closest("td");
  if (duplicateCell) {
    duplicateCell.style.display = "none";
  } else {
    const duplicateWrapper = duplicateImg.parentElement;
    if (duplicateWrapper && duplicateWrapper !== duplicateImg.closest("figure")) {
      duplicateWrapper.style.display = "none";
    } else {
      duplicateImg.style.display = "none";
    }
  }
  const primaryCell = primaryImg.closest("td");
  if (primaryCell) {
    primaryCell.style.width = "100%";
    primaryCell.style.padding = "0";
  }
  const table = primaryImg.closest("table");
  if (table) {
    table.style.width = "100%";
  }
}

function enhancePreviewInlineEditors(doc) {
  if (!doc || !state.detail) return;
  const inlineItems = Array.isArray(state.detail.images?.inlineItems) ? state.detail.images.inlineItems : [];
  if (!inlineItems.length) return;
  injectPreviewInlineEditorStyles(doc);

  const assetMap = new Map();
  inlineItems.forEach((item) => {
    const normalized = normalizeAssetUrl(assetUrl(item));
    const slot = Number(item.slot || 0);
    if (normalized && slot) {
      assetMap.set(normalized, slot);
    }
  });
  if (!assetMap.size) return;

  const groups = new Map();
  Array.from(doc.querySelectorAll("img")).forEach((img) => {
    const normalized = normalizeAssetUrl(img.getAttribute("src") || img.src);
    const slot = assetMap.get(normalized);
    if (!slot) return;
    const figure = img.closest("figure") || img.closest("table") || img.parentElement;
    if (!figure) return;
    let figureGroup = groups.get(figure);
    if (!figureGroup) {
      figureGroup = new Map();
      groups.set(figure, figureGroup);
    }
    const slotImages = figureGroup.get(slot) || [];
    slotImages.push(img);
    figureGroup.set(slot, slotImages);
  });

  groups.forEach((figureGroup, figure) => {
    figureGroup.forEach((images, slot) => {
      const [primaryImg, ...duplicates] = images;
      duplicates.forEach((duplicateImg) => hideDuplicatePreviewImage(primaryImg, duplicateImg));
      attachPreviewInlineEditControl(doc, figure, primaryImg, slot);
    });
  });
}

function renderDetail() {
  const hasDetail = Boolean(state.detail);
  refs.detailEmptyState.classList.toggle("hidden", hasDetail);
  refs.detailWrap.classList.toggle("hidden", !hasDetail);
  if (!hasDetail) return;
  syncFormFromDetail();
  renderArticleInfo(state.detail);
  renderWarnings(state.detail);
  renderVisualStatus(state.detail);
  renderCover(state.detail);
  renderInlineImages(state.detail);
  renderDraft(state.detail);
  renderPreview(state.detail);
}

function renderSettings() {
  if (!state.settings) return;
  refs.wechatMode.textContent = state.settings.wechat.mode || "-";
  refs.wechatAppid.textContent = state.settings.wechat.appid || "-";
  refs.wechatConfigured.textContent = state.settings.wechat.configured ? "已配置" : "未配置";
  refs.imageProvider.textContent = state.settings.image.provider || "-";
  refs.imageModel.textContent = state.settings.image.model || "-";
  refs.imageConfigured.textContent = state.settings.image.configured ? "已配置" : "未配置";
  refs.settingsWorkspace.textContent = state.settings.workspace || "-";
  refs.settingsTheme.textContent = themeLabel(state.settings.defaultTheme || "-");
  refs.settingsCover.textContent = state.settings.defaultCover || "未设置";
}

function renderActiveView() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === state.activeView);
  });
  refs.workbenchView.classList.toggle("hidden", state.activeView !== "workbench");
  refs.workbenchView.classList.toggle("is-active", state.activeView === "workbench");
  refs.settingsView.classList.toggle("hidden", state.activeView !== "settings");
  refs.settingsView.classList.toggle("is-active", state.activeView === "settings");
}

function currentActionPayload() {
  return {
    tone: {
      theme: refs.themeSelect.value || state.form.tone.theme,
      primaryColor: refs.primaryColorInput.value || state.form.tone.primaryColor,
      saturation: Number(refs.saturationRange.value || state.form.tone.saturation),
      opacity: Number(refs.opacityRange.value || state.form.tone.opacity),
    },
    typography: {
      template: refs.templateSelect.value || state.form.typography.template,
      titleStyle: refs.titleStyleSelect.value || state.form.typography.titleStyle,
      bodySize: Number(refs.bodySizeRange.value || state.form.typography.bodySize),
      lineHeight: Number(refs.lineHeightRange.value || state.form.typography.lineHeight),
      paragraphGap: Number(refs.paragraphGapRange.value || state.form.typography.paragraphGap),
      sectionStyle: refs.sectionStyleSelect.value || state.form.typography.sectionStyle,
      imageRadius: Number(refs.imageRadiusRange.value || state.form.typography.imageRadius),
      imageSpacing: Number(refs.imageSpacingRange.value || state.form.typography.imageSpacing),
    },
    inlinePositions: {
      1: refs.inlinePositionSlot1.value || state.form.inlinePositions[1],
      2: refs.inlinePositionSlot2.value || state.form.inlinePositions[2],
    },
  };
}

function schedulePreviewRefresh() {
  updateRangeReadouts();
  refs.themeHint.textContent = themeDescription(refs.themeSelect.value) || "选择文章的整体气质基底。";
  refs.templateHint.textContent = templateDescription(refs.templateSelect.value) || "控制标题区、小节结构和图文节奏。";
  if (!state.selectedId) return;
  clearTimeout(state.autoPreviewTimer);
  state.autoPreviewTimer = setTimeout(() => {
    handlePreview({ silent: true }).catch((error) => showToast(error.message || "预览刷新失败"));
  }, 420);
}

async function loadSettings() {
  state.settings = await requestJson("/api/settings/status");
  updateWorkspaceBadge();
  renderSettings();
}

async function loadArticles() {
  const payload = await requestJson("/api/articles");
  state.articles = payload.articles || [];
  if (state.selectedId && state.articles.some((item) => item.id === state.selectedId)) {
    renderArticleList();
    return;
  }
  state.selectedId = state.articles[0]?.id || "";
  renderArticleList();
}

async function loadArticleDetail(articleId) {
  if (!articleId) {
    state.detail = null;
    renderDetail();
    return;
  }
  state.selectedId = articleId;
  renderArticleList();
  const payload = await requestJson(`/api/articles/${encodeURIComponent(articleId)}`);
  state.detail = payload.detail;
  renderDetail();
}

async function handlePreview({ silent = false } = {}) {
  if (!state.selectedId) {
    if (!silent) showToast("先导入或选择一篇文章");
    return;
  }
  setButtonBusy(refs.generatePreviewButton, true, "立即刷新预览", "刷新中...");
  try {
    const result = await requestJson(`/api/articles/${encodeURIComponent(state.selectedId)}/layout/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentActionPayload()),
    });
    state.detail = result.detail;
    renderDetail();
    if (!silent) showToast(result.message || "预览已刷新");
  } finally {
    setButtonBusy(refs.generatePreviewButton, false, "立即刷新预览", "刷新中...");
  }
}

async function handleUpload(file) {
  if (!file) return;
  if (!/\.md$/i.test(file.name)) {
    showToast("只支持导入 .md 文件");
    return;
  }
  const formData = new FormData();
  formData.append("file", file, file.name);
  refs.uploadDropzone.classList.add("is-busy");
  setButtonBusy(refs.importButton, true, "选择 Markdown", "导入中...");
  try {
    const result = await requestJson("/api/articles/import", {
      method: "POST",
      body: formData,
    });
    await loadArticles();
    state.selectedId = result.detail.article.id;
    state.detail = result.detail;
    renderArticleList();
    renderDetail();
    const warningCount = Array.isArray(result.detail.source?.warnings) ? result.detail.source.warnings.length : 0;
    showToast(warningCount ? `导入完成，先调风格再生成内容（${warningCount} 条提醒）` : "Markdown 导入完成，先调风格再生成内容");
  } finally {
    refs.uploadDropzone.classList.remove("is-busy");
    refs.markdownFileInput.value = "";
    setButtonBusy(refs.importButton, false, "选择 Markdown", "导入中...");
  }
}

async function handleGenerateCover() {
  if (!state.selectedId) return;
  setButtonBusy(refs.generateCoverButton, true, "重新生成封面候选", "生成中...");
  try {
    const result = await requestJson(`/api/articles/${encodeURIComponent(state.selectedId)}/images/cover`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...currentActionPayload(),
        prompt: refs.coverPromptInput.value.trim(),
      }),
    });
    state.detail = result.detail;
    renderDetail();
    showToast(result.message || "封面候选已生成");
  } finally {
    setButtonBusy(refs.generateCoverButton, false, "重新生成封面候选", "生成中...");
  }
}

async function handleSelectCover(localPath) {
  if (!state.selectedId || !localPath) return;
  const result = await requestJson(`/api/articles/${encodeURIComponent(state.selectedId)}/images/cover/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: localPath }),
  });
  state.detail = result.detail;
  renderDetail();
  showToast(result.message || "当前封面已更新");
}

async function handleDeleteCover(localPath) {
  if (!state.selectedId || !localPath) return;
  if (!window.confirm("删除后会移除本地封面文件和当前记录，是否继续？")) return;
  const result = await requestJson(`/api/articles/${encodeURIComponent(state.selectedId)}/images/cover/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: localPath }),
  });
  state.detail = result.detail;
  renderDetail();
  showToast(result.message || "封面图片已删除");
}

async function handleGenerateInline(slot = 0) {
  if (!state.selectedId) return;
  const idleLabel = slot ? `重生成插图 ${slot}` : "重新生成正文配图";
  setButtonBusy(refs.generateInlineButton, true, "重新生成正文配图", "生成中...");
  try {
    const result = await requestJson(`/api/articles/${encodeURIComponent(state.selectedId)}/images/inline`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...currentActionPayload(),
        prompt: refs.inlinePromptInput.value.trim(),
        slot,
      }),
    });
    state.detail = result.detail;
    renderDetail();
    showToast(slot ? `${idleLabel} 已完成` : (result.message || "正文配图已生成"));
  } finally {
    setButtonBusy(refs.generateInlineButton, false, "重新生成正文配图", "生成中...");
  }
}

async function handleSelectInline(slot, localPath) {
  if (!state.selectedId || !slot || !localPath) return;
  const result = await requestJson(`/api/articles/${encodeURIComponent(state.selectedId)}/images/inline/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slot, path: localPath }),
  });
  state.detail = result.detail;
  renderDetail();
  showToast(result.message || "正文插图已切换");
}

async function handleDeleteInline(localPath) {
  if (!state.selectedId || !localPath) return;
  if (!window.confirm("删除后会移除本地正文配图文件和当前记录，是否继续？")) return;
  const result = await requestJson(`/api/articles/${encodeURIComponent(state.selectedId)}/images/inline/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: localPath }),
  });
  state.detail = result.detail;
  renderDetail();
  showToast(result.message || "正文配图已删除");
}

async function handlePushDraft() {
  if (!state.selectedId) return;
  setButtonBusy(refs.pushDraftButton, true, "推送到草稿箱", "推送中...");
  try {
    const result = await requestJson(`/api/articles/${encodeURIComponent(state.selectedId)}/draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...currentActionPayload(),
        coverPath: refs.coverCandidatePath.value.trim(),
      }),
    });
    state.detail = result.detail;
    renderDetail();
    showToast(result.message || "已推送到草稿箱");
  } finally {
    setButtonBusy(refs.pushDraftButton, false, "推送到草稿箱", "推送中...");
  }
}

async function copyHtml() {
  const html = state.detail?.preview?.sourceHtml || "";
  if (!html) {
    showToast("先生成预览再复制");
    return;
  }
  try {
    await navigator.clipboard.writeText(html);
    showToast("HTML 已复制");
  } catch (_error) {
    showToast("复制失败，请稍后重试");
  }
}

function saveHtml() {
  const html = state.detail?.preview?.sourceHtml || "";
  if (!html) {
    showToast("先生成预览再保存");
    return;
  }
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = state.lastSavedName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
  showToast("HTML 已保存到本地下载");
}

function bindUploadEvents() {
  refs.importButton.addEventListener("click", () => refs.markdownFileInput.click());
  refs.markdownFileInput.addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    handleUpload(file).catch((error) => showToast(error.message || "导入失败"));
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    refs.uploadDropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      refs.uploadDropzone.classList.add("is-dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    refs.uploadDropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      refs.uploadDropzone.classList.remove("is-dragover");
    });
  });

  refs.uploadDropzone.addEventListener("drop", (event) => {
    const file = event.dataTransfer?.files?.[0];
    handleUpload(file).catch((error) => showToast(error.message || "导入失败"));
  });

  refs.uploadDropzone.addEventListener("click", () => refs.markdownFileInput.click());
  refs.uploadDropzone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      refs.markdownFileInput.click();
    }
  });
}

function bindEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeView = button.dataset.view;
      renderActiveView();
    });
  });

  bindUploadEvents();

  refs.articleSwitcher.addEventListener("change", (event) => {
    const articleId = event.target.value;
    if (!articleId || articleId === state.selectedId) return;
    loadArticleDetail(articleId).catch((error) => showToast(error.message || "加载文章失败"));
  });

  [
    refs.themeSelect,
    refs.primaryColorInput,
    refs.saturationRange,
    refs.opacityRange,
    refs.templateSelect,
    refs.titleStyleSelect,
    refs.bodySizeRange,
    refs.lineHeightRange,
    refs.paragraphGapRange,
    refs.sectionStyleSelect,
    refs.imageRadiusRange,
    refs.imageSpacingRange,
    refs.inlinePositionSlot1,
    refs.inlinePositionSlot2,
  ].forEach((input) => {
    input.addEventListener("input", schedulePreviewRefresh);
    input.addEventListener("change", schedulePreviewRefresh);
  });

  refs.generatePreviewButton.addEventListener("click", () => {
    handlePreview().catch((error) => showToast(error.message || "预览刷新失败"));
  });
  refs.generateCoverButton.addEventListener("click", () => {
    handleGenerateCover().catch((error) => showToast(error.message || "封面生成失败"));
  });
  refs.selectCoverButton.addEventListener("click", () => {
    const localPath = refs.selectCoverButton.dataset.coverPath || state.detail?.images?.coverGenerated?.localPath;
    handleSelectCover(localPath).catch((error) => showToast(error.message || "封面切换失败"));
  });
  refs.deleteCoverButton.addEventListener("click", () => {
    const localPath = refs.deleteCoverButton.dataset.deleteCoverPath || state.detail?.images?.coverGenerated?.localPath;
    handleDeleteCover(localPath).catch((error) => showToast(error.message || "封面删除失败"));
  });
  refs.generateInlineButton.addEventListener("click", () => {
    handleGenerateInline().catch((error) => showToast(error.message || "正文配图生成失败"));
  });
  refs.pushDraftButton.addEventListener("click", () => {
    handlePushDraft().catch((error) => showToast(error.message || "草稿推送失败"));
  });

  refs.coverHistoryGallery.addEventListener("click", (event) => {
    const deleteButton = event.target.closest("[data-delete-cover-path]");
    if (deleteButton) {
      handleDeleteCover(deleteButton.dataset.deleteCoverPath).catch((error) => showToast(error.message || "封面删除失败"));
      return;
    }
    const button = event.target.closest("[data-cover-path]");
    if (!button) return;
    handleSelectCover(button.dataset.coverPath).catch((error) => showToast(error.message || "封面切换失败"));
  });

  refs.inlineGallery.addEventListener("click", (event) => {
    const deleteButton = event.target.closest("[data-delete-inline-path]");
    if (deleteButton) {
      handleDeleteInline(deleteButton.dataset.deleteInlinePath).catch((error) => showToast(error.message || "正文配图删除失败"));
      return;
    }
    const button = event.target.closest("[data-inline-regenerate]");
    if (!button) return;
    const slot = Number(button.dataset.inlineRegenerate || "0");
    if (!slot) return;
    handleGenerateInline(slot).catch((error) => showToast(error.message || "插图重生成失败"));
  });

  refs.inlineHistoryGallery.addEventListener("click", (event) => {
    const deleteButton = event.target.closest("[data-delete-inline-path]");
    if (deleteButton) {
      handleDeleteInline(deleteButton.dataset.deleteInlinePath).catch((error) => showToast(error.message || "正文配图删除失败"));
      return;
    }
    const button = event.target.closest("[data-inline-slot]");
    if (!button) return;
    const slot = Number(button.dataset.inlineSlot || "0");
    const localPath = button.dataset.inlinePath || "";
    if (!slot || !localPath) return;
    handleSelectInline(slot, localPath).catch((error) => showToast(error.message || "插图切换失败"));
  });

  refs.previewModeButton.addEventListener("click", () => {
    state.previewMode = state.previewMode === "preview" ? "source" : "preview";
    renderPreviewMode();
  });
  refs.copyHtmlButton.addEventListener("click", () => copyHtml());
  refs.saveHtmlButton.addEventListener("click", saveHtml);
  refs.previewFrame.addEventListener("load", resizePreviewFrame);
}

async function init() {
  bindEvents();
  renderActiveView();
  try {
    await loadSettings();
    await loadArticles();
    if (state.selectedId) {
      await loadArticleDetail(state.selectedId);
    } else {
      renderDetail();
    }
  } catch (error) {
    showToast(error.message || "初始化失败");
  }
}

init();
