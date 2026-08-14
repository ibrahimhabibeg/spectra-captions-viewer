import streamlit as st

HTML_CONTENT = """
<div id="annotator-root" class="annotator-container">
  <div id="caption-content" class="caption-text"></div>
  
  <div id="popover-toolbar" class="popover-box" style="display: none;">
    <div class="popover-header">
      <span id="popover-modal-title" class="popover-title">Add span feedback</span>
      <button id="popover-close-btn" class="popover-close" type="button" title="Close">✕</button>
    </div>
    <div class="popover-quote" id="popover-selected-quote"></div>
    
    <div class="popover-field-label">Issue tag (optional):</div>
    <div class="popover-tags-grid">
      <button class="tag-chip" type="button" data-tag="Hallucinated feature">Hallucinated</button>
      <button class="tag-chip" type="button" data-tag="Incorrect redshift (z)">Redshift</button>
      <button class="tag-chip" type="button" data-tag="Physical conflict">Conflict</button>
      <button class="tag-chip" type="button" data-tag="Literature conflict">Literature</button>
      <button class="tag-chip" type="button" data-tag="Vague / Missing detail">Vague</button>
      <button class="tag-chip" type="button" data-tag="Other">Other</button>
    </div>
    
    <div class="popover-field-label">Comment:</div>
    <textarea id="popover-comment-input" class="popover-textarea" rows="2" placeholder="e.g. Line absent in optical & NIR spectra..."></textarea>
    
    <div class="popover-actions">
      <button id="popover-delete-btn" class="btn-danger" type="button" style="display: none;">Delete</button>
      <button id="popover-cancel-btn" class="btn-secondary" type="button">Cancel</button>
      <button id="popover-save-btn" class="btn-primary" type="button">Add annotation</button>
    </div>
  </div>
</div>
"""

