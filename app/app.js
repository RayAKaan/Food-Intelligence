const ingredientGrid = document.querySelector("#ingredientGrid");
const addRow = document.querySelector("#addIngredientRow");
const ingredientInput = document.querySelector("#ingredientInput");
const toast = document.querySelector("#toast");
const briefDialog = document.querySelector("#briefDialog");
const prepareButton = document.querySelector("#prepareBrief");
const projectList = document.querySelector(".project-list");
const projectHeading = document.querySelector(".breadcrumbs strong");
const savedLabel = document.querySelector(".saved-label");
let toastTimer;
let activeProject = null;

function notify(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

function setSavedState(message) {
  savedLabel.textContent = message;
}

document.querySelectorAll(".nav-item").forEach((item) => {
  item.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((node) => node.classList.remove("active"));
    item.classList.add("active");
    if (item.dataset.view !== "Workbench") notify(`${item.dataset.view} is part of the workspace roadmap.`);
  });
});

document.querySelector("#addIngredientToggle").addEventListener("click", () => {
  addRow.hidden = !addRow.hidden;
  if (!addRow.hidden) ingredientInput.focus();
});
document.querySelector("#cancelIngredient").addEventListener("click", () => {
  addRow.hidden = true;
  ingredientInput.value = "";
});

function addIngredient() {
  const name = ingredientInput.value.trim();
  if (!name) { ingredientInput.focus(); return; }
  const card = document.createElement("article");
  card.className = "ingredient-card";
  const visual = document.createElement("div");
  visual.className = "ingredient-visual almond";
  const glyph = document.createElement("span");
  glyph.className = "ingredient-glyph";
  glyph.textContent = name.charAt(0).toLowerCase();
  visual.append(glyph);
  const info = document.createElement("div");
  info.className = "ingredient-info";
  const title = document.createElement("strong");
  title.textContent = name;
  const detail = document.createElement("span");
  detail.textContent = "Added to this research brief";
  info.append(title, detail);
  const amount = document.createElement("span");
  amount.className = "ingredient-amount";
  amount.textContent = "—";
  const remove = document.createElement("button");
  remove.className = "remove-ingredient";
  remove.type = "button";
  remove.setAttribute("aria-label", `Remove ${name}`);
  remove.textContent = "×";
  card.append(visual, info, amount, remove);
  ingredientGrid.append(card);
  ingredientInput.value = "";
  addRow.hidden = true;
  notify(`${name} added to the research bench.`);
}
document.querySelector("#confirmIngredient").addEventListener("click", addIngredient);
ingredientInput.addEventListener("keydown", (event) => { if (event.key === "Enter") addIngredient(); });
ingredientGrid.addEventListener("click", (event) => {
  const button = event.target.closest(".remove-ingredient");
  if (button) button.closest(".ingredient-card").remove();
});

function collectBriefInput() {
  const ingredients = [...ingredientGrid.querySelectorAll(".ingredient-card")].map((card) => ({
    name: card.querySelector(".ingredient-info strong")?.textContent?.trim() || "",
    amount: card.querySelector(".ingredient-amount")?.textContent?.trim() || null,
  }));
  return {
    prompt: document.querySelector("#researchPrompt").value.trim(),
    ingredients,
    direction: {
      experience: "Creamy centre, delicate crunch",
      flavour: "Deep cacao, warm spice",
      time: "Under 30 minutes",
    },
  };
}

