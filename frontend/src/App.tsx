import { AppRouter } from "./utils/router";

function App() {
  return (
    // <AppSideBarProvider>
      <div className="flex w-[100vw] flex-col">
        <AppRouter />
      </div>
    // </AppSideBarProvider>
  );
}

export default App;
