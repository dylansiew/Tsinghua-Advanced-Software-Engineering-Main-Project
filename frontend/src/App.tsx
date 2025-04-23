import { AppRouter } from "./utils/router";

function App() {
  return (
    // <AppSideBarProvider>
      <div className="flex w-[100vw] flex-col gap-5">
        <AppRouter />
      </div>
    // </AppSideBarProvider>
  );
}

export default App;
