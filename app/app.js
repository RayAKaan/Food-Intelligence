const ingredientGrid = document.querySelector("#ingredientGrid");
const addRow = document.querySelector("#addIngredientRow");
const ingredientInput = document.querySelector("#ingredientInput");
const toast = document.querySelector("#toast");
const briefDialog = document.querySelector("#briefDialog");
const prepareButton = document.querySelector("#prepareBrief");
let toastTimer;

function notify(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
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
  if (!name) {
    ingredientInput.focus();
    return;
  }
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
ingredientInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") addIngredient();
});

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

  const intro = document.querySelector(".dialog-intro");
  intro.textContent = `Draft ${brief.brief_id}. This is a structured research brief, not a simulation result.`;

  const list = document.querySelector(".brief-block ul");
  list.replaceChildren();
  brief.research_questions.forEach((question) => {
    const item = document.createElement("li");
    item.textContent = question;
    list.append(item);
  });

  const limitations = document.querySelector("#briefLimitations");
  if (limitations) limitations.remove();
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

prepareButton.addEventListener("click", async () => {
  const payload = collectBriefInput();
  if (!payload.prompt && payload.ingredients.length === 0) {
    notify("Add an ingredient or describe your idea first.");
    return;
  }

  prepareButton.disabled = true;
  prepareButton.textContent = "Structuring brief…";
  try {
    const response = await fetch("/api/research-brief", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.message || "Could not prepare the research brief.");
    renderResearchBrief(result);
    briefDialog.showModal();
  } catch (error) {
    notify(error.message || "The research API is unavailable. Start the local application server and try again.");
  } finally {
    prepareButton.disabled = false;
    prepareButton.innerHTML = 'Prepare research brief <span>↗</span>';
  }
});

document.querySelector(".dialog-close").addEventListener("click", () => briefDialog.close());
document.querySelector("#shareButton").addEventListener("click", async () => {
  const url = window.location.href;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(url);
      notify("Workspace link copied.");
    } else {
      notify("Sharing is not connected yet.");
    }
  } catch {
    notify("Sharing is not connected in this prototype.");
  }
});
document.querySelector("#newProject").addEventListener("click", () => notify("Project creation will be added with workspace persistence."));