function renderResearchBrief(brief) {
  document.querySelector("#briefIngredients").textContent = brief.ingredients
    .map((item) => item.amount && item.amount !== "—" ? `${item.name} (${item.amount})` : item.name)
    .join(" · ") || "No ingredients specified yet.";
  document.querySelector("#briefDescription").textContent = brief.prompt || "No additional creative direction supplied.";
  document.querySelector("#briefTitle").textContent = brief.title || "A new formulation to investigate";
  document.querySelector(".dialog-intro").textContent =
    `Draft ${brief.brief_id}. Stored in project “${activeProject.name}”. This is not a simulation result.`;
  const list = document.querySelector(".brief-block ul");
  list.replaceChildren();
  brief.research_questions.forEach((question) => {
    const item = document.createElement("li");
    item.textContent = question;
    list.append(item);
  });
  const previous = document.querySelector("#briefLimitations");
  if (previous) previous.remove();
  const block = document.createElement("div");
  block.className = "brief-block";
  block.id = "briefLimitations";
  const label = document.createElement("span");
  label.textContent = "CURRENT CAPABILITY BOUNDARY";
  const text = document.createElement("p");
  text.textContent = brief.limitations.join(" ");
  block.append(label, text);
  document.querySelector(".dialog-actions").before(block);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || "Workspace request failed.");
  return result;
}

function renderProjects(projects) {
  projectList.replaceChildren();
  projects.forEach((project) => {
    const button = document.createElement("button");
    button.className = `project-item${activeProject?.project_id === project.project_id ? " selected" : ""}`;
    button.type = "button";
    const swatch = document.createElement("span");
    swatch.className = "project-swatch copper";
    button.append(swatch, document.createTextNode(project.name));
    button.addEventListener("click", () => selectProject(project.project_id));
    projectList.append(button);
  });
}

async function refreshProjects() {
  const result = await api("/api/projects");
  renderProjects(result.projects);
  return result.projects;
}

async function selectProject(projectId) {
  const result = await api(`/api/projects/${encodeURIComponent(projectId)}`);
  activeProject = result.project;
  projectHeading.textContent = activeProject.name;
  document.querySelector(".workspace-switch span:nth-child(2)").textContent = activeProject.name;
  const projects = await refreshProjects();
  renderProjects(projects);
  const saved = await api(`/api/projects/${encodeURIComponent(projectId)}/briefs`);
  setSavedState(`${saved.briefs.length} saved research brief${saved.briefs.length === 1 ? "" : "s"}`);
}

async function createProject(name) {
  const result = await api("/api/projects", {
    method: "POST",
    body: JSON.stringify({name, description: ""}),
  });
  await selectProject(result.project.project_id);
  notify("Project created and ready.");
}

document.querySelector("#newProject").addEventListener("click", async () => {
  const name = window.prompt("Name this research project:");
  if (name === null) return;
  try {
    await createProject(name);
  } catch (error) {
    notify(error.message);
  }
});

prepareButton.addEventListener("click", async () => {
  const payload = collectBriefInput();
  if (!payload.prompt && payload.ingredients.length === 0) {
    notify("Add an ingredient or describe your idea first.");
    return;
  }
  if (!activeProject) { notify("Create or select a project first."); return; }
  prepareButton.disabled = true;
  prepareButton.textContent = "Structuring and saving…";
  setSavedState("Saving research brief…");
  try {
    const draft = await api("/api/research-brief", {method: "POST", body: JSON.stringify(payload)});
    const result = await api(`/api/projects/${encodeURIComponent(activeProject.project_id)}/briefs`, {
      method: "POST", body: JSON.stringify(payload),
    });
    renderResearchBrief(result);
    briefDialog.showModal();
    setSavedState("All changes saved");
    await refreshProjects();
  } catch (error) {
    setSavedState("Save failed");
    notify(error.message || "The research API is unavailable. Start the local application server and try again.");
  } finally {
    prepareButton.disabled = false;
    prepareButton.innerHTML = 'Prepare research brief <span>↗</span>';
  }
});

document.querySelector(".dialog-close").addEventListener("click", () => briefDialog.close());
document.querySelector("#shareButton").addEventListener("click", async () => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(window.location.href);
      notify("Workspace link copied.");
    } else notify("Sharing is not connected yet.");
  } catch { notify("Sharing is not connected in this prototype."); }
});

(async function initializeWorkspace() {
  try {
    const projects = await refreshProjects();
    if (projects.length) await selectProject(projects[0].project_id);
    else await createProject("Chocolate, reimagined");
  } catch (error) {
    setSavedState("Workspace unavailable");
    notify(error.message || "Could not load the persistent workspace.");
  }
})();
