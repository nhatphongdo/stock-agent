// ===========================================
// USER MANAGEMENT MODULE
// ===========================================

// User state
let users = [];
let currentUser = null;

// DOM element references (will be initialized on DOMContentLoaded)
let userAvatarBtn = null;
let userMenu = null;
let userListContainer = null;
let menuAvatar = null;
let menuUserName = null;
let menuUserEmail = null;

/**
 * Fetches users from the API and initializes the current user.
 */
async function fetchUsers() {
  try {
    const response = await fetch("/users");
    users = await response.json();

    if (users.length > 0) {
      // Load saved user or first user
      const savedUserId = localStorage.getItem("lastUserId");
      const user = users.find((u) => u.id == savedUserId) || users[0];
      selectUser(user);
    }
    renderUserList();
  } catch (error) {
    console.error("Error fetching users:", error);
  }
}

/**
 * Selects a user and updates the UI.
 * @param {Object} user - The user object to select.
 */
function selectUser(user) {
  currentUser = user;
  localStorage.setItem("lastUserId", user.id);

  if (typeof getInitials !== "function") {
    console.error("getInitials not found!");
    return;
  }
  const initials = getInitials(user.full_name);
  if (userAvatarBtn) userAvatarBtn.innerText = initials;
  if (menuAvatar) menuAvatar.innerText = initials;
  if (menuUserName) menuUserName.innerText = user.full_name;
  if (menuUserEmail) menuUserEmail.innerText = user.email;

  // Update welcome message
  const welcomeText = document.getElementById("welcome-text");
  if (welcomeText) {
    welcomeText.innerHTML = `Xin chào <b>${user.full_name}</b>! Tôi là <b>Stock Trading Assistant</b>. Hãy nhập yêu cầu phân tích để tôi có thể hỗ trợ bạn tìm kiếm cơ hội đầu tư tốt nhất.`;
  }

  // Hide menu
  if (userMenu) userMenu.classList.remove("show");
}

/**
 * Renders the user list in the user menu.
 */
function renderUserList() {
  if (!userListContainer) return;
  userListContainer.innerHTML = "";

  const template = /** @type {HTMLTemplateElement | null} */ (
    document.getElementById("user-list-item-template")
  );
  if (!template) return;

  users.forEach((user) => {
    const clone = /** @type {HTMLElement} */ (template.content.cloneNode(true));
    const item = /** @type {HTMLElement} */ (clone.querySelector(".menu-item"));
    const initialsEl = clone.querySelector(".user-initials");
    const nameEl = clone.querySelector(".user-name");

    if (initialsEl) initialsEl.textContent = getInitials(user.full_name);
    if (nameEl) nameEl.textContent = user.full_name;
    if (item) item.onclick = () => selectUser(user);

    userListContainer.appendChild(clone);
  });
}

/**
 * Initializes user module - sets up DOM references and event listeners.
 */
function initUserModule() {
  userAvatarBtn = document.getElementById("user-avatar-btn");
  userMenu = document.getElementById("user-menu");
  userListContainer = document.getElementById("user-list-container");
  menuAvatar = document.getElementById("menu-avatar");
  menuUserName = document.getElementById("menu-user-name");
  menuUserEmail = document.getElementById("menu-user-email");

  if (userAvatarBtn) {
    userAvatarBtn.onclick = (e) => {
      e.stopPropagation();
      if (userMenu) userMenu.classList.toggle("show");
    };
  }

  window.onclick = (e) => {
    // Close user menu when clicking outside
    if (userMenu && !userMenu.contains(/** @type {Node} */ (e.target))) {
      userMenu.classList.remove("show");
    }
  };

  if (userMenu) {
    userMenu.onclick = (e) => e.stopPropagation();
    // Initialize Lucide for the menu
    if (typeof lucide !== "undefined") {
      lucide.createIcons({ root: userMenu });
    }
  }

  // Fetch users on load
  fetchUsers();
}

// Initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initUserModule);
} else {
  initUserModule();
}
