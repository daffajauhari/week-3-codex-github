import { useState } from "react";
import ObjectsPage from "./pages/ObjectsPage";
import ProjectConfigPage from "./pages/ProjectConfigPage";
import "./App.css";

type Page = "objects" | "project-config";

function App() {
  const [page, setPage] = useState<Page>("objects");

  return (
    <main>
      <nav className="top-nav">
        <button
          type="button"
          className={page === "objects" ? "nav-button is-active" : "nav-button"}
          onClick={() => setPage("objects")}
        >
          Objects
        </button>
        <button
          type="button"
          className={
            page === "project-config" ? "nav-button is-active" : "nav-button"
          }
          onClick={() => setPage("project-config")}
        >
          Project Configuration
        </button>
      </nav>

      {page === "objects" ? <ObjectsPage /> : <ProjectConfigPage />}
    </main>
  );
}

export default App;
