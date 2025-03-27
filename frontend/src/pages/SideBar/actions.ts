interface Action {
  name: string;
  url: string;
}

export const SidebarActions = [
  { name: "Home", url: "home" },
  { name: "Categories", url: "categories" },
  { name: "My Account", url: "account" },
] as Action[];
