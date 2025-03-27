import { AppSideBarProvider } from "./pages/SideBar/main";
import { AppRouter } from "./utils/router";

function App() {
  return (
    <AppSideBarProvider>
      <div className="flex w-full flex-col p-2 gap-5">
        <AppRouter />
      </div>
    </AppSideBarProvider>
  );
}

export default App;