CSS_CONTENT = """
.annotator-container {
  position: relative;
  font-family: var(--st-font-sans, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
  line-height: 1.7;
  font-size: 0.98rem;
  color: var(--st-text-color, #1E293B);
  user-select: text;
  -webkit-user-select: text;
  padding: 4px 0 16px 0;
}

.caption-text {
  word-break: break-word;
  white-space: pre-wrap;
  cursor: text;
}

.caption-text .katex {
  font-size: 1.05em;
}

.caption-text mark.span-highlight {
  background-color: rgba(245, 158, 11, 0.28);
  color: inherit;
  border-bottom: 2px solid #D97706;
  border-radius: 3px;
  padding: 1px 3px;
  cursor: pointer;
  position: relative;
  transition: background-color 0.15s ease;
}

.caption-text mark.span-highlight:hover {
  background-color: rgba(245, 158, 11, 0.45);
}

.caption-text mark.span-highlight .span-tag-badge {
  font-size: 0.72em;
  font-weight: 700;
  background-color: #D97706;
  color: #FFFFFF;
  padding: 1px 5px;
  border-radius: 3px;
  margin-left: 4px;
  vertical-align: middle;
  display: inline-flex;
  align-items: center;
}

.caption-text mark.span-highlight .span-tag-badge.span-tag-plain {
  background-color: rgba(100, 116, 139, 0.65);
  padding: 1px 4px;
}

.caption-text mark.span-highlight .span-remove-btn {
  margin-left: 4px;
  cursor: pointer;
  font-weight: bold;
  opacity: 0.8;
}
.caption-text mark.span-highlight .span-remove-btn:hover {
  opacity: 1;
}

.popover-box {
  position: absolute;
  z-index: 99999;
  width: 320px;
  background-color: var(--st-secondary-background-color, #1E293B);
  color: var(--st-text-color, #F8FAFC);
  border: 1px solid var(--st-border-color, #475569);
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35), 0 4px 10px rgba(0, 0, 0, 0.2);
}

.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.popover-title {
  font-weight: 600;
  font-size: 0.85rem;
}

.popover-close {
  background: none;
  border: none;
  font-size: 0.9rem;
  cursor: pointer;
  color: inherit;
  opacity: 0.6;
}
.popover-close:hover {
  opacity: 1;
}

.popover-quote {
  font-style: italic;
  font-size: 0.82rem;
  background: rgba(125, 125, 125, 0.15);
  border-left: 3px solid #3B82F6;
  padding: 5px 8px;
  border-radius: 0 4px 4px 0;
  margin-bottom: 10px;
  max-height: 60px;
  overflow-y: auto;
  word-break: break-word;
  white-space: normal;
}

.popover-field-label {
  font-size: 0.74rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.75;
  margin-bottom: 4px;
}

.popover-tags-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
  margin-bottom: 10px;
}

.tag-chip {
  font-size: 0.72rem;
  padding: 4px 6px;
  border-radius: 5px;
  border: 1px solid var(--st-border-color, #475569);
  background: var(--st-background-color, #0F172A);
  color: inherit;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s ease;
}

.tag-chip.active {
  background: #3B82F6;
  color: #FFFFFF;
  border-color: #2563EB;
  font-weight: 600;
}

.popover-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 6px 8px;
  font-size: 0.82rem;
  font-family: inherit;
  border-radius: 5px;
  border: 1px solid var(--st-border-color, #475569);
  background: var(--st-background-color, #0F172A);
  color: inherit;
  margin-bottom: 12px;
  resize: vertical;
  min-height: 48px;
}

.popover-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-secondary {
  padding: 5px 10px;
  font-size: 0.78rem;
  border-radius: 5px;
  border: 1px solid var(--st-border-color, #475569);
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.btn-danger {
  padding: 5px 10px;
  font-size: 0.78rem;
  border-radius: 5px;
  border: 1px solid #EF4444;
  background: rgba(239, 68, 68, 0.15);
  color: #F87171;
  cursor: pointer;
  margin-right: auto;
}
.btn-danger:hover {
  background: rgba(239, 68, 68, 0.3);
}

.btn-primary {
  padding: 5px 12px;
  font-size: 0.78rem;
  border-radius: 5px;
  border: none;
  background: #2563EB;
  color: #FFFFFF;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:hover {
  background: #1D4ED8;
}
"""

