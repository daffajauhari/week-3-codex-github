import "./App.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function App() {
  return (
    <main>
      <header className="page-header">
        <h1>AISIMS Backend</h1>
        <p className="page-subtitle">
          The Week 2 member schedule browser was retired along with the{" "}
          <code>Member</code> table it depended on - Project Design data
          (objects, reinforcement) is now written through the Bulk Upload and
          Interactive Edit revision endpoints instead, and{" "}
          <a href={`${API_BASE_URL}/docs`}>{API_BASE_URL}/docs</a> is the
          interface for exercising them, per this week's deliverables.
        </p>
      </header>
    </main>
  );
}

export default App;
