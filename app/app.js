const ingredientGrid = document.querySelector("#ingredientGrid");
const addRow = document.querySelector("#addIngredientRow");
const ingredientInput = document.querySelector("#ingredientInput");
const toast = document.querySelector("#toast");
const briefDialog = document.querySelector("#briefDialog");
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
  remove.addEventListener("click", () => card.remove());
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

document.querySelector("#prepareBrief").addEventListener("click", () => {
  const prompt = document.querySelector("#researchPrompt").value.trim();
  const ingredients = [...ingredientGrid.querySelectorAll(".ingredient-info strong")].map((node) => node.textContent);
  if (!prompt && ingredients.length === 0) {
    notify("Add an ingredient or describe your idea first.");
    return;
  }
  document.querySelector("#briefIngredients").textContent = ingredients.join(" · ") || "No ingredients specified yet.";
  document.querySelector("#briefDescription").textContent = prompt || "No additional creative direction supplied.";
  document.querySelector("#briefTitle").textContent = prompt ? "Your creation, framed as a research question" : "A new formulation to investigate";
  briefDialog.showModal();
});

document.querySelector(".dialog-close").addEventListener("click", () => briefDialog.close());
document.querySelector("#shareButton").addEventListener("click", async () => {
  const url = window.location.href;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(url);
      notify("Workspace link copied.");
    } else {
      notify("Open this prototype locally; sharing is not connected yet.");
    }
  } catch {
    notify("Sharing is not connected in this prototype.");
  }
});
document.querySelector("#newProject").addEventListener("click", () => notify("Project creation will be added with workspace persistence."));