JS_CONTENT = """
export default function (component) {
  const { data, parentElement, setStateValue } = component;
  const root = parentElement.querySelector("#annotator-root");
  const captionEl = parentElement.querySelector("#caption-content");
  const popover = parentElement.querySelector("#popover-toolbar");
  const titleEl = parentElement.querySelector("#popover-modal-title");
  const quoteEl = parentElement.querySelector("#popover-selected-quote");
  const commentInput = parentElement.querySelector("#popover-comment-input");
  const saveBtn = parentElement.querySelector("#popover-save-btn");
  const deleteBtn = parentElement.querySelector("#popover-delete-btn");
  const cancelBtn = parentElement.querySelector("#popover-cancel-btn");
  const closeBtn = parentElement.querySelector("#popover-close-btn");
  const tagChips = parentElement.querySelectorAll(".tag-chip");

  if (!root || !captionEl || !popover) return;

  const rawText = (data && data.text) ? String(data.text) : "";
  let annotations = Array.isArray(data?.annotations) ? [...data.annotations] : [];
  let selectedTag = null;
  let pendingSelection = null;
  let katexLoaded = !!window.katex;

  function loadKaTeX(onLoad) {
    if (window.katex) {
      katexLoaded = true;
      onLoad();
      return;
    }

    if (!document.getElementById("katex-css")) {
      const link = document.createElement("link");
      link.id = "katex-css";
      link.rel = "stylesheet";
      link.href = "https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css";
      document.head.appendChild(link);
    }

    if (!document.getElementById("katex-js")) {
      const script = document.createElement("script");
      script.id = "katex-js";
      script.src = "https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.js";
      script.onload = () => {
        katexLoaded = true;
        onLoad();
      };
      document.head.appendChild(script);
    } else {
      const checkInterval = setInterval(() => {
        if (window.katex) {
          clearInterval(checkInterval);
          katexLoaded = true;
          onLoad();
        }
      }, 50);
    }
  }

  // Tokenize a substring into plain, bold, and LaTeX tokens with raw character bounds
  function tokenizeText(str, baseOffset) {
    const tokens = [];
    const regex = /(\\$[^\\$]+\\$|\\*\\*[^\\*]+\\*\\*)/g;
    let last = 0;
    let match;

    while ((match = regex.exec(str)) !== null) {
      if (match.index > last) {
        tokens.push({
          type: "plain",
          text: str.substring(last, match.index),
          start: baseOffset + last,
          end: baseOffset + match.index,
        });
      }
      const tokenStr = match[0];
      const type = tokenStr.startsWith("$") ? "latex" : "bold";
      tokens.push({
        type: type,
        text: tokenStr,
        start: baseOffset + match.index,
        end: baseOffset + match.index + tokenStr.length,
      });
      last = match.index + tokenStr.length;
    }

    if (last < str.length) {
      tokens.push({
        type: "plain",
        text: str.substring(last),
        start: baseOffset + last,
        end: baseOffset + str.length,
      });
    }
    return tokens;
  }

  // Render tokens into HTML with exact data-start and data-end bounds
  function renderTokensToHtml(tokens) {
    return tokens
      .map((tok) => {
        if (tok.type === "latex") {
          const math = tok.text.slice(1, -1);
          let rendered = escapeHtml(tok.text);
          if (katexLoaded && window.katex) {
            try {
              rendered = window.katex.renderToString(math, { throwOnError: false });
            } catch (e) {
              rendered = escapeHtml(tok.text);
            }
          }
          return `<span class="raw-seg raw-latex" data-start="${tok.start}" data-end="${tok.end}">${rendered}</span>`;
        } else if (tok.type === "bold") {
          const inner = escapeHtml(tok.text.slice(2, -2));
          return `<span class="raw-seg raw-bold" data-start="${tok.start}" data-end="${tok.end}"><b>${inner}</b></span>`;
        } else {
          return `<span class="raw-seg raw-plain" data-start="${tok.start}" data-end="${tok.end}">${escapeHtml(tok.text)}</span>`;
        }
      })
      .join("");
  }

  function renderSegment(str, baseOffset) {
    const tokens = tokenizeText(str, baseOffset);
    return renderTokensToHtml(tokens);
  }

  function renderText() {
    if (!annotations || annotations.length === 0) {
      captionEl.innerHTML = renderSegment(rawText, 0);
      return;
    }

    const sorted = [...annotations].sort((a, b) => a.start_char - b.start_char);
    let html = "";
    let lastIdx = 0;

    sorted.forEach((ann) => {
      const start = Math.max(0, Math.min(rawText.length, ann.start_char));
      const end = Math.max(start, Math.min(rawText.length, ann.end_char));

      if (start > lastIdx) {
        html += renderSegment(rawText.substring(lastIdx, start), lastIdx);
      }

      const snippetHtml = renderSegment(rawText.substring(start, end), start);
      const tagText = ann.tag ? escapeHtml(ann.tag) : (ann.comment ? "Note" : "");
      const titleAttr = escapeHtml((ann.tag || "") + (ann.comment ? (ann.tag ? ": " : "") + ann.comment : ""));
      const badgeClass = ann.tag ? "span-tag-badge" : "span-tag-badge span-tag-plain";

      html += `<mark class="span-highlight" data-id="${escapeHtml(ann.id)}" data-start="${start}" data-end="${end}" title="${titleAttr}">` +
              `${snippetHtml}<span class="${badgeClass}">${tagText}` +
              `<span class="span-remove-btn" data-remove-id="${escapeHtml(ann.id)}" title="Remove annotation">✕</span></span>` +
              `</mark>`;

      lastIdx = end;
    });

    if (lastIdx < rawText.length) {
      html += renderSegment(rawText.substring(lastIdx), lastIdx);
    }

    captionEl.innerHTML = html;

    captionEl.querySelectorAll(".span-highlight").forEach((mark) => {
      mark.onclick = (e) => {
        if (e.target.classList.contains("span-remove-btn")) return;
        const annId = mark.getAttribute("data-id");
        openEditPopover(annId, mark);
      };
    });

    captionEl.querySelectorAll(".span-remove-btn").forEach((btn) => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const removeId = btn.getAttribute("data-remove-id");
        removeAnnotation(removeId);
      };
    });
  }

  function openEditPopover(annId, markEl) {
    const ann = annotations.find((a) => a.id === annId);
    if (!ann) return;

    pendingSelection = {
      ...ann,
      isEditing: true,
    };

    titleEl.textContent = "Edit span feedback";
    saveBtn.textContent = "Save changes";
    deleteBtn.style.display = "inline-block";
    quoteEl.textContent = `"${ann.selected_text}"`;
    commentInput.value = ann.comment || "";

    selectedTag = ann.tag || null;
    tagChips.forEach((c) => {
      if (selectedTag && c.getAttribute("data-tag") === selectedTag) {
        c.classList.add("active");
      } else {
        c.classList.remove("active");
      }
    });

    const rect = markEl.getBoundingClientRect();
    const rootRect = root.getBoundingClientRect();
    const topOffset = Math.max(0, rect.bottom - rootRect.top + 8);
    const leftOffset = Math.max(0, Math.min(rect.left - rootRect.left, rootRect.width - 330));

    popover.style.top = `${topOffset}px`;
    popover.style.left = `${leftOffset}px`;
    popover.style.display = "block";
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function removeAnnotation(id) {
    annotations = annotations.filter((a) => a.id !== id);
    setStateValue("annotations", annotations);
    renderText();
    hidePopover();
  }

  function hidePopover() {
    popover.style.display = "none";
    pendingSelection = null;
    commentInput.value = "";
    selectedTag = null;
    titleEl.textContent = "Add span feedback";
    saveBtn.textContent = "Add annotation";
    deleteBtn.style.display = "none";
    tagChips.forEach((c) => c.classList.remove("active"));
  }

  tagChips.forEach((chip) => {
    chip.onclick = () => {
      if (chip.classList.contains("active")) {
        chip.classList.remove("active");
        selectedTag = null;
      } else {
        tagChips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        selectedTag = chip.getAttribute("data-tag");
      }
    };
  });

  // Calculate raw character offset from DOM node and offset
  function getRawOffset(node, offset, isEnd) {
    let el = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    while (el && !el.hasAttribute("data-start") && el !== captionEl && el !== root) {
      el = el.parentElement;
    }

    if (!el || !el.hasAttribute("data-start")) {
      return -1;
    }

    const dStart = parseInt(el.getAttribute("data-start"), 10);
    const dEnd = parseInt(el.getAttribute("data-end"), 10);

    if (el.classList.contains("raw-latex")) {
      return isEnd ? dEnd : dStart;
    }

    if (el.classList.contains("raw-bold")) {
      const textOffset = node.nodeType === Node.TEXT_NODE ? offset : (isEnd ? el.textContent.length : 0);
      return Math.min(dEnd, dStart + 2 + textOffset);
    }

    const textOffset = node.nodeType === Node.TEXT_NODE ? offset : (isEnd ? el.textContent.length : 0);
    return Math.min(dEnd, dStart + textOffset);
  }

  function handleSelection() {
    try {
      const rootNode = parentElement.getRootNode();
      const selection = (rootNode && rootNode.getSelection) ? rootNode.getSelection() : window.getSelection();

      if (!selection || selection.isCollapsed || !selection.rangeCount) return;

      const range = selection.getRangeAt(0);
      let startChar = getRawOffset(range.startContainer, range.startOffset, false);
      let endChar = getRawOffset(range.endContainer, range.endOffset, true);

      // If selection was dragged in reverse
      if (startChar > endChar) {
        const tmp = startChar;
        startChar = endChar;
        endChar = tmp;
      }

      if (startChar === -1 || endChar === -1 || startChar >= endChar) {
        // Fallback: substring search
        const selText = selection.toString().trim();
        if (!selText || selText.length < 1) return;
        const found = rawText.indexOf(selText);
        if (found !== -1) {
          startChar = found;
          endChar = found + selText.length;
        } else {
          return;
        }
      }

      const selectedText = rawText.substring(startChar, endChar);
      if (!selectedText || selectedText.trim().length === 0) return;

      pendingSelection = {
        id: "ann_" + Date.now(),
        selected_text: selectedText,
        start_char: startChar,
        end_char: endChar,
        isEditing: false,
      };

      titleEl.textContent = "Add span feedback";
      saveBtn.textContent = "Add annotation";
      deleteBtn.style.display = "none";
      quoteEl.textContent = `"${selectedText}"`;
      commentInput.value = "";
      selectedTag = null;
      tagChips.forEach((c) => c.classList.remove("active"));

      let topOffset = 40;
      let leftOffset = 10;
      try {
        const rect = range.getBoundingClientRect();
        const rootRect = root.getBoundingClientRect();
        if (rect.height > 0) {
          topOffset = Math.max(0, rect.bottom - rootRect.top + 8);
          leftOffset = Math.max(0, Math.min(rect.left - rootRect.left, rootRect.width - 330));
        }
      } catch (err) {
        // use defaults
      }

      popover.style.top = `${topOffset}px`;
      popover.style.left = `${leftOffset}px`;
      popover.style.display = "block";
    } catch (err) {
      console.error("[annotator] handleSelection error", err);
    }
  }

  captionEl.addEventListener("mouseup", () => setTimeout(handleSelection, 20));
  captionEl.addEventListener("touchend", () => setTimeout(handleSelection, 20));
  captionEl.addEventListener("keyup", () => setTimeout(handleSelection, 20));

  saveBtn.onclick = () => {
    if (!pendingSelection) return;

    if (pendingSelection.isEditing) {
      const idx = annotations.findIndex((a) => a.id === pendingSelection.id);
      if (idx !== -1) {
        annotations[idx] = {
          ...annotations[idx],
          tag: selectedTag,
          comment: commentInput.value.trim(),
        };
      }
    } else {
      const newAnnotation = {
        id: pendingSelection.id,
        selected_text: pendingSelection.selected_text,
        start_char: pendingSelection.start_char,
        end_char: pendingSelection.end_char,
        tag: selectedTag,
        comment: commentInput.value.trim(),
      };
      annotations.push(newAnnotation);
    }

    setStateValue("annotations", annotations);
    renderText();
    hidePopover();
  };

  deleteBtn.onclick = () => {
    if (pendingSelection && pendingSelection.id) {
      removeAnnotation(pendingSelection.id);
    }
  };

  cancelBtn.onclick = hidePopover;
  closeBtn.onclick = hidePopover;

  loadKaTeX(() => {
    renderText();
  });
}
"""

_CAPTION_ANNOTATOR_COMPONENT = st.components.v2.component(
    "spectra_caption_annotator",
    html=HTML_CONTENT,
    css=CSS_CONTENT,
    js=JS_CONTENT,
)


def render_caption_annotator(
    caption_text: str,
    key: str,
) -> list[dict]:
    """
    Renders an interactive caption box with full KaTeX math formatting
    and Google Docs-style span highlighting & annotations.
    """
    session_data = st.session_state.get(key, {})
    current_annotations = session_data.get("annotations", [])

    result = _CAPTION_ANNOTATOR_COMPONENT(
        key=key,
        data={
            "text": caption_text,
            "annotations": current_annotations,
        },
        default={"annotations": []},
        on_annotations_change=lambda: None,
    )

    if hasattr(result, "annotations") and result.annotations is not None:
        return result.annotations
    return current_annotations
